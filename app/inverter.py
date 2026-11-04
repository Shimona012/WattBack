from .tariffs import TARIFFS

def _t(x): return TARIFFS[x] if isinstance(x, str) else x      # accept a state code or a tariff dict

def _energy(kwh: float, t: dict, months: int) -> float:
    sl = [((u * months if u else None), r) for u, r in t["slabs"]]
    if not t.get("telescopic", True):                           # whole consumption at the slab rate it lands in
        return kwh * next(r for u, r in sl if u is None or kwh <= u)
    energy, prev = 0.0, 0
    for upper, rate in sl:
        top = kwh if upper is None else min(kwh, upper)
        if top > prev: energy += (top - prev) * rate
        if upper is None or kwh <= upper: break
        prev = upper
    return energy

def forward_bill(kwh: float, t, months: int = 1) -> float:
    """kWh over `months` -> rupees. Bi-monthly billing scales slab limits and fixed charge."""
    t = _t(t)
    return (_energy(kwh, t, months) + kwh * t["fppa_per_kwh"] + t["fixed_charge"] * months) * (1 + t["duty"])

def invert_bill(bill: float, t, hi: float = 10000.0, months: int = 1) -> float:
    """rupees -> kWh. Telescopic bills only rise, so bisection works. Non-telescopic bills can drop at a slab
    edge (two usages can give one bill), so we scan and return the lowest match."""
    t = _t(t)
    if bill <= forward_bill(0, t, months): return 0.0
    if not t.get("telescopic", True):
        best, err = 0.0, float("inf")
        for i in range(int(hi * 10)):
            k = i / 10; e = abs(forward_bill(k, t, months) - bill)
            if e < err - 1e-9: best, err = k, e
        return round(best, 1)
    lo = 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if forward_bill(mid, t, months) < bill: lo = mid
        else: hi = mid
    return round((lo + hi) / 2, 1)

def slab_info(kwh: float, t) -> dict:
    """Units past the second-highest slab limit and the extra cost versus the rate below it."""
    t = _t(t)
    if len(t["slabs"]) < 2: return {"cliff_kwh": 0, "units_over": 0, "penalty_rs": 0}
    cliff = t["slabs"][-2][0]; over = max(0.0, kwh - cliff)
    step = (t["slabs"][-1][1] - t["slabs"][-2][1]) * (1 + t["duty"])
    pen = over * step if t.get("telescopic", True) else (kwh * step if over else 0)
    return {"cliff_kwh": cliff, "units_over": round(over, 1), "penalty_rs": round(pen)}
