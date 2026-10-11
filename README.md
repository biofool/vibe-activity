# vibe-activity

A Rize replacement: private, local productivity tracking and reporting.
[ActivityWatch](https://activitywatch.net/) records what you do;
this repo categorizes it (regex first, local LLM for the rest) and renders
a self-contained ECharts dashboard. No cloud, no account, no subscription —
your window titles never leave the machine.

## Replaces

- **Rize** (~$120/yr) — same job (auto time-tracking + focus analytics),
  minus the fee and the telemetry.

## Pipeline

```
aw-server (ActivityWatch)
    └─ fetch_aw.py      -> data/events_<date>.json      (raw events)
    └─ categorize.py    -> data/categorized_<date>.json (regex + LLM)
    └─ build_dashboard  -> dist/index.html              (ECharts)
```

## Install

```bash
# 1. ActivityWatch — app/flatpak/deb from https://activitywatch.net
#    enable aw-watcher-window + aw-watcher-afk (on by default)
# 2. optional: LM Studio with any instruct model at http://127.0.0.1:1234/v1
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt        # only needed for tests; runtime is stdlib-only
```

## Run

```bash
./run.sh              # today, LLM categorization if the endpoint is up
./run.sh --days 7     # trailing week
./run.sh --offline    # regex rules only, no LLM calls
# open dist/index.html
```

Try it without ActivityWatch using the bundled sample day:

```bash
python3 categorize.py --offline data/sample_events.json
python3 build_dashboard.py
```

## Categorization

- `data/categories.json` — regex rules over `app + window title` → category.
  Edit freely; first match wins. Most days resolve here in milliseconds.
- Uncategorized `app | title` pairs go to the local LLM **once**, batched,
  and are cached in `data/category_cache.json` — the LLM is a
  cold-start helper, not a per-event dependency.
- AFK time comes from the `aw-watcher-afk` bucket, not title inference.

## Configuration (env)

| Var | Default | Purpose |
|---|---|---|
| `VIBE_AW_SERVER` | `http://127.0.0.1:5600` | ActivityWatch API |
| `VIBE_AW_ENDPOINT` | `http://127.0.0.1:1234/v1` | OpenAI-compatible LLM |
| `VIBE_AW_MODEL` | `local-model` | model name for the LLM call |
| `VIBE_AW_KEY` | — | API key (only for hosted endpoints) |

## Dashboard

Focus score, focus/active time, minutes-by-hour stacked bars, category
donut, top apps, multi-day focus trend. Static file — share or host anywhere.

## Tests

```bash
python3 -m pytest tests/    # requires: pip install -r requirements.txt
```

## Deploy

`dist/index.html` is a self-contained static file. Open it locally or
copy it to any static host. ECharts loads from CDN — vendor
`echarts.min.js` into `dist/` and update the `<script src>` in
`build_dashboard.py` for fully offline use.

## License

MIT — see `LICENSE`.

## Limitations

- Wayland window titles need `aw-awatcher` or the Hyprland/GNOME watcher —
  the stock X11 watcher sees nothing under pure Wayland.
- Regex rules cover common apps; niche apps go through the LLM once, then
  the cache.
- ECharts loads from CDN — the dashboard is local but needs network for the
  library on first view (vendor `echarts.min.js` into `dist/` to go fully
  offline).
