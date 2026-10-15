"""Derive current lines from NHL shift charts + play-by-play (free api.nhle.com / api-web.nhle.com).
Not official line combinations: linemates are inferred from shared ice time in the team's most recent games."""
import json, os
from itertools import combinations

def mmss(t):
    try: m, s = t.split(":"); return int(m) * 60 + int(s)
    except Exception: return None

def game_lines(gid, get, cache_dir):
    cf = os.path.join(cache_dir, f"{gid}.json")
    if os.path.exists(cf): return json.load(open(cf))
    sh = get(f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gid}")
    pbp = get(f"https://api-web.nhle.com/v1/gamecenter/{gid}/play-by-play")
    if not sh or not pbp or not sh.get("data"): return None
    home, away = pbp["homeTeam"]["abbrev"], pbp["awayTeam"]["abbrev"]
    # strength timeline from situationCode (awayG, awaySk, homeSk, homeG)
    ev = []
    for p in pbp.get("plays", []):
        sc = p.get("situationCode"); per = p.get("periodDescriptor", {}).get("number", 1)
        t = mmss(p.get("timeInPeriod", "")); 
        if sc and len(sc) == 4 and t is not None: ev.append(((per - 1) * 1200 + t, sc))
    ev.sort()
    def state_at(sec):
        lo, hi, s = 0, len(ev) - 1, "1551"
        while lo <= hi:
            mid = (lo + hi) // 2
            if ev[mid][0] <= sec: s = ev[mid][1]; lo = mid + 1
            else: hi = mid - 1
        return s
    shifts, names = {}, {}
    for r in sh["data"]:
        if r.get("typeCode") != 517: continue
        a, b = mmss(r.get("startTime") or ""), mmss(r.get("endTime") or "")
        if a is None or b is None or b <= a: continue
        off = (r["period"] - 1) * 1200
        shifts.setdefault((r["teamAbbrev"], r["playerId"]), []).append((off + a, off + b))
        names[r["playerId"]] = f'{r["firstName"]} {r["lastName"]}'
    end = max((b for v in shifts.values() for _, b in v), default=0)
    # per-second on-ice sets (games are ~3600-3900 s; cheap)
    out = {}
    for team, side in ((home, "h"), (away, "a")):
        on = [set() for _ in range(end + 1)]
        for (tm, pid), v in shifts.items():
            if tm != team: continue
            for a, b in v:
                for s in range(a, b): on[s].add(pid)
        ev_t, pp_t, toi = {}, {}, {}
        pair_ev, pair_pp = {}, {}
        for s in range(end):
            st = state_at(s)
            ask, hsk = int(st[1]), int(st[2])
            mine, theirs = (hsk, ask) if side == "h" else (ask, hsk)
            kind = "ev" if mine == theirs == 5 else "pp" if mine > theirs else None
            cur = on[s]
            for p in cur: toi[p] = toi.get(p, 0) + 1
            if not kind: continue
            d, pd = (ev_t, pair_ev) if kind == "ev" else (pp_t, pair_pp)
            for p in cur: d[p] = d.get(p, 0) + 1
            for x, y in combinations(sorted(cur), 2): pd[f"{x}-{y}"] = pd.get(f"{x}-{y}", 0) + 1
        out[team] = dict(ev=ev_t, pp=pp_t, toi=toi, pev=pair_ev, ppp=pair_pp)
    res = dict(gid=gid, date=pbp.get("gameDate"), home=home, away=away, names={str(k): v for k, v in names.items()}, teams=out)
    json.dump(res, open(cf, "w"), separators=(",", ":"))
    return res

def build_lines(team, g, posmap):
    t = g["teams"].get(team)
    if not t: return None
    ev = {int(k): v for k, v in t["ev"].items()}; pp = {int(k): v for k, v in t["pp"].items()}
    def ov(d, a, b): x, y = sorted((a, b)); return d.get(f"{x}-{y}", d.get(f"{str(x)}-{str(y)}", 0))
    pos = lambda p: posmap.get(p, "F")
    sk = [p for p in ev if pos(p) != "G"]
    F = sorted([p for p in sk if pos(p) != "D"], key=lambda p: -ev[p]); D = sorted([p for p in sk if pos(p) == "D"], key=lambda p: -ev[p])
    lines, used = [], set()
    for _ in range(4):
        rem = [p for p in F if p not in used]
        if len(rem) < 3: break
        a = rem[0]; best = None
        for b, c in combinations(rem[1:], 2):
            sc = ov(t["pev"], a, b) + ov(t["pev"], a, c) + ov(t["pev"], b, c)
            if not best or sc > best[0]: best = (sc, b, c)
        trio = [a, best[1], best[2]]; used |= set(trio)
        lines.append(dict(p=trio, sec=best[0] // 3))
    pairs, used = [], set()
    for _ in range(3):
        rem = [p for p in D if p not in used]
        if len(rem) < 2: break
        a = rem[0]; b = max(rem[1:], key=lambda x: ov(t["pev"], a, x))
        used |= {a, b}; pairs.append(dict(p=[a, b], sec=ov(t["pev"], a, b)))
    units, used = [], set()
    P = sorted([p for p in pp if pos(p) != "G" and pp[p] >= 20], key=lambda p: -pp[p])
    for _ in range(2):
        rem = [p for p in P if p not in used]
        if not rem: break
        a = rem[0]; mates = sorted(rem[1:], key=lambda x: -ov(t["ppp"], a, x))[:4]
        u = [a] + mates; used |= set(u); units.append(dict(p=u, sec=pp[a]))
    return dict(gid=g["gid"], date=g["date"], opp=g["away"] if g["home"] == team else g["home"], F=lines, D=pairs, PP=units,
                ppTotal=max(pp.values(), default=0))

def merge_games(team, games, weights=(1.0, 0.5, 0.25), exclude=()):
    """Weighted blend of the team's most recent games (newest first) so one in-game shuffle doesn't flip the lines.
    exclude = player ids known unavailable (injured/out or no longer on the roster)."""
    acc = dict(ev={}, pp={}, toi={}, pev={}, ppp={})
    base = None
    ex = {str(p) for p in exclude}
    for w, g in zip(weights, games):
        t = (g or {}).get("teams", {}).get(team)
        if not t: continue
        base = base or g
        for k in acc:
            for key, v in t[k].items():
                if any(part in ex for part in str(key).split("-")): continue
                acc[k][key] = acc[k].get(key, 0) + w * v
    if not base: return None
    acc = {k: {kk: int(round(vv)) for kk, vv in v.items()} for k, v in acc.items()}
    return dict(base, teams={team: acc})
