"""Eligibility: success, failure, and boundary cases."""

from coursepath.eligibility import check_all, check_course
from coursepath.models import Course


def _course(code, prereq=None):
    return Course(code=code, prerequisite=prereq)


def test_no_prerequisite_is_eligible():
    assert check_course(_course("DEMO 101"), set()).eligible is True


def test_leaf_pass_and_fail():
    c = _course("DEMO 201", {"course": "DEMO 101"})
    assert check_course(c, {"DEMO 101"}).eligible is True
    r = check_course(c, set())
    assert r.eligible is False and "DEMO 101" in r.reason


def test_and_requires_every_child():
    c = _course("DEMO 301", {"op": "and", "children": [{"course": "DEMO 101"}, {"course": "DEMO 201"}]})
    assert check_course(c, {"DEMO 101", "DEMO 201"}).eligible is True
    assert check_course(c, {"DEMO 101"}).eligible is False


def test_or_needs_any_child():
    c = _course("DEMO 301", {"op": "or", "children": [{"course": "DEMO 201"}, {"course": "DEMO 202"}]})
    assert check_course(c, {"DEMO 202"}).eligible is True
    assert check_course(c, {"DEMO 101"}).eligible is False


def test_nested_and_of_or():
    # DEMO 101 AND (DEMO 201 OR DEMO 202) — the README's example shape.
    c = _course("DEMO 301", {"op": "and", "children": [
        {"course": "DEMO 101"},
        {"op": "or", "children": [{"course": "DEMO 201"}, {"course": "DEMO 202"}]},
    ]})
    assert check_course(c, {"DEMO 101", "DEMO 202"}).eligible is True
    assert check_course(c, {"DEMO 201", "DEMO 202"}).eligible is False  # missing DEMO 101
    assert check_course(c, {"DEMO 101"}).eligible is False  # neither OR branch


def test_completed_codes_are_normalized():
    c = _course("DEMO 201", {"course": "DEMO 101"})
    assert check_course(c, {"demo  101"}).eligible is True


def test_unknown_completed_codes_are_ignored():
    c = _course("DEMO 201", {"course": "DEMO 101"})
    assert check_course(c, {"DEMO 999", "DEMO 101"}).eligible is True


def test_check_all_preserves_file_order_and_reasons():
    courses = [_course("DEMO 101"), _course("DEMO 201", {"course": "DEMO 101"})]
    results = check_all(courses, {"DEMO 101"})
    assert [r.code for r in results] == ["DEMO 101", "DEMO 201"]
    assert all(r.eligible for r in results)
    assert all(r.reason for r in results)  # every verdict carries a checkable reason


def test_nested_failure_reasons_preserve_grouping():
    course = _course("DEMO 401", {"op": "and", "children": [
        {"course": "DEMO 101"},
        {"op": "or", "children": [{"course": "DEMO 201"}, {"course": "DEMO 202"}]},
    ]})
    result = check_course(course, set())
    assert result.reason == "missing DEMO 101 and (needs one of: missing DEMO 201 or missing DEMO 202)"


def test_or_of_and_reasons_preserve_grouping():
    course = _course("DEMO 401", {"op": "or", "children": [
        {"op": "and", "children": [{"course": "DEMO 101"}, {"course": "DEMO 201"}]},
        {"course": "DEMO 202"},
    ]})
    result = check_course(course, set())
    assert result.reason == "needs one of: (missing DEMO 101 and missing DEMO 201) or missing DEMO 202"
    result = check_course(course, {"DEMO 101", "DEMO 201"})
    assert result.eligible
    assert result.reason == "(has DEMO 101 and has DEMO 201)"
