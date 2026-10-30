#!/usr/bin/env python3
"""Seed script for Offline Ofrenda Keeper.

Creates the fictional 'Abuela Rosa' demo ofrenda with pre-filled facts,
portrait photo, written memories, and pre-generated remembrance so demonstrations
never depend on live speech recognition or model latency.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import get_data_dir


def generate_sample_photo_bytes() -> bytes:
    """Generate a minimal valid 1x1 PNG or dignified sample portrait icon."""
    # 1x1 transparent PNG header
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
        b"?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def seed_demo_ofrenda() -> str:
    """Create Abuela Rosa demo ofrenda on disk."""
    data_dir = get_data_dir()
    demo_id = "00000000-0000-4000-8000-000000000001"
    folder = data_dir / "ofrendas" / demo_id
    folder.mkdir(parents=True, exist_ok=True)

    # Save photo
    photo_file = folder / "photo.png"
    photo_file.write_bytes(generate_sample_photo_bytes())

    remembrance_text = (
        "Rosa Hernandez es recordada con infinito amor por toda su familia. Su hogar siempre estuvo impregnado "
        "del dulce aroma del pan de muerto, los tamales de mole y el reconfortante café de olla. Cada rincón "
        "guardaba el eco de su risa y de canciones entrañables como Cielito Lindo y Amor Eterno, que llenaban de "
        "alegría las tardes familiares. Su rosario de plata y sus agujas de tejer permanecen como testimonios "
        "silenciosos de sus manos generosas y su corazón paciente. Este altar rinde homenaje a su vida luminosa "
        "y mantiene encendida la llama de su memoria."
    )

    demo_data = {
        "id": demo_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": "Rosa Hernandez",
        "relationship": "Abuela",
        "birth_year": 1941,
        "death_year": 2023,
        "language": "es",
        "foods": ["tamales de mole", "arroz con leche", "pan de muerto", "mole negro"],
        "drinks": ["café de olla", "atole de vainilla"],
        "songs": ["Cielito Lindo", "Amor Eterno"],
        "objects": ["su rosario de plata", "agujas de tejer", "rebozo bordado"],
        "story_text": (
            "Abuela Rosa nos enseñó que la cocina es el corazón del hogar. Cada diciembre nos reuníamos "
            "todos para preparar tamales juntos, mientras ella cantaba y contaba historias de su juventud."
        ),
        "transcript": (
            "Recuerdo cuando nos decía: 'La vida se celebra con amor, con música y compartiendo lo que "
            "tenemos en la mesa'."
        ),
        "photo": "photo.png",
        "remembrance": remembrance_text,
        "generated_by": "ollama:llama3.2:3b",
        "model_used": "llama3.2:3b",
    }

    json_path = folder / "ofrenda.json"
    json_path.write_text(json.dumps(demo_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[OK] Fictional 'Abuela Rosa' demo ofrenda created successfully!")
    print(f"     ID: {demo_id}")
    print(f"     Folder: {folder}")
    print(f"     Preview URL: http://127.0.0.1:8000/api/ofrendas/{demo_id}/page")
    return demo_id


if __name__ == "__main__":
    seed_demo_ofrenda()
