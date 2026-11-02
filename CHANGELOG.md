# Changelog: Offline Ofrenda Keeper

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-rc1] - 2026-11-02

### Added
- **Whisper ASR → Kokoro TTS → OpenVoice Tone-Colour Conversion:**
  - Integrated local speech transcription using `faster-whisper` (`tiny` and `base`).
  - Added editable transcript review box in Step 3 for human fidelity and Devanagari/English correction.
  - Primary voice synthesis engine powered by `Kokoro-82M` (Apache-2.0 License) via official `KPipeline` API.
  - Vocal timbre and tone-colour transfer using `OpenVoice V2 ToneColorConverter` (MIT License) with dual source/target speaker embeddings.
  - Support for English (`af_heart`) and native Hindi phonemization (`hf_alpha`).
  - Explicit `experimental_hindi: true` flag and UI badge for Hindi tone transfer transparency.
  - Seed-VC preserved as an alternative English zero-shot voice conversion engine.
- **Security & Privacy Hardening:**
  - Secure default network binding: server binds strictly to `127.0.0.1:8000` (loopback only).
  - Explicit opt-in for local Wi-Fi sharing (`--lan` flag or `ALLOW_LAN=1`) with mandatory unauthenticated security banner.
  - Backend affirmative consent enforcement requiring family authorizer name and permission confirmation.
  - Thread-safe concurrency lock on voice conversion returning `HTTP 409 Conflict`.
  - Stamped RIFF INFO metadata provenance tags (`IART`, `INAM`, `ICMT`, `ISFT`).
  - Path traversal protection blocking `../` traversal attempts.
  - Whitelist validation for photo uploads (PNG, JPEG, WebP) and audio uploads (WebM, WAV, MP3, OGG, M4A).
- **Single-File Standalone Exports:**
  - Single-file HTML export with embedded base64 photographs and audio (0 remote URLs).
  - Headless Chrome print-to-PDF export with dedicated `@media print` styling.
  - Full memorial ZIP archive export with metadata, transcripts, photos, and synthesized WAVs.
- **Licensing & Documentation:**
  - Complete machine-readable `THIRD_PARTY_LICENSES.json` auditing all 193 packages and model weights.
  - Dedicated `docs/INSTALLATION.md`, `docs/PRIVACY.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.
  - Windows PowerShell setup scripts (`scripts/fetch_models.ps1`, `scripts/run_production.bat`).
  - GitHub Actions CI workflow for automated testing on push and pull requests.
  - GitHub issue templates and PR template.

### Changed
- Excluded non-commercial models (`Coqui XTTS-v2` under CPML and `Facebook MMS-TTS` under CC-BY-NC 4.0) from default distribution, pre-warming, and `requirements.txt`.
- Reconciled hardware memory recommendations: 8 GB RAM minimum with OS/browser overhead, 16 GB recommended; documented 512 MB cloud container OOM limitation.
- Configured single-worker uvicorn (`--workers 1`) to eliminate memory duplication during PyTorch CPU inference.

### Fixed
- Fixed Windows PowerShell console encoding for Devanagari text streams.
- Fixed PyAV audio decoding compatibility by pinning `av<14`.
- Replaced direct speech-to-speech terminology with grounded ASR $\to$ TTS $\to$ tone conversion pipeline.
- Fixed mock voice engine Hindi experimental flag propagation in unit tests.

