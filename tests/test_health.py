"""Health check endpoint tests."""


def test_health_shape(client):
    """Verify health endpoint shape and required fields."""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    for key in ("status", "ollama", "whisper", "model", "models"):
        assert key in body
    assert isinstance(body["models"], list)
    assert isinstance(body["ollama"], bool)
    assert isinstance(body["whisper"], bool)


def test_health_never_crashes_when_ollama_down(client, monkeypatch):
    """Health check must never crash or return 500 when Ollama is unavailable."""
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")  # closed port
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ollama"] is False
