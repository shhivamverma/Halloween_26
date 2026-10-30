# Local AI Voice Recreation: Architectural Blueprint & Implementation Plan

> **Feature Status:** Optional Add-On Subsystem  
> **Ethics Mandate:** Strict Family Authorization Required • 100% Offline • Deception Prohibited  
> **Scope:** Architecture, dependencies, licensing, folder structure, and execution roadmap (without altering existing core features).

---

## 1. Executive Summary & Philosophy

Offline Ofrenda Keeper honors deceased loved ones by weaving memories, offerings, and written remembrances into a digital altar. The **Voice Recreation Feature** introduces an *optional, local-only speech synthesis subsystem* that can vocalize the AI-generated remembrance using a voice profile synthesized from family-provided archival recordings (e.g. old cassette tapes, phone voice notes, or home videos).

### Non-Negotiable Ethical & Security Tenets
1. **Explicit Family Permission Gate:** Voice synthesis cannot be invoked without explicit, affirmative consent by the user certifying family authorization.
2. **Anti-Deception & Clear Provenance:** Synthesized speech must be prominently watermarked and labeled as `"AI-Generated Voice Recreation - Memorial Simulation"`. The system will **never** imply or claim that the deceased spoke those exact words. Genuine verbatim quotes from voice recordings remain strictly separated in the "In their own words" section.
3. **100% Local Processing:** Reference audio, speaker embedding latents, and generated speech never leave the user's computer. Outbound network requests remain strictly guarded to `127.0.0.1` / `localhost`.
4. **No Degradation of Core App:** The voice synthesis feature is completely decoupled and optional. Users on lower-spec machines or without reference recordings retain full access to all existing features without downloading multi-gigabyte TTS weights.

---

## 2. Open-Weight Model Evaluation & License Matrix

| Model | Architecture | Zero-Shot Cloning Quality | Languages Supported | License | Resource Footprint | Verdict |
|---|---|---|---|---|---|---|
| **Coqui XTTS-v2** | Autoregressive + Diffusion Latent Matching | **High** (exceptional naturalness, captures emotional cadence) | 17 languages: `en`, `es`, `fr`, `de`, `it`, `pt`, `pl`, `tr`, `ru`, `nl`, `cs`, `ar`, `zh`, `ja`, `hu`, `ko`, `hi` | **Coqui Public Model License (CPML)** *(Non-commercial, personal/research use only)* | Model: ~1.8 GB<br>RAM: ~4-6 GB<br>GPU: CUDA supported; CPU ~30-60s for 150 words | **Primary Choice for Quality:** Matches English & Spanish native ofrenda needs; excellent prosody. |
| **MyShell OpenVoice V2** | Decoupled Base TTS (MeloTTS) + Tone Color Converter | **Good to High** (very clear tone matching, less prosody cloning) | 6 languages: `en`, `es`, `fr`, `zh`, `ja`, `ko` | **CC BY-NC 4.0** (OpenVoice V2) / **MIT** (MeloTTS) | Model: ~450 MB<br>RAM: ~2 GB<br>CPU: Fast (~10-15s) | **Strong Alternative for Low-Spec / CPU:** Lightweight and faster CPU inference. |
| **F5-TTS / E2-TTS** | Non-autoregressive Flow Matching | **Very High** | Primarily `en`, `zh` (limited `es`) | **MIT** | Model: ~1.5 GB<br>VRAM: >6 GB (Slow on CPU) | **Deferred:** Spanish support is currently experimental. |
| **Kokoro / Piper** | Single/Multi-speaker VITS / StyleTTS | Fixed voices only (no reference cloning) | Multiple | Apache 2.0 / MIT | Lightweight | **Not Applicable:** Cannot clone voice from user reference audio. |

### Selected Architecture Recommendation
We adopt an **Adapter Pattern (`VoiceSynthesisEngine`)** that defines a standard interface:
1. **Engine Implementation:** Default to **XTTS-v2** for highest emotional fidelity and native English + Spanish support. Provide a CPU-optimized fallback to **OpenVoice V2 / MeloTTS** for constrained machines.
2. **Testing Engine:** A lightweight **`MockVoiceEngine`** bundled in the repository for unit and integration testing without requiring GPU hardware or 2 GB downloads.

### Licensing & Legal Constraints
- **CPML (XTTS-v2)** and **CC BY-NC 4.0 (OpenVoice V2)** both explicitly permit **personal, non-commercial, and open research use**, which aligns with Hacktoberfest educational submissions and personal family memorialization.
- Commercial redistribution is prohibited by these licenses. This must be prominently documented in `docs/DECISIONS.md` and `LICENSE-MODELS.md`.

---

## 3. Storage Hierarchy & Data Model

All voice assets reside strictly within the existing `./data/` isolation boundary under the specific ofrenda's folder:

```
data/
└── ofrendas/
    └── <uuid4>/
        ├── ofrenda.json                   # Updated with voice metadata
        ├── photo.png                      # Memorial portrait
        └── voice/
            ├── reference_audio.wav        # Family-provided reference recording (3-30s)
            ├── speaker_profile.json       # Speaker embedding latents / conditioning tensors
            ├── remembrance_synthesized.wav# Generated synthetic memorial audio
            └── consent_log.json           # Cryptographic timestamp of affirmative family authorization
```

### Data Model Schema Updates (`app/schemas.py`)

```python
class VoiceConsentRecord(BaseModel):
    """Audit record certifying explicit family authorization for voice synthesis."""
    authorized_by: str = Field(..., max_length=100, description="Name or relationship of authorizing family member")
    confirmed_permission: bool = Field(..., description="Affirmative confirmation of right to use recordings")
    timestamp: str = Field(..., description="ISO-8601 timestamp of consent")
    statement: str = Field(
        default="I certify that I have explicit family authorization to generate an AI voice recreation for memorial purposes."
    )

class VoiceSynthesisRequest(BaseModel):
    """Payload to trigger voice recreation synthesis."""
    language: Literal["en", "es", "fr", "de", "it", "pt"] = "es"
    speed: float = Field(default=1.0, ge=0.7, le=1.3)
    consent: VoiceConsentRecord

class VoiceProfileMetadata(BaseModel):
    """Metadata regarding synthesized voice status."""
    has_reference: bool = False
    reference_duration_s: Optional[float] = None
    has_synthesized_audio: bool = False
    synthesized_duration_s: Optional[float] = None
    model_used: Optional[str] = None
    language: Optional[str] = None
    synthesized_at: Optional[str] = None
    watermark_label: str = "AI-Generated Voice Recreation - Memorial Simulation Only"
```

---

## 4. End-to-End Workflow with Voice Recreation

```
[Browser UI]                        [FastAPI on localhost]                     [Local Models]
                                                                        
1. Memories & Stories     --------> POST /api/ofrendas/{id}/audio    -------> faster-whisper (STT)
2. Generate Remembrance   --------> POST /api/ofrendas/{id}/generate -------> Ollama (llama3.2:3b)
                                                                        
[Optional Step: AI Voice Recreation]
3. Family Consent & Audio --------> POST /api/ofrendas/{id}/voice/reference
                                      (Validates consent + extracts speaker latents)
4. Synthesize Remembrance --------> POST /api/ofrendas/{id}/voice/synthesize
                                      (Feeds remembrance text + speaker latents)
                                      ------> XTTS-v2 / OpenVoice V2
                                      ------> remembrance_synthesized.wav
5. Preview & Listen       <-------- GET  /api/ofrendas/{id}/voice/audio
6. Altar Integration      --------> GET  /api/ofrendas/{id}/page
                                      (Includes accessible <audio> player with prominent AI label)
```

---

## 5. Proposed Folder Structure

```
ofrenda-keeper/
  app/
    voice/                          # NEW: Decoupled voice synthesis package
      __init__.py
      base.py                       # Abstract base class: VoiceSynthesisEngine
      xtts_engine.py                # Coqui XTTS-v2 adapter (lazy loaded)
      openvoice_engine.py           # OpenVoice V2 adapter (lightweight option)
      mock_engine.py                # Synthetic WAV generator for tests
      service.py                    # High-level coordinator, latents cache, WAV labeling
      watermark.py                  # RIFF metadata injector for provenance
    schemas.py                      # Updated with voice consent and synthesis schemas
    storage.py                      # Updated with voice directory operations
    main.py                         # New /api/ofrendas/{id}/voice/* routes
  docs/
    VOICE_SYNTHESIS_PLAN.md         # THIS PLAN
    ARCHITECTURE.md                 # Updated with voice synthesis architecture
    DECISIONS.md                    # Updated architectural decision records
  scripts/
    fetch_voice_models.py           # Optional one-time script to pull XTTS-v2 / OpenVoice
  requirements.txt                  # Core lightweight app requirements (unchanged)
  requirements-voice.txt            # Optional heavy dependencies (torch, TTS)
  tests/
    test_voice.py                   # Unit tests for voice consent, upload, synthesis mocks
```

---

## 6. Dependency Strategy (`requirements-voice.txt`)

To ensure the core app stays lightweight, fast-starting, and accessible on any laptop, voice synthesis dependencies are separated into an **optional profile**:

```txt
# requirements-voice.txt (Optional voice synthesis add-on)
torch>=2.2.0
torchaudio>=2.2.0
TTS>=0.22.0  # Coqui TTS for XTTS-v2
# Alternative lightweight: openvoice-cli or melo
soundfile>=0.12.1
scipy>=1.11.0
```

When `requirements-voice.txt` is not installed, the app operates gracefully:
- `/api/health` reports `"voice_synthesis": false` (or `"engine": "not_installed"`).
- The UI displays an informative card: *"Voice synthesis model not installed. Run `pip install -r requirements-voice.txt` and `python scripts/fetch_voice_models.py` to enable."*

---

## 7. Phased Implementation Roadmap

### Phase A: Architecture, Schemas, & Engine Abstraction
- Define `app/voice/base.py` and `VoiceSynthesisEngine` protocol.
- Implement `MockVoiceEngine` that generates valid tone/beep WAV audio for instant unit tests.
- Extend `app/schemas.py` with consent verification and voice metadata.
- Extend `app/storage.py` to manage `data/ofrendas/<id>/voice/` subfolders.

### Phase B: Local Voice Synthesis Engine Implementation
- Implement `XTTSv2Engine` in `app/voice/xtts_engine.py` with lazy checkpoint loading on CPU/CUDA.
- Implement `watermark.py` to stamp metadata (`Artist: AI Recreation`, `Comment: Memorial Simulation`) directly into the output WAV header.
- Add `scripts/fetch_voice_models.py` to download weights once while online with checksum verification.

### Phase C: API Endpoints & Consent Enforcement
- `POST /api/ofrendas/{id}/voice/reference`: Upload reference audio (WAV, MP3, WebM) + required `consent` payload.
- `POST /api/ofrendas/{id}/voice/synthesize`: Synthesize remembrance text into audio using reference voice.
- `GET /api/ofrendas/{id}/voice/audio`: Stream synthetic audio with `Content-Type: audio/wav`.
- `GET /api/ofrendas/{id}/voice/download`: Download WAV with clear filename: `<Name>_AI_Voice_Recreation.wav`.
- `DELETE /api/ofrendas/{id}/voice`: Purge voice profiles, reference audio, and synthesized audio.

### Phase D: Altar Template & UI Wizard Integration
- Update Step 4 in wizard UI to include an optional accordion: **"Voice Recreation (Simulated Memorial Voice)"**.
- Include mandatory consent modal with clear disclaimer before enabling the voice upload button.
- Add audio preview player with visible badge: `[⚠️ AI-Generated Voice Recreation - Not Spoken by Deceased]`.
- Update `ofrenda.html.j2` with an elegant, respectful audio player component styled to match the altar.

### Phase E: Testing, Offline Guard, & Documentation
- Unit tests in `tests/test_voice.py` verifying consent enforcement, non-local network guard, and synthesis pipeline.
- Integration test marked `@pytest.mark.voice_integration`.
- Verify `scripts/check_offline.py` remains 100% clean of external URLs.
- Update `README.md` and user manual.

