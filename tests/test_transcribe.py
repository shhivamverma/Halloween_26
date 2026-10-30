"""Speech-to-text audio upload and transcription tests."""

import pytest


def test_audio_wrong_type_415(client, created_id):
    """Uploading unsupported non-audio file returns 415."""
    r = client.post(
        f"/api/ofrendas/{created_id}/audio",
        files={"file": ("x.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert r.status_code == 415


def test_audio_appends_transcript_mocked(client, created_id, monkeypatch, wav_bytes):
    """Audio transcription appends speech to the ofrenda transcript."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "She made tamales every December.",
            "language": "en",
            "duration": 4.2,
        },
    )
    r = client.post(
        f"/api/ofrendas/{created_id}/audio",
        files={"file": ("a.wav", wav_bytes, "audio/wav")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "tamales" in data["text"]

    ofrenda = client.get(f"/api/ofrendas/{created_id}").json()
    assert "tamales" in ofrenda["transcript"]


def test_two_voice_notes_append(client, created_id, monkeypatch, wav_bytes):
    """Multiple voice notes must be appended, never overwriting previous notes."""
    # First note
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "First story about baking bread.",
            "language": "en",
            "duration": 3.0,
        },
    )
    r1 = client.post(
        f"/api/ofrendas/{created_id}/audio",
        files={"file": ("note1.wav", wav_bytes, "audio/wav")},
    )
    assert r1.status_code == 200

    # Second note
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "Second story about singing folk songs.",
            "language": "en",
            "duration": 3.5,
        },
    )
    r2 = client.post(
        f"/api/ofrendas/{created_id}/audio",
        files={"file": ("note2.wav", wav_bytes, "audio/wav")},
    )
    assert r2.status_code == 200

    # Fetch and verify both stories exist in transcript
    ofrenda = client.get(f"/api/ofrendas/{created_id}").json()
    assert "First story about baking bread." in ofrenda["transcript"]
    assert "Second story about singing folk songs." in ofrenda["transcript"]


def test_silence_returns_warning(client, created_id, monkeypatch, wav_bytes):
    """Silent or empty speech audio returns 200 with warning field."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "",
            "language": "en",
            "duration": 2.0,
        },
    )
    r = client.post(
        f"/api/ofrendas/{created_id}/audio",
        files={"file": ("silence.wav", wav_bytes, "audio/wav")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == ""
    assert "warning" in data


@pytest.mark.integration
def test_real_whisper_on_fixture(client, created_id):
    """End-to-end integration test with real faster-whisper model transcribing fixture."""
    with open("tests/fixtures/sample_en.wav", "rb") as f:
        r = client.post(
            f"/api/ofrendas/{created_id}/audio",
            files={"file": ("sample_en.wav", f, "audio/wav")},
        )
    assert r.status_code == 200
    text = r.json()["text"].lower()
    assert "tamales" in text
