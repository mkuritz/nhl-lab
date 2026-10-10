import json, os, datetime as dt
def load_events():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schedule.json")
    if not os.path.exists(p): return []
    out = []
    for g in json.load(open(p)):
        st = dt.datetime.fromisoformat(g["start"].replace("Z", "+00:00"))
        out.append((str(g["id"]), st, f'{g["away"]}+{g["home"]}'))   # target = both teams
    return out
