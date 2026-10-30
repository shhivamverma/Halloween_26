"""Local LLM interaction via Ollama with fallback and output cleaning."""

import logging
import re
import time
from typing import Any, Optional, Tuple

from app.config import get_llm_timeout_s, get_ollama_host, get_ollama_model
from app.net import assert_local_url, local_client
from app.prompts import build_fallback_remembrance, build_prompt

logger = logging.getLogger("ofrenda.llm")


def get_client():
    """Return local HTTP client for Ollama, refusing any non-local host."""
    host = get_ollama_host()
    assert_local_url(host)
    return local_client(timeout=float(get_llm_timeout_s()))


def clean(text: str) -> str:
    """Clean LLM output: strip markdown, conversational AI intros, and enforce 250-word cap."""
    if not text:
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Drop lines that are purely conversational intro like 'Here is ...'
        stripped_meta = re.sub(r"[*#_~`]", "", line).strip()
        if re.match(r"(?i)^(here\s+is|here\'s|certainly|sure,|of course,)\b", stripped_meta):
            continue

        # Remove markdown heading markers (#, ##, etc.)
        line = re.sub(r"^\s*#+\s*", "", line)

        # Remove bullet markers
        line = re.sub(r"^\s*[-*•]\s*", "", line)

        # Strip 'As an AI' phrasing
        line = re.sub(r"(?i)\bas an ai\b\s*,?\s*(?:i\b)?\s*(?:\.{3}|…)?\s*", "", line)

        if line.strip():
            cleaned_lines.append(line.strip())

    out = "\n".join(cleaned_lines).strip()

    # Strip remaining markdown symbols
    out = out.replace("**", "").replace("*", "").replace("#", "").replace("__", "").replace("_", "")

    # Strip enclosing quotes if present
    if (out.startswith('"') and out.endswith('"')) or (out.startswith("'") and out.endswith("'")):
        out = out[1:-1].strip()

    # Enforce 250 word limit
    words = out.split()
    if len(words) > 250:
        out = " ".join(words[:250])

    return out.strip()


def generate_remembrance(ofrenda: Any, model: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """Generate remembrance via Ollama or fallback template. Logs timing only, never content.

    Returns: (remembrance_text, generated_by, model_used)
    """
    selected_model = model or get_ollama_model()
    prompt = build_prompt(ofrenda)
    start_t = time.perf_counter()

    try:
        client = get_client()
        host = get_ollama_host()
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 450,
            },
        }
        with client:
            resp = client.post(f"{host}/api/chat", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data.get("message", {}).get("content", "")
                cleaned_text = clean(raw_text)
                if cleaned_text:
                    elapsed = time.perf_counter() - start_t
                    est_tokens = len(cleaned_text.split()) * 1.33
                    tok_s = est_tokens / elapsed if elapsed > 0 else 0.0
                    logger.info("Generated remembrance with %s in %.2fs (~%.1f tokens/sec)", selected_model, elapsed, tok_s)
                    return cleaned_text, f"ollama:{selected_model}", selected_model

    except Exception:
        pass

    # Safe fallback
    elapsed = time.perf_counter() - start_t
    logger.info("Used fallback template remembrance in %.3fs", elapsed)
    fallback_text = build_fallback_remembrance(ofrenda)
    return fallback_text, "template", None
