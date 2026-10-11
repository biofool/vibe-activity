<!-- AI coding config version: 2026-10-11 — sourced from biofool/starter template. -->

# CLAUDE.md

## Project overview

vibe-activity — local Rize replacement. ActivityWatch events -> regex/LLM
categorization -> static ECharts dashboard. Stdlib-only runtime.

## Commands

```bash
./run.sh [--days N] [--offline]
python3 categorize.py --offline data/sample_events.json   # no AW needed
python3 build_dashboard.py
python3 -m pytest tests/
```

## Conventions

- Runtime stays stdlib-only — HTTP via urllib, no requests.
- Category rules live in `data/categories.json`, never hardcode lists in code.
- LLM results are cached in `data/category_cache.json`; the LLM path must
  degrade to the fallback category on any failure (never fail silently —
  log WARNING).
- `data/categorized_*.json`, `data/events_*.json`, `dist/` are generated —
  keep them gitignored.
- `0.0.0.0` is a bind address, not a connect address.
- **Don't trust, verify** — post-edit lint hook runs automatically
  (`.claude/hooks/post_edit_lint.py`); findings are defects, fix them.
  Never claim done without a command that proves it (`verify-change` skill).
- **Automate the annoying stuff** — a process explained twice becomes a
  hook, a `scripts/` tool, or a `.devin/skills/` entry.
