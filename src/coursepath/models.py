"""Course and prerequisite-rule-tree types, loading, and validation.

A sample file is a JSON object with a ``courses`` array. Each course::

    {
      "code": "DEMO 301",
      "title": "Demo Course 301",
      "raw_prerequisite": "DEMO 101 and (DEMO 201 or DEMO 202)",
      "prerequisite": {"op": "and", "children": [
          {"course": "DEMO 101"},
          {"op": "or", "children": [{"course": "DEMO 201"}, {"course": "DEMO 202"}]}
      ]}
    }

``raw_prerequisite`` is kept only for display / cross-checking; eligibility
never parses it. ``prerequisite`` may be absent or null (= no prerequisite).
Codes are normalized on load: upper-cased, whitespace collapsed
("cmput  174" -> "CMPUT 174"), so matching is case/space-insensitive.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_WS = re.compile(r"\s+")


def normalize_code(code: str) -> str:
    """Normalize a course code: strip, collapse inner whitespace, upper-case."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"invalid course code: {code!r}")
    return _WS.sub(" ", code.strip()).upper()


def _validate_rule(node: Any, where: str) -> None:
    if not isinstance(node, dict):
        raise ValueError(f"{where}: rule node must be an object, got {node!r}")
    if "course" in node:
        if set(node) != {"course"}:
            raise ValueError(f"{where}: leaf node must have only 'course', got {sorted(node)}")
        normalize_code(node["course"])
    elif "op" in node:
        if set(node) != {"op", "children"}:
            raise ValueError(f"{where}: branch node must have only 'op' and 'children', got {sorted(node)}")
        if node["op"] not in ("and", "or"):
            raise ValueError(f"{where}: op must be 'and' or 'or', got {node['op']!r}")
        children = node["children"]
        if not isinstance(children, list) or not children:
            raise ValueError(f"{where}: 'children' must be a non-empty list")
        for i, child in enumerate(children):
            _validate_rule(child, f"{where}.children[{i}]")
    else:
        raise ValueError(f"{where}: rule node needs 'course' or 'op', got {sorted(node)}")


@dataclass(frozen=True)
class Course:
    code: str
    title: str = ""
    raw_prerequisite: str = ""
    prerequisite: dict | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", normalize_code(self.code))
        if self.prerequisite is not None:
            _validate_rule(self.prerequisite, f"prerequisite of {self.code}")


def load_courses(path: str | Path) -> list[Course]:
    """Load and validate a sample-courses JSON file. Raises ValueError on bad data."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"courses file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path}: invalid JSON: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("courses"), list):
        raise ValueError(f"{path}: top level must be an object with a 'courses' array")
    courses: list[Course] = []
    seen: set[str] = set()
    for i, raw in enumerate(data["courses"]):
        if not isinstance(raw, dict) or "code" not in raw:
            raise ValueError(f"courses[{i}]: each course needs a 'code'")
        course = Course(
            code=raw["code"],
            title=raw.get("title", ""),
            raw_prerequisite=raw.get("raw_prerequisite") or "",
            prerequisite=raw.get("prerequisite"),
        )
        if course.code in seen:
            raise ValueError(f"courses[{i}]: duplicate course code {course.code}")
        seen.add(course.code)
        courses.append(course)
    return courses
