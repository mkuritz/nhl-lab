#!/usr/bin/env python3
"""NHL Lab data builder. Free public sources only:
api-web.nhle.com, api.nhle.com/stats/rest, ESPN injuries. Writes data/*.json."""
import json, os, math, time, datetime as dt, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); CACHE = os.path.join(DATA, "cache", "gl")
os.makedirs(os.path.join(DATA, "players"), exist_ok=True); os.makedirs(CACHE, exist_ok=True)
ET = ZoneInfo("America/New_York")
NOW = dt.datetime.now(ET); TODAY = NOW.date()
SEASON = (TODAY.year if TODAY.month >= 7 else TODAY.year - 1) * 10001 + 1  # derived from date, e.g. 20262027
y0 = SEASON // 10000
if TODAY >= dt.date(y0 + 1, 7, 1): SEASON = (y0 + 1) * 10000 + y0 + 2
PREV = (SEASON // 10000 - 1) * 10000 + SEASON // 10000
TARGET = {t for t in os.environ.get("TARGET_TEAMS", "").replace("+", ",").split(",") if t}  # pre-game targeted mode
W = "https://api-web.nhle.com/v1"; S = "https://api.nhle.com/stats/rest/en"

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nhl-lab/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == tries - 1: print("FAIL", url, e); return None
            time.sleep(1.5 * (i + 1))

def pmap(fn, items, n=12):
    with ThreadPoolExecutor(n) as ex: return list(ex.map(fn, items))

def wj(name, obj):
    with open(os.path.join(DATA, name), "w") as f: json.dump(obj, f, separators=(",", ":"))

def r3(x, n=3): return None if x is None else round(x, n)
def norm(s): return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace(".", "").replace("-", " ").strip()
def toi_s(t):
    try: m, s = t.split(":"); return int(m) * 60 + int(s)
    except Exception: return 0

def stats(kind, report, season, extra=""):
    exp = f"seasonId={season}%20and%20gameTypeId=2" + extra
    d = get(f"{S}/{kind}/{report}?limit=-1&cayenneExp={exp}")
    return {r["playerId" if kind != "team" else "teamId"]: r for r in (d or {}).get("data", [])}

# ---------------- teams / standings ----------------
st = get(f"{W}/standings/now")["standings"]
TEAMS = {}
for s in st:
    ab = s["teamAbbrev"]["default"]
    TEAMS[ab] = dict(abbrev=ab, name=s["teamName"]["default"], common=s["teamCommonName"]["default"],
        logo=s["teamLogo"], conf=s["conferenceName"], div=s["divisionName"],
        gp=s["gamesPlayed"], w=s["wins"], l=s["losses"], otl=s["otLosses"], pts=s["points"],
        ptsPct=r3(s["pointPctg"]), gf=s["goalFor"], ga=s["goalAgainst"], diff=s["goalDifferential"],
        rw=s.get("regulationWins"), streak=f'{s.get("streakCode","")}{s.get("streakCount","")}',
        home=f'{s["homeWins"]}-{s["homeLosses"]}-{s["homeOtLosses"]}', road=f'{s["roadWins"]}-{s["roadLosses"]}-{s["roadOtLosses"]}',
        l10=f'{s["l10Wins"]}-{s["l10Losses"]}-{s["l10OtLosses"]}', divRank=s["divisionSequence"], confRank=s["conferenceSequence"],
        leagueRank=s["leagueSequence"], wildcard=s.get("wildcardSequence"))
ABBRS = sorted(TEAMS)
ID2AB = {}
for season, key in ((SEASON, "cur"), (PREV, "prev")):
    ts = stats("team", "summary", season)
    for tid, r in ts.items():
        ab = next((a for a in ABBRS if TEAMS[a]["name"] == r["teamFullName"]), None)
        if not ab: continue
        ID2AB[tid] = ab
        TEAMS[ab][key] = dict(gp=r["gamesPlayed"], gfpg=r3(r["goalsForPerGame"], 2), gapg=r3(r["goalsAgainstPerGame"], 2),
            sfpg=r3(r["shotsForPerGame"], 1), sapg=r3(r["shotsAgainstPerGame"], 1), pp=r3(r["powerPlayPct"]),
            pk=r3(r["penaltyKillPct"]), fo=r3(r["faceoffWinPct"]))

# ---------------- schedules ----------------
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rivalries import tag as RIV
def sched(ab): return ab, get(f"{W}/club-schedule-season/{ab}/{SEASON}")
GAMES = {}
for ab, d in pmap(sched, ABBRS):
    for g in (d or {}).get("games", []):
        if g["gameType"] != 2: continue
        GAMES[g["id"]] = g
games = []
for g in sorted(GAMES.values(), key=lambda g: g["startTimeUTC"]):
    a, h = g["awayTeam"], g["homeTeam"]
    t = dt.datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00")).astimezone(ET)
    fin = g["gameState"] in ("OFF", "FINAL")
    games.append(dict(id=g["id"], date=t.date().isoformat(), time=t.strftime("%-I:%M %p"), away=a["abbrev"], home=h["abbrev"],
        state=g["gameState"], venue=g.get("venue", {}).get("default"), as_=a.get("score") if fin or g["gameState"] in ("LIVE","CRIT") else None,
        hs=h.get("score") if fin or g["gameState"] in ("LIVE","CRIT") else None,
        end=(g.get("gameOutcome") or {}).get("lastPeriodType") if fin else None,
        riv=(RIV(a["abbrev"], h["abbrev"]) or {}).get("label")))
# rest days / back-to-backs
last = {}
for g in games:
    d = dt.date.fromisoformat(g["date"])
    for side in ("away", "home"):
        ab = g[side]; p = last.get(ab)
        rest = (d - p).days - 1 if p else None
        g[side[0] + "Rest"] = rest; g[side[0] + "B2B"] = rest == 0
        last[ab] = d
# team home/away splits from results
for ab in ABBRS:
    sp = {"H": [0, 0, 0], "R": [0, 0, 0]}
    for g in games:
        if g["hs"] is None or g["state"] not in ("OFF", "FINAL"): continue
        if g["home"] == ab: k, gf, ga = "H", g["hs"], g["as_"]
        elif g["away"] == ab: k, gf, ga = "R", g["as_"], g["hs"]
        else: continue
        sp[k][0] += 1; sp[k][1] += gf; sp[k][2] += ga
    TEAMS[ab]["splits"] = {k: dict(gp=v[0], gfpg=r3(v[1] / v[0], 2) if v[0] else None, gapg=r3(v[2] / v[0], 2) if v[0] else None) for k, v in sp.items()}
    TEAMS[ab]["b2b"] = sum(1 for g in games if (g["home"] == ab and g["hB2B"]) or (g["away"] == ab and g["aB2B"]))

# ---------------- injuries (ESPN) ----------------
inj = {}
d = get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries") or {}
name2ab = {TEAMS[a]["name"]: a for a in ABBRS}
name2ab.update({"Montreal Canadiens": "MTL", "St. Louis Blues": "STL", "Utah Mammoth": "UTA"})
for t in d.get("injuries", []):
    ab = name2ab.get(t["displayName"]) or next((a for a in ABBRS if norm(TEAMS[a]["name"]) == norm(t["displayName"])), None)
    for i in t.get("injuries", []):
        nm = i["athlete"]["displayName"]
        inj[(ab, norm(nm))] = dict(status=i.get("status"), note=i.get("shortComment"), date=(i.get("date") or "")[:10])

# ---------------- rosters ----------------
def roster(ab): return ab, get(f"{W}/roster/{ab}/current")
PL = {}
for ab, r in pmap(roster, ABBRS):
    for grp in ("forwards", "defensemen", "goalies"):
        for p in (r or {}).get(grp, []):
            nm = f'{p["firstName"]["default"]} {p["lastName"]["default"]}'
            PL[p["id"]] = dict(id=p["id"], name=nm, team=ab, pos=p["positionCode"], num=p.get("sweaterNumber"),
                head=p.get("headshot"), shoots=p.get("shootsCatches"), inj=inj.get((ab, norm(nm))))
print("players", len(PL))

# ---------------- league stats tables ----------------
def skater_tables(season):
    out = {}
    for rep in ("summary", "timeonice", "summaryshooting", "percentages", "powerplay", "realtime"):
        for pid, r in stats("skater", rep, season).items(): out.setdefault(pid, {}).update(r)
    return out
SK = {SEASON: skater_tables(SEASON), PREV: skater_tables(PREV)}
GO = {SEASON: stats("goalie", "summary", SEASON), PREV: stats("goalie", "summary", PREV)}

# ---------------- landing + game logs (cached) ----------------
def slim(land):
    return {k: land.get(k) for k in ("birthDate", "careerTotals", "draftDetails", "birthCity")} | {
        "seasonTotals": [s for s in land.get("seasonTotals", []) if s.get("leagueAbbrev") == "NHL" and s.get("gameTypeId") == 2]}
def player_detail(pid):
    cf = os.path.join(CACHE, f"{pid}.json")
    cache = json.load(open(cf)) if os.path.exists(cf) else {}
    if TARGET and PL[pid]["team"] not in TARGET and cache.get("_land"):
        return pid, cache["_land"], cache   # targeted run: reuse cached data for teams not playing soon
    land = get(f"{W}/player/{pid}/landing")
    if not land: return pid, cache.get("_land"), cache
    land = slim(land); cache["_land"] = land
    seasons = sorted({s["season"] for s in land.get("seasonTotals", []) if s.get("leagueAbbrev") == "NHL" and s.get("gameTypeId") == 2})
    for se in seasons:
        k = str(se)
        if k in cache and se not in (SEASON, PREV): continue
        if k in cache and se == PREV and cache.get("_prevfinal"): continue
        gl = get(f"{W}/player/{pid}/game-log/{se}/2")
        if gl is None: continue
        rows = []
        for g in gl.get("gameLog", []):
            if "shotsAgainst" in g:
                rows.append([g["gameId"], g["gameDate"], g["teamAbbrev"], g["opponentAbbrev"], g["homeRoadFlag"],
                    g.get("gamesStarted", 0), g.get("shotsAgainst", 0), g.get("goalsAgainst", 0), g.get("decision"), toi_s(g.get("toi", "0:00"))])
            else:
                rows.append([g["gameId"], g["gameDate"], g["teamAbbrev"], g["opponentAbbrev"], g["homeRoadFlag"],
                    g.get("goals", 0), g.get("assists", 0), g.get("shots", 0), g.get("powerPlayPoints", 0), toi_s(g.get("toi", "0:00")), g.get("plusMinus", 0)])
        cache[k] = rows
        if se == PREV and TODAY.month >= 9: cache["_prevfinal"] = True
    json.dump(cache, open(cf, "w"), separators=(",", ":"))
    return pid, land, cache
details = {pid: (land, cache) for pid, land, cache in pmap(player_detail, list(PL), 12)}

# ---------------- league baselines ----------------
def lg_sv(season):
    sa = sum(r["shotsAgainst"] for r in GO[season].values()); ga = sum(r["goalsAgainst"] for r in GO[season].values())
    return 1 - ga / sa if sa else 0.900
LSV = {SEASON: lg_sv(SEASON), PREV: lg_sv(PREV)}
def lg_gpg(key):
    t = [TEAMS[a].get(key) for a in ABBRS if TEAMS[a].get(key)]
    gp = sum(x["gp"] for x in t)
    return (sum(x["gfpg"] * x["gp"] for x in t) / gp if gp else 3.0), (sum(x["sfpg"] * x["gp"] for x in t) / gp if gp else 28.5)
LG = {"cur": lg_gpg("cur"), "prev": lg_gpg("prev")}

# ---------------- WAR (GAR) ----------------
GOALS_PER_WIN = 6.0
def gar_season(season):
    sk = SK[season]; res = {}
    rows = [r for r in sk.values() if r.get("gamesPlayed", 0) >= 5]
    def grp(r): return "D" if r.get("positionCode") == "D" else "F"
    def per60(r, kind):
        if kind == "ev":
            t = r.get("evTimeOnIce", 0) / 3600
            return t, (r.get("evGoals", 0) + 0.5 * (r.get("evPoints", 0) - r.get("evGoals", 0)))
        t = r.get("ppTimeOnIce", 0) / 3600
        return t, (r.get("ppGoals", 0) + 0.5 * (r.get("ppPoints", 0) - r.get("ppGoals", 0)))
    repl = {}
    for gname, cut in (("F", 13 * 32), ("D", 7 * 32)):
        g = sorted([r for r in rows if grp(r) == gname], key=lambda r: -r.get("timeOnIce", 0))
        rp = g[cut:] if len(g) > cut else g[int(len(g) * 0.75):]
        for kind in ("ev", "pp"):
            T = sum(per60(r, kind)[0] for r in rp); X = sum(per60(r, kind)[1] for r in rp)
            repl[(gname, kind)] = X / T if T else 0
        repl[(gname, "rel")] = sum(r.get("satRelative") or 0 for r in rp) / max(1, len(rp))
    att_per60 = 110.0; g_per_att = 0.045
    for r in sk.values():
        gname = grp(r)
        te, xe = per60(r, "ev"); tp, xp = per60(r, "pp")
        ev = xe - repl[(gname, "ev")] * te
        pp = xp - repl[(gname, "pp")] * tp
        t5 = (r.get("timeOnIcePerGame5v5") or 0) * r.get("gamesPlayed", 0) / 3600
        poss = ((r.get("satRelative") or 0) - repl[(gname, "rel")]) * att_per60 * t5 * g_per_att * 0.5
        gar = ev + pp + poss
        res[r["playerId"]] = dict(ev=r3(ev, 1), pp=r3(pp, 1), poss=r3(poss, 1), gar=r3(gar, 1), war=r3(gar / GOALS_PER_WIN, 2), gp=r.get("gamesPlayed"))
    # goalies: replacement sv% = SA-weighted sv% of goalies outside top 64 by shots against (min 1 GP)
    go = sorted(GO[season].values(), key=lambda r: -r["shotsAgainst"])
    rp = go[64:] if len(go) > 70 else go[int(len(go) * 0.66):]
    sa = sum(r["shotsAgainst"] for r in rp); ga = sum(r["goalsAgainst"] for r in rp)
    rsv = 1 - ga / sa if sa else LSV[season] - 0.01
    rsv = min(rsv, LSV[season] - 0.004)
    for r in go:
        gsaa = (r["savePct"] or 0) * r["shotsAgainst"] - LSV[season] * r["shotsAgainst"] if r["shotsAgainst"] else 0
        gar = ((r["savePct"] or 0) - rsv) * r["shotsAgainst"]
        res[r["playerId"]] = dict(gsaa=r3(gsaa, 1), gar=r3(gar, 1), war=r3(gar / GOALS_PER_WIN, 2), gp=r["gamesPlayed"])
    return res, dict(F_ev60=r3(repl[("F", "ev")]), F_pp60=r3(repl[("F", "pp")]), D_ev60=r3(repl[("D", "ev")]), D_pp60=r3(repl[("D", "pp")]),
                     F_rel=r3(repl[("F", "rel")]), D_rel=r3(repl[("D", "rel")]), goalie_sv=r3(rsv, 4), league_sv=r3(LSV[season], 4))
WAR = {}; REPL = {}
for se in (SEASON, PREV): WAR[se], REPL[se] = gar_season(se)

# ---------------- goalie quality & projected starters ----------------
def goalie_sv(pid):
    c, p = GO[SEASON].get(pid), GO[PREV].get(pid)
    sa = (c["shotsAgainst"] if c else 0) + 0.7 * (p["shotsAgainst"] if p else 0)
    sv = (c["saves"] if c else 0) + 0.7 * (p["saves"] if p else 0)
    k = 600
    return (sv + LSV[SEASON] * k) / (sa + k) if True else None, sa
INJ_OUT = ("Out", "Injured Reserve", "Day-To-Day", "Long Term Injured Reserve", "Suspension")
team_goalies = {}
for pid, p in PL.items():
    if p["pos"] != "G": continue
    cache = details.get(pid, (None, {}))[1]
    cur = cache.get(str(SEASON), []); prev = cache.get(str(PREV), [])
    starts_cur = [r for r in cur if r[5] and r[2] == p["team"]]
    q, sa = goalie_sv(pid)
    team_goalies.setdefault(p["team"], []).append(dict(id=pid, name=p["name"], sv=r3(q, 4), shots=round(sa),
        starts=len(starts_cur), prevStarts=sum(1 for r in prev if r[5]),
        last=max([r[1] for r in starts_cur], default=None), inj=p["inj"],
        out=bool(p["inj"] and p["inj"]["status"] in INJ_OUT)))
def team_starter_order(ab):
    gs = team_goalies.get(ab, [])
    return sorted(gs, key=lambda g: -(g["starts"] * 3 + g["prevStarts"] * 0.3 + g["shots"] / 1000))
def project_goalie(ab, b2b):
    order = team_starter_order(ab)
    healthy = [g for g in order if not g["out"]]
    if not healthy: return None, "No healthy goalie found on roster", False
    st = healthy[0]; why = f'{st["name"]} has the most starts ({st["starts"]} this season)'
    backup = False
    if order and order[0]["out"]:
        why = f'Usual No. 1 {order[0]["name"]} is listed {order[0]["inj"]["status"]} (ESPN) — next man {st["name"]} projected'; backup = True
    elif b2b and len(healthy) > 1:
        st = healthy[1]; backup = True
        why = f'Second night of a back-to-back — teams usually rest the starter, so backup {st["name"]} is projected'
    return st, why, backup

# ---------------- skater rates ----------------
POSMEAN = {}
def rate_parts(pid):
    c, p = SK[SEASON].get(pid, {}), SK[PREV].get(pid, {})
    gpc, gpp = c.get("gamesPlayed", 0), p.get("gamesPlayed", 0)
    return c, p, gpc, gpp
for grp in ("F", "D"):
    rows = [r for r in SK[PREV].values() if r.get("gamesPlayed", 0) >= 20 and (r.get("positionCode") == "D") == (grp == "D")]
    gp = sum(r["gamesPlayed"] for r in rows) or 1
    POSMEAN[grp] = dict(g=sum(r["goals"] for r in rows) / gp, p=sum(r["points"] for r in rows) / gp, s=sum(r["shots"] for r in rows) / gp,
                        a=sum(r["assists"] for r in rows) / gp)
K_SHRINK = 12; W_PREV = 0.6
def skater_rates(pid, pos):
    c, p, gpc, gpp = rate_parts(pid)
    pm = POSMEAN["D" if pos == "D" else "F"]
    den = gpc + W_PREV * gpp + K_SHRINK
    f = lambda k, m: (c.get(k, 0) + W_PREV * p.get(k, 0) + K_SHRINK * m * 0.6) / den
    ppshare = ((c.get("ppPoints", 0) + W_PREV * p.get("ppPoints", 0)) / max(1, c.get("points", 0) + W_PREV * p.get("points", 0)))
    return dict(g=f("goals", pm["g"]), p=f("points", pm["p"]), s=f("shots", pm["s"]), a=f("assists", pm["a"]),
                gp=gpc + gpp, ppshare=ppshare, toi=(c.get("timeOnIcePerGame") or p.get("timeOnIcePerGame") or 0))

def team_factor(ab, key, lgv, kgames=10):
    t = TEAMS[ab]; c = t.get("cur") or {}; p = t.get("prev") or {}
    gc, gpv = c.get("gp", 0), p.get("gp", 0)
    vc, vp = c.get(key), p.get(key)
    num = (vc or 0) * gc + (vp or lgv) * min(gpv, 82) * 0.35 + lgv * kgames
    den = gc + min(gpv, 82) * 0.35 + kgames
    return (num / den) / lgv
LGA = (LG["cur"][0] * 1 if (TEAMS[ABBRS[0]].get("cur") or {}).get("gp") else LG["prev"][0])
LGA = (LG["cur"][0] + LG["prev"][0] * 2) / 3; LSA = (LG["cur"][1] + LG["prev"][1] * 2) / 3
LPK = sum((TEAMS[a].get("prev") or {}).get("pk") or 0.79 for a in ABBRS) / 32

# ---------------- H2H ----------------
def pois_tail(k, lam):
    if k <= 0: return 1.0
    s = 0.0; term = math.exp(-lam)
    for i in range(k): s += term; term *= lam / (i + 1)
    return max(0.0, 1 - s)
def rarity(pv):
    if pv is None: return ""
    if pv <= 0: return "rarer than 1-in-10,000 by luck"
    n = 1 / pv
    return f"about 1-in-{n:,.0f} by luck" if n < 10000 else "rarer than 1-in-10,000 by luck"
def h2h_for(pid, cache, cur_team):
    rows = [r for k, v in cache.items() if not k.startswith("_") for r in v]
    if not rows: return {}, {}
    gp = len(rows); G = sum(r[5] for r in rows); P = sum(r[5] + r[6] for r in rows)
    since_rows = []
    for r in sorted(rows, key=lambda r: r[1], reverse=True):
        if r[2] != cur_team: break
        since_rows.append(r)
    since_date = min((r[1] for r in since_rows), default=None)
    out = {}
    def blank(): return [0, 0, 0, 0, 0]
    for scope, rs in (("career", rows), ("team", since_rows)):
        for r in rs:
            o = out.setdefault(r[3], {"career": blank(), "team": blank(), "home": blank(), "road": blank(), "trail": []})
            for k in ((scope,) if scope == "team" else ("career", "home" if r[4] == "H" else "road")):
                x = o[k]; x[0] += 1; x[1] += r[5]; x[2] += r[6]; x[3] += r[5] + r[6]; x[4] += r[7]
            if scope == "career": o["trail"].append([r[1], r[4], r[5], r[6], r[7], r[2]])
    base = dict(gp=gp, gpg=G / gp, ppg=P / gp, since=since_date)
    tn = len(since_rows)
    base["teamGp"] = tn
    base["teamGpg"] = (sum(r[5] for r in since_rows) / tn) if tn else None
    base["teamPpg"] = (sum(r[5] + r[6] for r in since_rows) / tn) if tn else None
    whole = tn == gp
    # career home/road baselines (venue flags compare like with like)
    hb = [r for r in rows if r[4] == "H"]; rb = [r for r in rows if r[4] != "H"]
    vb = {"home": (sum(r[5] + r[6] for r in hb) / max(1, len(hb)), sum(r[5] for r in hb) / max(1, len(hb))),
          "road": (sum(r[5] + r[6] for r in rb) / max(1, len(rb)), sum(r[5] for r in rb) / max(1, len(rb)))}
    for opp, o in out.items():
        o["trail"] = sorted(o["trail"], reverse=True)[:6]
        flags = []
        # LEGENDARY: strict rate multiple + rarity (<= 1-in-500) + real sample
        for scope, minN, label in (("career", 12, "career"), ("team", 8, f"since joining {cur_team}")):
            n, g, a, p, sh = o[scope]
            if n < minN or (scope == "team" and whole): continue
            bp = base["ppg"] if scope == "career" else 0.5 * base["ppg"] + 0.5 * base["teamPpg"]
            bg = base["gpg"] if scope == "career" else 0.5 * base["gpg"] + 0.5 * base["teamGpg"]
            pvP, pvG = pois_tail(p, bp * n), pois_tail(g, bg * n)
            if p >= 10 and p / n >= 1.6 * bp and p / n >= 0.75 and pvP < 0.002:
                flags.append(dict(kind="legendary", scope=scope, stat="P", n=n, val=p, rate=r3(p / n, 2), base=r3(bp, 2), pv=pvP,
                                  label=f"{p} PTS in {n} GP {label} vs {opp} ({p/n:.2f}/gm vs his {bp:.2f})"))
            if g >= 7 and g / n >= 1.75 * bg and g / n >= 0.35 and pvG < 0.002:
                flags.append(dict(kind="legendary", scope=scope, stat="G", n=n, val=g, rate=r3(g / n, 2), base=r3(bg, 2), pv=pvG,
                                  label=f"{g} G in {n} GP {label} vs {opp} ({g/n:.2f}/gm vs his {bg:.2f})"))
        # VENUE crusher: home vs opp, or at opp's arena
        for v, where in (("home", f"at home vs {opp}"), ("road", f"at {opp}")):
            n, g, a, p, sh = o[v]; bpv, bgv = vb[v]
            if n < 8: continue
            pvP, pvG = pois_tail(p, bpv * n), pois_tail(g, bgv * n)
            if p >= 8 and p / n >= 1.7 * bpv and pvP < 0.005:
                flags.append(dict(kind="venue", scope=v, stat="P", n=n, val=p, rate=r3(p / n, 2), base=r3(bpv, 2), pv=pvP,
                                  label=f"{p} PTS in {n} GP {where} ({p/n:.2f}/gm vs his {bpv:.2f} {v} rate)"))
            elif g >= 5 and g / n >= 1.8 * bgv and pvG < 0.005:
                flags.append(dict(kind="venue", scope=v, stat="G", n=n, val=g, rate=r3(g / n, 2), base=r3(bgv, 2), pv=pvG,
                                  label=f"{g} G in {n} GP {where} ({g/n:.2f}/gm vs his {bgv:.2f} {v} rate)"))
        # HEATING UP: strong last 2-3 meetings (small sample, labeled)
        tr = o["trail"][:3]
        recent_cut = f"{PREV // 10000}-09-01"
        if len(tr) >= 2 and all(x[0] >= recent_cut for x in tr) and all(x[2] + x[3] > 0 for x in tr):
            tp = sum(x[2] + x[3] for x in tr); tg = sum(x[2] for x in tr); pvh = pois_tail(tp, base["ppg"] * len(tr))
            if (tg >= 3 or tp >= max(6, 2.2 * base["ppg"] * len(tr))) and pvh < 0.01:
                flags.append(dict(kind="heating", scope="recent", stat="P", n=len(tr), val=tp, rate=r3(tp / len(tr), 2), base=r3(base["ppg"], 2), pv=pvh,
                                  label=f"Last {len(tr)} vs {opp}: " + ", ".join(f"{x[2]}G {x[3]}A" for x in tr) + " (small sample)"))
        if flags: o["flags"] = flags
    return out, base

# ---------------- projections ----------------
upcoming = [g for g in games if g["state"] in ("FUT", "PRE") and g["date"] >= TODAY.isoformat()]
slate_days = sorted({g["date"] for g in upcoming})[:3]
goalie_proj = {}
for g in upcoming:
    if g["date"] not in slate_days: continue
    for side, opp in (("home", "away"), ("away", "home")):
        st, why, backup = project_goalie(g[side], g[side[0] + "B2B"])
        goalie_proj[(g["id"], g[side])] = (st, why, backup)
def goalie_for(gid, ab, b2b):
    if (gid, ab) in goalie_proj: return goalie_proj[(gid, ab)]
    order = [x for x in team_starter_order(ab) if not x["out"]]
    return (order[0] if order else None), "season-long: assumes usual starter", False

H2H = {}; BASE = {}
for pid, p in PL.items():
    if p["pos"] == "G": continue
    land, cache = details.get(pid, (None, {}))
    H2H[pid], BASE[pid] = h2h_for(pid, cache or {}, p["team"])

def project(pid, p, g, rates, detail=True):
    home = g["home"] == p["team"]; opp = g["away"] if home else g["home"]
    side = "h" if home else "a"; oside = "a" if home else "h"
    fac = {}; why = []
    ga_f = team_factor(opp, "gapg", LGA); fac["oppGA"] = ga_f
    sa_f = team_factor(opp, "sapg", LSA); fac["oppSA"] = sa_f
    gl, gwhy, backup = goalie_for(g["id"], opp, g[oside + "B2B"])
    gsv = gl["sv"] if gl else LSV[SEASON]
    g_f = max(0.75, min(1.3, (1 - gsv) / (1 - LSV[SEASON])))
    # opp GA already includes their goalies; weight goalie-specific 60%, team GA 40%
    goal_env = 0.6 * g_f + 0.4 * ga_f
    ha = 1.03 if home else 0.97
    b2b = 0.94 if g[side + "B2B"] else 1.0
    ob2b = 1.04 if g[oside + "B2B"] else 1.0
    opk = (TEAMS[opp].get("cur") or TEAMS[opp].get("prev") or {}).get("pk") or LPK
    pk_f = 1 + rates["ppshare"] * (((1 - opk) / (1 - LPK)) - 1) * 0.5
    m = goal_env * ha * b2b * ob2b * pk_f
    lg_, lp_, ls_ = rates["g"] * m, rates["p"] * (0.5 + 0.5 * m), rates["s"] * sa_f * ha * b2b
    out = dict(gid=g["id"], date=g["date"], opp=opp, home=home, xg=r3(lg_), xp=r3(lp_), xs=r3(ls_, 2),
               pG=r3(1 - math.exp(-lg_)), pP=r3(1 - math.exp(-lp_)),
               p3S=r3(pois_tail(3, ls_)), goalie=gl["name"] if gl else None, gsv=r3(gsv, 3), backup=backup)
    if not detail: return out
    if gl:
        if backup: why.append(f"Opp goalie: {gwhy}")
        elif g_f > 1.05: why.append(f"Faces {gl['name']} ({gsv:.3f} SV%, below league {LSV[SEASON]:.3f})")
        elif g_f < 0.95: why.append(f"Tough goalie: {gl['name']} ({gsv:.3f} SV%)")
    if ga_f > 1.08: why.append(f"{opp} allows {ga_f*LGA:.2f} GA/gm (blended) vs league {LGA:.2f}")
    if ga_f < 0.92: why.append(f"{opp} is stingy: {ga_f*LGA:.2f} GA/gm blended")
    if sa_f > 1.06: why.append(f"{opp} allows a lot of shots ({sa_f*LSA:.1f}/gm)")
    if g[oside + "B2B"]: why.append(f"{opp} on 2nd night of a back-to-back")
    if g[side + "B2B"]: why.append(f"{p['team']} on 2nd night of a back-to-back (-6%)")
    if pk_f > 1.03: why.append(f"PP-heavy producer vs weak {opp} PK ({opk:.1%})")
    h = (H2H.get(pid) or {}).get(opp)
    if h and h.get("flags"):
        venue_ok = lambda f: f["kind"] != "venue" or (f["scope"] == "home") == home
        fl = [f for f in h["flags"] if venue_ok(f)]
        tag = {"legendary": "LEGENDARY H2H", "venue": "VENUE CRUSHER", "heating": "HEATING UP vs " + opp}
        if fl:
            out["legend"] = [f["label"] for f in fl if f["kind"] == "legendary"] or None
            out["h2hNotes"] = [dict(kind=f["kind"], text=f"{tag[f['kind']]}: {f['label']} · {rarity(f['pv'])}") for f in fl]
            why.append(out["h2hNotes"][0]["text"])
    fo = rates.get("form")
    if fo and detail:
        mp = fo["mult"]["p"]
        if mp >= 1.04: why.append("Hot form boost" + (("; " + "; ".join(fo["notes"])) if fo.get("notes") else ""))
        elif mp <= 0.96: why.append("Cold form")
        elif fo["notes"]: why.append("Opportunity: " + "; ".join(fo["notes"]))
        out["form"] = fo["mult"]["p"]
    out["why"] = why; out["m"] = r3(m)
    return out

# ================= recent form + opportunity (shrunk) =================
# Last-10 per-game rates blended with the season/career baseline using phantom games (FORM_K), so 5 hot early-season games
# move the projection only modestly. Opportunity = last-5 TOI vs baseline TOI, PP TOI up vs last season, and a promotion to
# top-6 F / PP1 in the previous build's derived lines (NHL shift charts). Form part capped 0.88-1.15; total multiplier capped 0.85-1.20.
FORM_K = {"p": 20, "g": 25, "s": 12}
_prev_lines = json.load(open(os.path.join(DATA, "lines.json"))) if os.path.exists(os.path.join(DATA, "lines.json")) else {}
def _promoted(pid, ab):
    b = (_prev_lines.get(ab) or {}).get("cur") or {}
    top6 = [u for u in sorted(b.get("F", []), key=lambda u: -u.get("sec", 0))[:2]]
    pp1 = sorted(b.get("PP", []), key=lambda u: -u.get("sec", 0))[:1]
    out = []
    for u in top6:
        if pid in u.get("p", []) and pid in u.get("new", []): out.append("promoted to top-6 line")
    for u in pp1:
        if pid in u.get("p", []) and pid in u.get("new", []): out.append("new on PP1")
    return out
def form_of(pid, p, rates):
    cache = details.get(pid, (None, {}))[1] or {}
    cur = sorted(cache.get(str(SEASON), []), key=lambda r: r[1]); prev = sorted(cache.get(str(PREV), []), key=lambda r: r[1])
    log = (prev + cur)[-10:]
    if len(log) < 3: return None
    n = len(log); obs = dict(p=sum(r[5] + r[6] for r in log) / n, g=sum(r[5] for r in log) / n, s=sum(r[7] for r in log) / n)
    sh = {k: (n * obs[k] + FORM_K[k] * rates[k]) / (n + FORM_K[k]) for k in obs}
    fm = {k: max(0.88, min(1.15, sh[k] / rates[k])) if rates[k] > 0 else 1.0 for k in obs}
    l5 = log[-5:]; toi5 = sum(r[9] for r in l5) / len(l5) / 60
    base_toi = (sum(r[9] for r in prev) / len(prev) / 60) if prev else (rates.get("toi") or 0) / 60 or None
    c, pv = SK[SEASON].get(pid, {}), SK[PREV].get(pid, {})
    pp, ppp = (c.get("ppTimeOnIcePerGame") or 0) / 60, (pv.get("ppTimeOnIcePerGame") or 0) / 60
    opp, notes = 1.0, []
    if base_toi:
        r = toi5 / base_toi; opp *= max(0.92, min(1.10, 1 + 0.5 * (r - 1) * len(l5) / (len(l5) + 5)))
        if r >= 1.12: notes.append(f"TOI up: {toi5:.1f} min last {len(l5)} vs {base_toi:.1f} baseline")
    if c.get("gamesPlayed", 0) >= 3 and pp - ppp >= 1.0: opp *= 1.04; notes.append(f"PP time up: {pp:.1f} vs {ppp:.1f} min/gm last season")
    pr = _promoted(pid, p["team"])
    if pr: opp *= 1.03; notes += pr
    mult = {k: max(0.85, min(1.2, fm[k] * opp)) for k in fm}
    return dict(n=n, obs={k: r3(v, 2) for k, v in obs.items()}, shr={k: r3(v, 3) for k, v in sh.items()}, mult={k: r3(v, 3) for k, v in mult.items()},
                opp=r3(opp, 3), toi5=r3(toi5, 1), baseToi=r3(base_toi, 1), pp=r3(pp, 1), ppPrev=r3(ppp, 1), notes=notes)
FORM = {}

proj_by_player = {}; slate = []
season_proj = {}
for pid, p in PL.items():
    if p["pos"] == "G": continue
    rates = skater_rates(pid, p["pos"])
    if rates["gp"] == 0: continue
    fo = form_of(pid, p, rates)
    if fo:
        FORM[pid] = fo; rates = dict(rates, g=rates["g"] * fo["mult"]["g"], p=rates["p"] * fo["mult"]["p"], s=rates["s"] * fo["mult"]["s"])
        rates["form"] = fo
    if p["inj"] and p["inj"]["status"] in ("Out", "Injured Reserve", "Long Term Injured Reserve"):
        out_flag = True
    else: out_flag = False
    tg = [g for g in upcoming if p["team"] in (g["home"], g["away"])]
    xs = [project(pid, p, g, rates, detail=(i < 10)) for i, g in enumerate(tg)]
    c = SK[SEASON].get(pid, {})
    season_proj[pid] = dict(G=round(c.get("goals", 0) + sum(x["xg"] for x in xs), 1), P=round(c.get("points", 0) + sum(x["xp"] for x in xs), 1),
                            S=round(c.get("shots", 0) + sum(x["xs"] for x in xs)), rem=len(xs),
                            rG=r3(rates["g"]), rP=r3(rates["p"]), rS=r3(rates["s"], 2), note="assumes full health; injured players shown but not discounted" if out_flag else None)
    proj_by_player[pid] = xs[:10]
    for x in xs:
        if x["date"] in slate_days[:2] and not out_flag and rates["toi"] > 600:
            slate.append(dict(pid=pid, name=p["name"], team=p["team"], pos=p["pos"], **{k: x[k] for k in ("gid", "date", "opp", "home", "pG", "pP", "xs", "p3S", "goalie", "backup", "why")}, legend=x.get("legend"), h2hNotes=x.get("h2hNotes")))
slate.sort(key=lambda r: -r["pG"])

# ---------------- write per-player files + index ----------------
def season_row(s): return dict(season=s["season"], gp=s.get("gamesPlayed"), g=s.get("goals"), a=s.get("assists"), p=s.get("points"),
    pm=s.get("plusMinus"), s=s.get("shots"), ppg=s.get("powerPlayGoals"), ppp=s.get("powerPlayPoints"), toi=s.get("avgToi"),
    team=(s.get("teamName") or {}).get("default"), w=s.get("wins"), gaa=r3(s.get("goalsAgainstAvg"), 2), sv=r3(s.get("savePctg"), 3),
    so=s.get("shutouts"), gs=s.get("gamesStarted"))
index = []
for pid, p in PL.items():
    land, cache = details.get(pid, (None, {}))
    c, pv = SK[SEASON].get(pid) or GO[SEASON].get(pid) or {}, SK[PREV].get(pid) or GO[PREV].get(pid) or {}
    def pack(r, isg):
        if not r: return None
        if isg: return dict(gp=r["gamesPlayed"], gs=r.get("gamesStarted"), w=r["wins"], l=r["losses"], otl=r.get("otLosses"), gaa=r3(r["goalsAgainstAverage"], 2),
                             sv=r3(r["savePct"], 3), sa=r["shotsAgainst"], ga=r["goalsAgainst"], so=r["shutouts"])
        return dict(gp=r["gamesPlayed"], g=r["goals"], a=r["assists"], p=r["points"], pm=r["plusMinus"], s=r["shots"], ppg=r["ppGoals"], ppp=r["ppPoints"],
                    toi=r3((r.get("timeOnIcePerGame") or 0) / 60, 1), pptoi=r3((r.get("ppTimeOnIcePerGame") or 0) / 60, 1),
                    cf=r3(r.get("satPercentage")), ff=r3(r.get("usatPercentage")), cfrel=r3(r.get("satRelative")), hits=r.get("hits"), blk=r.get("blockedShots"),
                    shp=r3(r.get("shootingPct")), fo=r3(r.get("faceoffWinPct")), shpts=r.get("shPoints"), pim=r.get("penaltyMinutes"))
    isg = p["pos"] == "G"
    row = dict(p, cur=pack(c, isg), prev=pack(pv, isg), war=WAR[SEASON].get(pid), warPrev=WAR[PREV].get(pid),
               proj=season_proj.get(pid), next=(proj_by_player.get(pid) or [None])[0])
    h = H2H.get(pid) or {}
    row["legend"] = sorted([f["label"] for o in h.values() for f in o.get("flags", []) if f["kind"] == "legendary"])[:6]
    if land:
        row["age"] = (TODAY - dt.date.fromisoformat(land["birthDate"])).days // 365 if land.get("birthDate") else None
        ct = (land.get("careerTotals") or {}).get("regularSeason") or {}
        row["career"] = dict(gp=ct.get("gamesPlayed"), g=ct.get("goals"), a=ct.get("assists"), p=ct.get("points"), w=ct.get("wins"), sv=r3(ct.get("savePctg"), 3), gaa=r3(ct.get("goalsAgainstAvg"), 2))
    index.append(row)
    full = dict(row, seasons=[season_row(s) for s in (land or {}).get("seasonTotals", []) if s.get("leagueAbbrev") == "NHL" and s.get("gameTypeId") == 2],
                log=(cache or {}).get(str(SEASON), []), logPrev=(cache or {}).get(str(PREV), []),
                h2h=h, base=BASE.get(pid), projGames=proj_by_player.get(pid, []),
                draft=(land or {}).get("draftDetails"), birth=(land or {}).get("birthCity", {}).get("default") if land else None)
    with open(os.path.join(DATA, "players", f"{pid}.json"), "w") as f: json.dump(full, f, separators=(",", ":"))

legends = []
for pid, h in H2H.items():
    for opp, o in h.items():
        for f in o.get("flags", []):
            nxt = next((g for g in upcoming if {g["home"], g["away"]} == {PL[pid]["team"], opp}), None)
            nh = nxt and ((nxt["home"] == PL[pid]["team"]) == (f["scope"] == "home")) if f["kind"] == "venue" else True
            legends.append(dict(pid=pid, name=PL[pid]["name"], team=PL[pid]["team"], opp=opp, **f, rare=rarity(f["pv"]), next=nxt["date"] if nxt else None, nextVenueMatch=bool(nh) if nxt else None))
legends.sort(key=lambda x: (x["next"] is None, x["next"] or "", x["pv"]))

goalies = {}
for ab in ABBRS:
    order = team_starter_order(ab)
    if len(order) >= 2: gap = r3(order[0]["sv"] - order[1]["sv"], 3)
    else: gap = None
    goalies[ab] = dict(order=order, gap=gap)
gproj = [dict(gid=gid, team=ab, goalie=st["name"] if st else None, gid_=st["id"] if st else None, sv=st["sv"] if st else None, why=why, backup=backup,
              status="Projected", source="Sports Labs model (starts, back-to-backs, ESPN injuries)", asOf=NOW.isoformat(timespec="minutes"),
              date=next(g["date"] for g in upcoming if g["id"] == gid)) for (gid, ab), (st, why, backup) in goalie_proj.items()]


# ================= v2: hot list, matchup grades, SOS, team sims, usage =================
import random
hot = []
for pid, p in PL.items():
    if p["pos"] == "G": continue
    cache = details.get(pid, (None, {}))[1] or {}
    cur = sorted(cache.get(str(SEASON), []), key=lambda r: r[1]); prev = sorted(cache.get(str(PREV), []), key=lambda r: r[1])
    log = prev + cur
    if len(log) < 5: continue
    rates = skater_rates(pid, p["pos"])
    def win(n):
        w = log[-n:]; k = len(w)
        return dict(n=k, g=sum(r[5] for r in w), p=sum(r[5] + r[6] for r in w), s=sum(r[7] for r in w), ppp=sum(r[8] for r in w),
                    toi=r3(sum(r[9] for r in w) / k / 60, 1), crossSeason=any(r in prev for r in w))
    l5, l10 = win(5), win(10)
    ps = 0
    for r in reversed(log):
        if r[5] + r[6] > 0: ps += 1
        else: break
    gs = 0
    for r in reversed(log):
        if r[5] > 0: gs += 1
        else: break
    base_toi = (sum(r[9] for r in prev) / len(prev) / 60) if prev else None
    hp = l10["p"] / l10["n"] - rates["p"]; hg = l10["g"] / l10["n"] - rates["g"]; hs = l10["s"] / l10["n"] - rates["s"]
    score = hp * 1.0 + hg * 1.5 + hs * 0.15 + 0.05 * ps
    fo = FORM.get(pid)
    # hot score: shrunk per-game lift over baseline (points, goals, shots) + opportunity; needs 2+ games this season
    hotScore = r3(100 * (fo["shr"]["p"] - rates["p"]) + 50 * (fo["shr"]["g"] - rates["g"]) + 3 * (fo["shr"]["s"] - rates["s"]) + 30 * (fo["opp"] - 1), 1) if fo and len(cur) >= 2 else None
    hot.append(dict(pid=pid, name=p["name"], team=p["team"], pos=p["pos"], l5=l5, l10=l10, ptStreak=ps, gStreak=gs,
                    base=dict(p=r3(rates["p"]), g=r3(rates["g"]), s=r3(rates["s"], 2)), baseToi=r3(base_toi, 1),
                    toiDelta=r3(l5["toi"] - base_toi, 1) if base_toi else None, curGp=len(cur), score=r3(score), hotScore=hotScore, formMult=fo["mult"] if fo else None, opp=fo["opp"] if fo else None, oppNotes=fo["notes"] if fo else [], inj=p["inj"]["status"] if p["inj"] else None))
hot.sort(key=lambda x: -(x["hotScore"] if x["hotScore"] is not None else -99))

# matchup grades per game per team (offense env vs opponent; defensive env = opponent offense)
LGF = LGA
def off_env(team, opp, gid, opp_b2b, own_b2b):
    gl, gwhy, backup = goalie_for(gid, opp, opp_b2b)
    gsv = gl["sv"] if gl else LSV[SEASON]
    g_f = max(0.75, min(1.3, (1 - gsv) / (1 - LSV[SEASON])))
    opk = (TEAMS[opp].get("cur") or TEAMS[opp].get("prev") or {}).get("pk") or LPK
    pk_f = 1 + 0.2 * (((1 - opk) / (1 - LPK)) - 1)
    v = (0.45 * g_f + 0.35 * team_factor(opp, "gapg", LGA) + 0.2 * team_factor(opp, "sapg", LSA)) * pk_f * (1.04 if opp_b2b else 1) * (0.96 if own_b2b else 1)
    return v, gl, backup
def def_env(team, opp, opp_b2b):
    opp_pp = (TEAMS[opp].get("cur") or TEAMS[opp].get("prev") or {}).get("pp") or 0.2
    v = (0.6 * team_factor(opp, "gfpg", LGF) + 0.4 * team_factor(opp, "sfpg", LSA)) * (1 + 0.2 * (opp_pp / 0.2 - 1)) * (0.96 if opp_b2b else 1)
    return v
def grade(v, inv=False):
    # offense: higher env = easier. defense: higher opp offense = harder.
    if not inv: return "Strong" if v >= 1.06 else "Weak" if v <= 0.94 else "Neutral"
    return "Easy" if v <= 0.94 else "Tough" if v >= 1.06 else "Neutral"
grades = {}
for g in upcoming:
    for side, oside in (("home", "away"), ("away", "home")):
        t, o = g[side], g[oside]
        ov, gl, backup = off_env(t, o, g["id"], g[oside[0] + "B2B"], g[side[0] + "B2B"])
        dv = def_env(t, o, g[oside[0] + "B2B"])
        grades[f'{g["id"]}-{t}'] = dict(o=r3(ov), og=grade(ov), d=r3(dv), dg=grade(dv, True), goalie=gl["name"] if gl else None, backup=backup)
sos = {}
for ab in ABBRS:
    tg = [g for g in upcoming if ab in (g["home"], g["away"])]
    def agg(n):
        x = [grades[f'{g["id"]}-{ab}'] for g in tg[:n]]
        if not x: return None
        return dict(n=len(x), off=r3(sum(y["o"] for y in x) / len(x)), dfn=r3(sum(y["d"] for y in x) / len(x)),
                    b2b=sum(1 for g in tg[:n] if (g["home"] == ab and g["hB2B"]) or (g["away"] == ab and g["aB2B"])),
                    home=sum(1 for g in tg[:n] if g["home"] == ab))
    sos[ab] = {"5": agg(5), "10": agg(10)}

# team season simulation (estimate)
def tstr(ab):
    gf = team_factor(ab, "gfpg", LGF, 15) * LGF; ga = team_factor(ab, "gapg", LGA, 15) * LGA
    return gf, ga
STR = {ab: tstr(ab) for ab in ABBRS}
def p_home_win(h, a):
    lh = (STR[h][0] * STR[a][1] / LGA) * 1.03; la = (STR[a][0] * STR[h][1] / LGA) * 0.97
    ph = sum(math.exp(-lh) * lh**i / math.factorial(i) * sum(math.exp(-la) * la**j / math.factorial(j) for j in range(i)) for i in range(1, 12))
    pt = sum(math.exp(-lh) * lh**i / math.factorial(i) * math.exp(-la) * la**i / math.factorial(i) for i in range(12))
    return ph, pt
rem = [g for g in games if g["state"] not in ("OFF", "FINAL")]
probs = [(g["home"], g["away"]) + p_home_win(g["home"], g["away"]) for g in rem]
N = 2000; rng = random.Random(42)
agg_pts = {ab: [] for ab in ABBRS}; po = {ab: 0 for ab in ABBRS}
DIV = {ab: TEAMS[ab]["div"] for ab in ABBRS}; CONF = {ab: TEAMS[ab]["conf"] for ab in ABBRS}
for _ in range(N):
    pts = {ab: TEAMS[ab]["pts"] for ab in ABBRS}
    for h, a, ph, pt in probs:
        u = rng.random()
        if u < ph: pts[h] += 2
        elif u < ph + pt:
            if rng.random() < 0.5: pts[h] += 2; pts[a] += 1
            else: pts[a] += 2; pts[h] += 1
        else: pts[a] += 2
    for ab in ABBRS: agg_pts[ab].append(pts[ab])
    for conf in set(CONF.values()):
        cteams = [ab for ab in ABBRS if CONF[ab] == conf]; inn = set()
        for dv in set(DIV[ab] for ab in cteams):
            inn |= set(sorted([ab for ab in cteams if DIV[ab] == dv], key=lambda x: -pts[x] - rng.random() * 0.1)[:3])
        inn |= set(sorted([ab for ab in cteams if ab not in inn], key=lambda x: -pts[x] - rng.random() * 0.1)[:2])
        for ab in inn: po[ab] += 1
sim = {}
for ab in ABBRS:
    v = sorted(agg_pts[ab])
    sim[ab] = dict(mean=round(sum(v) / N, 1), p10=v[N // 10], p90=v[9 * N // 10], playoff=r3(po[ab] / N), gf=r3(STR[ab][0], 2), ga=r3(STR[ab][1], 2),
                   pace=round(TEAMS[ab]["pts"] / TEAMS[ab]["gp"] * 82, 1) if TEAMS[ab]["gp"] else None)

# usage / estimated PP units
usage = {}
for ab in ABBRS:
    sk = [(pid, SK[SEASON].get(pid) or {}) for pid, p in PL.items() if p["team"] == ab and p["pos"] != "G"]
    sk = [(pid, r) for pid, r in sk if r.get("gamesPlayed")]
    rows = [dict(pid=pid, name=PL[pid]["name"], pos=PL[pid]["pos"], gp=r["gamesPlayed"], toi=r3((r.get("timeOnIcePerGame") or 0) / 60, 1),
                 ev=r3((r.get("evTimeOnIcePerGame") or 0) / 60, 1), pp=r3((r.get("ppTimeOnIcePerGame") or 0) / 60, 1),
                 sh=r3((r.get("shTimeOnIcePerGame") or 0) / 60, 1), shifts=r3(r.get("shiftsPerGame"), 1)) for pid, r in sk]
    rows.sort(key=lambda x: -(x["pp"] or 0))
    for i, x in enumerate(rows): x["ppUnit"] = "PP1" if i < 5 and x["pp"] and x["pp"] > 1 else "PP2" if i < 10 and x["pp"] and x["pp"] > 0.5 else None
    rows.sort(key=lambda x: -(x["toi"] or 0))
    usage[ab] = rows
team_inj = {ab: [] for ab in ABBRS}
for (ab, nm), v in inj.items():
    if ab in team_inj:
        pid = next((pid for pid, p in PL.items() if p["team"] == ab and norm(p["name"]) == nm), None)
        team_inj[ab].append(dict(v, name=next((p["name"] for p in PL.values() if p["team"] == ab and norm(p["name"]) == nm), nm.title()), pid=pid))

# ================= v3: derived lines, news, role trends =================
import lines as LN
SHC = os.path.join(DATA, "cache", "shifts"); os.makedirs(SHC, exist_ok=True)
finals = [g for g in games if g["state"] in ("OFF", "FINAL")]
need = {}
for ab in ABBRS:
    if TARGET and ab not in TARGET and os.path.exists(os.path.join(DATA, "lines.json")): continue
    tg = [g for g in finals if ab in (g["home"], g["away"])][-4:]
    for g in tg: need.setdefault(g["id"], []).append(ab)
gl_res = dict(zip(need, pmap(lambda gid: LN.game_lines(gid, get, SHC), list(need), 6)))
posmap = {pid: p["pos"] for pid, p in PL.items()}
prev_lines = json.load(open(os.path.join(DATA, "lines.json"))) if os.path.exists(os.path.join(DATA, "lines.json")) else {}
LINES = {}
for ab in ABBRS:
    tg = [g for g in finals if ab in (g["home"], g["away"])][-4:]
    if not any(g["id"] in gl_res for g in tg):
        if ab in prev_lines: LINES[ab] = prev_lines[ab]
        continue
    res = []
    for g in tg:
        r = gl_res.get(g["id"]) or (LN.game_lines(g["id"], get, SHC) if g["id"] not in gl_res else None)
        if r:
            for k, v in r["names"].items(): posmap.setdefault(int(k), "F")
            res.append(r)
    # unavailable: ESPN injury status Out/IR, or no longer on this team's current roster
    gone = {pid for pid, p in PL.items() if p["team"] == ab and p.get("inj") and str(p["inj"].get("status", "")).lower().startswith(("out", "injured", "ir"))}
    gone |= {int(k) for r in res for k in r["teams"].get(ab, {}).get("toi", {}) if int(k) not in PL or PL[int(k)]["team"] != ab}
    built = []
    for i in range(len(res)):   # blended view as of each game: that game + up to 2 earlier (weights 1, .5, .25)
        m = LN.merge_games(ab, list(reversed(res[max(0, i - 2):i + 1])), exclude=gone if i == len(res) - 1 else ())
        b = LN.build_lines(ab, m, posmap) if m else None
        if b: b["names"] = {str(p): (PL[p]["name"] if p in PL else m["names"].get(str(p), str(p))) for grp in ("F", "D", "PP") for u in b[grp] for p in u["p"]}; built.append(b)
    if not built: continue
    cur = built[-1]; prv = built[-2] if len(built) > 1 else None
    cur["method"] = f"Shift charts, last {min(3, len(res))} games weighted 1/0.5/0.25; excludes {len(gone)} unavailable (injured or off roster)"
    cur["builtAt"] = NOW.isoformat(timespec="minutes"); cur["excluded"] = sorted(gone)
    if prv:
        for grp in ("F", "D", "PP"):
            for i, u in enumerate(cur[grp]):
                old = max((set(x["p"]) for x in prv[grp]), key=lambda st: len(st & set(u["p"])), default=set())
                u["new"] = [p for p in u["p"] if p not in old]
                u["same"] = not u["new"]
    LINES[ab] = dict(cur=cur, prev=dict(gid=prv["gid"], date=prv["date"], opp=prv["opp"]) if prv else None)
wj("lines.json", LINES)

# news (ESPN)
ESPN_AB = {"LA": "LAK", "NJ": "NJD", "SJ": "SJS", "TB": "TBL", "UTAH": "UTA"}
et = get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams") or {}
eids = {ESPN_AB.get(x["team"]["abbreviation"], x["team"]["abbreviation"]): x["team"]["id"] for x in et.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])}
def art(a):
    teams = [c.get("description") for c in a.get("categories", []) if c.get("type") == "team"]
    return dict(h=a.get("headline"), d=a.get("description"), t=a.get("published"), u=((a.get("links") or {}).get("web") or {}).get("href"),
                img=((a.get("images") or [{}])[0]).get("url"), type=a.get("type"), nteams=len(teams), teams=teams[:4])
def team_news(ab):
    if ab not in eids: return ab, []
    d = get(f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/news?team={eids[ab]}&limit=15") or {}
    return ab, [art(a) for a in d.get("articles", [])]
NEWS = dict(pmap(team_news, ABBRS, 8))
lg = get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/news?limit=30") or {}
wj("news.json", dict(league=[art(a) for a in lg.get("articles", [])], teams=NEWS))

# role trends (forwards vs defense): last-5 TOI & shots vs last season; PP TOI this season vs last
for h in hot:
    c, p = SK[SEASON].get(h["pid"], {}), SK[PREV].get(h["pid"], {})
    h["ppToi"] = r3((c.get("ppTimeOnIcePerGame") or 0) / 60, 1) if c else None
    h["ppToiPrev"] = r3((p.get("ppTimeOnIcePerGame") or 0) / 60, 1) if p else None
    h["shotsPrev"] = r3(p["shots"] / p["gamesPlayed"], 2) if p.get("gamesPlayed") else None

wj("hot.json", hot[:600]);
# ================= v4: fantasy =================
def fz(): return [0.0] * 9   # G A PPP SHP SOG HIT BLK PIM PM
def comp_rates(pid, pos):
    c, p = SK[SEASON].get(pid, {}), SK[PREV].get(pid, {})
    gpc, gpp = c.get("gamesPlayed", 0), p.get("gamesPlayed", 0)
    den = gpc + W_PREV * gpp + K_SHRINK
    pm = FPOS["D" if pos == "D" else "F"]
    f = lambda k: (c.get(k, 0) + W_PREV * p.get(k, 0) + K_SHRINK * pm[k] * 0.6) / den
    return dict(ppp=f("ppPoints"), shp=f("shPoints"), hits=f("hits"), blk=f("blockedShots"), pim=f("penaltyMinutes"), pm=f("plusMinus"))
FPOS = {}
for grp in ("F", "D"):
    rows = [r for r in SK[PREV].values() if r.get("gamesPlayed", 0) >= 20 and (r.get("positionCode") == "D") == (grp == "D")]
    gp = sum(r["gamesPlayed"] for r in rows) or 1
    FPOS[grp] = {k: sum(r.get(k, 0) or 0 for r in rows) / gp for k in ("ppPoints", "shPoints", "hits", "blockedShots", "penaltyMinutes", "plusMinus")}
wk0 = TODAY - dt.timedelta(days=TODAY.weekday())   # fantasy weeks Mon-Sun (ESPN default matchup period)
WEEKS = [dict(key=f"w{i}", start=(wk0 + dt.timedelta(days=7 * i)).isoformat(), end=(wk0 + dt.timedelta(days=7 * i + 6)).isoformat()) for i in range(4)]
def wkey(d):
    for w in WEEKS:
        if w["start"] <= d <= w["end"]: return w["key"]
up4 = [g for g in upcoming if g["date"] <= WEEKS[-1]["end"]]
FSK = {}
for pid, p in PL.items():
    if p["pos"] == "G": continue
    rates = skater_rates(pid, p["pos"])
    if rates["gp"] == 0: continue
    cr = comp_rates(pid, p["pos"])
    wk = {}
    for g in [g for g in up4 if p["team"] in (g["home"], g["away"])]:
        x = project(pid, p, g, rates, detail=False)
        k = wkey(g["date"])
        v = wk.setdefault(k, dict(n=0, c=fz(), opp=[]))
        ratio = x["xp"] / rates["p"] if rates["p"] else 1
        add_ = [x["xg"], max(0, x["xp"] - x["xg"]), cr["ppp"] * ratio, cr["shp"], x["xs"], cr["hits"], cr["blk"], cr["pim"], cr["pm"]]
        v["n"] += 1; v["c"] = [a + b for a, b in zip(v["c"], add_)]
        v["opp"].append(("" if x["home"] else "@") + x["opp"])
    for v in wk.values(): v["c"] = [round(a, 3) for a in v["c"]]
    FSK[pid] = dict(w=wk, r=[r3(rates["g"]), r3(rates["a"]), r3(cr["ppp"]), r3(cr["shp"]), r3(rates["s"]), r3(cr["hits"]), r3(cr["blk"]), r3(cr["pim"]), r3(cr["pm"])])
FG = {}
for g in up4:
    for side, oside in (("home", "away"), ("away", "home")):
        t, o = g[side], g[oside]
        st, why, backup = project_goalie(t, g[side[0] + "B2B"])
        if not st: continue
        ph, pt = p_home_win(g["home"], g["away"])
        pw = (ph if side == "home" else 1 - ph - pt) + pt * 0.5
        lam = STR[o][0] * STR[t][1] / LGA * (0.97 if side == "home" else 1.03)
        gfac = 0.5 + 0.5 * max(0.75, min(1.3, (1 - st["sv"]) / (1 - LSV[SEASON])))
        lam *= gfac
        sa = 0.5 * team_factor(t, "sapg", LSA) * LSA + 0.5 * team_factor(o, "sfpg", LSA) * LSA
        k = wkey(g["date"])
        v = FG.setdefault(st["id"], {}).setdefault(k, dict(n=0, c=[0.0] * 5, opp=[], alt=0))
        v["n"] += 1; v["alt"] += 1 if backup else 0
        v["c"] = [a + b for a, b in zip(v["c"], [pw, pt * 0.5, lam, max(0, sa - lam), math.exp(-lam)])]
        v["opp"].append(("" if side == "home" else "@") + o + ("*" if backup else ""))
for d in FG.values():
    for v in d.values(): v["c"] = [round(a, 3) for a in v["c"]]
grid = {}
for ab in ABBRS:
    for w in WEEKS:
        tg = [g for g in up4 if ab in (g["home"], g["away"]) and w["start"] <= g["date"] <= w["end"]]
        gr = [grades.get(f'{g["id"]}-{ab}') for g in tg]
        grid.setdefault(ab, {})[w["key"]] = dict(n=len(tg), off=r3(sum(x["o"] for x in gr if x) / len(tg)) if tg else None,
            dfn=r3(sum(x["d"] for x in gr if x) / len(tg)) if tg else None, b2b=sum(1 for g in tg if (g["home"] == ab and g["hB2B"]) or (g["away"] == ab and g["aB2B"])),
            opp=[("" if g["home"] == ab else "@") + (g["away"] if g["home"] == ab else g["home"]) for g in tg])
# ESPN fantasy rostership (public read API)
OWN = {}
try:
    req = urllib.request.Request(f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/{SEASON % 10000}/players?view=players_wl",
                                 headers={"User-Agent": "nhl-lab/1.0", "X-Fantasy-Filter": json.dumps({"filterActive": {"value": True}})})
    with urllib.request.urlopen(req, timeout=40) as r: ew = json.loads(r.read())
    tid2ab = {v: k for k, v in eids.items()}
    byname = {}
    for x in ew:
        byname.setdefault(norm(x.get("fullName", "")), []).append((tid2ab.get(str(x.get("proTeamId"))), (x.get("ownership") or {}).get("percentOwned")))
    for pid, p in PL.items():
        c = byname.get(norm(p["name"]), [])
        m = [o for t, o in c if t == p["team"]] or ([c[0][1]] if len(c) == 1 else [])
        if m and m[0] is not None: OWN[pid] = round(m[0], 1)
except Exception as e:
    print("ownership fetch failed", e)
wj("fantasy.json", dict(weeks=WEEKS, sk=FSK, g=FG, grid=grid, own=OWN, ownSource="ESPN fantasy public player list (percentOwned)" if OWN else None))
print("fantasy", len(FSK), "skaters", len(FG), "goalies", len(OWN), "ownership matches")
wj("grades.json", dict(grades=grades, sos=sos)); wj("teamx.json", dict(sim=sim, usage=usage, inj=team_inj, sims=N))

wj("schedule.json", [dict(id=g["id"], start=GAMES[g["id"]]["startTimeUTC"], away=g["away"], home=g["home"]) for g in games
    if g["state"] in ("FUT", "PRE") and g["date"] <= (TODAY + dt.timedelta(days=3)).isoformat()])
wj("teams.json", TEAMS); wj("games.json", games); wj("players.json", index)
wj("slate.json", dict(days=slate_days[:2], rows=slate[:300], goalies=gproj))
wj("h2h_flags.json", legends); wj("goalies.json", goalies)
wj("model.json", dict(season=SEASON, prev=PREV, leagueSV=r3(LSV[SEASON], 4), leagueSVprev=r3(LSV[PREV], 4), lgGA=r3(LGA, 3), lgSA=r3(LSA, 2), lgPK=r3(LPK, 3),
    repl={str(k): v for k, v in REPL.items()}, posmean=POSMEAN, goalsPerWin=GOALS_PER_WIN, kShrink=K_SHRINK, wPrev=W_PREV))
wj("meta.json", dict(mode=("pregame:" + ",".join(sorted(TARGET))) if TARGET else "full", updated=NOW.isoformat(timespec="minutes"), updatedET=NOW.strftime("%b %-d, %-I:%M %p ET"), season=SEASON,
    counts=dict(players=len(index), games=len(games), played=sum(1 for g in games if g["state"] in ("OFF", "FINAL")), slate=len(slate), legends=len(legends), injuries=len(inj))))
print("done", len(index), "players", len(games), "games", len(legends), "legend flags", len(slate), "slate rows")
