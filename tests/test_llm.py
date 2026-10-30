"""Local LLM remembrance generation tests."""

import re
import pytest

from app.llm import clean, get_client
from app.prompts import build_prompt


def test_prompt_contains_all_facts(sample_ofrenda_es):
    """Verify built prompt contains all provided user facts without invention."""
    p = build_prompt(sample_ofrenda_es)
    for item in ("Rosa", "tamales", "Cielito Lindo", "cafe de olla"):
        assert item in p.user
    assert "espanol" in p.system.lower() or "spanish" in p.system.lower()


def test_generate_with_mock_ollama(client, created_id, mock_ollama):
    """When Ollama succeeds, response returns generated remembrance and ollama prefix."""
    mock_ollama("Rosa filled every December with the smell of tamales.")
    r = client.post(f"/api/ofrendas/{created_id}/generate")
    assert r.status_code == 200
    data = r.json()
    assert data["generated_by"].startswith("ollama:")
    assert "tamales" in data["remembrance"]


def test_fallback_when_ollama_down(client, created_id, mock_ollama_down):
    """When Ollama is unreachable, endpoint falls back gracefully to template without 500 error."""
    r = client.post(f"/api/ofrendas/{created_id}/generate")
    assert r.status_code == 200
    data = r.json()
    assert data["generated_by"] == "template"
    assert "Rosa" in data["remembrance"]


def test_cleaner_strips_markdown_and_ai_phrases():
    """Output cleaner strips markdown headings, bold, bullet points, and AI preamble."""
    out = clean("**Here is a remembrance:**\n# Title\nAs an AI, I ... Rosa loved music.")
    assert "*" not in out
    assert "As an AI" not in out
    assert "#" not in out
    assert "Rosa loved music." in out


def test_word_limit_250():
    """Remembrance must be capped at 250 words maximum."""
    out = clean("word " * 900)
    assert len(out.split()) <= 250


def test_non_local_host_refused(monkeypatch):
    """Refuse any host that is not localhost or 127.0.0.1."""
    monkeypatch.setenv("OLLAMA_HOST", "https://api.example.com")
    with pytest.raises(ValueError):
        get_client()


@pytest.mark.integration
def test_real_model_quality(client, created_id_with_facts):
    """Integration test checking quality and fact fidelity with real local Ollama model."""
    r = client.post(f"/api/ofrendas/{created_id_with_facts}/generate")
    assert r.status_code == 200
    out = r.json()["remembrance"]
    assert 60 <= len(out.split()) <= 250
    assert "Rosa" in out
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", out))
    assert years <= {"1941", "2023"}  # no invented years
