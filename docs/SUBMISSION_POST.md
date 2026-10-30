# Submission Post: Hacktoberfest 2026, Week 4 ("Ghost in the Machine")

**TITLE:** Offline Ofrenda Keeper: honoring the people we love, with the Wi-Fi off

### WHAT IT IS
A local web app that turns a family's memories (typed stories, a recorded voice note, favorite foods and songs, and a photo) into a beautiful Día de los Muertos ofrenda page and a written remembrance. Everything runs 100% on the user's laptop.

### WHY OPEN INNOVATION MATTERS FOR WHAT I BUILT
- **Privacy:** A grandmother's voice, family photographs, and memories of the dead should not live on a server I do not control. With open-weight models, they never leave the machine.
- **Works offline:** The entire application runs smoothly in Airplane Mode. Once initial weights are downloaded, no internet connection is ever touched.
- **No lock-in:** The generated output is a single self-contained HTML file (inline CSS, embedded SVGs, base64 photo). No external company can change terms, charge subscriptions, or shut down access.
- **Swappable:** Tested `llama3.2:3b` vs `qwen3:1.7b` alongside `faster-whisper` (base):

| Model | Task | Hardware | Output Length | Latency | Speed |
|---|---|---|---|---|---|
| **faster-whisper (base)** | Audio Transcription | CPU (int8) | 7 words (3.2s clip) | 3.16s | ~1.0x Realtime |
| **llama3.2:3b** | Remembrance Generation | Ollama (CPU) | 154 words | 37.1s | **~5.5 tokens/sec** |
| **qwen3:1.7b** | Remembrance Generation | Ollama (CPU) | 47 words | 48.2s | ~1.3 tokens/sec |

- **Free:** No API keys, no monthly fees, no per-use meter.

*Where closed would have been worse:* A hosted proprietary API would have required uploading sacred family recordings, cost money per use, and failed completely in areas without stable Wi-Fi.

### HOW IT WORKS
1. **Speech-to-Text:** `faster-whisper` (Whisper base, CPU int8) transcribes uploaded voice notes and browser microphone recordings in a background threadpool.
2. **Local LLM:** Ollama runs `llama3.2:3b` (or user-swapped models like Qwen) using a strict prompt preventing invented facts or dates. If Ollama is offline, a deterministic template fallback immediately crafts a remembrance without error.
3. **Self-Contained Altar Page:** Jinja2 renders a three-tier Día de los Muertos altar page with flickering CSS candle animations, papel picado garland, and print stylesheet.
4. **Stack:** Python 3.12 + FastAPI + vanilla HTML/CSS/JavaScript + JSON disk storage. No database server, no frontend build pipeline, no external CDN calls.

### WHAT I LEARNED
1. **Controlling Small-Model Hallucinations:** Smaller models (like 3B parameters) are prone to inventing dates, family members, or jobs when writing biographical prose. Imposing strict negative constraints in the system prompt ("Use ONLY the facts provided; if a detail is not given, leave it out") and presenting the remembrance in an editable textarea prior to final altar generation gave complete peace of mind.
2. **PyAV Compatibility in Local Whisper Pipelines:** Newer versions of PyAV (14+) removed the `metadata_errors` argument from `av.open()`, which caused unhandled errors in audio decoding. Pinning `av<14` ensured bulletproof offline transcription for WebM, Opus, WAV, MP3, and M4A.
3. **The Power of Single-File HTML Artifacts:** By inlining CSS, embedding SVGs without remote namespaces, and inlining photos as base64 data URIs, families receive an artifact that is resilient, offline-ready, and printable for decades.

---

**REPO:** https://github.com/your-username/ofrenda-keeper  
**DEMO VIDEO:** https://youtu.be/your-demo-video  
**LICENSE:** MIT  
*Built for Hacktoberfest 2026, Week 4: Ghost in the Machine. #hacktoberfest*
