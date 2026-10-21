#!/usr/bin/env python3
"""Pull window + AFK events from a local ActivityWatch server.

    python3 fetch_aw.py                 # today
    python3 fetch_aw.py --date 2026-10-11
    python3 fetch_aw.py --days 7        # last 7 days

Writes data/events_<date>.json per day: {"day", "events", "afk"}.
"""

import argparse
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("fetch_aw")
HERE = Path(__file__).resolve().parent
AW = os.environ.get("VIBE_AW_SERVER", "http://127.0.0.1:5600").rstrip("/")


def api(path: str):
    with urllib.request.urlopen(AW + "/api/0" + path, timeout=30) as r:
        return json.loads(r.read())


def find_buckets() -> tuple[str, str]:
    buckets = api("/buckets")
    win = next((b for b in buckets if b.startswith("aw-watcher-window")), None)
    afk = next((b for b in buckets if b.startswith("aw-watcher-afk")), None)
    if not win:
        raise SystemExit("no aw-watcher-window bucket — is the window watcher running?")
    return win, afk


def events(bucket: str, start: datetime, end: datetime) -> list:
    q = urllib.parse.urlencode({
        "start": start.astimezone(timezone.utc).isoformat(),
        "end": end.astimezone(timezone.utc).isoformat(),
        "limit": -1,
    })
    return api(f"/buckets/{urllib.parse.quote(bucket)}/events?{q}")


def fetch_day(d: date) -> dict:
    win, afk = find_buckets()
    # Local midnight -> local midnight (events() converts to UTC for the
    # query). Treating `d` as a UTC day shifts the window by the TZ offset.
    start = datetime(d.year, d.month, d.day).astimezone()
    end = start + timedelta(days=1)
    payload = {"day": d.isoformat(), "events": events(win, start, end)}
    if afk:
        afk_events = [e for e in events(afk, start, end)
                      if isinstance(e.get("data"), dict)
                      and e["data"].get("status") == "afk"]
        payload["afk"] = [{"timestamp": e.get("timestamp", ""),
                           "duration": e.get("duration", 0)}
                          for e in afk_events]
    else:
        payload["afk"] = []
    return payload


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="YYYY-MM-DD (default today)")
    p.add_argument("--days", type=int, default=1)
    a = p.parse_args()

    end_day = date.fromisoformat(a.date) if a.date else date.today()
    (HERE / "data").mkdir(exist_ok=True)
    for i in range(a.days):
        d = end_day - timedelta(days=i)
        payload = fetch_day(d)
        out = HERE / "data" / f"events_{d}.json"
        out.write_text(json.dumps(payload, indent=1))
        log.info("%s — %d events, %d afk", out.name,
                 len(payload["events"]), len(payload["afk"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
