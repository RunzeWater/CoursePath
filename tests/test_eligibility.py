"""Eligibility: success, failure, and boundary cases."""

import pytest

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


# DEMO 101 AND (DEMO 201 OR (DEMO 202 AND (DEMO 203 OR DEMO 204))) — four levels deep.
_DEEP_RULE = {"op": "and", "children": [
    {"course": "DEMO 101"},
    {"op": "or", "children": [
        {"course": "DEMO 201"},
        {"op": "and", "children": [
            {"course": "DEMO 202"},
            {"op": "or", "children": [{"course": "DEMO 203"}, {"course": "DEMO 204"}]},
        ]},
    ]},
]}


@pytest.mark.parametrize("completed, expected", [
    ({"DEMO 101", "DEMO 201"}, True),                # shallow OR branch
    ({"DEMO 101", "DEMO 202", "DEMO 203"}, True),    # deepest branch, first option
    ({"DEMO 101", "DEMO 202", "DEMO 204"}, True),    # deepest branch, second option
    ({"DEMO 101", "DEMO 202"}, False),               # inner AND half satisfied
    ({"DEMO 101", "DEMO 203", "DEMO 204"}, False),   # inner AND missing DEMO 202
    ({"DEMO 201", "DEMO 202", "DEMO 203"}, False),   # top-level AND missing DEMO 101
    (set(), False),
])
def test_deeply_nested_rule(completed, expected):
    result = check_course(_course("DEMO 401", _DEEP_RULE), completed)
    assert result.eligible is expected


def test_deeply_nested_failure_reason_names_missing_courses():
    result = check_course(_course("DEMO 401", _DEEP_RULE), {"DEMO 101", "DEMO 202"})
    assert result.eligible is False
    for code in ("DEMO 201", "DEMO 203", "DEMO 204"):
        assert code in result.reason
    assert "DEMO 101" not in result.reason  # already satisfied, so not reported


def _catalogue():
    return [
        _course("DEMO 101"),
        _course("DEMO 102"),
        _course("DEMO 201", {"course": "DEMO 101"}),
        _course("DEMO 301", {"course": "DEMO 201"}),
    ]


def test_check_all_keeps_completed_courses_by_default():
    results = check_all(_catalogue(), {"DEMO 101"})
    assert [r.code for r in results] == ["DEMO 101", "DEMO 102", "DEMO 201", "DEMO 301"]


def test_check_all_excludes_completed_courses():
    results = check_all(_catalogue(), {"DEMO 101"}, exclude_completed=True)
    # DEMO 101 is dropped; everything else stays, in file order, eligible or not.
    assert [r.code for r in results] == ["DEMO 102", "DEMO 201", "DEMO 301"]
    assert [r.eligible for r in results] == [True, True, False]


def test_excluded_course_still_counts_as_a_prerequisite():
    # Dropping DEMO 101 from the output must not stop it satisfying DEMO 201.
    results = check_all(_catalogue(), {"DEMO 101", "DEMO 201"}, exclude_completed=True)
    assert [(r.code, r.eligible) for r in results] == [("DEMO 102", True), ("DEMO 301", True)]


def test_exclude_completed_normalizes_codes():
    results = check_all(_catalogue(), {"demo  101"}, exclude_completed=True)
    assert "DEMO 101" not in [r.code for r in results]


def test_exclude_completed_with_nothing_completed_changes_nothing():
    assert check_all(_catalogue(), set(), exclude_completed=True) == check_all(_catalogue(), set())


def test_exclude_completed_when_everything_is_completed():
    done = {c.code for c in _catalogue()}
    assert check_all(_catalogue(), done, exclude_completed=True) == []
