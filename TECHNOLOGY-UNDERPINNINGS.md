# Technology Underpinnings — vibe-activity

Three-stage local pipeline: ActivityWatch events → categorization →
static dashboard. Python 3, **stdlib-only at runtime** (HTTP via
`urllib`). `pytest` is the only dev dependency (`requirements.txt`).

## Stage 1 — Event collection (`fetch_aw.py`)

Reads the ActivityWatch REST API (`VIBE_AW_SERVER`, default
`http://127.0.0.1:5600/api/0`).

- `find_buckets()` auto-discovers the `aw-watcher-window*` and
  `aw-watcher-afk*` buckets.
- `events()` queries each bucket for a UTC day range.
- AFK events are filtered to `data.status == "afk"` and stored
  separately — idle time is measured by the AFK watcher, not inferred
  from titles.
- Output: `data/events_<date>.json` = `{"day", "events", "afk"}`
  (gitignored).

## Stage 2 — Categorization (`categorize.py`)

Two passes over each event's `app + window title`:

1. **Regex rules** from `data/categories.json` — ordered, first match
   wins (`regex_category()`). Distraction/media rules intentionally
   precede work rules so entertainment keywords outrank generic hits
   like "code". Rule order, `afk_category`, and `fallback_category`
   live in the JSON file, not in code.
2. **Local LLM fallback** (`llm_categories()`) — uncategorized unique
   `app | title` keys are sent in one batched `/chat/completions` call
   to an OpenAI-compatible endpoint (`VIBE_AW_ENDPOINT`, default LM
   Studio at `http://127.0.0.1:1234/v1`; `VIBE_AW_MODEL`,
   `VIBE_AW_KEY`). `response_format: json_object`, temperature 0.
   Returned labels are validated against the known category set.

Results are cached by `app | title` key in `data/category_cache.json`,
so the LLM is a cold-start helper, not a per-event dependency. Any LLM
failure logs a warning and falls back to the `other` category — the
run never fails. `--offline` skips the LLM pass entirely.

Output: `data/categorized_<date>.json` (same payload plus a
`category` field per event).

## Stage 3 — Dashboard (`build_dashboard.py`)

Reads every `data/categorized_*.json`, aggregates per day in
`aggregate()`:

- minutes per category and per app (`top_apps`, top 10)
- minutes per hour per category (stacked bar chart)
- `focus_minutes` / `active_minutes` / `focus_score` — focus is the
  sum of the `FOCUS` categories (`work`, `writing`, `research`) over
  non-AFK time

Writes `dist/index.html`: a single HTML string (`HTML`) with the
aggregated JSON inlined into `const DATA`, Apache ECharts 5 loaded
from the jsDelivr CDN. Four charts — minutes-by-hour stacked bars,
category donut, top-apps bar, multi-day focus-score line — plus KPIs
and a day selector. Category order and colors come from the `ORDER`
and `PALETTE` constants; `FOCUS` defines what counts as focus time.

## Orchestration (`run.sh`)

`./run.sh [--days N] [--offline]` — fetches N days ending today,
runs `categorize.py` on every `data/events_*.json`, then rebuilds the
dashboard. `set -euo pipefail`; unknown args exit 2.

## Data files

| File | Role | Tracked |
|---|---|---|
| `data/categories.json` | regex rules, afk/fallback category names | yes |
| `data/sample_events.json` | sample day for demo/testing without ActivityWatch | yes |
| `data/events_*.json` | raw fetched events | no (gitignored) |
| `data/categorized_*.json` | categorized events | no (gitignored) |
| `data/category_cache.json` | LLM label cache | no (gitignored) |
| `dist/index.html` | generated dashboard | no (gitignored) |

## Tests (`tests/test_categorize.py`)

pytest unit tests for the regex pass, the offline fallback, and LLM
response filtering (mocked `urlopen`; labels outside the known
category set are dropped).

## External dependencies

- **ActivityWatch** (`aw-server` + `aw-watcher-window` +
  `aw-watcher-afk`) — required for real data. Wayland needs
  `aw-awatcher` or a compositor-specific watcher.
- **LM Studio or any OpenAI-compatible server** — optional; only for
  titles the regex misses.
- **ECharts 5 via CDN** — required once per browser to render the
  dashboard (or vendor `echarts.min.js` locally).

## Conventions

From `.devin/wiki/conventions.md`: stdlib-only runtime, rules in JSON
never hardcoded, LLM path degrades gracefully with a logged warning,
generated files stay out of git.
