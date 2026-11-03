"""Synthetic training set for a Hindi/Gujarati/English tip model. Ground truth comes from our own tariff
engine, so every number in every row is correct by construction.
    python scripts/make_dataset.py 2000 > wattback_train.jsonl"""
import json, random, sys
sys.path.insert(0, ".")
from app.tariffs import TARIFFS
from app.inverter import forward_bill, slab_info
from app.engine import expected_kwh
from app.features import nudge

random.seed(7)
t = TARIFFS["GJ"]
for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 2000):
    kwh = round(random.uniform(60, 520), 1); n = random.randint(1, 8)
    cdd = round(random.uniform(0, 330), 1); months = random.choice([1, 2])
    bill = round(forward_bill(kwh * months, t, months))
    exp = expected_kwh(n, cdd); score = round(kwh / exp, 2); slab = slab_info(kwh, "GJ")
    cause = ("slab_overrun" if slab["units_over"] else "cooling_heavy" if cdd > 200 and score > 1 else "on_track")
    lang = random.choice(["en", "hi", "gu"])
    prompt = (f"Bill Rs {bill} for {months} month(s), {n} people, {cdd} cooling degree-days, "
              f"{kwh} units a month. Write a short household tip in {lang}.")
    print(json.dumps({"prompt": prompt, "completion": nudge(slab, lang), "input": {"bill_rs": bill, "months": months, "members": n, "cdd": cdd, "kwh": kwh, "score": score, "slab": slab},
                      "root_cause": cause, "lang": lang, "target_text": nudge(slab, lang)}, ensure_ascii=False))
