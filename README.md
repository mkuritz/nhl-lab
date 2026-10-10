# NHL Lab

Full-season NHL suite: schedules (rest/back-to-backs), skater + goalie stats, team stats, an approximate WAR, career/current-team head-to-head engine with "Legendary H2H" flags, goalie context, and Poisson game & season projections.

Live: https://mkuritz.github.io/nhl-lab/

Data: free public feeds only — api-web.nhle.com, api.nhle.com/stats/rest, ESPN NHL injuries. `scripts/build.py` writes `data/*.json`; GitHub Actions rebuilds ~7:00 AM and ~11:30 PM ET (and on demand). Past-season game logs cached in `data/cache/gl/`. Methodology is in the app (Methodology tab). All probabilities are model estimates, not sportsbook odds.
