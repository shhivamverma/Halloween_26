"""FastAPI application entry point, route definitions, and static file mount."""

import io
import logging
import os
from pathlib import Path
import re
import tempfile
from typing import List, Optional
import uuid
import zipfile

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_max_audio_mb, get_max_photo_mb, get_ollama_host, get_ollama_model
from app.llm import generate_remembrance
from app.net import local_client
from app.render import render_ofrenda
from app.schemas import (
    GenerateRequest,
    OfrendaCreate,
    OfrendaRecord,
    OfrendaSummary,
    OfrendaUpdate,
    VoiceConsentRecord,
    VoiceProfileMetadata,
    VoiceSynthesisRequest,
)
from app.storage import Storage
import app.transcribe as transcribe_module
from app.voice import get_voice_service

# Configure privacy-safe logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ofrenda")

app = FastAPI(
    title="Offline Ofrenda Keeper",
    description="Local-first Dia de los Muertos ofrenda generator",
)


def get_storage() -> Storage:
    """Return configured storage instance."""
    return Storage()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return JSON error for HTTP exceptions without exposing stack traces."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return JSON 422 error for Pydantic validation failures."""
    errors = exc.errors()
    msg = "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in errors) if errors else "Validation failed"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": f"Validation error: {msg}"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return friendly JSON error for any unexpected server exceptions."""
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    msg = str(exc) or "An internal server error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": msg, "detail": msg},
    )


@app.get("/api/health")
def health_check():
    """Report status of Ollama, Whisper, installed models, and local voice synthesis. Never raises 500."""
    whisper_available = False
    try:
        import faster_whisper  # noqa: F401

        whisper_available = True
    except Exception:
        whisper_available = False

    ollama_host = get_ollama_host()
    ollama_available = False
    installed_models: list[str] = []

    try:
        with local_client(timeout=2.0) as client:
            resp = client.get(f"{ollama_host}/api/tags")
            if resp.status_code == 200:
                ollama_available = True
                data = resp.json()
                installed_models = [m["name"] for m in data.get("models", []) if "name" in m]
    except Exception:
        ollama_available = False

    overall_status = "ok" if (ollama_available and whisper_available) else "degraded"

    voice_status = get_voice_service().get_engine_status()

    return {
        "status": overall_status,
        "ollama": ollama_available,
        "whisper": whisper_available,
        "model": get_ollama_model(),
        "models": installed_models,
        "voice": voice_status,
        "voice_synthesis": voice_status,
    }


# --- Ofrenda CRUD Endpoints ---


@app.post("/api/demo/seed", response_model=OfrendaRecord)
def seed_demo_endpoint():
    """Seed or reset the fictional 'Abuela Rosa' demo ofrenda with photo, offerings, remembrance, and voice."""
    from app.demo import seed_demo_ofrenda

    storage = get_storage()
    return seed_demo_ofrenda(storage)


@app.post("/api/ofrendas", response_model=OfrendaRecord, status_code=status.HTTP_201_CREATED)
def create_ofrenda(payload: OfrendaCreate):
    """Create a new ofrenda record on disk."""
    storage = get_storage()
    return storage.create(payload)


@app.get("/api/ofrendas", response_model=List[OfrendaSummary])
def list_ofrendas():
    """List all saved ofrendas."""
    storage = get_storage()
    return storage.list()


@app.get("/api/ofrendas/{id}", response_model=OfrendaRecord)
def get_ofrenda(id: uuid.UUID):
    """Fetch an ofrenda by UUID."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")
    return record


@app.patch("/api/ofrendas/{id}", response_model=OfrendaRecord)
def update_ofrenda(id: uuid.UUID, updates: OfrendaUpdate):
    """Update fields on an ofrenda record."""
    storage = get_storage()
    updated = storage.update(str(id), updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")
    return updated


@app.delete("/api/ofrendas/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ofrenda(id: uuid.UUID):
    """Delete an ofrenda folder from disk."""
    storage = get_storage()
    deleted = storage.delete(str(id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Photo Upload Endpoint ---

ALLOWED_PHOTO_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}


@app.post("/api/ofrendas/{id}/photo")
async def upload_photo(id: uuid.UUID, file: UploadFile = File(...)):
    """Upload photo (PNG, JPEG, WebP) for an ofrenda."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    content_type = (file.content_type or "").lower()
    ext = ALLOWED_PHOTO_TYPES.get(content_type)
    if not ext and file.filename:
        suffix = Path(file.filename).suffix.lower().lstrip(".")
        if suffix in ("png", "jpg", "jpeg", "webp"):
            ext = "jpg" if suffix == "jpeg" else suffix

    if not ext:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported media type. Only PNG, JPEG, and WebP are allowed.",
        )

    content = await file.read()
    max_bytes = get_max_photo_mb() * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Photo exceeds maximum size of {get_max_photo_mb()} MB",
        )

    updated_record = storage.save_photo(str(id), content, ext)
    return {
        "status": "ok",
        "id": str(id),
        "photo": updated_record.photo,
    }


# --- Audio Upload & Transcription Endpoint ---

ALLOWED_AUDIO_EXTENSIONS = {".webm", ".ogg", ".wav", ".mp3", ".m4a"}
ALLOWED_AUDIO_MIMES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "video/webm",
}


@app.post("/api/ofrendas/{id}/audio")
def upload_audio(id: uuid.UUID, file: UploadFile = File(...)):
    """Upload voice note, transcribe locally using faster-whisper, and append to transcript."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    ext = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()

    if ext not in ALLOWED_AUDIO_EXTENSIONS and content_type not in ALLOWED_AUDIO_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported audio format. Allowed: webm, ogg, wav, mp3, m4a.",
        )

    audio_bytes = file.file.read()
    max_bytes = get_max_audio_mb() * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio exceeds maximum size of {get_max_audio_mb()} MB",
        )

    suffix = ext if ext in ALLOWED_AUDIO_EXTENSIONS else ".webm"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)

    keep_audio = os.environ.get("KEEP_AUDIO", "0") in ("1", "true", "True")

    try:
        temp_file.write(audio_bytes)
        temp_file.close()

        result = transcribe_module.transcribe(temp_path, language_hint=record.language)
        text = result.get("text", "").strip()

        if not text:
            return {
                "text": "",
                "language": result.get("language", record.language),
                "duration": result.get("duration", 0.0),
                "warning": "No speech detected in audio note.",
            }

        existing_transcript = record.transcript.strip() if record.transcript else ""
        if existing_transcript:
            new_transcript = f"{existing_transcript}\n\n{text}"
        else:
            new_transcript = text

        storage.update(str(id), {"transcript": new_transcript})

        return {
            "text": text,
            "language": result.get("language", record.language),
            "duration": result.get("duration", 0.0),
        }
    finally:
        if not keep_audio and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


# --- Remembrance Generation Endpoint ---


@app.post("/api/ofrendas/{id}/generate")
def generate_ofrenda_remembrance(id: uuid.UUID, body: Optional[GenerateRequest] = None):
    """Generate remembrance for ofrenda using local Ollama model or fallback template."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    model = body.model if body and body.model else None
    remembrance, generated_by, model_used = generate_remembrance(record, model=model)

    storage.update(
        str(id),
        {
            "remembrance": remembrance,
            "generated_by": generated_by,
            "model_used": model_used,
        },
    )

    return {
        "remembrance": remembrance,
        "generated_by": generated_by,
        "model_used": model_used,
    }


# --- Optional AI Voice Recreation Endpoints ---


@app.post("/api/ofrendas/{id}/voice/reference", response_model=VoiceProfileMetadata)
def upload_voice_reference(
    id: uuid.UUID,
    file: UploadFile = File(...),
    authorized_by: str = Form(...),
    confirmed_permission: bool = Form(...),
):
    """Upload family-authorized reference voice recording for voice synthesis."""
    if not confirmed_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Affirmative family authorization is strictly required for voice recreation.",
        )

    if not authorized_by or not authorized_by.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorizing family member name is required.",
        )

    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in ("wav", "mp3", "webm", "ogg", "m4a"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported audio format for reference voice. Allowed: wav, mp3, webm, ogg, m4a.",
        )

    audio_bytes = file.file.read()
    max_bytes = get_max_audio_mb() * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio exceeds maximum size of {get_max_audio_mb()} MB",
        )

    consent = VoiceConsentRecord(
        authorized_by=authorized_by.strip(),
        confirmed_permission=True,
    )

    voice_service = get_voice_service()
    profile = voice_service.process_and_save_reference(
        ofrenda_id=str(id),
        audio_bytes=audio_bytes,
        ext=ext,
        consent=consent,
        storage=storage,
    )
    return profile


@app.post("/api/ofrendas/{id}/voice/synthesize", response_model=VoiceProfileMetadata)
def synthesize_voice(id: uuid.UUID, request: VoiceSynthesisRequest):
    """Synthesize remembrance speech using reference voice."""
    if not request.consent.confirmed_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Affirmative family permission is strictly required for voice recreation.",
        )

    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    if not record.remembrance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No remembrance text found. Please generate a remembrance first before synthesizing voice.",
        )

    voice_service = get_voice_service()
    try:
        profile = voice_service.synthesize_remembrance(
            ofrenda_id=str(id),
            language=request.language,
            speed=request.speed,
            consent=request.consent,
            storage=storage,
        )
        return profile
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except (RuntimeError, MemoryError) as run_err:
        logger.error("Voice synthesis runtime error: %s", run_err, exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(run_err))
    except Exception as exc:
        logger.error("Voice synthesis unexpected error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice synthesis error: {str(exc) or 'Internal error during voice generation.'}",
        )


@app.post("/api/ofrendas/{id}/voice/convert")
def convert_speech_to_speech(
    id: uuid.UUID,
    file: UploadFile = File(...),
    authorized_by: str = Form(...),
    confirmed_permission: bool = Form(...),
    language: Optional[str] = Form(None),
):
    """Speech-to-Speech deceased voice conversion pipeline.

    Accepts user microphone audio, transcribes it locally with faster-whisper,
    and converts speech conditioned on the uploaded family-authorized reference voice.
    Supports Hindi (hi), English (en), and Spanish (es).
    """
    if not confirmed_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Affirmative family authorization is strictly required for voice conversion.",
        )
    if not authorized_by or not authorized_by.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The authorizing family member name must be provided.",
        )

    ext = Path(file.filename or "speech.wav").suffix.lower()
    if ext not in (".wav", ".mp3", ".webm", ".ogg", ".m4a"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported audio format for microphone recording. Allowed: wav, mp3, webm, ogg, m4a.",
        )

    audio_bytes = file.file.read()
    if len(audio_bytes) > get_max_audio_mb() * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Microphone audio recording exceeds {get_max_audio_mb()}MB limit.",
        )

    storage = get_storage()
    consent = VoiceConsentRecord(
        authorized_by=authorized_by.strip(),
        confirmed_permission=True,
    )

    voice_service = get_voice_service()
    try:
        result = voice_service.convert_speech_to_speech(
            ofrenda_id=str(id),
            user_audio_bytes=audio_bytes,
            ext=ext,
            consent=consent,
            storage=storage,
            target_language=language,
        )
        return result
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except (RuntimeError, MemoryError) as run_err:
        logger.error("Voice conversion runtime error: %s", run_err, exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(run_err))
    except Exception as exc:
        logger.error("Voice conversion unexpected error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice conversion error: {str(exc) or 'Internal error during speech conversion.'}",
        )


@app.get("/api/ofrendas/{id}/voice/audio")
def get_synthesized_voice_audio(id: uuid.UUID):
    """Stream synthesized memorial voice recreation audio with byte-range support."""
    storage = get_storage()
    synth_path = storage.get_synthesized_voice_path(str(id))
    if not synth_path or not synth_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Synthesized voice audio not found.")

    return FileResponse(
        path=synth_path,
        media_type="audio/wav",
        headers={
            "X-AI-Voice-Recreation": "Memorial-Simulation",
            "X-Provenance": "Not spoken by deceased",
        },
    )


@app.get("/api/ofrendas/{id}/voice/download")
def download_synthesized_voice_audio(id: uuid.UUID):
    """Download synthesized memorial voice audio file with attachment header."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    synth_path = storage.get_synthesized_voice_path(str(id))
    if not synth_path or not synth_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Synthesized voice audio not found.")

    safe_name = re.sub(r"[^\w\-]", "_", record.name.strip()) or "ofrenda"
    filename = f"{safe_name}_AI_Voice_Recreation.wav"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "audio/wav",
        "X-AI-Voice-Recreation": "Memorial-Simulation",
    }
    return Response(content=synth_path.read_bytes(), media_type="audio/wav", headers=headers)


@app.delete("/api/ofrendas/{id}/voice", response_model=OfrendaRecord)
def delete_voice_profile(id: uuid.UUID):
    """Delete voice profile, reference recordings, and synthesized audio for an ofrenda."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    return storage.delete_voice_profile(str(id))


# --- Ofrenda HTML Render & Download Endpoints ---


@app.get("/api/ofrendas/{id}/page", response_class=HTMLResponse)
def view_ofrenda_page(id: uuid.UUID):
    """Render self-contained HTML altar page."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    html_content = render_ofrenda(record, storage=storage)
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/api/ofrendas/{id}/download")
def download_ofrenda_page(id: uuid.UUID):
    """Download self-contained HTML altar page with attachment header."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    html_content = render_ofrenda(record, storage=storage)
    safe_name = re.sub(r"[^\w\-]", "_", record.name.strip()) or "ofrenda"
    filename = f"{safe_name}_ofrenda.html"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "text/html; charset=utf-8",
    }
    return Response(content=html_content, media_type="text/html", headers=headers)


# --- ZIP Export Endpoint ---


@app.get("/api/ofrendas/{id}/export.zip")
def export_ofrenda_zip(id: uuid.UUID):
    """Export complete ofrenda package as ZIP."""
    storage = get_storage()
    record = storage.get(str(id))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ofrenda not found")

    folder = storage.get_folder(str(id))
    html_content = render_ofrenda(record, storage=storage)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. ofrenda.html
        zf.writestr("ofrenda.html", html_content.encode("utf-8"))

        # 2. ofrenda.json
        zf.writestr("ofrenda.json", record.model_dump_json(indent=2).encode("utf-8"))

        # 3. transcript.txt
        transcript_parts = []
        if record.story_text:
            transcript_parts.append(f"WRITTEN MEMORIES:\n{record.story_text}")
        if record.transcript:
            transcript_parts.append(f"VOICE TRANSCRIPT:\n{record.transcript}")
        if record.remembrance:
            transcript_parts.append(f"REMEMBRANCE:\n{record.remembrance}")
        transcript_content = "\n\n---\n\n".join(transcript_parts)
        zf.writestr("transcript.txt", transcript_content.encode("utf-8"))

        # 4. photo file if present
        if record.photo:
            photo_path = folder / record.photo
            if photo_path.exists():
                zf.writestr(record.photo, photo_path.read_bytes())

        # 5. synthesized voice audio if present
        synth_path = storage.get_synthesized_voice_path(str(id))
        if synth_path and synth_path.exists():
            zf.writestr("remembrance_synthesized.wav", synth_path.read_bytes())

        # 6. reference voice recording if present
        ref_path = storage.get_reference_audio_path(str(id))
        if ref_path and ref_path.exists():
            zf.writestr(ref_path.name, ref_path.read_bytes())

    buf.seek(0)
    safe_name = re.sub(r"[^\w\-]", "_", record.name.strip()) or "ofrenda"
    filename = f"{safe_name}_export.zip"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/zip",
    }
    return Response(content=buf.getvalue(), media_type="application/zip", headers=headers)


# Static assets mount (served at /)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
