"""Pytest configuration, shared fixtures, and test mocks."""

import struct
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.config as config


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Ensure every test gets an isolated temporary DATA_DIR."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    return data_dir


@pytest.fixture
def tmp_data_dir(isolated_data_dir):
    """Return the temporary DATA_DIR path."""
    return isolated_data_dir


@pytest.fixture
def client():
    """Return FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def tiny_png() -> bytes:
    """Minimal valid 1x1 transparent PNG."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
        b"?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture
def wav_bytes() -> bytes:
    """Minimal valid RIFF WAV audio file."""
    num_samples = 16000  # 1 sec at 16kHz
    header = b"RIFF" + struct.pack("<I", 36 + num_samples * 2) + b"WAVEfmt "
    fmt_chunk = struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16)
    data_header = b"data" + struct.pack("<I", num_samples * 2)
    data = b"\x00" * (num_samples * 2)
    return header + fmt_chunk + data_header + data


@pytest.fixture
def created_id(client) -> str:
    """Create a sample ofrenda and return its ID."""
    r = client.post(
        "/api/ofrendas",
        json={
            "name": "Rosa Hernandez",
            "relationship": "grandmother",
            "birth_year": 1941,
            "death_year": 2023,
            "language": "es",
            "foods": ["tamales", "arroz con leche"],
            "drinks": ["cafe de olla"],
            "songs": ["Cielito Lindo"],
            "objects": ["her rosary"],
            "story_text": "Rosa loved making tamales for the family every winter.",
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
def sample_ofrenda():
    """Return a dictionary representing sample ofrenda data."""
    from app.schemas import OfrendaRecord

    return OfrendaRecord(
        id="12345678-1234-5678-1234-567812345678",
        created_at="2026-10-31T00:00:00Z",
        name="Rosa Hernandez",
        relationship="grandmother",
        birth_year=1941,
        death_year=2023,
        language="es",
        foods=["tamales", "arroz con leche"],
        drinks=["cafe de olla"],
        songs=["Cielito Lindo"],
        objects=["her rosary", "knitting needles"],
        story_text="Rosa loved music and cooking for everyone.",
        transcript="She taught us how to fold tamale leaves.",
        photo=None,
        remembrance="Rosa is remembered with love.",
        generated_by="template",
        model_used=None,
    )


@pytest.fixture
def sample_ofrenda_with_photo(sample_ofrenda, tmp_data_dir, tiny_png):
    """Return sample ofrenda with photo file written to disk."""
    folder = tmp_data_dir / "ofrendas" / sample_ofrenda.id
    folder.mkdir(parents=True, exist_ok=True)
    photo_file = folder / "photo.png"
    photo_file.write_bytes(tiny_png)
    sample_ofrenda.photo = "photo.png"
    return sample_ofrenda


@pytest.fixture
def minimal_ofrenda():
    """Return minimal valid ofrenda record."""
    from app.schemas import OfrendaRecord

    return OfrendaRecord(
        id="87654321-4321-8765-4321-876543210987",
        created_at="2026-10-31T00:00:00Z",
        name="Rosa",
        relationship=None,
        birth_year=None,
        death_year=None,
        language="en",
        foods=[],
        drinks=[],
        songs=[],
        objects=[],
        story_text=None,
        transcript=None,
        photo=None,
        remembrance=None,
        generated_by=None,
        model_used=None,
    )
