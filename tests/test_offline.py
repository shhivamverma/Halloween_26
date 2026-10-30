"""Static scan, HTTP guard, and offline verification tests."""

import pathlib
import re
import subprocess
import sys
import pytest

BAD = re.compile(r"(https?:)?//(?!127\.0\.0\.1|localhost)[a-z0-9.-]+\.[a-z]{2,}", re.I)


def test_static_files_have_no_external_urls():
    """Verify static assets contain no external CDN links, web fonts, or scripts."""
    static_dir = pathlib.Path("app/static")
    files_checked = 0
    for f in static_dir.rglob("*"):
        if f.suffix in {".html", ".js", ".css"}:
            text = f.read_text(encoding="utf-8")
            match = BAD.search(text)
            assert not match, f"External URL found in {f}: {match.group(0)}"
            files_checked += 1
    assert files_checked >= 3


def test_static_files_served(client):
    """Verify static assets are properly mounted and served by FastAPI."""
    r_index = client.get("/")
    assert r_index.status_code == 200
    assert "Offline Ofrenda Keeper" in r_index.text

    r_js = client.get("/app.js")
    assert r_js.status_code == 200

    r_css = client.get("/style.css")
    assert r_css.status_code == 200


def test_http_guard_blocks_external(monkeypatch):
    """Network client guard strictly raises ValueError when attempting to contact non-local host."""
    from app.net import local_client

    with pytest.raises(ValueError) as excinfo:
        local_client().get("https://example.com")
    assert "forbidden" in str(excinfo.value).lower()


def test_check_offline_script_passes():
    """Scripts/check_offline.py must exit 0, confirming zero external URLs across the project."""
    proc = subprocess.run([sys.executable, "scripts/check_offline.py"], capture_output=True, text=True)
    assert proc.returncode == 0, f"check_offline.py failed:\n{proc.stdout}\n{proc.stderr}"
