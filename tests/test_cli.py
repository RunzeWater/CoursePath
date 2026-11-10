"""CLI: output filtering and exit codes."""

import json

import pytest

from coursepath.__main__ import main


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
