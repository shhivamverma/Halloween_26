"""Full end-to-end mocked pipeline test."""

import zipfile
import io


def test_full_pipeline(client, mock_ollama, mock_whisper, tiny_png, wav_bytes):
    """Test full pipeline: create -> photo -> audio -> generate -> page -> export.zip.

    Must run in under 5 seconds using mocks.
    """
    mock_ollama("Rosa filled every December with the smell of tamales.")

    # 1. Create
    res_create = client.post(
        "/api/ofrendas",
        json={"name": "Rosa", "language": "es", "foods": ["tamales"]},
    )
    assert res_create.status_code == 201
    oid = res_create.json()["id"]

    # 2. Upload photo
    res_photo = client.post(
        f"/api/ofrendas/{oid}/photo",
        files={"file": ("p.png", tiny_png, "image/png")},
    )
    assert res_photo.status_code == 200

    # 3. Upload audio
    res_audio = client.post(
        f"/api/ofrendas/{oid}/audio",
        files={"file": ("a.wav", wav_bytes, "audio/wav")},
    )
    assert res_audio.status_code == 200

    # 4. Generate remembrance
    res_gen = client.post(f"/api/ofrendas/{oid}/generate")
    assert res_gen.status_code == 200

    # 5. Render HTML page
    res_page = client.get(f"/api/ofrendas/{oid}/page")
    assert res_page.status_code == 200
    page = res_page.text
    assert "Rosa" in page
    assert "tamales" in page
    assert "data:image/" in page

    # 6. Export ZIP
    res_zip = client.get(f"/api/ofrendas/{oid}/export.zip")
    assert res_zip.status_code == 200
    assert "application/zip" in res_zip.headers.get("content-type", "")

    # Inspect ZIP contents
    with zipfile.ZipFile(io.BytesIO(res_zip.content), "r") as zf:
        namelist = zf.namelist()
        assert "ofrenda.html" in namelist
        assert "ofrenda.json" in namelist
        assert "transcript.txt" in namelist
        assert "photo.png" in namelist
