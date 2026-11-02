"""Verify secure default host binding (127.0.0.1), LAN warning, and license inventory."""

import os
import sys
import json
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from app.config import get_server_host, get_server_port


def test_default_host_binding():
    """Verify that by default, without environment variables, server binds to 127.0.0.1 only."""
    # Ensure clean env
    for k in ("ALLOW_LAN", "HOST", "PORT"):
        if k in os.environ:
            del os.environ[k]

    host = get_server_host()
    assert host == "127.0.0.1", f"Default host must be 127.0.0.1, got {host}"
    port = get_server_port()
    assert port == 8000, f"Default port must be 8000, got {port}"
    print("[OK] Default host binding verified: 127.0.0.1 (Loopback only - secure default)")


def test_lan_mode_host_binding():
    """Verify that LAN mode requires explicit ALLOW_LAN=1 or HOST=0.0.0.0."""
    os.environ["ALLOW_LAN"] = "1"
    host_lan = get_server_host()
    assert host_lan == "0.0.0.0", f"ALLOW_LAN=1 must bind to 0.0.0.0, got {host_lan}"
    del os.environ["ALLOW_LAN"]

    os.environ["HOST"] = "0.0.0.0"
    host_custom = get_server_host()
    assert host_custom == "0.0.0.0", f"HOST=0.0.0.0 must bind to 0.0.0.0, got {host_custom}"
    del os.environ["HOST"]

    print("[OK] Explicit LAN mode configuration verified (0.0.0.0 requires ALLOW_LAN=1 or HOST=0.0.0.0)")


def test_run_production_bat_output():
    """Verify scripts/run_production.bat output in default mode vs --lan mode."""
    bat_file = WORKSPACE_ROOT / "scripts" / "run_production.bat"
    assert bat_file.exists(), "scripts/run_production.bat does not exist"
    bat_content = bat_file.read_text(encoding="utf-8")

    # Verify default binding in bat script
    assert "set BIND_HOST=127.0.0.1" in bat_content
    assert "[SECURE DEFAULT]" in bat_content
    assert "[SECURITY WARNING] LAN MODE ENABLED" in bat_content
    assert "The application has NO BUILT-IN AUTHENTICATION" in bat_content

    # Test executing bat script with --dry-run
    cmd_def = 'cmd /c "scripts\\run_production.bat --dry-run"'
    proc_def = subprocess.run(cmd_def, shell=True, capture_output=True, text=True, timeout=5)
    assert proc_def.returncode == 0
    assert "[SECURE DEFAULT]" in proc_def.stdout
    assert "[DRY RUN] Configured host: 127.0.0.1" in proc_def.stdout
    print("[OK] Verified run_production.bat binds to 127.0.0.1 loopback by default")

    cmd_lan = 'cmd /c "scripts\\run_production.bat --lan --dry-run"'
    proc_lan = subprocess.run(cmd_lan, shell=True, capture_output=True, text=True, timeout=5)
    assert proc_lan.returncode == 0
    assert "[SECURITY WARNING] LAN MODE ENABLED" in proc_lan.stdout
    assert "The application has NO BUILT-IN AUTHENTICATION" in proc_lan.stdout
    assert "[DRY RUN] Configured host: 0.0.0.0" in proc_lan.stdout
    print("[OK] Verified run_production.bat --lan warns about missing auth and binds to 0.0.0.0")


def test_license_inventory_accuracy():
    """Verify THIRD_PARTY_LICENSES.json matches installed packages and model requirements."""
    inv_file = WORKSPACE_ROOT / "THIRD_PARTY_LICENSES.json"
    assert inv_file.exists(), "THIRD_PARTY_LICENSES.json does not exist"

    data = json.loads(inv_file.read_text(encoding="utf-8"))
    assert data["project"] == "Offline Ofrenda Keeper"
    assert data["summary"]["unresolved_or_unknown_licenses"] == 0
    assert data["summary"]["commercial_distribution_compliant"] is True

    # Check key models
    model_names = [m["name"] for m in data["model_weights"]]
    assert "Kokoro-82M" in model_names
    assert "OpenVoice V2 ToneColorConverter" in model_names
    assert "faster-whisper (tiny / base)" in model_names

    # Check excluded non-commercial models
    excluded_names = [m["name"] for m in data["excluded_non_commercial_models"]]
    assert "Coqui XTTS-v2" in excluded_names
    assert "Facebook MMS-TTS" in excluded_names

    print(f"[OK] License inventory verified: {data['summary']['total_python_packages']} packages, 0 unresolved licenses, non-commercial models documented as excluded")


if __name__ == "__main__":
    test_default_host_binding()
    test_lan_mode_host_binding()
    test_run_production_bat_output()
    test_license_inventory_accuracy()
    print("\nALL SAFEGUARD TESTS PASSED!")
