# Conventions

- Runtime stays stdlib-only — HTTP via urllib, no requests/httpx.
- Category rules live in `data/categories.json` — never hardcode lists in code.
- LLM path must degrade to the fallback category on failure and log WARNING.
- `data/events_*.json`, `data/categorized_*.json`, `data/category_cache.json`,
  `dist/` are generated — gitignored.
- `0.0.0.0` is a bind address, not a connect address — use `127.0.0.1` in URLs.
- Post-edit lint hook runs automatically (`.claude/hooks/post_edit_lint.py`);
  findings are defects — fix them. Never claim done without a proving
  command (`verify-change` skill).
- A process explained twice becomes a hook, a `scripts/` tool, or a
  `.devin/skills/` entry.
