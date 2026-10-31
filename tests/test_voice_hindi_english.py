"""Tests for Hindi and English voice synthesis and Speech-to-Speech conversion."""

import pytest
from app.voice.mock_engine import MockVoiceEngine
from app.voice.watermark import read_riff_metadata
from app.voice.service import get_voice_service
from app.storage import Storage


def test_mock_voice_engine_supports_hindi_and_english():
    """Verify mock voice engine supports Hindi and English."""
    engine = MockVoiceEngine()
    assert "hi" in engine.supported_languages
    assert "en" in engine.supported_languages
    assert "es" in engine.supported_languages


def test_hindi_remembrance_synthesis(client, created_id, wav_bytes):
    """Test Hindi remembrance text synthesis with authorized consent."""
    # 1. Upload authorized reference audio
    ref_res = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("reference_voice.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Aarav Sharma (Son)", "confirmed_permission": "true"},
    )
    assert ref_res.status_code == 200

    # 2. Add Hindi remembrance text
    patch_res = client.patch(
        f"/api/ofrendas/{created_id}",
        json={"remembrance": "उनकी मधुर स्मृति और आशीर्वाद सदैव हमारे हृदय में जीवंत रहेंगे।", "language": "hi"},
    )
    assert patch_res.status_code == 200

    # 3. Synthesize Hindi voice
    synth_res = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "language": "hi",
            "speed": 1.0,
            "consent": {
                "authorized_by": "Aarav Sharma (Son)",
                "confirmed_permission": True,
            },
        },
    )
    assert synth_res.status_code == 200
    data = synth_res.json()
    assert data["has_synthesized_audio"] is True
    assert data["language"] == "hi"

    # 4. Fetch audio stream and verify WAV header and watermark
    audio_res = client.get(f"/api/ofrendas/{created_id}/voice/audio")
    assert audio_res.status_code == 200
    assert audio_res.headers["content-type"] == "audio/wav"
    audio_content = audio_res.content
    assert audio_content.startswith(b"RIFF")

    meta = read_riff_metadata(audio_content)
    assert "AI Remembrance Recreation" in meta.get("INAM", "")
    assert "Offline Ofrenda Keeper" in meta.get("IART", "")
    assert "Simulated memorial voice recreation" in meta.get("ICMT", "")


def test_english_remembrance_synthesis(client, created_id, wav_bytes):
    """Test English remembrance text synthesis with authorized consent."""
    # 1. Upload reference audio
    ref_res = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("reference_voice.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Emily Johnson (Granddaughter)", "confirmed_permission": "true"},
    )
    assert ref_res.status_code == 200

    # 2. Add English remembrance text
    client.patch(
        f"/api/ofrendas/{created_id}",
        json={"remembrance": "Their gentle laughter, kindness, and eternal love light our path always.", "language": "en"},
    )

    # 3. Synthesize English voice
    synth_res = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "language": "en",
            "speed": 1.0,
            "consent": {
                "authorized_by": "Emily Johnson (Granddaughter)",
                "confirmed_permission": True,
            },
        },
    )
    assert synth_res.status_code == 200
    data = synth_res.json()
    assert data["has_synthesized_audio"] is True
    assert data["language"] == "en"

    # 4. Stream audio
    audio_res = client.get(f"/api/ofrendas/{created_id}/voice/audio")
    assert audio_res.status_code == 200
    assert audio_res.content.startswith(b"RIFF")


def test_speech_to_speech_hindi_conversion(client, created_id, monkeypatch, wav_bytes):
    """Test Speech-to-Speech pipeline with Hindi microphone input."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "नमस्ते, हम आपको सदैव याद रखेंगे।",
            "language": "hi",
            "duration": 3.0,
        },
    )

    # 1. Upload reference audio
    client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("reference_voice.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Pooja Verma", "confirmed_permission": "true"},
    )

    # 2. Convert microphone speech in Hindi
    convert_res = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic_input.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "Pooja Verma",
            "confirmed_permission": "true",
            "language": "hi",
        },
    )
    assert convert_res.status_code == 200
    result = convert_res.json()
    assert result["status"] == "success"
    assert result["model_ready"] is True
    assert result["detected_language"] == "hi"
    assert "नमस्ते" in result["transcription"]

    # 3. Check audio download
    audio_res = client.get(f"/api/ofrendas/{created_id}/voice/audio")
    assert audio_res.status_code == 200
    assert audio_res.content.startswith(b"RIFF")


def test_speech_to_speech_english_conversion(client, created_id, monkeypatch, wav_bytes):
    """Test Speech-to-Speech pipeline with English microphone input."""
    monkeypatch.setattr(
        "app.transcribe.transcribe",
        lambda p, language_hint=None: {
            "text": "We miss you every single day and honor your memory.",
            "language": "en",
            "duration": 3.2,
        },
    )

    # 1. Upload reference audio
    client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("reference_voice.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "John Doe", "confirmed_permission": "true"},
    )

    # 2. Convert microphone speech in English
    convert_res = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic_input.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "John Doe",
            "confirmed_permission": "true",
            "language": "en",
        },
    )
    assert convert_res.status_code == 200
    result = convert_res.json()
    assert result["status"] == "success"
    assert result["model_ready"] is True
    assert result["detected_language"] == "en"
    assert "honor your memory" in result["transcription"]


def test_speech_to_speech_requires_consent(client, created_id, wav_bytes):
    """S2S conversion is rejected without explicit affirmative consent."""
    res = client.post(
        f"/api/ofrendas/{created_id}/voice/convert",
        files={"file": ("mic_input.wav", wav_bytes, "audio/wav")},
        data={
            "authorized_by": "John Doe",
            "confirmed_permission": "false",
            "language": "hi",
        },
    )
    assert res.status_code == 400


def test_voice_status_endpoint_reports_hindi():
    """Verify voice status endpoint reports Hindi support."""
    service = get_voice_service()
    status = service.get_engine_status()
    assert "hi" in status["supported_languages"]
    assert "en" in status["supported_languages"]
