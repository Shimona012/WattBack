def insights(rows: list[dict]) -> dict:
    """Personal tips from a user's saved checks. Estimate-mode rows are ignored: they aren't reliable."""
    rows = [r for r in rows if r["confidence"] != "estimate"]
    if not rows: return {"checks": 0, "tips": [{"title": "No saved checks yet", "text": "Run a bill check while signed in and your history builds up here."}]}
    last, tips = rows[-1], []
    if len(rows) >= 2:
        d = (last["kwh"] - rows[-2]["kwh"]) / rows[-2]["kwh"] * 100 if rows[-2]["kwh"] else 0
        tips.append({"title": "Since your last check", "text": f"Your use {'rose' if d > 0 else 'fell'} {abs(d):.0f}% ({rows[-2]['kwh']:.0f} to {last['kwh']:.0f} units a month)."})
    recent = rows[-3:]
    if sum(r["units_over"] > 0 for r in recent) >= 2:
        tips.append({"title": "You keep crossing the top slab", "text": "Two of your last three checks went past the top slab. Cutting AC hours on the hottest nights, or a rooftop system sized to your use, would pay back fastest."})
    if sum(r["cooling_share"] for r in recent) / len(recent) > 0.45:
        tips.append({"title": "Cooling is your biggest load", "text": "Over 45% of your use tracks the weather. Set the AC to 24 degrees with a fan on, and service the filters before summer."})
    scores = [r["score"] for r in rows if r["score"]]
    if scores and last["score"] == min(scores) and len(scores) > 1:
        tips.append({"title": "Personal best", "text": f"Your score of {last['score']} is your best so far. Lower means you use less than expected for a home your size."})
    if not tips: tips.append({"title": "Steady", "text": "Nothing unusual in your recent bills. Check again after your next bill to spot trends."})
    return {"checks": len(rows), "latest_kwh": last["kwh"], "best_score": min(scores) if scores else None, "tips": tips}
