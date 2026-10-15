"""NHL rivalry tags. Label only — never change projections until Edge Tracker proves the signal."""
# Canonical pairs (bidirectional). Original Six + well-known divisional / historic rivalries.
PAIRS = {
    frozenset({"BOS", "MTL"}),  # Original Six / Battle of Quebec-adjacent
    frozenset({"BOS", "TOR"}),
    frozenset({"MTL", "TOR"}),
    frozenset({"CHI", "DET"}),
    frozenset({"NYR", "NYI"}),
    frozenset({"NYR", "NJD"}),
    frozenset({"NYI", "NJD"}),
    frozenset({"PHI", "PIT"}),
    frozenset({"PHI", "NJD"}),
    frozenset({"WSH", "PIT"}),
    frozenset({"EDM", "CGY"}),  # Battle of Alberta
    frozenset({"VAN", "CGY"}),
    frozenset({"VAN", "EDM"}),
    frozenset({"LAK", "ANA"}),  # Freeway Faceoff
    frozenset({"LAK", "SJS"}),
    frozenset({"SJS", "VGK"}),
    frozenset({"VGK", "COL"}),
    frozenset({"COL", "DAL"}),
    frozenset({"DAL", "STL"}),
    frozenset({"MIN", "WPG"}),
    frozenset({"TOR", "OTT"}),  # Battle of Ontario
    frozenset({"MTL", "OTT"}),
    frozenset({"DET", "TOR"}),
    frozenset({"CHI", "STL"}),
    frozenset({"TBL", "FLA"}),  # Battle of Florida
    frozenset({"CAR", "WSH"}),
    frozenset({"SEA", "VAN"}),
    frozenset({"UTA", "COL"}),
    frozenset({"BUF", "TOR"}),
    frozenset({"BUF", "OTT"}),
}

LABELS = {
    frozenset({"BOS", "MTL"}): "Original Six rivalry",
    frozenset({"BOS", "TOR"}): "Original Six rivalry",
    frozenset({"MTL", "TOR"}): "Original Six rivalry",
    frozenset({"CHI", "DET"}): "Original Six rivalry",
    frozenset({"DET", "TOR"}): "Original Six rivalry",
    frozenset({"EDM", "CGY"}): "Battle of Alberta",
    frozenset({"TOR", "OTT"}): "Battle of Ontario",
    frozenset({"TBL", "FLA"}): "Battle of Florida",
    frozenset({"LAK", "ANA"}): "Freeway Faceoff",
    frozenset({"NYR", "NYI"}): "Battle of New York",
    frozenset({"NYR", "NJD"}): "Hudson River rivalry",
    frozenset({"NYI", "NJD"}): "Hudson River rivalry",
    frozenset({"SEA", "VAN"}): "Pacific Northwest rivalry",
    frozenset({"BUF", "TOR"}): "Battle of the QEW",
    frozenset({"BUF", "OTT"}): "Provincial rivalry",
}

def tag(away, home):
    key = frozenset({away, home})
    if key not in PAIRS:
        return None
    return dict(tag="rivalry", label=LABELS.get(key, "Rivalry"), pair=sorted(key))
