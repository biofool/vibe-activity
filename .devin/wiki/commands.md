# Commands

```bash
./run.sh [--days N] [--offline]     # full pipeline: fetch -> categorize -> dashboard
python3 categorize.py --offline data/sample_events.json   # demo without ActivityWatch
python3 build_dashboard.py          # rebuild dist/index.html from categorized_*.json
python3 -m pytest tests/            # unit tests
```
