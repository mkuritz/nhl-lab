#!/usr/bin/env python3
"""Matchup Analyzer data for NHL Lab player profiles -> data/matchup_an.json.
Built only from files NHL Lab already publishes (data/players/*.json game logs, teams.json,
goalies.json, goalie_starters.json, team_model.json, teamx.json, games.json). No estimates:
anything without logged games is left out."""
import json, glob, os, statistics as st
from collections import defaultdict
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
L = lambda f: json.load(open(os.path.join(R, f)))
TEAMS, GOAL, P = L("teams.json"), L("goalies.json"), L("players.json")
STARTERS = L("goalie_starters.json") if os.path.exists(os.path.join(R, "goalie_starters.json")) else {}
TM = L("team_model.json"); TX = L("teamx.json")
SEASON = str(L("meta.json")["season"])[:4]
GRP = lambda pos: "C" if pos == "C" else "W" if pos in ("L", "R") else "D" if pos == "D" else None
KS = ["g", "a", "p", "s", "ppp", "toi"]  # per-game stats from the skater game log
DIV = {a: t.get("div") for a, t in TEAMS.items()}
TA = sorted(TEAMS)

def rows_of(log):  # skater log row -> dict
    out = []
    for r in log or []:
        if len(r) < 11: continue
        out.append(dict(gid=r[0], date=r[1], team=r[2], opp=r[3], home=r[4] == "H", g=r[5], a=r[6], p=r[5] + r[6], s=r[7], ppp=r[8], toi=round(r[9] / 60, 1), pm=r[10]))
    return out

def avg(rs, k):
    return round(sum(x[k] for x in rs) / len(rs), 3) if rs else None

def pctile(v, pop, inv=False):
    if v is None or not pop: return None
    lo = sum(1 for x in pop if x < v); eq = sum(1 for x in pop if x == v)
    p = round((lo + eq / 2) / len(pop) * 100)
    return 100 - p if inv else p

# ---- load every skater log once
PL, LOG, LOGP, NXT, GLOG = {}, {}, {}, {}, {}
for f in glob.glob(os.path.join(R, "players", "*.json")):
    d = json.load(open(f)); pid = str(d["id"])
    if d.get("pos") == "G":
        GLOG[pid] = d; continue
    if not GRP(d.get("pos")): continue
    PL[pid] = d; LOG[pid] = rows_of(d.get("log")); LOGP[pid] = rows_of(d.get("logPrev"))

# ---- what each team allowed to each position group, per game (this season)
allow = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))  # team -> grp -> gid -> stat
gdate = {}
for pid, rs in LOG.items():
    g = GRP(PL[pid]["pos"])
    for r in rs:
        a = allow[r["opp"]][g][r["gid"]]; gdate[r["gid"]] = r["date"]
        for k in ("g", "a", "p", "s", "ppp"): a[k] += r[k]
def team_games(t):  # completed games this season, newest first
    gs = set()
    for g in allow[t].values(): gs |= set(g)
    return sorted(gs, key=lambda x: gdate[x], reverse=True)
TG = {t: team_games(t) for t in TA}
def owin(t, grp, n=None):
    gids = TG[t][:n] if n else TG[t]
    if not gids: return None
    return {k: round(sum(allow[t][grp].get(gid, {}).get(k, 0) for gid in gids) / len(gids), 2) for k in ("g", "a", "p", "s", "ppp")}, len(gids)
OWN = {"L5": 5, "L10": 10, "All": None}
OW = {w: {grp: {t: owin(t, grp, n) for t in TA} for grp in "CWD"} for w, n in OWN.items()}

# ---- player population per group (season per-game, 5+ GP) for percentiles
POP = defaultdict(lambda: defaultdict(list))
for pid, rs in LOG.items():
    if len(rs) >= 5:
        for k in KS: POP[GRP(PL[pid]["pos"])][k].append(avg(rs, k))

# team-level context
def tstat(t):
    c = TEAMS[t].get("cur", {}); gp = c.get("gp") or TEAMS[t].get("gp")
    pim = sum((x.get("cur") or {}).get("pim") or 0 for x in P if x["team"] == t)
    return dict(gapg=c.get("gapg"), sapg=c.get("sapg"), gfpg=c.get("gfpg"), sfpg=c.get("sfpg"), pk=c.get("pk"),
                pace=round(c["gfpg"] + c["gapg"], 2) if c.get("gfpg") is not None else None,
                space=round(c["sfpg"] + c["sapg"], 1) if c.get("sfpg") is not None else None,
                pim=round(pim / gp, 1) if gp else None)
TS = {t: tstat(t) for t in TA}
def trank(k, t, hi_first=False):
    vals = sorted([(TS[x][k], x) for x in TA if TS[x][k] is not None], reverse=hi_first)
    return next((i + 1 for i, (v, x) in enumerate(vals) if x == t), None)
# "similar" opponents: the 8 teams whose goals-against per game is closest to tonight's opponent
def similar_teams(opp):
    g = TS[opp]["gapg"]
    return [x for x in sorted((x for x in TA if x != opp and TS[x]["gapg"] is not None), key=lambda x: abs(TS[x]["gapg"] - g))[:8]]

# opposing goalie
def gl_rows(gid):
    d = GLOG.get(str(gid)); 
    if not d: return []
    return [dict(date=r[1], opp=r[3], gs=r[5], sa=r[6], ga=r[7]) for r in (d.get("log") or []) if len(r) >= 8 and r[5]]
def goalie_info(team, name, gid):
    o = next((x for x in GOAL.get(team, {}).get("order", []) if x["name"] == name), None)
    if not o: return None
    st_ = STARTERS.get(f"{gid}|{team}") or {}
    status = st_.get("status") if st_.get("name") == name else None
    if not status:
        for g in TM.get("games", []):
            if g["id"] == gid:
                side = "home" if g["home"] == team else "away"
                x = (g.get("goalies") or {}).get(side) or {}
                if x.get("name") == name: status = x.get("status")
    rs = gl_rows(o["id"]); sa = sum(r["sa"] for r in rs); ga = sum(r["ga"] for r in rs)
    last = [[r["date"][5:].replace("-", "/"), round(1 - r["ga"] / r["sa"], 3) if r["sa"] else None, r["ga"], r["sa"]] for r in rs[:5]][::-1]
    return dict(id=o["id"], name=name, status=status, starts=len(rs), sv=round(1 - ga / sa, 3) if sa else None,
                gaa=None, l10_sv=o.get("l10_sv"), l10_gsax=o.get("l10_gsax"), last=last)

def inj_list(t):
    return [dict(n=x["name"], st=x["status"], d=x.get("date")) for x in TX.get("inj", {}).get(t, [])]

OUT = {"season": SEASON, "stats": [["g", "Goals"], ["a", "Assists"], ["p", "Points"], ["s", "Shots on goal"], ["ppp", "PP points"], ["toi", "Ice time"]], "players": {}}
SIMK = "s"
for pid, d in PL.items():
    nx = d.get("next"); rs = LOG[pid]
    if not nx or not rs or nx.get("opp") not in TEAMS: continue
    grp, opp, team = GRP(d["pos"]), nx["opp"], d["team"]
    win = {}
    sims = set(similar_teams(opp))
    sel = {"L5": rs[:5], "L10": rs[:10], "Home": [r for r in rs if r["home"]], "Away": [r for r in rs if not r["home"]],
           "Div": [r for r in rs if DIV.get(r["opp"]) == DIV.get(opp)], "Similar": [r for r in rs if r["opp"] in sims], "All": rs}
    for w, xs in sel.items():
        v = {k: avg(xs, k) for k in KS}
        win[w] = {"n": len(xs), "v": v, "p": {k: pctile(v[k], POP[grp][k]) for k in KS}}
    ow = {}
    for w in OWN:
        cur = OW[w][grp][opp]
        if not cur: continue
        vals, n = cur
        pops = {k: [OW[w][grp][t][0][k] for t in TA if OW[w][grp][t]] for k in vals}
        ow[w] = {"n": n, "v": vals, "p": {k: pctile(vals[k], pops[k]) for k in vals},
                 "r": {k: 1 + sum(1 for x in pops[k] if x < vals[k]) for k in vals}, "of": len(pops["g"])}
    # similar players: same group, season shots/gm within 30%, their games vs opp (this + last season)
    me = avg(rs, SIMK); simrows = []
    if me:
        for q, qr in LOG.items():
            if q == pid or GRP(PL[q]["pos"]) != grp or len(qr) < 5: continue
            qa = avg(qr, SIMK)
            if not qa or abs(qa - me) / me > .3: continue
            for r in qr + LOGP[q]:
                if r["opp"] == opp:
                    base = qa if r in qr else avg(LOGP[q], SIMK)
                    simrows.append(dict(d=r["date"], t=r["team"], n=PL[q]["name"], avg=round(base, 2), res=r[SIMK]))
        simrows.sort(key=lambda x: x["d"], reverse=True)
    OUT["players"][pid] = dict(name=d["name"], team=team, pos=d["pos"], grp=grp, opp=opp, home=nx.get("home"), date=nx.get("date"),
        div=DIV.get(team), odiv=DIV.get(opp), simteams=sorted(sims), inj=d.get("inj"),
        win=win, owin=ow, goalie=goalie_info(opp, nx.get("goalie"), nx.get("gid")) if nx.get("goalie") else None,
        ctx={k: dict(v=TS[opp][k], r=trank(k, opp, k in ("pace", "space", "pim", "pk"))) for k in ("gapg", "sapg", "pace", "space", "pim", "pk")},
        oinj=inj_list(opp), tinj=inj_list(team), sim=dict(stat="Shots on goal", me=round(me, 2) if me else None, rows=simrows[:12]),
        oweek=[[gdate[g][5:].replace("-", "/"), int(allow[opp][grp][g].get("g", 0))] for g in TG[opp][:10]][::-1])
json.dump(OUT, open(os.path.join(R, "matchup_an.json"), "w"), separators=(",", ":"))
print("players", len(OUT["players"]))
