# Architectural Decisions Log

This document records architectural decisions, assumptions, and simplifications made during the implementation of Offline Ofrenda Keeper.

## Decision Log

### 1. Workspace and Template Structure
- **Decision:** Place `templates/` and `static/` inside `app/` (`app/templates/` and `app/static/`) while allowing configuration via `app/config.py` with relative path fallback.
- **Reason:** Keeps the Python application package self-contained and clean, matching `pathlib.Path("app/static")` referenced in spec test requirements.

### 2. Audio Processing Threadpool
- **Decision:** Use standard sync `def` handler in FastAPI for audio transcription endpoint (`/api/ofrendas/{id}/audio`).
- **Reason:** FastAPI automatically executes synchronous route handlers in an `anyio` threadpool worker, avoiding blocking the async event loop during CPU-intensive faster-whisper inference.

### 3. Strict Offline Network Guard
- **Decision:** Refuse any outbound HTTP connection to addresses other than `127.0.0.1` and `localhost` at the client creation and request layer.
- **Reason:** Ensures zero data leakage and 100% offline compliance as required by the challenge.

### 4. Audio Decoding Compatibility (PyAV)
- **Decision:** Pin `av>=12.0.0,<14.0.0` in `requirements.txt`.
- **Reason:** Newer versions of PyAV (14+) removed the `metadata_errors` argument from `av.open()`, causing an unhandled `TypeError` inside `faster_whisper/audio.py`. Pinning `av<14` ensures reliable offline decoding for browser audio (WebM/Opus, OGG, WAV, MP3, M4A).
