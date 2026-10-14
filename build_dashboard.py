#!/usr/bin/env python3
"""Build the ECharts dashboard from categorized day files.

Reads every data/categorized_*.json (and data/categorized_sample*), writes
dist/index.html — a self-contained page (ECharts via CDN, data inlined).

    python3 build_dashboard.py
"""

import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

log = logging.getLogger("build_dashboard")
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DIST = HERE / "dist"

FOCUS = {"work", "writing", "research"}
PALETTE = {
    "work": "#4e79a7", "writing": "#59a14f", "research": "#9c755f",
    "communication": "#f28e2b", "media": "#b07aa1", "system": "#76b7b2",
    "distraction": "#e15759", "afk": "#bab0ac", "other": "#bab0ac",
}
ORDER = ["work", "writing", "research", "communication",
         "system", "media", "distraction", "afk", "other"]


def load_days() -> dict[str, dict]:
    days = {}
    for f in sorted(DATA.glob("categorized_*.json")):
        p = json.loads(f.read_text())
        day = p.get("day", f.stem)
        if day in days:
            log.warning("duplicate day %s in %s — keeping first", day, f.name)
            continue
        days[day] = p
    if not days:
        raise SystemExit("no data/categorized_*.json — run categorize.py first")
    return days


def aggregate(days: dict[str, dict]) -> dict:
    per_day = {}
    for day, payload in days.items():
        cat_min = defaultdict(float)
        app_min = defaultdict(float)
        hourly = defaultdict(lambda: defaultdict(float))
        for ev in payload.get("events", []):
            dur = ev.get("duration", 0) / 60.0
            cat = ev.get("category", "other")
            cat_min[cat] += dur
            app = ev.get("data", {}).get("app", "?")
            app_min[app] += dur
            try:
                hour = int(str(ev.get("timestamp", ""))[11:13] or 0)
            except ValueError:
                hour = 0
            hourly[hour][cat] += dur
        afk_min = sum(e.get("duration", 0) for e in payload.get("afk", [])) / 60.0
        if afk_min:
            cat_min["afk"] += afk_min
        focus = sum(cat_min[c] for c in FOCUS)
        total = sum(v for k, v in cat_min.items() if k != "afk")
        per_day[day] = {
            "categories": {k: round(v, 1) for k, v in sorted(cat_min.items())},
            "hourly": {h: {c: round(v, 1) for c, v in cats.items()}
                       for h, cats in sorted(hourly.items())},
            "top_apps": sorted(app_min.items(), key=lambda kv: -kv[1])[:10],
            "focus_minutes": round(focus, 1),
            "active_minutes": round(total, 1),
            "focus_score": round(100 * focus / total) if total else 0,
        }
    return {"days": per_day, "order": ORDER, "palette": PALETTE}


HTML = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vibe-activity</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
 body{margin:0;font:14px system-ui,sans-serif;background:#0f1420;color:#e8ecf4}
 main{max-width:1100px;margin:0 auto;padding:20px}
 h1{font-size:20px;margin:0 0 4px}.sub{color:#9aa4b8;margin:0 0 16px}
 .kpis{display:flex;gap:24px;margin:10px 0 20px;flex-wrap:wrap}
 .kpi b{font-size:26px;display:block}.kpi span{color:#9aa4b8;font-size:12px}
 .chart{height:320px;background:#171e2e;border:1px solid #2a3450;border-radius:8px;margin-bottom:16px}
 select{background:#171e2e;color:#e8ecf4;border:1px solid #2a3450;border-radius:6px;padding:6px}
</style></head><body><main>
<h1>vibe-activity</h1>
<p class="sub">Local ActivityWatch data + local-LLM categorization. Nothing leaves the machine.</p>
<label>Day <select id="day"></select></label>
<div class="kpis">
 <div class="kpi"><b id="k-score">–</b><span>focus score</span></div>
 <div class="kpi"><b id="k-focus">–</b><span>focus time</span></div>
 <div class="kpi"><b id="k-active">–</b><span>active time</span></div>
</div>
<div class="chart" id="c-hours"></div>
<div class="chart" id="c-cats"></div>
<div class="chart" id="c-apps"></div>
<div class="chart" id="c-trend"></div>
</main>
<script>
const DATA = __DATA__;
// Escape untrusted strings (app/category/day names) before they reach
// ECharts tooltips — tooltips render HTML, so raw names enable XSS.
const enc = s => String(s).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";");
const tip = p => {
 const a = Array.isArray(p) ? p : [p];
 const head = a[0] && a[0].axisValue != null ? enc(a[0].axisValue) + "<br>" : "";
 return head + a.map(x => enc(x.seriesName || x.name || "") + ": " + x.value).join("<br>");
};
const days = Object.keys(DATA.days).sort();
const sel = document.getElementById("day");
days.forEach(d => sel.appendChild(new Option(d, d)));
sel.value = days[days.length - 1];
const mk = id => echarts.init(document.getElementById(id), null, {renderer:"canvas"});
const charts = {hours: mk("c-hours"), cats: mk("c-cats"), apps: mk("c-apps"), trend: mk("c-trend")};
const base = {textStyle:{color:"#e8ecf4"}, backgroundColor:"transparent",
 legend:{textStyle:{color:"#9aa4b8"}}, tooltip:{trigger:"axis"}};
const cats = DATA.order.filter(c => days.some(d => DATA.days[d].categories[c]));

function hoursOption(d){
 const hours = Object.keys(DATA.days[d].hourly).map(Number);
 return {...base, tooltip:{trigger:"axis", formatter:tip}, xAxis:{type:"category",
   data: hours.map(h => String(h).padStart(2,"0")+":00")},
   yAxis:{type:"value",name:"min"},
   series: cats.map(c => ({name:c, type:"bar", stack:"t", itemStyle:{color:DATA.palette[c]},
     data: hours.map(h => (DATA.days[d].hourly[h]||{})[c]||0)})),
   title:{text:"Minutes by hour", textStyle:{color:"#e8ecf4",fontSize:14}}};
}
function catsOption(d){
 const c = DATA.days[d].categories;
 return {...base, tooltip:{trigger:"item", formatter:tip}, legend:{type:"scroll",textStyle:{color:"#9aa4b8"}},
   series:[{type:"pie", radius:["40%","70%"], label:{color:"#e8ecf4"},
     data:Object.entries(c).map(([k,v])=>({name:k,value:v,itemStyle:{color:DATA.palette[k]}}))}],
   title:{text:"Where the day went", textStyle:{color:"#e8ecf4",fontSize:14}}};
}
function appsOption(d){
 const apps = DATA.days[d].top_apps;
 return {...base, tooltip:{trigger:"axis", formatter:tip},
   xAxis:{type:"value",name:"min"}, yAxis:{type:"category",
   data:apps.map(a=>a[0]).reverse()},
   series:[{type:"bar", itemStyle:{color:"#4e79a7"},
     data:apps.map(a=>Math.round(a[1]*10)/10).reverse()}],
   title:{text:"Top apps", textStyle:{color:"#e8ecf4",fontSize:14}}};
}
function trendOption(){
 return {...base, tooltip:{trigger:"axis", formatter:tip},
   xAxis:{type:"category",data:days}, yAxis:{type:"value",name:"focus %"},
   series:[{name:"focus score",type:"line",smooth:true,itemStyle:{color:"#59a14f"},
     areaStyle:{opacity:.15}, data:days.map(d=>DATA.days[d].focus_score)}],
   title:{text:"Focus trend", textStyle:{color:"#e8ecf4",fontSize:14}}};
}
function render(){
 const d = sel.value, dd = DATA.days[d];
 document.getElementById("k-score").textContent = dd.focus_score + "%";
 document.getElementById("k-focus").textContent = Math.round(dd.focus_minutes) + " min";
 document.getElementById("k-active").textContent = Math.round(dd.active_minutes/60*10)/10 + " h";
 charts.hours.setOption(hoursOption(d), true);
 charts.cats.setOption(catsOption(d), true);
 charts.apps.setOption(appsOption(d), true);
 charts.trend.setOption(trendOption(), true);
}
sel.onchange = render; render();
addEventListener("resize", () => Object.values(charts).forEach(c => c.resize()));
</script></body></html>
"""


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    agg = aggregate(load_days())
    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    # Escape "<" so a value containing "</script>" cannot break out of the
    # inlined <script> block — json.dumps alone leaves it intact (XSS).
    blob = json.dumps(agg).replace("<", "\\u003c")
    out.write_text(HTML.replace("__DATA__", blob))
    log.info("wrote %s (%d days)", out, len(agg["days"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
