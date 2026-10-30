"""FastAPI application entry point, route definitions, and static file mount."""

from pathlib import Path
from typing import List
import uuid

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_max_photo_mb, get_ollama_host, get_ollama_model
from app.net import local_client
from app.schemas import OfrendaCreate, OfrendaRecord, OfrendaSummary, OfrendaUpdate
from app.storage import Storage

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
        content={"error": str(exc.detail)},
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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An internal server error occurred."},
    )


@app.get("/api/health")
def health_check():
    """Report status of Ollama, Whisper, and installed models. Never raises 500."""
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

    return {
        "status": overall_status,
        "ollama": ollama_available,
        "whisper": whisper_available,
        "model": get_ollama_model(),
        "models": installed_models,
    }


# --- Ofrenda CRUD Endpoints ---


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


# Static assets mount (served at /)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
