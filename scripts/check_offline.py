#!/usr/bin/env python3
"""Offline integrity verification script.

Scans application source code, templates, static files, and a rendered ofrenda
to ensure no external URLs, CDN links, analytics, or remote fonts exist.
Exits 0 on success, non-zero if an external URL is found.
"""

import pathlib
import re
import sys

# Configure UTF-8 output if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Regex matching external URLs (excluding localhost and 127.0.0.1)
BAD_URL_PATTERN = re.compile(
    r"(https?:)?//(?!127\.0\.0\.1|localhost)[a-z0-9.-]+\.[a-z]{2,}",
    re.IGNORECASE,
)

EXTENSIONS_TO_CHECK = {".py", ".html", ".j2", ".js", ".css", ".sh"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "data"}


def scan_files(root_dir: pathlib.Path) -> list[str]:
    """Scan directory recursively for external URLs."""
    violations = []
    for path in root_dir.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix in EXTENSIONS_TO_CHECK and path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue

            for line_no, line in enumerate(content.splitlines(), start=1):
                if path.name in ("check_offline.py", "test_offline.py") and "BAD" in line:
                    continue
                match = BAD_URL_PATTERN.search(line)
                if match:
                    violations.append(f"{path}:{line_no} -> {match.group(0)}")
    return violations


def check_rendered_ofrenda() -> list[str]:
    """Render a sample ofrenda and scan output for external URLs."""
    from app.render import render_ofrenda
    from app.schemas import OfrendaRecord

    sample = OfrendaRecord(
        id="00000000-0000-4000-8000-000000000001",
        created_at="2026-10-31T00:00:00Z",
        name="Rosa Hernandez",
        relationship="grandmother",
        birth_year=1941,
        death_year=2023,
        language="es",
        foods=["tamales de mole", "arroz con leche"],
        drinks=["café de olla"],
        songs=["Cielito Lindo"],
        objects=["her rosary"],
        story_text="Rosa loved music and family gatherings.",
        transcript="We remember her warmth every day.",
        photo=None,
        remembrance="Rosa is remembered with love.",
        generated_by="template",
        model_used=None,
    )

    rendered_html = render_ofrenda(sample)
    violations = []
    for line_no, line in enumerate(rendered_html.splitlines(), start=1):
        match = BAD_URL_PATTERN.search(line)
        if match:
            violations.append(f"Rendered HTML line {line_no} -> {match.group(0)}")
        if "http://" in line or "https://" in line:
            violations.append(f"Rendered HTML line {line_no} contains http/https protocol")
    return violations


def main() -> int:
    violations = scan_files(REPO_ROOT / "app")
    violations.extend(scan_files(REPO_ROOT / "scripts"))
    violations.extend(check_rendered_ofrenda())

    if violations:
        print("[FAIL] OFFLINE CHECK FAILED! External URLs detected:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("[OK] OFFLINE CHECK PASSED: Zero external network references detected.")
    print("     App code, templates, static assets, and rendered output are 100% offline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
