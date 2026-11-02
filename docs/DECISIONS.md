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
- **Decision:** Refuse any outbound HTTP connection to addresses other than `127.0.0.1` and `localhost` at the client creation and request layer via `app/net.py`.
- **Reason:** Ensures zero data leakage and 100% offline compliance as required by the challenge.

### 4. Audio Decoding Compatibility (PyAV)
- **Decision:** Pin `av>=12.0.0,<14.0.0` in `requirements.txt`.
- **Reason:** Newer versions of PyAV (14+) removed the `metadata_errors` argument from `av.open()`, causing an unhandled `TypeError` inside `faster_whisper/audio.py`. Pinning `av<14` ensures reliable offline decoding for browser audio (WebM/Opus, OGG, WAV, MP3, M4A).

### 5. Deterministic Fallback Remembrance Structure
- **Decision:** Implement template fallback in both English and Spanish in `app/prompts.py` using user-provided offerings and stories.
- **Reason:** Guarantees that if Ollama is not running, the application never returns an HTTP 500 error and the user still receives an evocative, beautifully rendered ofrenda altar.

### 6. SVG Without XMLNS Namespace
- **Decision:** Omit `xmlns="http://www.w3.org/2000/svg"` attribute from inline SVG elements within the HTML altar page.
- **Reason:** Modern HTML5 parses inline SVG elements natively without needing the XML namespace URI. Omitting `http://` prevents false positives during strict offline security scans.

### 7. Voice Synthesis Engine Selection & Licensing (XTTS-v2 & OpenVoice V2)
- **Decision:** Design an engine adapter interface supporting **Coqui XTTS-v2** as the primary high-fidelity model and **OpenVoice V2** as the lightweight CPU-friendly alternative.
- **Reason:** XTTS-v2 natively supports 17 languages including Spanish (`es`) and English (`en`) with excellent prosody from short reference clips. XTTS-v2 is licensed under the Coqui Public Model License (CPML), which permits non-commercial personal use. OpenVoice V2 (CC BY-NC 4.0) offers a faster, lower-memory alternative for CPU-only systems.

### 8. Strict Family Authorization & Anti-Deception Guardrails
- **Decision:** Require affirmative family consent records for voice synthesis and mandate prominent watermarking and labeling on all synthetic audio outputs.
- **Reason:** Simulating the voice of a deceased relative carries deep emotional and ethical sensitivity. The system must never permit unauthorized cloning or create the illusion that the deceased spoke words they never uttered. Authentic voice recordings ("In their own words") remain strictly distinct from synthetic readings ("AI Voice Reading of Remembrance").

### 9. Local-Only Audio Storage Hierarchy
- **Decision:** Store voice reference recordings, speaker embeddings/latents, and generated audio inside `data/ofrendas/<id>/voice/` on the local machine.
- **Reason:** Enforces zero cloud leakage and complies with the project's strict offline architecture. Speaker profiles are cached locally to avoid re-computing conditioning latents on subsequent generation requests.

### 10. Decoupled Service Boundary with Mock Testing
- **Decision:** Decouple the voice synthesis service behind a `VoiceSynthesisEngine` abstraction, providing a bundled `MockVoiceEngine` for test suites.
- **Reason:** Heavy deep-learning packages (PyTorch, torchaudio, TTS) and multi-gigabyte checkpoints would cause test bloat and prevent tests from running in seconds on standard developer machines. The mock engine allows verifying API contracts, consent gating, and storage workflows instantly.

### 11. Dependency Separation via `requirements-voice.txt`
- **Decision:** Keep `requirements.txt` lightweight for the core MVP application and place voice synthesis dependencies into an optional `requirements-voice.txt`.
- **Reason:** Ensures the core app can be cloned and run on any machine in under 60 seconds without forcing users to install 2+ GB of PyTorch and TTS packages if they do not intend to use the voice recreation feature.

### 12. Pure-Offline 3D Visual Engine & Hackathon UX Showcase
- **Decision:** Build a zero-dependency HTML5 Canvas 3D particle engine (marigold/cempasúchil petals and glowing embers) and CSS 3D perspective card tilt with dynamic specular reflection, without importing Three.js or remote CDNs.
- **Reason:** External 3D or animation libraries would violate the strict offline / zero-CDN constraint. A tailored vanilla JavaScript 3D perspective projection engine (`FOV = 450`) provides silky 60fps cultural ambient storytelling while staying 100% offline. A 1-click demo seed endpoint (`/api/demo/seed`) enables hackathon judges to inspect a complete multi-modal ofrenda in seconds. All animations respect `prefers-reduced-motion`.

### 13. Primary Voice Architecture: Kokoro-82M + OpenVoice V2
- **Decision:** Make Kokoro-82M + OpenVoice V2 the primary production voice engine, preserving Seed-VC and MMS-TTS as alternatives.
- **Reason:** Coqui XTTS-v2 was governed by CPML (non-commercial only) and required high memory (~2.5+ GB). Kokoro-82M is permissively licensed under Apache-2.0, possesses an 82M parameter footprint (~320 MB), and pairs with OpenVoice V2's ToneColorConverter (MIT License) for efficient CPU tone color transfer using reference recordings.

### 14. Voice Workflow: Whisper ASR → Kokoro TTS → OpenVoice Tone-Colour Conversion
- **Decision:** Implement a three-stage acoustic pipeline: (1) Local Whisper ASR transcribes recorded microphone audio; (2) Frontend presents an editable text review box allowing the user to review and correct phonetic/Devanagari/English text nuances; (3) Kokoro TTS synthesizes natural base speech from the confirmed transcript; (4) OpenVoice ToneColorConverter applies the vocal timbre of the authorized reference audio. Direct, ungrounded speech-to-speech latent conversion without intermediate phonetic grounding is explicitly rejected.
- **Reason:** Direct speech-to-speech latent conversion without intermediate phonetic grounding is vulnerable to acoustic hallucination, slur, and word dropping. Grounding through Whisper ASR and human review guarantees that the synthesized words faithfully match the family's remembrance.

### 15. Hindi Support with Explicit Experimental Disclosure
- **Decision:** Support Hindi speech synthesis via Kokoro's native G2P phonemizer (`h`, voice `hf_alpha`) and OpenVoice tone transfer, while explicitly returning and displaying an `experimental_hindi: true` badge.
- **Reason:** Kokoro natively supports Hindi phonemization, but OpenVoice V2's training data was predominantly English and Chinese. While Indian accent and tone transfer work audibly, tonal coloration on Devanagari phonemes requires honest ethical disclosure of experimental status rather than unverified perfection claims.

### 16. Thread-Safe Voice Conversion Lock (HTTP 409 Conflict)
- **Decision:** Implement a backend mutex lock (`_conversion_lock`) tracking `_active_conversions` per ofrenda UUID, returning HTTP 409 Conflict if duplicate conversions are submitted simultaneously.
- **Reason:** Neural voice conversion is CPU-intensive. Preventing re-entrant conversions on the same memorial prevents CPU thrashing, out-of-memory crashes, and race conditions during audio file writes.

