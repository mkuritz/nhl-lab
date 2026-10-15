#!/usr/bin/env python3
"""Game-day live feed (official api-web.nhle.com only). Writes to $LIVE_OUT (default data/):
  live.json   - today's games: state, score, period, clock, SOG; starting goalies with status/source/timestamp
  recaps.json - Sports Labs-written recap of each skater/goalie's most recent game (box score + play-by-play + shift charts)
Does not change projections. Published to the `live` branch so it doesn't trigger Pages rebuilds."""
import json, os, sys, datetime as dt, urllib.request, time
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as LN
from rivalries import tag as rival_tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.environ.get("LIVE_OUT", DATA)
ET = ZoneInfo("America/New_York")
W = "https://api-web.nhle.com/v1"
NOW = dt.datetime.now(ET)
SHC = os.path.join(DATA, "cache", "shifts"); os.makedirs(SHC, exist_ok=True)

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nhl-lab-live/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == tries - 1: print("FAIL", url, e); return None
            time.sleep(1.2 * (i + 1))

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def mmss(t):
    try: m, s = t.split(":"); return int(m) * 60 + int(s)
    except Exception: return 0

def fmt(sec): return f"{sec // 60}:{sec % 60:02d}"

def dfo_confirmed():
    """Daily Faceoff statuses already collected by the main refresh's cross-check (data/xcheck.json); no extra fetch here."""
    x = load(os.path.join(DATA, "xcheck.json"), {})
    out = {}
    for t in x.get("tables", []):
        if t.get("title", "").startswith("Starting goalies"):
            for r in t.get("rows", []):
                if len(r) >= 5 and str(r[4]).lower().startswith("confirm"):
                    out[(r[0], r[1])] = dict(goalie=r[3], asOf=x.get("generated"))
    return out

def game_state(g):
    a, h = g.get("awayTeam") or {}, g.get("homeTeam") or {}
    st = g.get("gameState"); clock = g.get("clock") or {}; pd = g.get("periodDescriptor") or {}
    riv = rival_tag(a.get("abbrev"), h.get("abbrev"))
    return dict(id=g["id"], state=st, away=a.get("abbrev"), home=h.get("abbrev"), as_=a.get("score"), hs=h.get("score"),
                sogA=a.get("sog"), sogH=h.get("sog"), period=pd.get("number"), periodType=pd.get("periodType"),
                clock=clock.get("timeRemaining"), intermission=clock.get("inIntermission"),
                end=(g.get("gameOutcome") or {}).get("lastPeriodType") if st in ("OFF", "FINAL") else None,
                startUTC=g.get("startTimeUTC"), rivalry=riv["label"] if riv else None)

def recap_game(gid, date):
    """Per-player recap dicts for one final game."""
    box = get(f"{W}/gamecenter/{gid}/boxscore"); pbp = get(f"{W}/gamecenter/{gid}/play-by-play")
    if not box or not pbp: return {}
    a, h = box["awayTeam"]["abbrev"], box["homeTeam"]["abbrev"]
    fa, fh = box["awayTeam"].get("score"), box["homeTeam"].get("score")
    end = (box.get("gameOutcome") or {}).get("lastPeriodType")
    names = {r["playerId"]: f'{r["firstName"]["default"]} {r["lastName"]["default"]}' for r in pbp.get("rosterSpots", [])}
    tid = {box["awayTeam"]["id"]: a, box["homeTeam"]["id"]: h}
    sh = None
    try: sh = LN.game_lines(gid, get, SHC)
    except Exception as e: print("shifts fail", gid, e)
    pp = {}
    if sh:
        for t in sh["teams"].values():
            for k, v in t["pp"].items(): pp[int(k)] = v
    notes = {}
    def add(pid, txt):
        if pid: notes.setdefault(pid, []).append(txt)
    for p in pbp.get("plays", []):
        d = p.get("details") or {}; per = (p.get("periodDescriptor") or {}).get("number"); tm = p.get("timeInPeriod")
        pl = f"P{per}" if per and per <= 3 else "OT" if per == 4 else "SO" if per and per > 4 else ""
        if p.get("typeDescKey") == "goal":
            sc = p.get("situationCode") or "1551"; team = tid.get(d.get("eventOwnerTeamId"))
            mine, theirs = (int(sc[2]), int(sc[1])) if team == h else (int(sc[1]), int(sc[2]))
            strength = "power-play " if mine > theirs else "shorthanded " if mine < theirs else ""
            if (team == h and sc[0] == "0") or (team == a and sc[3] == "0"): strength += "empty-net "
            sco = d.get("scoringPlayerId"); st_ = d.get("shotType")
            add(sco, f"{strength}goal ({st_ + ' shot, ' if st_ else ''}{pl} {tm}), making it {a} {d.get('awayScore')}, {h} {d.get('homeScore')}".strip())
            for k in ("assist1PlayerId", "assist2PlayerId"):
                if d.get(k): add(d[k], f"assist on {names.get(sco, 'a')} {strength}goal ({pl} {tm})")
    out = {}
    for side, team, opp, home in (("awayTeam", a, h, False), ("homeTeam", h, a, True)):
        pbg = (box.get("playerByGameStats") or {}).get(side) or {}
        won = (fh > fa) if home else (fa > fh)
        res = f'{"W" if won else "L"} {max(fa, fh)}-{min(fa, fh)}{" " + end if end and end != "REG" else ""}'
        for grp in ("forwards", "defense"):
            for s in pbg.get(grp, []):
                pid = s["playerId"]; toi = mmss(s.get("toi", "0:00"))
                if toi == 0: continue
                nm = names.get(pid, s.get("name", {}).get("default", ""))
                g_, a_, sog = s.get("goals", 0), s.get("assists", 0), s.get("sog", 0)
                line = f'{g_}G {a_}A, {sog} SOG, {s.get("plusMinus", 0):+d}, {s.get("hits", 0)} hits, {s.get("blockedShots", 0)} blocks'
                lead = (f"{nm} had {g_ + a_} point{'s' if g_ + a_ != 1 else ''} ({g_}G, {a_}A)" if g_ + a_ else f"{nm} was held off the scoresheet")
                txt = f"{lead} with {sog} shot{'s' if sog != 1 else ''} in {fmt(toi)} of ice time"
                if pid in pp and pp[pid] >= 10: txt += f", including {fmt(pp[pid])} on the power play"
                txt += f" as {team} {'beat' if won else 'fell to'} {opp} {max(fa, fh)}-{min(fa, fh)}{' in ' + end if end and end != 'REG' else ''}."
                out[pid] = dict(gid=gid, date=date, team=team, opp=opp, home=home, result=res, line=line, toi=fmt(toi), pptoi=fmt(pp[pid]) if pid in pp else None,
                                g=g_, a=a_, sog=sog, pm=s.get("plusMinus", 0), hits=s.get("hits", 0), blk=s.get("blockedShots", 0), pim=s.get("pim", 0),
                                shifts=s.get("shifts"), fo=s.get("faceoffWinningPctg"), plays=notes.get(pid, [])[:6], text=txt)
        for s in pbg.get("goalies", []):
            pid = s["playerId"]; toi = mmss(s.get("toi", "0:00"))
            if toi == 0: continue
            nm = names.get(pid, ""); sa, sv, ga = s.get("shotsAgainst", 0), s.get("saves", 0), s.get("goalsAgainst", 0)
            dec = s.get("decision")
            txt = f"{nm} stopped {sv} of {sa} shots ({(sv / sa if sa else 0):.3f}) in {fmt(toi)}{' and took the ' + {'W': 'win', 'L': 'loss', 'O': 'OT loss'}.get(dec, '') if dec else ''} as {team} {'beat' if won else 'fell to'} {opp} {max(fa, fh)}-{min(fa, fh)}."
            out[pid] = dict(gid=gid, date=date, team=team, opp=opp, home=home, result=res, goalie=True, line=f"{sv}/{sa} saves, {ga} GA", toi=fmt(toi),
                            sa=sa, sv=sv, ga=ga, starter=bool(s.get("starter")), plays=[], text=txt)
    return out

def main():
    today = NOW.date().isoformat()
    score = get(f"{W}/score/{today}") or {}
    games = [game_state(g) for g in score.get("games") or []]
    dfo = dfo_confirmed(); goalies = []
    for g, raw in zip(games, score.get("games") or []):
        if g["state"] in ("LIVE", "CRIT", "OFF", "FINAL"):
            box = get(f"{W}/gamecenter/{g['id']}/boxscore") or {}
            pbg = box.get("playerByGameStats") or {}
            for side, team in (("awayTeam", g["away"]), ("homeTeam", g["home"])):
                gl = next((x for x in (pbg.get(side) or {}).get("goalies", []) if x.get("starter")), None)
                if gl:
                    goalies.append(dict(gid=g["id"], team=team, goalieId=gl["playerId"], goalie=gl.get("name", {}).get("default"),
                                        status="Confirmed", source="NHL official boxscore (starter)", asOf=NOW.isoformat(timespec="minutes")))
        else:
            for team in (g["away"], g["home"]):
                c = dfo.get((today, team))
                if c: goalies.append(dict(gid=g["id"], team=team, goalie=c["goalie"], status="Confirmed", source="Daily Faceoff (reported confirmed)", asOf=c["asOf"]))
    json.dump(dict(date=today, updated=NOW.isoformat(timespec="minutes"), updatedET=NOW.strftime("%b %-d, %-I:%M %p ET"),
                   games=games, goalies=goalies, source="api-web.nhle.com"), open(os.path.join(OUT, "live.json"), "w"), separators=(",", ":"))
    # recaps: every final game today + yesterday not yet recapped
    rp = os.path.join(OUT, "recaps.json"); R = load(rp, {"players": {}, "games": []})
    done = set(R.get("games", []))
    finals = [(g["id"], today) for g in games if g["state"] in ("OFF", "FINAL")]
    for back in range(1, int(os.environ.get("RECAP_DAYS", "4")) + 1):   # look back so every team's latest game is covered
        yd = (NOW.date() - dt.timedelta(days=back)).isoformat()
        for g in (get(f"{W}/score/{yd}") or {}).get("games", []):
            if g.get("gameState") in ("OFF", "FINAL") and g["id"] not in done: finals.append((g["id"], yd))
    new = 0
    for gid, d in finals:
        if gid in done: continue
        rc = recap_game(gid, d)
        if not rc: continue
        for pid, v in rc.items():
            old = R["players"].get(str(pid))
            if not old or old["date"] <= d: R["players"][str(pid)] = v
        done.add(gid); new += 1
    R["games"] = sorted(done)[-400:]; R["updated"] = NOW.isoformat(timespec="minutes")
    R["note"] = "Recaps written by Sports Labs from official NHL box scores, play-by-play and shift charts (api-web.nhle.com, api.nhle.com)."
    json.dump(R, open(rp, "w"), separators=(",", ":"))
    print("live", today, len(games), "games,", len(goalies), "goalies,", new, "new recaps,", NOW.strftime("%H:%M ET"))
    # tell the loop whether games are still active (pre/live) today
    active = any(g["state"] in ("PRE", "LIVE", "CRIT") for g in games) or any(
        g["state"] == "FUT" and g["startUTC"] and dt.datetime.fromisoformat(g["startUTC"].replace("Z", "+00:00")) - NOW < dt.timedelta(minutes=90) for g in games)
    p = os.environ.get("GITHUB_OUTPUT")
    if p: open(p, "a").write(f"active={'1' if active else '0'}\n")
    return active

if __name__ == "__main__":
    main()
