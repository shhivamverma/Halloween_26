"""Disk storage implementation for ofrenda records and media."""

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import List, Optional
import uuid

from app.config import get_data_dir
from app.schemas import OfrendaCreate, OfrendaRecord, OfrendaSummary, OfrendaUpdate


def validate_uuid(val: str | uuid.UUID) -> str:
    """Validate that val is a valid UUID4 string to prevent path traversal."""
    try:
        parsed = uuid.UUID(str(val).strip())
        return str(parsed)
    except Exception as exc:
        raise ValueError(f"Invalid UUID format: {val}") from exc


class Storage:
    """Manage ofrenda records and files stored on disk."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir is not None else get_data_dir()
        self.ofrendas_dir = self.data_dir / "ofrendas"
        self.ofrendas_dir.mkdir(parents=True, exist_ok=True)

    def _get_folder(self, ofrenda_id: str) -> Path:
        valid_id = validate_uuid(ofrenda_id)
        folder = self.ofrendas_dir / valid_id
        return folder

    def get_folder(self, ofrenda_id: str) -> Path:
        """Return path to ofrenda directory after validating UUID."""
        return self._get_folder(ofrenda_id)

    def create(self, payload: OfrendaCreate) -> OfrendaRecord:
        """Create a new ofrenda directory and save ofrenda.json."""
        new_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        record = OfrendaRecord(
            id=new_id,
            created_at=created_at,
            name=payload.name,
            relationship=payload.relationship,
            birth_year=payload.birth_year,
            death_year=payload.death_year,
            language=payload.language,
            foods=payload.foods,
            drinks=payload.drinks,
            songs=payload.songs,
            objects=payload.objects,
            story_text=payload.story_text,
            transcript=None,
            photo=None,
            remembrance=None,
            generated_by=None,
            model_used=None,
        )

        folder = self._get_folder(new_id)
        folder.mkdir(parents=True, exist_ok=True)
        json_path = folder / "ofrenda.json"
        json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def get(self, ofrenda_id: str) -> Optional[OfrendaRecord]:
        """Fetch an ofrenda by ID or return None if not found."""
        folder = self._get_folder(ofrenda_id)
        json_path = folder / "ofrenda.json"
        if not json_path.exists():
            return None
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return OfrendaRecord(**data)

    def list(self) -> List[OfrendaSummary]:
        """List summary of all existing ofrendas."""
        summaries: List[OfrendaSummary] = []
        if not self.ofrendas_dir.exists():
            return summaries

        for entry in self.ofrendas_dir.iterdir():
            if entry.is_dir():
                json_path = entry / "ofrenda.json"
                if json_path.exists():
                    try:
                        data = json.loads(json_path.read_text(encoding="utf-8"))
                        summaries.append(
                            OfrendaSummary(
                                id=data["id"],
                                name=data["name"],
                                created_at=data["created_at"],
                                relationship=data.get("relationship"),
                                photo=data.get("photo"),
                            )
                        )
                    except Exception:
                        continue
        summaries.sort(key=lambda s: s.created_at, reverse=True)
        return summaries

    def update(self, ofrenda_id: str, updates: OfrendaUpdate | dict) -> Optional[OfrendaRecord]:
        """Update fields on an ofrenda record."""
        record = self.get(ofrenda_id)
        if not record:
            return None

        update_dict = updates.model_dump(exclude_unset=True) if isinstance(updates, OfrendaUpdate) else updates

        record_dict = record.model_dump()
        for k, v in update_dict.items():
            if v is not None:
                record_dict[k] = v

        updated_record = OfrendaRecord(**record_dict)
        folder = self._get_folder(ofrenda_id)
        json_path = folder / "ofrenda.json"
        json_path.write_text(updated_record.model_dump_json(indent=2), encoding="utf-8")
        return updated_record

    def delete(self, ofrenda_id: str) -> bool:
        """Delete an ofrenda directory from disk. Returns True if deleted."""
        folder = self._get_folder(ofrenda_id)
        if not folder.exists():
            return False
        shutil.rmtree(folder)
        return True

    def save_photo(self, ofrenda_id: str, photo_bytes: bytes, ext: str) -> OfrendaRecord:
        """Save photo to ofrenda directory and update record."""
        record = self.get(ofrenda_id)
        if not record:
            raise KeyError(f"Ofrenda {ofrenda_id} not found")

        folder = self._get_folder(ofrenda_id)
        filename = f"photo.{ext}"
        target_path = folder / filename

        # Remove existing photo files if extension differs
        for old_file in folder.glob("photo.*"):
            try:
                old_file.unlink()
            except OSError:
                pass

        target_path.write_bytes(photo_bytes)
        record.photo = filename

        json_path = folder / "ofrenda.json"
        json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record
