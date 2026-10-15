#!/usr/bin/env python3
"""Event-driven refresh dispatcher. Runs every 15 min from GitHub Actions and exits fast.
Decides: full refresh (overnight ~2:30 AM ET, morning ~7:00 AM ET) or a targeted pre-game refresh
(~90 and ~30 min before each event's start), otherwise nothing. Each window fires once (data/refresh_state.json).
GitHub cron can lag 5-15+ min, so every window is a span, not an instant.
Usage: dispatch.py [--now ISO8601] [--dry]   -> prints decision; writes $GITHUB_OUTPUT mode/targets."""
import json, os, sys, datetime as dt
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York"); UTC = dt.timezone.utc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "refresh_state.json")
FULL = [("overnight", 2, 30), ("morning", 7, 0)]   # ET; window = target .. target+3h
FULL_SPAN = dt.timedelta(hours=3)
SKATE = (11, 30)   # ET morning-skate goalie/lines check for every team playing today (window 11:30 AM-1:30 PM ET)
PRE = {90: (dt.timedelta(minutes=150), dt.timedelta(minutes=45)),   # widened: GitHub often runs */15 crons only every 1-2 h   # fire when start-105m <= now < start-45m
       30: (dt.timedelta(minutes=40), dt.timedelta(minutes=0))}     # fire when start-40m  <= now < start

from events import load_events   # repo-specific: returns [(event_key, start_utc_datetime, target_label)]

def decide(now, events, state):
    fired = state.setdefault("fired", {})
    due_full = []
    for name, h, m in FULL:
        d = now.astimezone(ET).date()
        for day in (d, d - dt.timedelta(days=1)):
            t = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=ET)
            key = f"full:{name}:{day.isoformat()}"
            if t - dt.timedelta(minutes=45) <= now < t + FULL_SPAN and key not in fired: due_full.append(key)
    due_pre = []
    for ek, start, target in events:
        for w, (a, b) in PRE.items():
            key = f"pre{w}:{ek}"
            if start - a <= now < start - b and key not in fired: due_pre.append((key, target))
    sd = now.astimezone(ET).date(); st = dt.datetime(sd.year, sd.month, sd.day, *SKATE, tzinfo=ET)
    if st <= now < st + dt.timedelta(hours=2) and f"skate:{sd}" not in fired:
        today = [t for ek, start, t in events if start.astimezone(ET).date() == sd]
        if today: due_pre += [(f"skate:{sd}", t) for t in today]
    if due_full:
        mode, targets, keys = "full", [], due_full + [k for k, _ in due_pre]   # full covers any pre-game window too
    elif due_pre:
        mode, targets, keys = "pregame", sorted({t for _, t in due_pre}), [k for k, _ in due_pre]
    else:
        mode, targets, keys = "none", [], []
    for k in keys: fired[k] = now.isoformat(timespec="minutes")
    cutoff = now - dt.timedelta(days=3)   # prune
    state["fired"] = {k: v for k, v in fired.items() if dt.datetime.fromisoformat(v) > cutoff}
    return mode, targets, keys

def main():
    args = sys.argv[1:]
    now = dt.datetime.fromisoformat(args[args.index("--now") + 1]) if "--now" in args else dt.datetime.now(UTC)
    if now.tzinfo is None: now = now.replace(tzinfo=UTC)
    if "--force-full" in args or os.environ.get("FORCE_FULL") == "true":
        print("mode=full (manual)"); out("full", []); return
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    mode, targets, keys = decide(now, load_events(), state)
    print(f"now={now.astimezone(ET):%Y-%m-%d %H:%M ET} mode={mode} targets={','.join(targets)} windows={keys}")
    if mode != "none" and "--dry" not in args:
        state["last"] = dict(at=now.isoformat(timespec="minutes"), mode=mode, targets=targets)
        json.dump(state, open(STATE, "w"), indent=0, sort_keys=True)
    out(mode, targets)

def out(mode, targets):
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a") as f: f.write(f"mode={mode}\ntargets={','.join(targets)}\n")

if __name__ == "__main__":
    main()
