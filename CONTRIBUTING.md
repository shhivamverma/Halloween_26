# Contributing to Offline Ofrenda Keeper

Welcome to **Offline Ofrenda Keeper**! We are thrilled you want to help preserve cherished family traditions through ethical, local open-source AI.

This project is part of **Hacktoberfest 2026** (Week 4: *Ghost in the Machine*).

---

## 🕯️ Our Guiding Principles

1. **Absolute Offline Privacy:** Never introduce dependencies, scripts, fonts, or assets that call external servers. The only allowed network calls are to `localhost` / `127.0.0.1`.
2. **Reverence & Respect:** The app deals with family grief and remembrance. Tone and copy must always be gentle, loving, and celebratory of life.
3. **Ethical Voice Studio Standards:** Any contributions to voice recreation must strictly maintain affirmative family authorization gating, RIFF INFO provenance watermarking, explicit AI simulation disclosures, and local offline execution.
4. **No LLM Hallucinations:** Prompts must strictly constrain generation to user-provided facts.
5. **Simplicity:** Vanilla HTML/CSS/JS frontend with no build step; FastAPI + disk storage backend with no external database service.

---

## 🚀 Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-username/ofrenda-keeper.git
cd ofrenda-keeper

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1

# 3. Install CPU PyTorch and dependencies
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 4. Pull local model and warm caches
bash scripts/fetch_models.sh  # Windows: .\scripts\fetch_models.ps1

# 5. Run tests
pytest -v

# 6. Verify offline compliance
python scripts/check_offline.py

# 7. Start local development server (loopback only)
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your web browser.

---

## 🌟 Good First Issues (Hacktoberfest Friendly)

Looking for a great first contribution for Hacktoberfest? Here are curated beginner-friendly areas:

### Issue #1: Additional Languages for Altar Page (Nahuatl, French, Portuguese)
- **Description:** Currently the altar template supports English and Spanish. Add prompt templates and localized altar headers in Nahuatl, French, or Portuguese.
- **Files to touch:** `app/prompts.py`, `app/templates/ofrenda.html.j2`, `app/schemas.py`.

### Issue #2: Alternate Visual Altar Themes
- **Description:** Provide alternate altar color themes (e.g. *Cempasúchil Golden Glow*, *Papel Picado Pastel*, and *Minimalist High-Contrast Print*).
- **Files to touch:** `app/templates/ofrenda.html.j2`, `app/static/style.css`.

### Issue #3: Whisper Model-Size Selector in UI
- **Description:** Allow users to choose between `tiny`, `base`, or `small` Whisper models from a dropdown in Step 3 based on their laptop CPU capabilities.
- **Files to touch:** `app/config.py`, `app/transcribe.py`, `app/static/index.html`, `app/static/app.js`.

### Issue #4: Screen-Reader Accessibility & ARIA Live Regions Audit
- **Description:** Perform an accessibility review using NVDA / VoiceOver. Improve ARIA announcement landmarks when adding offering chips and during recording state transitions.
- **Files to touch:** `app/static/index.html`, `app/static/app.js`.

### Issue #5: Optional Calaverita Literaria Mode
- **Description:** Día de los Muertos traditions often include playful, rhythmic verses known as *calaveritas literarias*. Add an optional checkbox allowing users to generate a traditional rhyming 4-stanza calaverita alongside the solemn remembrance.
- **Files to touch:** `app/prompts.py`, `app/llm.py`, `app/static/index.html`.

---

## 📋 Pull Request Checklist

Before submitting a PR, ensure all checks pass:
- [ ] Unit tests pass: `pytest -v` (all 69 tests pass)
- [ ] Offline check passes: `python scripts/check_offline.py`
- [ ] No personal or identifiable data in git commits (`./data/` is gitignored)
- [ ] Permissive licensing maintained: No non-commercial models or proprietary packages added
- [ ] Code formatted cleanly with descriptive docstrings
