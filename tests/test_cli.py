"""CLI regressions for invalid arguments, unreadable input, and valid results."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(
        [sys.executable, "-m", "coursepath", *args],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


@pytest.mark.parametrize("codes", [[""], ["   "], ["DEMO", "101"], ["DEMO101"], ["101"], ["DEMO !"]])
def test_invalid_completed_codes_exit_cleanly(codes):
    result = run_cli("--courses", "data/sample_courses.json", "--completed", *codes)
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout


def test_directory_input_exits_cleanly(tmp_path):
    result = run_cli("--courses", str(tmp_path))
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_encoding_exits_cleanly(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_bytes(b"\xff\xfe")
    result = run_cli("--courses", str(path))
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_quoted_normalized_codes_are_eligible():
    result = run_cli("--courses", "data/sample_courses.json", "--completed", " demo  101 ", "DEMO 201", "--json")
    assert result.returncode == 0
    assert all(row["eligible"] for row in json.loads(result.stdout))


def test_missing_prerequisite_is_a_result_not_an_error():
    result = run_cli("--courses", "data/sample_courses.json", "--completed", "DEMO 101", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout)[1]["eligible"] is False


def test_help_shows_quoted_examples():
    result = run_cli("--help")
    assert result.returncode == 0
    assert '"DEMO 101" "DEMO 201"' in " ".join(result.stdout.split())


def test_permission_error_is_a_validation_error(monkeypatch):
    from coursepath.models import load_courses

    def deny_read(*args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "read_text", deny_read)
    with pytest.raises(ValueError, match="cannot read courses file"):
        load_courses("restricted.json")

