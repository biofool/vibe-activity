"""Categorizer unit tests — regex pass, LLM label parsing, fallback."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import categorize  # noqa: E402

RULES, AFK, FALLBACK = categorize.load_rules()


def test_regex_hits_common_apps():
    assert categorize.regex_category("code", "x.py — VS Code", RULES) == "work"
    assert categorize.regex_category("firefox", "YouTube — video", RULES) == "distraction"
    assert categorize.regex_category("ghostty", "zsh", RULES) == "work"
    assert categorize.regex_category("firefox", "SQLite FTS5 documentation", RULES) == "research"


def test_regex_miss_returns_none():
    assert categorize.regex_category("mystery-app", "Untitled", RULES) is None


def test_offline_falls_back():
    payload = {"day": "d", "events": [
        {"timestamp": "2026-01-01T10:00:00Z", "duration": 60,
         "data": {"app": "mystery-app", "title": "???"}}], "afk": []}
    out = categorize.categorize(payload, offline=True)
    assert out["events"][0]["category"] == FALLBACK


def test_llm_labels_filtered_to_known_categories():
    fake = {"choices": [{"message": {"content": json.dumps({"labels": {
        "weird | x": "work", "weird | y": "NOT_A_CATEGORY"}})}}]}
    with patch.object(categorize.urllib.request, "urlopen") as m:
        m.return_value.__enter__.return_value.read.return_value = \
            json.dumps(fake).encode()
        labels = categorize.llm_categories(["weird | x", "weird | y"],
                                           ["work", "other"])
    assert labels == {"weird | x": "work"}
