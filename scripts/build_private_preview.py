#!/usr/bin/env python3
"""Build the PRIVATE, unlisted preview bundle of the NHL Lab hub with the Live Analyzer tab.
The bundle is a copy of the hub shell that reads all normal hub data from the public NHL Lab site (read-only) and the
Live Analyzer data from its own data/live/ folder. It is meant to be dropped under an unguessable /p/<token>/ path
(blocked in robots.txt, noindex meta). Nothing here touches the public NHL Lab site or its main branch.
  python3 scripts/build_private_preview.py --out DIR
"""
import argparse, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = "https://nhllab.sportslabshq.com/"
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
# noindex + land on the Live Analyzer tab; hub data (teams, slate, players, ...) is read from the public site (read-only) via a fetch shim,
# only data/live/ is local to the preview
shim = ('(function(){const f=window.fetch;window.fetch=function(u,o){try{if(typeof u==="string"&&/^(\\.\\/)?data\\//.test(u)&&!/^(\\.\\/)?data\\/live\\//.test(u))u="%sdata/"+u.replace(/^(\\.\\/)?data\\//,"")}catch(e){}return f.call(this,u,o)}})();' % PUB)
s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta name="robots" content="noindex,nofollow,noarchive"><script>if(!location.hash)location.hash="#live"</script><script>' + shim + '</script>', 1)
# preview only: keep the member-gate script from covering the Live Analyzer container (same attribute the Shot Map tab uses)
if "<div id=\"lvbox\" data-sl-public>" not in s:
    assert "<div id=\"lvbox\">" in s
    s = s.replace("<div id=\"lvbox\">", "<div id=\"lvbox\" data-sl-public>")
# preview only: drop the member-gate / lead-capture scripts so the private page shows no sign-up sheet
import re as _re
for _pat in (r'<script[^>]*sl/sl\.js[^>]*></script>', r'<script[^>]*leads-config\.js[^>]*></script>', r'<script[^>]*js/leads\.js[^>]*></script>'):
    s, _n = _re.subn(_pat, '', s)
    assert _n == 1, _pat
s = s.replace('src="/sl-neutral.js?v=2"', 'src="sl-neutral.js?v=2"')
s = s.replace("<title>NHL Lab</title>", "<title>NHL Lab (private preview)</title>", 1)
open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(s)
for f in ("live-analyzer.js", "matchup-analyzer.js", "tailcard.js", "slip.js", "sl-neutral.js", "sl-sports.js", "side.js", "nhl-analyst.js", "shotlab.js"):
    if os.path.exists(os.path.join(ROOT, f)): shutil.copy2(os.path.join(ROOT, f), os.path.join(a.out, f))
d = os.path.join(a.out, "data", "live")
if os.path.isdir(d): shutil.rmtree(d)
shutil.copytree(os.path.join(ROOT, "data", "live"), d)
for bad in ("board_log.jsonl", "role_priors.json", "ot_history.json"):   # never ship private files
    assert not os.path.exists(os.path.join(d, bad)), bad
print("built", a.out, sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(a.out) for f in fs) // 1024, "KB")
