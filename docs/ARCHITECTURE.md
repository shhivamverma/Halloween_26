# Architecture: Offline Ofrenda Keeper

Offline Ofrenda Keeper is an offline-first web application designed to preserve family memories for Día de los Muertos without sending personal voices, photos, or memories to external servers.

## 1. System Overview

The application is built on three core tenets:
1. **Absolute Local Privacy:** Zero data leaves the machine. All inference (Whisper speech-to-text, Ollama LLM remembrance generation) occurs locally on CPU / local GPU.
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
```

## 3. Storage Hierarchy

All user data lives inside the `./data/` directory (strictly gitignored):
```
data/
└── ofrendas/
    └── <uuid4>/
        ├── ofrenda.json       # Metadata, offerings, story text, transcripts, remembrance
        ├── photo.png|jpg|webp # Uploaded memorial photo
        └── (temp audio is immediately unlinked after transcription)
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
  - **Tier 2 (Heart):** Written remembrance and "In their own words" quote block.
  - **Tier 3 (Base):** Offering cards for favorite foods, drinks, music, and keepsakes.
- Includes a dedicated print stylesheet (`@media print`) with exact color preservation for framing or PDF export.

## 5. Security & Isolation Boundaries
- **Local Network Guard (`app/net.py`):** Outbound HTTP calls to any host other than `127.0.0.1` and `localhost` are blocked at the client layer with a `ValueError`.
- **Zero Logging of User Memories:** Logging statements capture execution timing and token metrics only; story texts and audio transcripts are strictly excluded from logs.
- **UUID Validation:** All IDs are validated as UUIDs to prevent directory traversal attacks.
