"""Measured scorecard: does a model state the correct slab-overrun units and rupee penalty?
Truth comes from our tariff engine. Compare a base model to your adapted stack:
  python scripts/eval_numbers.py qwen3.5-397b 50
  python scripts/eval_numbers.py stack:wattback 50
Add --with-tariff to give the model the slab table (fair test for base models)."""
import random, re, sys
sys.path.insert(0, ".")
import app  # loads .env
from app.tariffs import TARIFFS
from app.inverter import forward_bill, slab_info
T = TARIFFS["GJ"]

def numbers(text): return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", text)]
def correct(text, truth):
    ns = numbers(text); has = lambda v, tol: any(abs(n - v) <= tol for n in ns)
    return has(truth["units_over"], 1) and has(truth["penalty_rs"], max(2, 0.03 * truth["penalty_rs"]))

def cases(n, seed=11):
    rnd = random.Random(seed)
    for _ in range(n):
        kwh = round(rnd.uniform(260, 480), 1); bill = round(forward_bill(kwh, T)); yield bill, slab_info(kwh, "GJ")

if __name__ == "__main__":
    from adaption import Adaption
    model, n, tariff = sys.argv[1], int(sys.argv[2]), "--with-tariff" in sys.argv
    c, ok = Adaption(), 0
    extra = f" Tariff: slabs {T['slabs']}, FPPPA Rs {T['fppa_per_kwh']}/unit, fixed Rs {T['fixed_charge']}, duty {T['duty']:.0%}." if tariff else ""
    for bill, truth in cases(n):
        q = f"My monthly bill is Rs {bill}.{extra} How many units did I go past the top-slab limit, and what extra did that cost me?"
        ok += correct(c.responses.create(model=model, input=q).output_text, truth)
    print(f"{model}: {ok}/{n} correct ({100 * ok / n:.1f}%)" + (" with tariff in prompt" if tariff else ""))
