#!/usr/bin/env bash
# Full pipeline: ActivityWatch -> categorize -> dashboard.
#   ./run.sh                  # today
#   ./run.sh --days 7         # trailing week
#   ./run.sh --offline        # skip the LLM pass (regex only)
set -euo pipefail
cd "$(dirname "$0")"

OFFLINE=""
DAYS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline) OFFLINE="--offline"; shift ;;
    --days) DAYS="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

python3 fetch_aw.py --days "$DAYS"
for f in data/events_*.json; do
  python3 categorize.py $OFFLINE "$f"
done
python3 build_dashboard.py
echo "open dist/index.html"
