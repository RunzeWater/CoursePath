"""CoursePath: prerequisite eligibility from structured rule trees.

Rule-tree format used by this scaffold (PROPOSAL — must be confirmed
against AGENTS.md section 4 before A and B treat it as the contract;
the README's own example is an AND of two ORs, which this mirrors):

    {"course": "DEMO 101"}                          # leaf: completed?
    {"op": "and", "children": [<node>, ...]}         # every child passes
    {"op": "or", "children": [<node>, ...]}          # any child passes

A course with no ``prerequisite`` key (or null) has no prerequisite.
``raw_prerequisite`` is display-only and is never parsed.
"""

from .eligibility import check_course, check_all, EligibilityResult
from .models import Course, load_courses, normalize_code

__all__ = ["Course", "EligibilityResult", "check_course", "check_all", "load_courses", "normalize_code"]
__version__ = "0.1.0"
