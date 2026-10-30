#!/usr/bin/env python3
"""Seed script for Offline Ofrenda Keeper.

Creates the fictional 'Abuela Rosa' demo ofrenda with pre-filled facts,
portrait photo, written memories, pre-generated remembrance, and synthetic voice
so demonstrations never depend on live speech recognition or model latency.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.demo import DEMO_OFRENDA_ID, seed_demo_ofrenda
from app.storage import Storage


def seed_demo_ofrenda_script() -> str:
    store = Storage()
    record = seed_demo_ofrenda(store)
    print("[OK] Fictional 'Abuela Rosa' demo ofrenda created successfully!")
    print(f"     ID: {record.id}")
    print(f"     Name: {record.name}")
    print(f"     Preview URL: http://127.0.0.1:8000/api/ofrendas/{record.id}/page")
    return record.id


if __name__ == "__main__":
    seed_demo_ofrenda_script()
