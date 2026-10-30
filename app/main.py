"""FastAPI application entry point, route definitions, and static file mount."""

from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_ollama_host, get_ollama_model
from app.net import local_client

app = FastAPI(
    title="Offline Ofrenda Keeper",
    description="Local-first Dia de los Muertos ofrenda generator",
)


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


# Static assets mount (served at /)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
