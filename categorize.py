#!/usr/bin/env python3
"""Categorize ActivityWatch window events.

Pass 1: regex rules from data/categories.json (free, deterministic).
Pass 2: remaining unique app|title pairs -> local LLM (LM Studio,
OpenAI-compatible) in one batch -> cached in data/category_cache.json.

Usage:
    python3 categorize.py data/events_2026-10-11.json [-o out.json]
    python3 categorize.py --offline data/sample_events.json   # no LLM call
"""

import argparse
import json
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path

log = logging.getLogger("categorize")
HERE = Path(__file__).resolve().parent
CATEGORIES = HERE / "data" / "categories.json"
CACHE = HERE / "data" / "category_cache.json"

ENDPOINT = os.environ.get("VIBE_AW_ENDPOINT", "http://127.0.0.1:1234/v1").rstrip("/")
MODEL = os.environ.get("VIBE_AW_MODEL", "local-model")
API_KEY = os.environ.get("VIBE_AW_KEY", "")


def load_rules() -> tuple[list[tuple[str, re.Pattern]], str, str]:
    cfg = json.loads(CATEGORIES.read_text())
    rules = [(r["category"], re.compile(r["pattern"])) for r in cfg["rules"]]
    return rules, cfg.get("afk_category", "afk"), cfg.get("fallback_category", "other")


def regex_category(app: str, title: str, rules) -> str | None:
    hay = f"{app} {title}"
    for cat, pat in rules:
        if pat.search(hay):
            return cat
    return None


def llm_categories(keys: list[str], known_categories: list[str]) -> dict[str, str]:
    """Ask the LLM to label 'app | title' strings. Returns key -> category."""
    if not keys:
        return {}
    cats = ", ".join(known_categories)
    prompt = (
        "Classify each desktop-activity entry (format: 'app | window title') "
        f"into exactly one category: {cats}.\n"
        'Return ONLY JSON: {"labels": {"<entry>": "<category>", ...}}\n'
        "Judge by what the person is doing, not the app name alone.\n"
        "Entries:\n" + "\n".join(f"- {k}" for k in keys)
    )
    req = urllib.request.Request(
        ENDPOINT + "/chat/completions",
        data=json.dumps({
            "model": MODEL, "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {API_KEY}"} if API_KEY else {})},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        content = json.loads(r.read())["choices"][0]["message"]["content"]
    labels = json.loads(content).get("labels", {})
    valid = set(known_categories)
    return {k: v for k, v in labels.items() if k in keys and v in valid}


def categorize(payload: dict, offline: bool = False) -> dict:
    rules, afk_cat, fallback = load_rules()
    known = [c for c, _ in rules] + [afk_cat, fallback]
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    events = payload.get("events", [])
    need_llm = []
    for ev in events:
        app, title = ev.get("data", {}).get("app", ""), ev.get("data", {}).get("title", "")
        key = f"{app} | {title}"
        cat = regex_category(app, title, rules) or cache.get(key)
        if cat:
            ev["category"] = cat
        else:
            need_llm.append(key)

    if need_llm and not offline:
        try:
            got = llm_categories(sorted(set(need_llm)), known)
            cache.update(got)
            CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True))
            log.info("llm categorized %d/%d titles", len(got), len(set(need_llm)))
        except Exception as e:  # noqa: BLE001 — fall back, never lose the run
            log.warning("llm categorize failed (%s) — marking uncategorized as %s", e, fallback)
    elif need_llm:
        log.info("offline mode — %d titles -> %s", len(set(need_llm)), fallback)

    for ev in events:
        ev["category"] = ev.get("category") or fallback
    for ev in payload.get("afk", []):
        ev["category"] = afk_cat
    return payload


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("events", help="events json from fetch_aw.py (or sample)")
    p.add_argument("-o", "--out")
    p.add_argument("--offline", action="store_true", help="skip the LLM pass")
    a = p.parse_args()

    payload = json.loads(Path(a.events).read_text())
    out = categorize(payload, offline=a.offline)
    dst = Path(a.out) if a.out else Path(a.events).with_name(
        f"categorized_{out.get('day', Path(a.events).stem)}.json")
    dst.write_text(json.dumps(out, indent=1))
    cats = {}
    for ev in out.get("events", []):
        cats[ev["category"]] = cats.get(ev["category"], 0) + 1
    print(f"{dst}  {cats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
