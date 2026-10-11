# Decisions

Append-only. Newest first.

## 2026-10-11 — regex-first, LLM-second categorization

Deterministic rules in `data/categories.json` handle ~90% of titles;
uncategorized `app | title` pairs go to the local LLM once and are cached.
Rationale: free, fast, private; LLM only earns its keep on unknowns.

## 2026-10-11 — mini-wiki replaces CLAUDE.md project sections

Project knowledge moved here; CLAUDE.md is now a router.

- 2026-10-12 — Adversarial review (magic-compact sweep); findings ticketed in GitHub issues.
