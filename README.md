# NHL Lab

Full-season NHL suite: schedules (rest/back-to-backs), skater + goalie stats, team stats, an approximate WAR, career/current-team head-to-head engine with "Legendary H2H" flags, goalie context, and Poisson game & season projections.

Live: https://mkuritz.github.io/nhl-lab/

Data: free public feeds only (api-web.nhle.com, api.nhle.com/stats/rest, ESPN injuries). Refresh is event-driven: full rebuild ~2:30 AM and ~7:00 AM ET, plus targeted rebuilds ~90 and ~30 min before each game (scripts/dispatch.py, every 15 min). Methodology is in the app. All probabilities are model estimates, not sportsbook odds.
