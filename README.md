#CoursePath
Plan a term at UAlberta end to end: check what you're eligible for, get a suggested course set, and turn it into a conflict-free timetable.

## Status
 
| Stage | What it does | Status |
|---|---|---|
| Eligibility | Parses prerequisites, checks them against your completed courses | 🚧 In progress |
| Offering filter | Narrows to courses actually scheduled this term | ⬜ Not started |
| Recommendation | Ranks eligible courses into a suggested set | ⬜ Not started |
| Timetable | Builds conflict-free section combinations | ⬜ Not started |
 
Each stage feeds the next, so they land in this order.
 
## Demo
 
<!-- TODO: record a 10-second GIF once one full path works end to end.
     Sequence: enter completed courses -> results appear. Nothing else,
     no cursor wandering. Commit to docs/demo.gif. This single item does
     more work than everything else in this file. -->
 
![Demo](docs/demo.gif)
 
## The problem

Picking a term's courses in Ualberta means answering four question in order, and the university's tools answer none of them

Prerequisites live inside each course's own catalogue entry, writing as English sentences--"CMPUT 174 or 275, and CMPUT 272 or Math 222"

The true question that student actually wants to ask:" Giving that I have passed these courses, what can I take." then of those which are even offered this term. 
Then which five are the right five? Then do their sections fit in a week without overlapping.
Done by hand, that's a lot of tabs and a spreadsheet.and the mistake don't surface until registration day.

## How it works

The pipeline is four stages, each consuming the previous one's output:

```
UAlberta catalogue
   │  scraper — runs nightly, writes courses + sections to data/
   ▼
local dataset  +  your completed courses
   │  eligibility engine — recursive walk over parsed prerequisite trees
   ▼
eligible courses
   │  offering filter — intersect with this term's scheduled sections
   ▼
available courses
   │  recommendation engine — rank by degree gap, prereq depth, load balance
   ▼
suggested set
   │  timetable engine — backtracking search over section combinations
   ▼
conflict-free schedule
```

The order isn't a preference, it's a dependency. A recommendar without the eligibility stage suggests courses you cannot register for. A timetable builder without the recommender is just a scheduling tool you have to feed by hand

## Prerequisite parsing

`CMPUT 175 or 275, and CMPUT 272 or MATH 222` is a boolean expression written in
English, so it's parsed into a tree:
 
```
AND
├── OR: CMPUT 175, CMPUT 275
└── OR: CMPUT 272, MATH 222
```
 
Eligibility is a recursive walk: `AND` passes when every child passes, `OR` when
any child does, a leaf when its code is in the completed set.

Two things make this harder than it looks.
**Subject codes get elided** - 
'CMPUT 201 and 272' means CMPUT 201 and CMPUT 272, with the subject started once and carried. Anything built on substring matching misses this silently, and silently is the dangerous part: nothing raises, the tool just reports a student
as ineligible for a course they can take. And **phrasing is inconsistent** —
`one of X, Y, or Z`, `X or Y or Z`, and `X, Y or Z` all appear and all mean the
same thing.
 
<!-- TODO: replace with what you actually built, and publish the measured
     accuracy on your hand-checked sample. A real number beats any adjective.
     If it's bad, publish the bad number and say what breaks — that reads as
     competence, not weakness. -->

<PARSING APPROACH: 2-3 sentences. Validated against <N> hand-checked
prerequisite strings, <N>% correct.>
 
### Keeping the data fresh
The catalogue is the upstream source of truth and it moves: sections get added and cancelled, time shift, prerequisites get reworded between calendar years. A dataset scraped once is wrong by the following term, and wrong quietly. 

So the scraper runs on a schedule rater than on demand.  A GitHub Actions cron job rescrapes nightly, writes the refreshed JSON to 'data/', and commits it back to the repo. The app always reads the committed snapshot, so a scrape failure degrades to yesterday's data instead of an empty page.

Two constraints shape the scraper:
 
- **It is polite.** Requests are rate-limited with a delay between pages and a
  descriptive User-Agent. A nightly full crawl of a public catalogue is a small
  load, but only if it's paced — an unthrottled loop over ten thousand pages is
  indistinguishable from an attack.
- **It fails loudly.** If a page's structure changes and a parse yields zero
  courses, the job errors instead of committing an empty dataset over a good
  one. Scrapers break when the site is redesigned; the question is whether you
  find out from a failed build or from a user.
<!-- TODO: once the cron job is running, add a line here with the actual
     schedule and a link to the workflow file. If you add change detection
     (diffing each run against the last so reworded prerequisites surface),
     that's worth a sentence too. -->
 
### Where the LLM is and isn't
 
Ranking is deterministic. Degree gap, prerequisite chain depth, and workload
balance are scored by explicit rules in code, not by a model. The LLM only
turns an already-ordered result into readable explanation.
 
This boundary is deliberate. A model asked to both rank and justify will
produce reasoning that sounds convincing and is post-hoc — and on a tool whose
output determines what someone registers for, a plausible wrong answer is worse
than no answer. Keeping the decision in code means the stated reason is the
actual reason.
 
## What it does not do
 
<!-- Keep this section. Move items up to the status table only when they
     genuinely work — don't quietly delete them as the project grows. -->
 
- **No degree audit against official program rules.** Recommendations use a
  hand-encoded subset of requirements, not the full Calendar.
- **CMPUT courses only.** Prerequisites naming other subjects are matched by
  code, but those catalogues aren't loaded.
- **No registration.** It does not connect to Bear Tracks and cannot enroll you.
- **No waitlist, capacity, or seat-availability data.**
## Quickstart
 
```bash
git clone https://github.com/RunzeWater/<REPO-NAME>.git
cd <REPO-NAME>
pip install -r requirements.txt
streamlit run app.py
```
 
<!-- Run these four lines in a fresh venv before pushing. A README with a
     command that doesn't work is worse than no README. -->
 
## Data
 
Scraped from the public UAlberta course catalogue
(<https://apps.ualberta.ca/catalogue>) and committed to `data/`. Course records
hold prerequisites; section records hold meeting days and times.
 
Refreshed automatically by a scheduled workflow — see
[Keeping the data fresh](#keeping-the-data-fresh). Last successful run is
recorded in `data/last_updated.json`.
 
> Personal project, not affiliated with the University of Alberta. Confirm
> eligibility in Bear Tracks or with an academic advisor before registering.
 
## Limitations
 
<!-- "Known to be wrong right now" — distinct from unbuilt stages above.
     Be specific enough that a reader can tell you went looking for your
     own failure modes. -->
 
- <SPECIFIC PARSER FAILURE CASE — a phrasing it mishandles>
- Consent-of-department and year-standing requirements are ignored
- No handling of equivalent or transfer credit
- Data is at most 24 hours old; same-day section changes won't appear
## Built with
 
Python, Streamlit, BeautifulSoup, GitHub Actions
