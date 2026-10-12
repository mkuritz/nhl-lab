"""NHL Lab cross-check: MoneyPuck xG/GSAx, Daily Faceoff starting goalies, NHL EDGE tracking vs our model."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from xlib import Src, fetch, js, rows, f, norm, verdict, write
D = os.path.join(os.path.dirname(__file__), "..", "data")
S = Src()
players = json.load(open(os.path.join(D, "players.json"))); slate = json.load(open(os.path.join(D, "slate.json")))
yr = int(time.strftime("%Y")) - (1 if int(time.strftime("%m")) < 9 else 0)
MP = "https://moneypuck.com/moneypuck/playerData/seasonSummary/%d/regular/" % yr
sk = S.get("MoneyPuck skaters (credit: MoneyPuck.com)", MP + "skaters.csv", "Expected goals (xG) per player and on-ice xG% vs actual goals/Corsi", lambda: {int(r["playerId"]): r for r in rows(MP + "skaters.csv") if r["situation"] == "all"}, link="https://moneypuck.com/data.htm") or {}
gl = S.get("MoneyPuck goalies (credit: MoneyPuck.com)", MP + "goalies.csv", "Goals saved above expected (GSAx) vs raw save %", lambda: {int(r["playerId"]): r for r in rows(MP + "goalies.csv") if r["situation"] == "all"}, link="https://moneypuck.com/data.htm") or {}
def dfo():
    s = fetch("https://www.dailyfaceoff.com/starting-goalies", hdr={"User-Agent": "Mozilla/5.0"}).decode()
    d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', s, re.S).group(1))
    out = {}
    for g in d["props"]["pageProps"]["data"]:
        for side in ("home", "away"):
            out[(g.get("date"), norm(g["%sTeamName" % side]))] = (g["%sGoalieName" % side], g.get("%sNewsStrengthName" % side) or "Unconfirmed")
    return out
df = S.get("Daily Faceoff starting goalies", "https://www.dailyfaceoff.com/starting-goalies", "Second opinion on tonight's starters (Confirmed / Likely / Unconfirmed)", dfo) or {}
S.list = [dict(name="Already used: NHL api-web + stats REST, ESPN news/injuries, ESPN fantasy", status="ok", what="Core model inputs (unchanged)", new=False)] + S.list
teams = json.load(open(os.path.join(D, "teams.json")))
tname = {a: norm(t["name"]) for a, t in teams.items()}
gt, nag, ncmp = [], 0, 0
for g in slate.get("goalies", []):
    o = df.get((g["date"], tname.get(g["team"], "")))
    if not o:
        gt.append([g["date"], g["team"], g["goalie"], "—", "—", "n/a"]); continue
    same = norm(o[0]) == norm(g["goalie"]); ncmp += 1; nag += same
    gt.append([g["date"], g["team"], g["goalie"], o[0], o[1], "agree" if same else ("disagree" if o[1].lower().startswith("confirm") else "watch")])
st = []
for p in players:
    r = sk.get(p["id"]); c = p.get("cur") or {}
    if not r or (c.get("gp") or 0) < 1: continue
    xg, g = f(r["I_F_xGoals"], 0), f(r["I_F_goals"], 0); gp = f(r["games_played"], 1)
    proj = (p.get("proj") or {}).get("rG")
    st.append([p["name"], p["team"], p["pos"], int(gp), int(g), round(xg, 2), round(g - xg, 2), round(xg / gp, 3), proj if proj is not None else "—",
               round(100 * f(r["onIce_xGoalsPercentage"], 0), 1), round(100 * (c.get("cf") or 0), 1),
               "running hot" if g - xg >= 2 else ("due" if xg - g >= 1.5 else "in line")])
st.sort(key=lambda r: -abs(r[6]))
gk = []
for a, t in json.load(open(os.path.join(D, "goalies.json"))).items():
    for x in t.get("order", []):
        r = gl.get(x["id"])
        if not r: continue
        xga, ga = f(r["xGoals"], 0), f(r["goals"], 0)
        gk.append([x["name"], a, int(f(r["games_played"], 0)), round(x.get("sv") or 0, 3), round(xga - ga, 2), round(xga, 1), int(ga), "above expected" if xga - ga > 1 else ("below expected" if ga - xga > 1 else "par")])
gk.sort(key=lambda r: -r[4])
def edge():
    out = []
    seen, top = set(), []
    for r in slate.get("rows", []):
        if r["pid"] not in seen: seen.add(r["pid"]); top.append((r["pid"], r["name"], r["team"]))
    top = top[:40]
    for pid, nm, tm in top:
        try: d = js("https://api-web.nhle.com/v1/edge/skater-detail/%d/%d%d/2" % (pid, yr, yr + 1))
        except Exception: continue
        sp = (d.get("skatingSpeed") or {}).get("speedMax") or {}; sh = d.get("topShotSpeed") or {}; oz = d.get("zoneTimeDetails") or {}
        hd = next((x for x in d.get("sogSummary", []) if x.get("locationCode") == "high"), {})
        out.append([nm, tm, round(sp.get("imperial") or 0, 1), round(100 * (sp.get("percentile") or 0)), round(sh.get("imperial") or 0, 1), round(100 * (oz.get("offensiveZonePctg") or 0), 1), round(100 * (oz.get("offensiveZonePercentile") or 0)), hd.get("shots", "—"), round(100 * (hd.get("shotsPercentile") or 0))])
        time.sleep(0.25)
    return out
ed = [] if os.environ.get("XMODE", "full") != "full" else S.get("NHL EDGE tracking (api-web.nhle.com)", "https://api-web.nhle.com/v1/edge/", "Skating speed, shot speed, offensive-zone time and high-danger shots for slate players", edge, link="https://edge.nhl.com/") or []
tables = [dict(title="Starting goalies: our projection vs Daily Faceoff", note="'disagree' = Daily Faceoff has a different goalie Confirmed: trust the confirmation and recheck props/slate.", cols=["Date", "Team", "Our projected starter", "Daily Faceoff", "DFO status", "Verdict"], rows=gt, flag=5),
          dict(title="Finishing luck: goals vs MoneyPuck expected goals", note="Goals minus xG this season. 'Running hot' players tend to cool off; 'due' players are generating chances without finishing. Our per-game goal rate (rG) shown for comparison. Data credit: MoneyPuck.com.", cols=["Player", "Team", "Pos", "GP", "Goals", "xG", "G − xG", "xG/GP", "Our rG", "On-ice xG%", "Corsi% (NHL)", "Read"], rows=st[:400]),
          dict(title="Goalies: save % vs MoneyPuck GSAx", note="Goals saved above expected adjusts for shot quality, so it's a better read on a goalie than raw save % this early. Data credit: MoneyPuck.com.", cols=["Goalie", "Team", "GP", "Our SV%", "GSAx", "xGA", "GA", "Read"], rows=gk),
          dict(title="NHL EDGE tracking: tonight's slate skaters", note="Percentiles are vs league this season.", cols=["Player", "Team", "Max speed (mph)", "Speed pctile", "Top shot (mph)", "OZ time %", "OZ pctile", "High-danger SOG", "HD SOG pctile"], rows=ed)]
summ = [["Goalie starters checked", ncmp, "vs Daily Faceoff"], ["Goalie agreement", "%d%%" % round(100 * nag / max(ncmp, 1)), ""], ["Skaters with xG", len(st), "MoneyPuck"], ["Sources OK", "%d/%d" % (sum(s["status"] == "ok" for s in S.list), len(S.list)), "this refresh"]]
write(os.path.join(D, "xcheck.json"), "NHL Lab · data sources & cross-check", S, tables, summ)
print([(s["name"][:28], s["status"], s.get("rows")) for s in S.list], summ)
