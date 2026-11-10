"""CLI entry point.

Usage:
    python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" "DEMO 201"
    python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" --json
    python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" --eligible-only
    python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" --eligible-only --skip-completed

Exit code is 0 when the file loads and the check runs (even if some courses
are ineligible — ineligibility is a result, not an error).
"""

from __future__ import annotations

import argparse
import json
import sys

from .eligibility import check_all
from .models import load_courses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="coursepath", description="Check prerequisite eligibility from a sample courses file.")
    parser.add_argument("--courses", required=True, help="path to sample courses JSON")
    parser.add_argument("--completed", nargs="*", default=[], help="completed course codes, e.g. DEMO 101 DEMO 201")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    parser.add_argument("--eligible-only", action="store_true", help="only output courses whose prerequisites are met")
    parser.add_argument("--skip-completed", action="store_true", help="leave already-completed courses out of the output")
    args = parser.parse_args(argv)

    try:
        courses = load_courses(args.courses)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    results = check_all(courses, set(args.completed), exclude_completed=args.skip_completed)
    if args.eligible_only:
        # Filter after the check so both the text and JSON outputs honor the flag.
        results = [r for r in results if r.eligible]
    if args.json:
        print(json.dumps(
            [{"code": r.code, "eligible": r.eligible, "reason": r.reason} for r in results],
            indent=2,
        ))
    else:
        for r in results:
            mark = "YES" if r.eligible else "NO "
            print(f"[{mark}] {r.code}: {r.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
