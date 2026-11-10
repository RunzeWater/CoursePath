"""Models: loading, normalization, and validation failures."""

import json

import pytest

from coursepath.models import Course, load_courses, normalize_code


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


@pytest.mark.parametrize("op", ["AND", "And", "OR", "Or"])
def test_op_must_be_lowercase(op, tmp_path):
    # Only lowercase "and" / "or" are valid; "AND" must not be silently accepted.
    rule = {"op": op, "children": [{"course": "DEMO 101"}]}
    with pytest.raises(ValueError, match="op must be"):
        Course(code="DEMO 301", prerequisite=rule)
    p = tmp_path / "bad_op.json"
    p.write_text(json.dumps({"courses": [{"code": "DEMO 301", "prerequisite": rule}]}))
    with pytest.raises(ValueError, match="op must be"):
        load_courses(p)


@pytest.mark.parametrize("op", ["and", "or"])
def test_empty_children_rejected(op, tmp_path):
    rule = {"op": op, "children": []}
    with pytest.raises(ValueError, match="non-empty"):
        Course(code="DEMO 301", prerequisite=rule)
    p = tmp_path / "empty_children.json"
    p.write_text(json.dumps({"courses": [{"code": "DEMO 301", "prerequisite": rule}]}))
    with pytest.raises(ValueError, match="non-empty"):
        load_courses(p)


def test_missing_children_rejected():
    with pytest.raises(ValueError):
        Course(code="DEMO 301", prerequisite={"op": "and"})


def test_bad_rule_nested_deep_is_rejected():
    # The invalid node sits three levels down; validation must still reach it.
    rule = {"op": "and", "children": [
        {"course": "DEMO 101"},
        {"op": "or", "children": [
            {"course": "DEMO 201"},
            {"op": "and", "children": [{"course": "DEMO 202"}, {"op": "or", "children": []}]},
        ]},
    ]}
    with pytest.raises(ValueError, match="non-empty"):
        Course(code="DEMO 401", prerequisite=rule)
