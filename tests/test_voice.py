"""Tests for local AI voice recreation, ethical consent validation, and provenance watermarking."""

import io
import zipfile
import pytest
from app.voice.watermark import inject_riff_provenance, read_riff_metadata
from app.voice.mock_engine import MockVoiceEngine
from app.render import render_ofrenda
from app.storage import Storage


def test_watermark_injection_and_extraction(wav_bytes):
    """Test embedding and reading RIFF INFO metadata chunks."""
    watermarked = inject_riff_provenance(
        wav_bytes,
        deceased_name="Rosa Hernandez",
        authorized_by="Maria Hernandez",
        model_name="MockVoiceEngine",
    )
    assert len(watermarked) > len(wav_bytes)
    assert b"LIST" in watermarked
    assert b"INFO" in watermarked
    assert b"IART" in watermarked

    meta = read_riff_metadata(watermarked)
    assert "Offline Ofrenda Keeper" in meta.get("IART", "")
    assert "Rosa Hernandez" in meta.get("INAM", "")
    assert "Maria Hernandez" in meta.get("ICMT", "")


def test_mock_voice_engine_generates_watermarked_wav(tmp_path):
    """Mock engine generates valid synthetic WAV audio with disclaimer metadata."""
    engine = MockVoiceEngine()
    assert engine.is_available()
    assert "mock" in engine.name
    assert "es" in engine.supported_languages

    out_file = tmp_path / "mock_test.wav"
    duration = engine.synthesize(
        text="Rosa es recordada con inmenso carino y gratitud.",
        reference_audio_path=tmp_path / "ref.wav",
        output_path=out_file,
        language="es",
    )
    assert duration > 0
    assert out_file.exists()
    wav_out = out_file.read_bytes()
    assert wav_out.startswith(b"RIFF")
    meta = read_riff_metadata(wav_out)
    assert "Offline Ofrenda Keeper" in meta.get("IART", "")
    assert "Memorial Simulation" in meta.get("INAM", "")


def test_upload_reference_requires_affirmative_consent(client, created_id, wav_bytes):
    """Uploading reference audio without affirmative consent is rejected with HTTP 400."""
    # Missing confirmed_permission
    r1 = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Maria Hernandez", "confirmed_permission": "false"},
    )
    assert r1.status_code == 400
    msg = r1.json()["detail"].lower()
    assert any(w in msg for w in ("consent", "authorization", "permission"))

    # Missing authorized_by name
    r2 = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "   ", "confirmed_permission": "true"},
    )
    assert r2.status_code == 400


def test_upload_reference_rejects_invalid_file_types(client, created_id):
    """Uploading executable or invalid extensions as reference audio is rejected."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("malicious.exe", b"fake binary", "application/octet-stream")},
        data={"authorized_by": "Maria Hernandez", "confirmed_permission": "true"},
    )
    assert r.status_code in (400, 415)


def test_upload_reference_success(client, created_id, wav_bytes):
    """Uploading valid reference audio records consent and updates metadata."""
    r = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("abuela_voice.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Maria Hernandez (Daughter)", "confirmed_permission": "true"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["has_reference"] is True
    assert data["authorized_by"] == "Maria Hernandez (Daughter)"

    # Verify consent log on disk
    store = Storage()
    voice_folder = store.get_voice_folder(created_id)
    assert (voice_folder / "consent_log.json").exists()
    assert (voice_folder / "reference_audio.wav").exists()


def test_synthesize_voice_requires_consent_and_reference(client, created_id):
    """Synthesis without consent, remembrance, or reference audio fails with HTTP 400 or 422."""
    # Attempt without consent
    r_no_consent = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "authorized_by": "Maria Hernandez",
            "confirmed_permission": False,
            "language": "es",
        },
    )
    assert r_no_consent.status_code in (400, 422)

    # Attempt without remembrance text
    r_no_rem = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "authorized_by": "Maria Hernandez",
            "confirmed_permission": True,
            "language": "es",
        },
    )
    assert r_no_rem.status_code == 400
    assert "remembrance" in r_no_rem.json()["detail"].lower()

    # Set remembrance text
    client.patch(
        f"/api/ofrendas/{created_id}",
        json={"remembrance": "Rosa es recordada con amor."},
    )

    # Attempt with consent but no reference audio uploaded yet
    r_no_ref = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "authorized_by": "Maria Hernandez",
            "confirmed_permission": True,
            "language": "es",
        },
    )
    assert r_no_ref.status_code == 400
    assert "reference" in r_no_ref.json()["detail"].lower()


def test_full_voice_synthesis_pipeline(client, created_id, wav_bytes):
    """Upload reference, synthesize remembrance audio, stream, download, and delete."""
    # 1. Provide a remembrance text
    client.patch(
        f"/api/ofrendas/{created_id}",
        json={"remembrance": "Rosa vivira por siempre en nuestros corazones."},
    )

    # 2. Upload reference voice with family permission
    r_ref = client.post(
        f"/api/ofrendas/{created_id}/voice/reference",
        files={"file": ("abuela.wav", wav_bytes, "audio/wav")},
        data={"authorized_by": "Maria Hernandez", "confirmed_permission": "true"},
    )
    assert r_ref.status_code == 200

    # 3. Synthesize voice recreation
    r_synth = client.post(
        f"/api/ofrendas/{created_id}/voice/synthesize",
        json={
            "authorized_by": "Maria Hernandez",
            "confirmed_permission": True,
            "language": "es",
            "engine": "mock",
        },
    )
    assert r_synth.status_code == 200
    res = r_synth.json()
    assert res["has_synthesized_audio"] is True
    assert res["synthesized_duration_s"] > 0
    assert "mock" in res["model_used"].lower()

    # 4. Stream synthesized audio
    r_audio = client.get(f"/api/ofrendas/{created_id}/voice/audio")
    assert r_audio.status_code == 200
    assert "audio/wav" in r_audio.headers.get("content-type", "")
    assert r_audio.content.startswith(b"RIFF")

    # 5. Test byte-range request support
    r_range = client.get(
        f"/api/ofrendas/{created_id}/voice/audio",
        headers={"Range": "bytes=0-99"},
    )
    assert r_range.status_code == 206
    assert len(r_range.content) == 100

    # 6. Test download endpoint
    r_dl = client.get(f"/api/ofrendas/{created_id}/voice/download")
    assert r_dl.status_code == 200
    assert "attachment" in r_dl.headers.get("content-disposition", "")

    # 7. Test Altar Page contains audio player and mandatory ethical simulation badge
    r_page = client.get(f"/api/ofrendas/{created_id}/page")
    assert r_page.status_code == 200
    page_html = r_page.text
    assert "<audio" in page_html
    assert "memorial-voice-player" in page_html
    assert "Recreaci\u00f3n de Voz con IA" in page_html or "AI-Generated Voice Recreation" in page_html
    assert "Maria Hernandez" in page_html

    # 8. Test ZIP export bundles synthetic audio
    r_zip = client.get(f"/api/ofrendas/{created_id}/export.zip")
    assert r_zip.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_zip.content)) as zf:
        namelist = zf.namelist()
        assert "remembrance_synthesized.wav" in namelist
        assert "reference_audio.wav" in namelist

    # 9. Delete voice profile
    r_del = client.delete(f"/api/ofrendas/{created_id}/voice")
    assert r_del.status_code == 200

    # Confirm audio endpoint now returns 404
    r_audio_after = client.get(f"/api/ofrendas/{created_id}/voice/audio")
    assert r_audio_after.status_code == 404

    # Confirm page no longer has the voice player element
    r_page_after = client.get(f"/api/ofrendas/{created_id}/page")
    assert "<audio" not in r_page_after.text
    assert '<div class="memorial-voice-player">' not in r_page_after.text


def test_health_check_includes_voice_status(client):
    """Health check includes voice synthesis availability and engine info."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "voice" in data
    assert "available" in data["voice"]
    assert "active_engine" in data["voice"]


def test_mms_engine_properties():
    """Verify MMS-VITS lightweight engine metadata and language support."""
    from app.voice.mms_engine import MMSVitsEngine

    engine = MMSVitsEngine()
    assert engine.name == "mms-vits"
    assert "hi" in engine.supported_languages
    assert "en" in engine.supported_languages
    assert "es" in engine.supported_languages
    assert engine.is_available() is True

