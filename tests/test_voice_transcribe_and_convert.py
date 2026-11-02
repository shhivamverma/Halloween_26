"""Tests for Microphone Transcription (transcribe-mic) and Editable Transcript Voice Conversion."""

from pathlib import Path
import pytest


def test_transcribe_mic_success_english(client, created_id, wav_bytes, monkeypatch):
    """Microphone audio upload transcribes English speech and returns text & language."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "In loving memory, you will forever remain in our hearts.",
            "language": "en",
            "duration": 3.8,
        },
    )

    r = client.post(
        f"/api/ofrendas/{created_id}/voice/transcribe-mic",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={"language": "en"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "In loving memory" in data["transcript"]
    assert data["detected_language"] == "en"
    assert data["duration_s"] == 3.8


def test_transcribe_mic_success_hindi(client, created_id, wav_bytes, monkeypatch):
    """Microphone audio upload transcribes Hindi speech and returns Devanagari text."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "नमस्ते आपकी स्मृति हमारे दिल में सदैव जीवित रहेगी",
            "language": "hi",
            "duration": 4.5,
        },
    )

    r = client.post(
        f"/api/ofrendas/{created_id}/voice/transcribe-mic",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={"language": "hi"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "नमस्ते" in data["transcript"]
    assert data["detected_language"] == "hi"


def test_transcribe_mic_nonexistent_ofrenda_404(client, wav_bytes):
    """Attempting to transcribe mic audio for a non-existent ofrenda returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000099"
    r = client.post(
        f"/api/ofrendas/{fake_id}/voice/transcribe-mic",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
    )
    assert r.status_code == 404


def test_transcribe_mic_invalid_format_415(client, created_id):
    """Uploading unsupported non-audio file to transcribe-mic returns 415."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/transcribe-mic",
        files={"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert r.status_code == 415


def test_transcribe_mic_empty_audio_400(client, created_id):
    """Uploading empty or tiny corrupt audio (< 300 bytes) returns 400."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/transcribe-mic",
        files={"file": ("empty.wav", b"RIFF" + b"\x00" * 50, "audio/wav")},
    )
    assert r.status_code == 400


def test_convert_voice_with_reviewed_transcript(client, created_id, wav_bytes):
    """Submitting reviewed/corrected transcript passes text directly to voice conversion."""
    # First upload authorized reference audio
    ref_res = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("ref.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Maria Rivera", "confirmed_permission": "true"},
    )
    assert ref_res.status_code == 200

    # Execute conversion with reviewed transcript
    reviewed_text = "In loving memory, you will forever remain in our hearts."
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "Maria Rivera",
            "confirmed_permission": "true",
            "language": "en",
            "transcript": reviewed_text,
            "engine": "kokoro-openvoice",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["model_ready"] is True
    assert data["detected_language"] == "en"
    assert "voice_profile" in data


def test_convert_voice_unauthorized_permission_rejected(client, created_id, wav_bytes):
    """Voice conversion without affirmative family authorization is strictly rejected."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "Stranger",
            "confirmed_permission": "false",
        },
    )
    assert r.status_code == 400
    assert "authorization is strictly required" in r.json()["detail"]


def test_convert_voice_missing_authorizer_rejected(client, created_id, wav_bytes):
    """Voice conversion with empty authorizer name is rejected with 400."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "   ",
            "confirmed_permission": "true",
        },
    )
    assert r.status_code == 400
    assert "authorizing family member name must be provided" in r.json()["detail"]


def test_convert_voice_with_inline_reference_file(client, created_id, wav_bytes):
    """Voice conversion succeeds when reference audio is provided directly as reference_file."""
    reviewed_text = "Cherished memories always live on."
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={
            "file": ("mic.wav", wav_bytes, "audio/wav"),
            "reference_file": ("deceased_reference.wav", wav_bytes, "audio/wav"),
        },
        data={
            "authorized_by": "Carlos Rivera",
            "confirmed_permission": "true",
            "language": "en",
            "transcript": reviewed_text,
            "engine": "kokoro-openvoice",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["model_ready"] is True
    assert data["voice_profile"]["has_reference"] is True

    # Verify download endpoint delivers the generated audio
    dl_res = client.get(f"/api/ofrendas/{created_id}/voice/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "audio/wav"
    assert "attachment" in dl_res.headers["content-disposition"]


def test_convert_voice_invalid_reference_format_415(client, created_id, wav_bytes):
    """Providing an invalid format for reference_file returns HTTP 415."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={
            "file": ("mic.wav", wav_bytes, "audio/wav"),
            "reference_file": ("voice.txt", b"plain text", "text/plain"),
        },
        data={
            "authorized_by": "Carlos Rivera",
            "confirmed_permission": "true",
        },
    )
    assert r.status_code == 415


def test_convert_voice_missing_reference_400(client, wav_bytes):
    """Converting voice without reference audio or reference_file returns HTTP 400."""
    create_r = client.post("/api/ofrendas", json={"name": "No Ref Person", "language": "en"})
    new_id = create_r.json()["id"]

    r = client.post(
        f"/api/ofrendas/{new_id}/voice/convert",
        files={"file": ("mic.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "Carlos Rivera",
            "confirmed_permission": "true",
        },
    )
    assert r.status_code == 400
    assert "No reference voice" in r.json()["detail"]


def test_convert_voice_hindi_experimental_flag(client, created_id, wav_bytes):
    """Hindi voice conversion is tagged with experimental_hindi=True."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={
            "file": ("mic.wav", wav_bytes, "audio/wav"),
            "reference_file": ("ref.wav", wav_bytes, "audio/wav"),
        },
        data={
            "authorized_by": "Carlos Rivera",
            "confirmed_permission": "true",
            "language": "hi",
            "transcript": "नमस्ते, आप हमेशा हमारे दिल में रहेंगे।",
            "engine": "kokoro-openvoice",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["detected_language"] == "hi"
    assert data["experimental_hindi"] is True

