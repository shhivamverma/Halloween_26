# Architecture: Offline Ofrenda Keeper

Offline Ofrenda Keeper is an offline-first web application designed to preserve family memories for Día de los Muertos without sending personal voices, photos, or memories to external servers.

## 1. System Overview

The application is built on three core tenets:
1. **Absolute Local Privacy:** Zero data leaves the machine. All inference (Whisper speech-to-text, Ollama LLM remembrance generation, and optional local voice synthesis) occurs locally on CPU / local GPU.
2. **Permanent Ownership:** The generated output is a single, self-contained HTML file containing inline CSS, SVG graphics, and photos encoded as base64 data URIs. No CDN links, remote fonts, or external scripts.
3. **Resilience & Fallbacks:** If the local LLM daemon is offline, a deterministic, respectful template fallback generates the remembrance seamlessly without application crashes.

## 2. End-to-End Workflow

```
[Browser UI]                  [FastAPI on localhost]                [Local models]
1. About them       --------> POST /api/ofrendas       --------> data/ofrendas/<id>/ofrenda.json
2. Offerings (foods, songs, objects)
3. Photo            --------> POST /api/ofrendas/<id>/photo ---> photo.jpg|png|webp
4. Memories:
   type text        --------> PATCH /api/ofrendas/<id>
   record voice     --------> POST /api/ofrendas/<id>/audio ---> faster-whisper -> transcript
5. Generate         --------> POST /api/ofrendas/<id>/generate-> Ollama -> remembrance
6. Preview          <-------- GET /api/ofrendas/<id>/page       (Jinja2 -> one HTML file)
7. Save             Download HTML | Print/Save as PDF | Export ZIP

[Optional Add-On: Local Voice Recreation]
8. Reference Audio  --------> POST /api/ofrendas/<id>/voice/reference (Requires family consent)
9. Synthesize Voice --------> POST /api/ofrendas/<id>/voice/synthesize -> XTTS-v2 / OpenVoice V2
10. Preview & Play  <-------- GET  /api/ofrendas/<id>/voice/audio     (Watermarked as AI recreation)
```

## 3. Storage Hierarchy

All user data lives inside the `./data/` directory (strictly gitignored):
```
data/
└── ofrendas/
    └── <uuid4>/
        ├── ofrenda.json                   # Metadata, offerings, story text, transcripts, remembrance
        ├── photo.png|jpg|webp             # Uploaded memorial photo
        ├── (temp audio is immediately unlinked after transcription)
        └── voice/                         # Optional local voice synthesis storage
            ├── reference_audio.wav        # Family-authorized reference audio clip (3-30s)
            ├── speaker_profile.json       # Extracted speaker embeddings / conditioning latents
            ├── remembrance_synthesized.wav# Synthesized memorial audio
            └── consent_log.json           # Affirmative family permission audit record
```

## 4. Subsystems

### Speech-to-Text (`app/transcribe.py`)
- Powered by `faster-whisper` using the `base` model with `int8` quantization on CPU.
- Runs in a synchronous FastAPI endpoint executed inside the threadpool to prevent blocking the async event loop.
- Browser audio (WebM/Opus), WAV, MP3, and M4A are supported.
- Temporary files are immediately deleted unless the `KEEP_AUDIO=1` debug flag is active.

### LLM Remembrance Generation (`app/llm.py`, `app/prompts.py`)
- Connects to local Ollama runtime (`http://127.0.0.1:11434`) using standard chat endpoint.
- Enforces strict factual fidelity prompts: the model is forbidden from inventing names, dates, or details not provided by the family.
- Output cleaner strips markdown hashes, bullets, and conversational AI disclaimers ("As an AI..."), capping length at 250 words.
- In case of Ollama outage or errors, graceful fallback to a deterministic remembrance template ensures 100% availability.

### Single-File HTML Altar Renderer (`app/render.py`, `app/templates/ofrenda.html.j2`)
- Jinja2 environment configured with strict HTML autoescaping.
- Inlines all styling, SVGs, and base64-encoded photos.
- Three-tier altar hierarchy:
  - **Tier 1 (Summit):** Papel picado banner, flickering animated candles (respecting `prefers-reduced-motion`), framed portrait, name, relationship, years.
  - **Tier 2 (Heart):** Written remembrance, "In their own words" quote block, and optional voice recreation audio player.
  - **Tier 3 (Base):** Offering cards for favorite foods, drinks, music, and keepsakes.
- Includes a dedicated print stylesheet (`@media print`) with exact color preservation for framing or PDF export.

### Optional Voice Recreation Subsystem (`app/voice/`)
- **Engine Interface:** Decoupled `VoiceSynthesisEngine` abstraction supporting **Coqui XTTS-v2** (high fidelity, 17 languages including `es` and `en`) and **MyShell OpenVoice V2** (lightweight CPU-friendly option).
- **Speaker Profile Conditioning:** Reference audio clips are processed locally to compute speaker latents saved in `voice/speaker_profile.json`.
- **Language Alignment:** Synthesis strictly validates that the requested language matches the model's actual supported set (e.g. `es`, `en`, `fr`, `de`, `it`, `pt`).
- **Isolation:** Operates as an optional plugin. If voice dependencies (`requirements-voice.txt`) are not installed, the core app runs smoothly with voice synthesis safely marked unavailable.

## 5. Security & Isolation Boundaries
- **Local Network Guard (`app/net.py`):** Outbound HTTP calls to any host other than `127.0.0.1` and `localhost` are blocked at the client layer with a `ValueError`.
- **Zero Logging of User Memories:** Logging statements capture execution timing and token metrics only; story texts, audio transcripts, and voice references are strictly excluded from logs.
- **UUID Validation:** All IDs are validated as UUIDs to prevent directory traversal attacks.

## 6. Ethical & Safety Framework for Voice Recreation
1. **Affirmative Family Authorization:** Voice cloning endpoints reject requests unless the client submits a certified consent statement acknowledging family permission.
2. **Prominent Provenance Labeling:** Generated audio is tagged in file metadata and labeled in the UI as `"AI-Generated Voice Recreation - Memorial Simulation"`.
3. **Deception Prevention:** The system strictly separates authentic recordings ("In their own words") from synthetic speech ("AI Voice Reading of Remembrance"). The UI never asserts or implies that the synthesized sentences were spoken by the deceased.
4. **Zero Cloud Leakage:** Audio files, speaker profiles, and models run exclusively in local environments; no audio data is ever transmitted to commercial speech APIs.
