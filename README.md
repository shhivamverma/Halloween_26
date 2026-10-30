# 🕯️ Offline Ofrenda Keeper

> **A fully local app that turns a family's memories of someone they love (typed stories, a recorded voice note, favorite foods and songs, a photo) into a beautiful digital ofrenda page and a written remembrance.**

Built for **Hacktoberfest 2026, Week 4: "Ghost in the Machine"**.

```
       ░█▀▀█ ░█▀▀▀ ░█▀▀█ ░█▀▀▀ ░█▄─░█ ░█▀▀▄ ─█▀▀█
       ░█─── ░█▀▀▀ ░█▄▄▀ ░█▀▀▀ ░█░█░█ ░█─░█ ░█▄▄█
       ░█▄▄█ ░█▄▄▄ ░█─░█ ░█▄▄▄ ░█──▀█ ░█▄▄▀ ░█──░█
   [ Día de los Muertos • Offline Altar & Remembrance Keeper ]
```

---

## 🌺 Why Open-Source AI is Essential

On Día de los Muertos, families construct altars (*ofrendas*) with photos, candles, cempasúchil marigolds, and the favorite foods, drinks, and songs of deceased loved ones. Using AI for grief and memorialization requires extraordinary respect and ethical responsibility:

- **Absolute Privacy:** Voice recordings, family photos, and stories of deceased relatives are among the most intimate, sacred data a family has. They must never be uploaded to remote cloud servers or used to train corporate models.
- **Works with Wi-Fi Off:** Runs completely in Airplane Mode. Once models are cached, zero internet connection is required.
- **No Lock-In:** Closed AI services can shut down, change API terms, or charge subscriptions. A local model and a plain, self-contained HTML file can be kept by a family forever.
- **Swappable Models:** Users can seamlessly choose between Llama 3.2, Qwen, or Gemma, or switch Whisper model sizes depending on hardware capabilities and language preferences.
- **Free to Run:** No API keys, no paywalls, no per-use charges.
- **Permanent Open Output:** The resulting altar page is a single self-contained HTML document with inline CSS, inline SVGs, and base64-embedded photos. It opens on any device, now and decades into the future.

---

## ⚡ 5-Command Quickstart

```bash
# 1. Clone repository
git clone https://github.com/your-username/ofrenda-keeper.git && cd ofrenda-keeper

# 2. Set up virtual environment and install dependencies
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Pull Ollama model & warm Whisper cache (one-time step with internet)
bash scripts/fetch_models.sh

# 4. (Optional) Disconnect Wi-Fi / enable Airplane Mode to verify offline operation!
export HF_HUB_OFFLINE=1  # Windows PowerShell: $env:HF_HUB_OFFLINE="1"

# 5. Launch the application
uvicorn app.main:app --reload
```

Visit **http://127.0.0.1:8000** in your browser.

---

## 📐 Architecture & Workflow

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

---

## 📊 Local Model Benchmarks

Tested on a standard laptop running CPU inference (8GB-16GB RAM):

| Model | Task | Device | Word Count | Avg Latency | Throughput |
|---|---|---|---|---|---|
| **faster-whisper (base)** | Speech-to-Text | CPU (int8) | — | 3.16s for 3.2s audio | ~1.0x Real-Time (RTFx: 1.0) |
| **llama3.2:3b** (Default) | Remembrance Generation | Ollama (CPU) | 154 words | 37.1s | **~5.5 tokens/sec** |
| **qwen3:1.7b** | Remembrance Generation | Ollama (CPU) | 47 words | 48.2s | ~1.3 tokens/sec |

*Notice: If Ollama is offline or unavailable, the built-in deterministic template fallback executes in **0.003 seconds**, guaranteeing 100% application uptime.*

---

## 🛡️ Privacy & Offline Hardening Guarantees

1. **Local Network Guard:** `app/net.py` wraps all HTTP client calls. Any outbound request directed to a host other than `127.0.0.1` or `localhost` immediately raises a `ValueError`.
2. **Offline Integrity Verification:** Run `python scripts/check_offline.py` to recursively scan all application source files, templates, styles, and a live-rendered ofrenda for external URLs. It exits `0` only if zero non-local URLs are found.
3. **No Story Logging:** System logs record inference timing and token throughput only; family memory texts and audio transcripts are never written to server logs.
4. **Data Isolation:** User records reside solely in `./data/ofrendas/` (which is gitignored).

---

## 🔄 How to Swap Models

The UI automatically queries `GET /api/health` and lists all models currently installed in your local Ollama daemon.

To install and use alternative open-source models:
```bash
# Faster English & Spanish alternative
ollama pull llama3.2:3b

# Lightweight multilingual model
ollama pull qwen2.5:3b

# High parameter option for 16GB+ systems
ollama pull llama3.1:8b
```
Select the desired model from the dropdown in **Step 4** and click **Generate** or **Regenerate**.

---

## 🧪 Running Automated Tests

```bash
# Run fast mocked unit test suite (runs in seconds)
pytest -q

# Run offline security check script
python scripts/check_offline.py

# Run real model integration tests (requires local Ollama & Whisper cache)
pytest -v -m integration
```

---

## ❓ Frequently Asked Questions (FAQ)

**Q: Does any audio or picture ever get uploaded to the cloud?**  
**A:** Never. `faster-whisper`, `llama3.2:3b`, and the local voice synthesis engine execute 100% directly on your local machine. You can disconnect your Wi-Fi or enable Airplane Mode, and the app continues to work without interruption.

**Q: How does local voice recreation work and what are the ethical safeguards?**  
**A:** In Step 4, families can optionally generate an audio remembrance using local models (XTTS-v2 or OpenVoice V2). To protect dignity and prevent deception, affirmative family authorization is strictly required, reference audio and speaker profiles remain strictly local, and all generated audio is explicitly labeled and watermarked as an AI-generated reading of remembrance (never implying the deceased uttered the words).

**Q: How do judges or first-time users quickly test the app?**  
**A:** Click the **✨ Demo (Abuela Rosa)** button in the top navigation bar. It instantly seeds an authentic, fictional ofrenda with photo, offerings, transcribed memories, AI remembrance, and voice recreation in 1 click!

**Q: Can I control the 3D visual effects and animations?**  
**A:** Yes. The top navigation bar includes an **Ambient 3D Toggle** (marigold petals and candle embers). Furthermore, all animations automatically detect and honor your operating system's `prefers-reduced-motion` settings.

**Q: What happens if Ollama is not installed or running?**  
**A:** The app gracefully detects that Ollama is offline and uses a gentle, respectful fallback template to compose the remembrance from the facts you provided. The app will never crash with a 500 error.

**Q: How do I print the ofrenda or save it as a PDF?**  
**A:** In Step 4, click **Print or Save as PDF**. The included `@media print` CSS ensures the background colors, altar candles, and portrait fit neatly on 1 to 2 printed pages.

---

## 🤝 Contributing

Contributions are warmly welcomed! Please read [CONTRIBUTING.md](file:///CONTRIBUTING.md) for our contribution guidelines and a list of **Good First Issues** for Hacktoberfest.

---

## 📄 License

This project is licensed under the [MIT License](file:///LICENSE).
