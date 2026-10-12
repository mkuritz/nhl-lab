# NHL Lab

Full-season NHL suite: schedules (rest/back-to-backs), skater + goalie stats, team stats, an approximate WAR, career/current-team head-to-head engine with "Legendary H2H" flags, goalie context, and Poisson game & season projections.

Live: https://mkuritz.github.io/nhl-lab/

Data: free public feeds only (api-web.nhle.com, api.nhle.com/stats/rest, ESPN injuries). Refresh is event-driven: full rebuild ~2:30 AM and ~7:00 AM ET, plus targeted rebuilds ~90 and ~30 min before each game (scripts/dispatch.py, every 15 min). Fantasy mode (ESPN standard points, cited; custom scoring) with weekly projections, start/sit, waiver risers (ESPN public rostership), games-per-week grid, goalie streamers. Methodology is in the app. All probabilities are model estimates, not sportsbook odds.

## Data sources

Core: NHL `api-web.nhle.com` + `api.nhle.com/stats/rest` (schedule, rosters, game logs, play-by-play, shifts), ESPN (news, injuries), ESPN fantasy.

Cross-check sources (added Oct 2026; `scripts/nhl_xcheck.py` → `data/xcheck.json`, shown on `sources.html`):

| Source | Used for |
|---|---|
| MoneyPuck season CSVs (skaters, goalies) | Goals vs expected goals ("running hot" / "due"), on-ice xG%, goalie GSAx. MoneyPuck's terms: free for non-commercial use with credit, so it's credited on the page; get permission before commercial use. |
| Daily Faceoff starting goalies (public page, robots-allowed; `/api/` is not used) | Second opinion on our projected starter; flags a different Confirmed goalie |
| NHL EDGE (`api-web.nhle.com/v1/edge/skater-detail`) | Skating speed, shot speed, OZ time, high-danger shots for the top 40 slate skaters (full refreshes only) |

Not used: Natural Stat Trick (robots disallows its report/line pages and it asks not to be scraped).
Cross-checks don't change projections. The step is `continue-on-error`, and failed sources keep their previous table.
