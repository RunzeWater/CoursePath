# CoursePath

A prerequisite eligibility checker for course planning: give it the courses you have completed, and it tells you which courses you can take and why.

The long-term goal is to plan a UAlberta term end to end (eligibility, a suggested course set, a conflict-free timetable). Today only the eligibility step exists, and it runs on hand-written sample data. Everything else is listed under [Planned](#planned).

## Status

| Stage | What it does | Status |
|---|---|---|
| Eligibility | Reads structured prerequisite trees from JSON and checks them against your completed courses | ✅ Working (sample data only) |
| Prerequisite text parsing | Turns catalogue sentences into prerequisite trees | ⬜ Planned |
| Catalogue data | Scrapes real courses and sections from the UAlberta catalogue | ⬜ Planned |
| Offering filter | Narrows to courses actually scheduled this term | ⬜ Planned |
| Recommendation | Ranks eligible courses into a suggested set | ⬜ Planned |
| Timetable | Builds conflict-free section combinations | ⬜ Planned |

Each stage feeds the next, so they will land in this order.

## Example

With only `DEMO 101` completed, `DEMO 301` is not available yet, and the output says what is missing:

```sh
python -m coursepath --courses data/sample_courses.json --completed "DEMO 101"
```

```
[YES] DEMO 101: no prerequisite
[NO ] DEMO 301: (needs one of: missing DEMO 201 or missing DEMO 202)
```

Add `DEMO 202` and it becomes eligible:

```sh
python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" "DEMO 202"
```

```
[YES] DEMO 101: no prerequisite
[YES] DEMO 301: has DEMO 101 and (has DEMO 202)
```

## The problem

Picking a term's courses in Ualberta means answering four question in order, and the university's tools answer none of them

Prerequisites live inside each course's own catalogue entry, writing as English sentences--"CMPUT 174 or 275, and CMPUT 272 or Math 222"

The true question that student actually wants to ask:" Giving that I have passed these courses, what can I take." then of those which are even offered this term. 
Then which five are the right five? Then do their sections fit in a week without overlapping.
Done by hand, that's a lot of tabs and a spreadsheet.and the mistake don't surface until registration day.

## How it works

The current flow has three steps:

```
courses JSON file  +  your completed courses
   │  load and validate — reject malformed prerequisite trees
   ▼
list of courses, each with a prerequisite tree (or none)
   │  eligibility check — recursive walk over each tree
   ▼
one result per course: eligible or not, with a reason
   │  command line — print as text or JSON
   ▼
output
```

### Prerequisite trees

Prerequisites are stored as a tree, not as text. `DEMO 101 and (DEMO 201 or DEMO 202)` is written as:

```json
{
  "op": "and",
  "children": [
    { "course": "DEMO 101" },
    {
      "op": "or",
      "children": [
        { "course": "DEMO 201" },
        { "course": "DEMO 202" }
      ]
    }
  ]
}
```

A node is either a course (`{"course": "DEMO 101"}`) or an operator with at least one child. The only operators are lowercase `and` and `or`. A course with no prerequisite has `"prerequisite": null`.

Each course record also has a `raw_prerequisite` string holding the original wording. It is kept for display and cross-checking only; the program never reads it to decide eligibility.

### Loading and validation

The file is validated when it is loaded. An unknown operator (including `AND` in upper case), an empty `children` list, extra keys on a node, or a duplicate course code is rejected with an error instead of being silently accepted. Course codes are normalized, so `demo  101` and `DEMO 101` match.

### Eligibility check

Eligibility is a recursive walk over the tree: `and` passes when every child passes, `or` passes when any child does, and a course node passes when its code is in the completed set.

The reason shown for each course is built during the same walk that makes the decision, so the stated reason is the actual reason.

## Quickstart

Requires Python 3.10 or newer. From the project folder:

```sh
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS / Linux:        source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

Check eligibility against the bundled sample data (`DEMO` courses, not real UAlberta rules):

```sh
python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" "DEMO 201"
```

```
[YES] DEMO 101: no prerequisite
[YES] DEMO 301: has DEMO 101 and (has DEMO 201)
```

### Command-line options

| Option | What it does |
|---|---|
| `--courses PATH` | Courses JSON file (required). |
| `--completed CODE [CODE ...]` | Courses you have completed. Quote each code, e.g. `"DEMO 101"`; codes are case- and space-insensitive. |
| `--json` | Print the results as JSON instead of text. |
| `--eligible-only` | Only show courses whose prerequisites are met. |
| `--skip-completed` | Leave courses you have already completed out of the output. |

`--eligible-only` and `--skip-completed` can be combined to list what you can take next:

```sh
python -m coursepath --courses data/sample_courses.json --completed "DEMO 101" "DEMO 202" --eligible-only --skip-completed
```

```
[YES] DEMO 301: has DEMO 101 and (has DEMO 202)
```

Exit code is `0` whenever the check runs, even if some courses are ineligible; `2` means the input was invalid (bad file or bad course code). See [RUNNING.md](RUNNING.md) for the VS Code setup.

## Planned

None of this exists yet. It is the intended direction, not a description of the code.

- **Prerequisite text parsing.** The catalogue writes prerequisites as English sentences, such as `CMPUT 175 or 275, and CMPUT 272 or MATH 222`. A parser will turn these into the tree format above. Two things will make this harder than it looks. Subject codes get elided: `CMPUT 201 and 272` means CMPUT 201 and CMPUT 272, and anything built on substring matching misses that silently. Phrasing is also inconsistent: `one of X, Y, or Z`, `X or Y or Z`, and `X, Y or Z` all mean the same thing. The parser's accuracy will be measured against a hand-checked sample and published here.
- **Catalogue scraper.** A scraper will read the public UAlberta course catalogue (<https://apps.ualberta.ca/catalogue>) and write course and section records to `data/`. It will be rate-limited with a descriptive User-Agent, and it will fail the run rather than overwrite good data if a page yields zero courses.
- **Scheduled refresh.** A scheduled job will rescrape nightly and commit the refreshed JSON, so a failed scrape will fall back to the previous day's data. The last successful run will be recorded in `data/last_updated.json`.
- **Offering filter.** Will intersect eligible courses with the sections actually scheduled in a given term.
- **Recommendation.** Will rank available courses by explicit rules in code (degree gap, prerequisite chain depth, workload balance). If a language model is used, it will only turn the already-ordered result into a readable explanation, never do the ranking, so the stated reason stays the actual reason.
- **Timetable.** Will search section combinations for a schedule with no time conflicts.

## Data

The only data in the repository is [`data/sample_courses.json`](data/sample_courses.json), a small hand-written file of `DEMO` courses. It is not scraped, and the course codes are examples, not real UAlberta prerequisite rules.

To check your own courses, write a JSON file in the same format (see [Prerequisite trees](#prerequisite-trees)) and pass it with `--courses`.

> Personal project, not affiliated with the University of Alberta. Confirm
> eligibility in Bear Tracks or with an academic advisor before registering.

## Limitations

- **Sample data only.** There is no real catalogue data, so the tool cannot yet answer questions about actual UAlberta courses unless you write the prerequisite trees yourself.
- **Prerequisites are `and` / `or` of course codes, nothing else.** There is no field for mutually exclusive courses ("credit cannot be obtained for both"), corequisites, minimum grades, consent of the department, or year standing.
- **No handling of equivalent or transfer credit.** A completed course only counts if its exact code appears in the tree.
- **Circular and self-referencing prerequisites are not detected.** A course that lists itself as a prerequisite loads without error and is simply never eligible.
- **Prerequisite codes are not checked against the file.** A tree can name a course that does not exist in the courses file, and a mistyped completed code that matches no course is accepted without a warning.
- **No degree audit and no registration.** It does not know program requirements, does not connect to Bear Tracks, and has no waitlist, capacity, or seat data.

## Built with

Python standard library (`argparse`, `json`, `dataclasses`) and `pytest` for tests. No third-party runtime dependencies.
