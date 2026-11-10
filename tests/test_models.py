"""Models: loading, normalization, and validation failures."""

import json

import pytest

from coursepath.models import load_courses, normalize_code


def test_normalize_code():
    assert normalize_code("  cmput   174 ") == "CMPUT 174"
    with pytest.raises(ValueError):
        normalize_code("   ")


def test_load_sample_file(tmp_path):
    data = {"courses": [
        {"code": "demo 101", "title": "Intro", "prerequisite": None},
        {"code": "DEMO 201", "prerequisite": {"course": "DEMO 101"}},
    ]}
    p = tmp_path / "courses.json"
    p.write_text(json.dumps(data))
    courses = load_courses(p)
    assert [c.code for c in courses] == ["DEMO 101", "DEMO 201"]


def test_load_rejects_bad_rule(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"courses": [{"code": "DEMO 301", "prerequisite": {"op": "xor", "children": []}}]}))
    with pytest.raises(ValueError):
        load_courses(p)


def test_load_rejects_duplicate_code(tmp_path):
    p = tmp_path / "dup.json"
    p.write_text(json.dumps({"courses": [{"code": "DEMO 101"}, {"code": "demo 101"}]}))
    with pytest.raises(ValueError):
        load_courses(p)


def test_load_rejects_missing_file(tmp_path):
    with pytest.raises(ValueError):
        load_courses(tmp_path / "nope.json")
