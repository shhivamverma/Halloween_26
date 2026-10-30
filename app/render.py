"""Jinja2 template renderer for standalone, self-contained ofrenda altar pages."""

import base64
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas import OfrendaRecord
from app.storage import Storage

# Path to templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Jinja2 environment with HTML autoescaping enabled
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)


def _get_photo_data_uri(ofrenda_id: str, photo_filename: Optional[str], storage: Optional[Storage] = None) -> Optional[str]:
    """Load photo from disk and convert to base64 data URI."""
    if not photo_filename:
        return None

    store = storage or Storage()
    folder = store.get_folder(ofrenda_id)
    photo_path = folder / photo_filename
    if not photo_path.exists():
        return None

    ext = photo_path.suffix.lower().lstrip(".")
    mime = "image/png"
    if ext in ("jpg", "jpeg"):
        mime = "image/jpeg"
    elif ext == "webp":
        mime = "image/webp"

    raw_bytes = photo_path.read_bytes()
    b64_str = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mime};base64,{b64_str}"


def _get_voice_data_uri(ofrenda_id: str, storage: Optional[Storage] = None) -> Optional[str]:
    """Load synthesized remembrance voice audio from disk and convert to base64 data URI."""
    if not ofrenda_id:
        return None
    store = storage or Storage()
    voice_path = store.get_synthesized_voice_path(ofrenda_id)
    if not voice_path or not voice_path.exists():
        return None
    raw_bytes = voice_path.read_bytes()
    b64_str = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:audio/wav;base64,{b64_str}"


def render_ofrenda(ofrenda: Any, storage: Optional[Storage] = None) -> str:
    """Render self-contained HTML for an ofrenda without any external network references."""
    template = jinja_env.get_template("ofrenda.html.j2")

    ofrenda_id = getattr(ofrenda, "id", None) or (ofrenda.get("id") if isinstance(ofrenda, dict) else "")
    photo_file = getattr(ofrenda, "photo", None) or (ofrenda.get("photo") if isinstance(ofrenda, dict) else None)

    photo_uri = None
    if ofrenda_id and photo_file:
        try:
            photo_uri = _get_photo_data_uri(str(ofrenda_id), photo_file, storage)
        except Exception:
            photo_uri = None

    voice_audio_uri = None
    if ofrenda_id:
        try:
            voice_audio_uri = _get_voice_data_uri(str(ofrenda_id), storage)
        except Exception:
            voice_audio_uri = None

    return template.render(
        ofrenda=ofrenda,
        photo_uri=photo_uri,
        voice_audio_uri=voice_audio_uri,
    )
