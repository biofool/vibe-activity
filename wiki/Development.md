# Development — vibe-activity

## Commands
```bash
./run.sh [--days N] [--offline]
python3 categorize.py --offline data/sample_events.json   # no AW needed
python3 build_dashboard.py
python3 -m pytest tests/
```

## Conventions
See `AGENTS.md` and `CLAUDE.md` at the repo root — they carry the shared
biofool rules (no secrets in git, never fail silently, fix scripts under
`scripts/fix/` with `--dry-run`, audit output to `data/audit/`).
