"""CLI regressions for invalid arguments, unreadable input, and valid results."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from coursepath.__main__ import main

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


@pytest.fixture
def two_course_file(tmp_path):
    # Self-contained courses file, so these tests do not depend on what
    # data/sample_courses.json happens to contain.
    data = {"courses": [
        {"code": "DEMO 101", "prerequisite": None},
        {"code": "DEMO 301", "prerequisite": {"op": "and", "children": [
            {"course": "DEMO 101"},
            {"op": "or", "children": [{"course": "DEMO 201"}, {"course": "DEMO 202"}]},
        ]}},
    ]}
    path = tmp_path / "courses.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_quoted_normalized_codes_are_eligible(two_course_file):
    result = run_cli("--courses", two_course_file, "--completed", " demo  101 ", "DEMO 201", "--json")
    assert result.returncode == 0
    rows = json.loads(result.stdout)
    assert [row["code"] for row in rows] == ["DEMO 101", "DEMO 301"]
    assert all(row["eligible"] for row in rows)


def test_missing_prerequisite_is_a_result_not_an_error(two_course_file):
    result = run_cli("--courses", two_course_file, "--completed", "DEMO 101", "--json")
    assert result.returncode == 0
    rows = {row["code"]: row["eligible"] for row in json.loads(result.stdout)}
    assert rows == {"DEMO 101": True, "DEMO 301": False}


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


# --- Output filtering: --eligible-only and --skip-completed (run in-process) ---

@pytest.fixture
def courses_file(tmp_path):
    data = {"courses": [
        {"code": "DEMO 101", "prerequisite": None},
        {"code": "DEMO 201", "prerequisite": {"course": "DEMO 101"}},
        {"code": "DEMO 301", "prerequisite": {"op": "and", "children": [
            {"course": "DEMO 201"},
            {"course": "DEMO 202"},
        ]}},
    ]}
    p = tmp_path / "courses.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_default_output_lists_every_course(courses_file, capsys):
    assert main(["--courses", courses_file, "--completed", "DEMO 101"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line[:5] for line in lines] == ["[YES]", "[YES]", "[NO ]"]


def test_eligible_only_hides_ineligible_courses(courses_file, capsys):
    assert main(["--courses", courses_file, "--completed", "DEMO 101", "--eligible-only"]) == 0
    out = capsys.readouterr().out
    assert "DEMO 201" in out
    assert "DEMO 301" not in out
    assert "[NO ]" not in out


def test_eligible_only_applies_to_json(courses_file, capsys):
    assert main(["--courses", courses_file, "--completed", "DEMO 101", "--eligible-only", "--json"]) == 0
    results = json.loads(capsys.readouterr().out)
    assert results  # not empty
    assert all(r["eligible"] for r in results)
    assert "DEMO 301" not in [r["code"] for r in results]


def test_eligible_only_with_nothing_eligible_still_exits_zero(tmp_path, capsys):
    p = tmp_path / "courses.json"
    p.write_text(json.dumps({"courses": [{"code": "DEMO 201", "prerequisite": {"course": "DEMO 101"}}]}))
    assert main(["--courses", str(p), "--eligible-only", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_bad_courses_file_exits_two(tmp_path, capsys):
    assert main(["--courses", str(tmp_path / "nope.json"), "--eligible-only"]) == 2
    assert "error" in capsys.readouterr().err


def test_skip_completed_hides_completed_courses(courses_file, capsys):
    assert main(["--courses", courses_file, "--completed", "DEMO 101", "--skip-completed"]) == 0
    lines = capsys.readouterr().out.splitlines()
    # DEMO 101 is gone; the ineligible DEMO 301 is still shown.
    assert [line.split(":")[0] for line in lines] == ["[YES] DEMO 201", "[NO ] DEMO 301"]


def test_skip_completed_combines_with_eligible_only(courses_file, capsys):
    args = ["--courses", courses_file, "--completed", "demo 101", "--skip-completed", "--eligible-only", "--json"]
    assert main(args) == 0
    assert [r["code"] for r in json.loads(capsys.readouterr().out)] == ["DEMO 201"]
