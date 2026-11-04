"""Turn crowd-submitted rates into registry entries once enough different devices agree.
    python scripts/promote_submissions.py            # report only
    python scripts/promote_submissions.py --apply    # write agreed rates into data/tariffs.json as status "community"
Promoted rates are reported by people, not read from the regulator's order: have someone compare them with the order
before you upgrade the status to "verified"."""
import json, sys
from collections import defaultdict
from datetime import date
from pathlib import Path
D = Path("data"); MIN = 3
groups = defaultdict(lambda: {"who": set(), "t": None})
f = D / "submissions.jsonl"
for line in (f.read_text().splitlines() if f.exists() else []):
    r = json.loads(line); g = groups[(r["state"], r["key"])]; g["who"].add(r["who"]); g["t"] = r["tariff"]
reg = json.loads((D / "tariffs.json").read_text()); changed = False
for (state, _), g in sorted(groups.items()):
    n = len(g["who"]); loaded = state in reg
    print(f"{state}: {n} device(s) agree" + (" (already loaded)" if loaded else ""))
    if n >= MIN and not loaded and "--apply" in sys.argv:
        reg[state] = {**g["t"], "effective": date.today().isoformat(), "status": "community",
                      "source": f"{n} devices agreed", "unverified": ["everything: community-reported, check the regulator's order"]}
        changed = True; print(f"  -> promoted {state}")
if changed: (D / "tariffs.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False))
