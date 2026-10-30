"""Automated API CRUD and photo upload tests."""

from app.schemas import OfrendaCreate
from app.storage import Storage


def test_create_get_roundtrip(client):
    """Test creating an ofrenda and retrieving it."""
    r = client.post(
        "/api/ofrendas",
        json={
            "name": "Rosa",
            "language": "es",
            "foods": ["tamales"],
            "songs": ["Cielito Lindo"],
        },
    )
    assert r.status_code == 201
    oid = r.json()["id"]
    assert client.get(f"/api/ofrendas/{oid}").json()["foods"] == ["tamales"]


def test_empty_name_rejected(client):
    """Empty or whitespace-only name must be rejected with 422."""
    assert client.post("/api/ofrendas", json={"name": ""}).status_code == 422
    assert client.post("/api/ofrendas", json={"name": "   "}).status_code == 422


def test_bad_language_rejected(client):
    """Language other than 'en' or 'es' must return 422."""
    assert client.post("/api/ofrendas", json={"name": "A", "language": "fr"}).status_code == 422


def test_unknown_id_404(client):
    """Valid UUID that doesn't exist returns 404."""
    assert client.get("/api/ofrendas/00000000-0000-4000-8000-000000000000").status_code == 404


def test_path_traversal_blocked(client):
    """Path traversal attempt in ID returns 404 or 422."""
    assert client.get("/api/ofrendas/..%2F..%2Fetc").status_code in (404, 422)


def test_photo_wrong_type_415(client, created_id):
    """Non-image upload returns 415."""
    r = client.post(
        f"/api/ofrendas/{created_id}/photo",
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 415


def test_photo_ok_and_delete(client, created_id, tiny_png):
    """Valid photo upload succeeds and deletion removes ofrenda."""
    r = client.post(
        f"/api/ofrendas/{created_id}/photo",
        files={"file": ("p.png", tiny_png, "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["photo"] == "photo.png"

    # Confirm list includes it
    listing = client.get("/api/ofrendas").json()
    assert any(o["id"] == created_id for o in listing)

    # Delete ofrenda
    assert client.delete(f"/api/ofrendas/{created_id}").status_code == 204
    assert client.get(f"/api/ofrendas/{created_id}").status_code == 404


def test_limits(client):
    """Enforce data limits: 13 foods -> 422, story_text > 5000 -> 422."""
    too_many_foods = [f"food_{i}" for i in range(13)]
    r1 = client.post("/api/ofrendas", json={"name": "Rosa", "foods": too_many_foods})
    assert r1.status_code == 422

    too_long_story = "a" * 5001
    r2 = client.post("/api/ofrendas", json={"name": "Rosa", "story_text": too_long_story})
    assert r2.status_code == 422

    too_long_food_name = ["a" * 61]
    r3 = client.post("/api/ofrendas", json={"name": "Rosa", "foods": too_long_food_name})
    assert r3.status_code == 422


def test_persistence_across_restart(tmp_data_dir):
    """Storage data persists on disk and is loaded accurately across restarts."""
    storage1 = Storage(tmp_data_dir)
    record = storage1.create(OfrendaCreate(name="Rosa Hernandez", language="es", foods=["tamales"]))

    storage2 = Storage(tmp_data_dir)
    loaded = storage2.get(record.id)
    assert loaded is not None
    assert loaded.name == "Rosa Hernandez"
    assert loaded.foods == ["tamales"]


def test_patch_ofrenda(client, created_id):
    """Test updating fields on an existing ofrenda via PATCH."""
    r = client.patch(
        f"/api/ofrendas/{created_id}",
        json={"story_text": "Updated family memories", "language": "en"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["story_text"] == "Updated family memories"
    assert data["language"] == "en"


def test_seed_demo_ofrenda(client):
    """Test seeding the 1-click hackathon demo ofrenda."""
    r = client.post("/api/demo/seed")
    assert r.status_code == 200
    demo = r.json()
    assert demo["name"] == "Rosa Hernandez"
    assert "tamales de mole" in demo["foods"]
    assert demo["photo"] == "photo.png"
    assert "Rosa" in demo["remembrance"]
    assert demo["voice_profile"]["has_reference"] is True
    assert demo["voice_profile"]["has_synthesized_audio"] is True

    # Standalone HTML altar page rendered
    page_r = client.get(f"/api/ofrendas/{demo['id']}/page")
    assert page_r.status_code == 200
    assert "Rosa Hernandez" in page_r.text
    assert "candle-interactive" in page_r.text

    # Voice audio accessible
    voice_r = client.get(f"/api/ofrendas/{demo['id']}/voice/audio")
    assert voice_r.status_code in (200, 206)

