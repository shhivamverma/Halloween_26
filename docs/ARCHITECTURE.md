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

[Voice Studio: Whisper ASR → Kokoro TTS → OpenVoice Tone-Colour Conversion]
8. Voice Note / Mic   --------> POST /api/ofrendas/<id>/voice/transcribe-mic -> faster-whisper -> transcript
9. Review & Correct   --------> User reviews/edits transcript in UI review box (English / Devanagari)
10. Authorized Ref    --------> Reference audio selected/uploaded with affirmative consent
11. Convert Speech    --------> POST /api/ofrendas/<id>/voice/convert
                                ├── Base TTS Synthesis: Kokoro-82M (English 'af_heart' / Hindi 'hf_alpha')
                                └── Tone Transfer: OpenVoice V2 ToneColorConverter (Reference Speaker)
12. Play & Download   <-------- GET  /api/ofrendas/<id>/voice/audio (Stamped with RIFF INFO provenance tags)
```

## 3. Storage Hierarchy

All user data lives inside the `./data/` directory (strictly gitignored):
```
data/
└── ofrendas/
    └── <uuid4>/
        ├── ofrenda.json                   # Metadata, offerings, story text, transcripts, remembrance
        ├── photo.png|jpg|webp             # Uploaded memorial photo
        └── voice/                         # Local voice synthesis storage
            ├── reference_audio.wav        # Family-authorized reference audio clip (3-30s)
            ├── reference_meta.json        # Affirmative family permission audit record
            └── remembrance_synthesized.wav# Synthesized memorial audio
```

## 4. Subsystems

### Speech-to-Text (`app/transcribe.py`, `app/main.py`)
- Powered by `faster-whisper` using the `tiny` model with `int8` quantization on CPU (~75 MB disk, ~39 MB runtime).
- Runs in asynchronous FastAPI threadpools for fast non-blocking speech recognition.
- Automatically detects and transcribes English and Hindi microphone inputs.
- Returns transcripts to the frontend for human review and phonetic correction before voice synthesis.

### LLM Remembrance Generation (`app/llm.py`, `app/prompts.py`)
- Connects to local Ollama runtime (`http://127.0.0.1:11434`) using standard chat endpoint.
- Enforces strict factual fidelity prompts: the model is forbidden from inventing names, dates, or details not provided by the family.
- Output cleaner strips markdown hashes, bullets, and conversational AI disclaimers ("As an AI..."), capping length at 250 words.
- In case of Ollama outage or errors, graceful fallback to a deterministic remembrance template ensures 100% availability in 0.002s.

### Single-File HTML Altar Renderer (`app/render.py`, `app/templates/ofrenda.html.j2`)
- Jinja2 environment configured with strict HTML autoescaping.
- Inlines all styling, SVGs, and base64-encoded photos and remembrance audio.
- Three-tier altar hierarchy:
  - **Tier 1 (Summit):** Papel picado banner, flickering animated candles (respecting `prefers-reduced-motion`), framed portrait, name, relationship, years.
  - **Tier 2 (Heart):** Written remembrance, "In their own words" quote block, and optional voice recreation audio player.
  - **Tier 3 (Base):** Offering cards for favorite foods, drinks, music, and keepsakes.
- Includes a dedicated print stylesheet (`@media print`) and headless Chrome PDF export.

### Voice Recreation Subsystem (`app/voice/`)
- **Primary Permissive Engine:** `KokoroOpenVoiceEngine` (`app/voice/kokoro_engine.py`):
  - **Base Synthesis:** `Kokoro-82M` (Apache-2.0 License) using official `KPipeline` API. Supports English (`lang_code='a'`, voice `af_heart`) and Hindi (`lang_code='h'`, voice `hf_alpha`).
  - **Tone Color Transfer:** `OpenVoice V2 ToneColorConverter` (MIT License) transferring the vocal timbre, pitch centroid, and acoustic envelope of the family's authorized reference recording.
- **Alternative Permissive Engine:**
  - `SeedVCEngine`: Lightweight zero-shot voice conversion for English (Apache-2.0 / MIT).
- **Non-Commercial Exclusion:**
  - Non-commercial models (such as Coqui XTTS-v2 under CPML and Facebook MMS-TTS under CC-BY-NC 4.0) are **not bundled, pre-warmed, or enabled by default** in this public commercial distribution.
- **Concurrency & Re-entrancy Lock:** Backend mutex `_conversion_lock` tracks `_active_conversions`, rejecting duplicate requests with HTTP 409 Conflict.
- **Isolation:** Standalone service. If models are absent or disabled, fallback mode gracefully marks voice synthesis unavailable while preserving the rest of the application.

## 5. Security, Privacy & Network Boundaries
- **Local Network Guard (`app/net.py`):** Outbound HTTP calls to any host other than `127.0.0.1` and `localhost` are blocked at the client layer with a `ValueError`.
- **Zero Logging of User Memories:** Logging statements capture execution timing and token metrics only; story texts, audio transcripts, and voice references are strictly excluded from logs.
- **UUID Validation:** All IDs are validated as UUIDs to prevent directory traversal attacks.
- **File Upload Guard:** Strict whitelist on MIME types and extensions for photos (PNG, JPEG, WebP) and audio (WebM, WAV, MP3, OGG, M4A) with enforced size limits.
- **Unencrypted Local Disk Storage Disclosure:** All memorial files in `data/ofrendas/` (JSON, photos, audio) are stored unencrypted on disk. Operating-system level disk encryption (BitLocker, FileVault, LUKS) is strongly recommended.
- **No LAN Authentication Disclosure:** When bound to `0.0.0.0`, all endpoints are accessible to anyone on the local Wi-Fi without passwords or session authentication. For untrusted environments, bind to `127.0.0.1` or place behind an authenticating reverse proxy or VPN.

## 6. Ethical Framework & Audio Watermarking Limitations
1. **Affirmative Family Authorization:** Voice conversion endpoints reject requests unless the client submits an authorizer name and affirmative confirmation of permission.
2. **Audio Watermarking Implementation:** Generated WAV files are stamped with standard RIFF INFO metadata chunks (`IART`, `INAM`, `ICMT`, `ISFT`) marking them as `"AI-Generated Voice Recreation - For Remembrance Only"`.
3. **Watermarking Limitations:**  
   - This is a container metadata tag, **not** an inaudible acoustic frequency-domain watermark embedded into the audio samples.
   - The metadata is easily stripped or discarded if the WAV file is transcoded, converted to MP3/AAC, or uploaded to social media platforms.
   - Stamping an authorizer's name proves only that the user submitted that text in the web form; **it does NOT guarantee legal consent, authenticity, or tamper-proof provenance.** It is an advisory provenance notice for compliant media players.
4. **Deception Prevention:** The system strictly separates authentic recordings ("In their own words") from synthetic speech ("AI Voice Reading of Remembrance"). The UI never asserts or implies that the synthesized sentences were spoken by the deceased.
5. **Experimental Disclosures:** Hindi speech conversion is explicitly marked with `experimental_hindi: true` in API responses and user interfaces.
6. **Zero Cloud Leakage:** Audio files, speaker profiles, and models run exclusively in local environments; no audio data is ever transmitted to commercial speech APIs.

## 7. Hardware Requirements & Docker Notice
- **Memory Reconciliation:**
  - Python process peak during conversion: ~1.4 GB to 1.7 GB RAM.
  - OS baseline (Windows 11 / macOS / Linux): ~3.0 GB to 4.2 GB RAM.
  - Browser (Chrome/Edge with tabs): ~1.0 GB to 1.5 GB RAM.
  - Combined system working memory: ~5.5 GB to 7.4 GB RAM.
  - This reconciles why **8 GB RAM (4 CPU cores)** is the absolute minimum requirement, and **16 GB RAM** is recommended. On 4 GB systems or 512 MB cloud containers, out-of-memory crashes will occur.
- **Docker Static Review Notice:**
  - The `Dockerfile` and `docker-compose.yml` have received static code review only. Because the Docker daemon and CLI were unavailable in this Windows execution environment, **no live container build or runtime test was performed**, and build success cannot be claimed without testing on a Docker-enabled host.
