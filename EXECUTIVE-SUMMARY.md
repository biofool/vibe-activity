# Executive Summary — vibe-activity

## What it is

vibe-activity is a personal, fully local replacement for Rize
(~$120/yr SaaS). It tracks computer activity through ActivityWatch,
classifies window titles into categories (work, writing, research,
distraction, etc.), and renders a static HTML dashboard with a focus
score, time-by-hour, and category breakdowns.

## Benefits for somatic studios and the field

Direct benefit is limited: this is a single-user productivity tool,
not studio-management software. It does not handle bookings, members,
or payments.

Indirect benefits:

- **Cost.** Studio owners and teachers who buy time-tracking SaaS get
  the same core job (automatic tracking + focus analytics) for free.
- **Privacy.** All data stays on the local machine. Window titles can
  contain client or student names; nothing is sent to a third party.
  The optional LLM pass runs against a local model by default.
- **Reusable pattern.** The pipeline (local event capture → regex
  rules → cached local-LLM fallback → static dashboard) is small,
  dependency-free, and easy to copy into other studio tooling.

## Caveats

- Single-user desktop tool; no multi-user or hosted mode.
- Dashboard needs network access once to load ECharts from a CDN
  (vendor the file into `dist/` to remove this).
- Wayland requires a compatible ActivityWatch window watcher.
