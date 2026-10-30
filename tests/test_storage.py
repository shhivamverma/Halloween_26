"""Unit tests for disk storage."""

import pytest
from app.schemas import OfrendaCreate, OfrendaUpdate
from app.storage import Storage, validate_uuid


def test_validate_uuid():
    """Verify UUID validation accepts valid UUIDs and rejects traversal/garbage."""
    valid = "12345678-1234-5678-1234-567812345678"
    assert validate_uuid(valid) == valid

    with pytest.raises(ValueError):
        validate_uuid("../../etc/passwd")

    with pytest.raises(ValueError):
        validate_uuid("invalid-uuid")


def test_storage_create_get_delete(tmp_data_dir):
    """Test full CRUD lifecycle in storage layer."""
    storage = Storage(tmp_data_dir)
    created = storage.create(
        OfrendaCreate(
            name="Rosa Hernandez",
            language="es",
            foods=["tamales"],
            songs=["Cielito Lindo"],
        )
    )
    assert created.id is not None
    assert created.name == "Rosa Hernandez"

    fetched = storage.get(created.id)
    assert fetched is not None
    assert fetched.name == "Rosa Hernandez"
    assert fetched.foods == ["tamales"]

    # Update
    updated = storage.update(created.id, OfrendaUpdate(story_text="A warm memory."))
    assert updated.story_text == "A warm memory."

    # List
    summaries = storage.list()
    assert len(summaries) == 1
    assert summaries[0].id == created.id

    # Delete
    assert storage.delete(created.id) is True
    assert storage.get(created.id) is None
    assert len(storage.list()) == 0


def test_storage_photo_save(tmp_data_dir, tiny_png):
    """Test saving a photo and updating the ofrenda record."""
    storage = Storage(tmp_data_dir)
    created = storage.create(OfrendaCreate(name="Rosa"))
    updated = storage.save_photo(created.id, tiny_png, "png")
    assert updated.photo == "photo.png"

    folder = storage.get_folder(created.id)
    assert (folder / "photo.png").exists()
    assert (folder / "photo.png").read_bytes() == tiny_png


def test_storage_persistence_across_instances(tmp_data_dir):
    """Verify data is persisted on disk and readable by a new Storage instance."""
    storage1 = Storage(tmp_data_dir)
    created = storage1.create(OfrendaCreate(name="Rosa Hernandez", foods=["tamales"]))

    storage2 = Storage(tmp_data_dir)
    fetched = storage2.get(created.id)
    assert fetched is not None
    assert fetched.name == "Rosa Hernandez"
    assert fetched.foods == ["tamales"]
