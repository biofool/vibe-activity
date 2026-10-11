# Architecture

Rize replacement — all local, no accounts:

```
aw-server (ActivityWatch, http://127.0.0.1:5600)
  → fetch_aw.py      data/events_<date>.json      raw window+afk events
  → categorize.py    data/categorized_<date>.json regex rules + cached local-LLM
  → build_dashboard  dist/index.html              self-contained ECharts page
```

- `data/categories.json` — ordered regex rules, first match wins;
  distraction/media rules deliberately precede work (entertainment
  keywords outrank generic work keywords like "code").
- `data/category_cache.json` — LLM labels cached by `app | title` key;
  the LLM is a cold-start helper, not a per-event dependency.
- AFK time comes from the `aw-watcher-afk` bucket, not title inference.
