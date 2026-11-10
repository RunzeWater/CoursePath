"""Pure eligibility logic: structured rule tree + completed set -> verdict.

No I/O, no parsing of English text, no network. The reason string is built
from the same walk that decides eligibility, so the stated reason is the
actual reason (per the README's LLM boundary).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Course, normalize_code


@dataclass(frozen=True)
class EligibilityResult:
    code: str
    eligible: bool
    reason: str


def _eval(node: dict, completed: set[str]) -> tuple[bool, str]:
    """Return (passes, human-checkable reason) for one rule node."""
    if "course" in node:
        code = normalize_code(node["course"])
        if code in completed:
            return True, f"has {code}"
        return False, f"missing {code}"
    op = node["op"]
    results = [_eval(child, completed) for child in node["children"]]
    if op == "and":
        missing = [reason for ok, reason in results if not ok]
        if not missing:
            return True, " and ".join(reason for _, reason in results)
        return False, " and ".join(missing)
    # op == "or"
    passing = [reason for ok, reason in results if ok]
    if passing:
        return True, passing[0]
    options = " or ".join(reason for _, reason in results)
    return False, f"needs one of: {options}"


def check_course(course: Course, completed: set[str]) -> EligibilityResult:
    """Judge one course. ``completed`` may hold un-normalized codes."""
    done = {normalize_code(c) for c in completed}
    if course.prerequisite is None:
        return EligibilityResult(course.code, True, "no prerequisite")
    ok, reason = _eval(course.prerequisite, done)
    return EligibilityResult(course.code, ok, reason)


def check_all(
    courses: list[Course],
    completed: set[str],
    *,
    exclude_completed: bool = False,
) -> list[EligibilityResult]:
    """Judge every course, in file order.

    With ``exclude_completed=True``, courses whose code is already in
    ``completed`` are left out of the result. The default keeps them, so
    existing callers see no change.
    """
    if exclude_completed:
        # Course.code is normalized on construction, so normalize here to match.
        done = {normalize_code(c) for c in completed}
        courses = [c for c in courses if c.code not in done]
    return [check_course(c, completed) for c in courses]
