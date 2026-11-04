from .tariffs import TariffNotLoaded, FALLBACK_LOW, FALLBACK_HIGH, TARIFFS, tariff_key, state_for_pin, state_name, coords_for, clean_tariff, regulator_for
from .inverter import invert_bill, slab_info
from .weather import daily_temps, cdd
from .llm import polish
from .features import solar_or_kit, reward, nudge

CO2_KG_PER_KWH = 0.82      # placeholder grid factor - cite CEA figure before demo
COOL_KWH_PER_CDD = 0.9     # placeholder - calibrate from synthetic dataset
BASE_KWH, COOL_COEF, SIZE_EXP, COOL_EXP = 60.0, 0.5, 0.6, 0.3

def expected_kwh(n: int, cdd_val: float) -> float:
    """Weather-adjusted expected use for a household of n. Shared loads (fridge, router, pump)
    don't scale with headcount, hence exponents < 1 instead of dividing by n."""
    return BASE_KWH * n**SIZE_EXP + COOL_COEF * cdd_val * n**COOL_EXP

def analyze(bill: float, pin: str, members: int, months: int = 1, renter: bool = False, lang: str = "en", verified: bool = False,
            state: str | None = None, custom: dict | None = None, coords: tuple | None = None) -> dict:
    if custom:                                   # the person typed their own rates
        t, code, origin = clean_tariff(custom), (state or state_for_pin(pin)), "custom"
    else:
        try: code = tariff_key(pin, state); t, origin = TARIFFS[code], "registry"
        except TariffNotLoaded: code, t, origin = (state or state_for_pin(pin)), None, "fallback"
    lat, lon = coords or coords_for(code)
    if t is None:                                # no record: bracket the answer between a cheap and a dear tariff
        hi_k = invert_bill(bill, FALLBACK_LOW, months=months) / months; lo_k = invert_bill(bill, FALLBACK_HIGH, months=months) / months
        kwh, t, rng = round((lo_k + hi_k) / 2, 1), FALLBACK_HIGH, [round(lo_k), round(hi_k)]
    else:
        kwh, rng = round(invert_bill(bill, t, months=months) / months, 1), None   # normalised to per-month
    mbill = bill / months
    temps, wsrc = daily_temps(lat, lon)
    c = cdd(temps)
    cooling = min(0.6 * kwh, c * COOL_KWH_PER_CDD)
    base = kwh - cooling
    standby = 0.1 * base
    est = origin == "fallback"
    slab = {"cliff_kwh": 0, "units_over": 0, "penalty_rs": 0} if est else slab_info(kwh, t)
    exp = expected_kwh(members, c)
    score = round(kwh / exp, 2) if exp else None
    return {
        "bill_rs": bill, "months": months, "pin": pin, "tariff": {"state": state_name(code), "regulator": regulator_for(code), "source": origin, "effective": t.get("effective"), "status": "estimate" if est else t.get("status", "unknown")}, "members": members,
        "kwh": kwh, "kwh_per_person": round(kwh / members, 1),
        "co2_kg": round(kwh * CO2_KG_PER_KWH),
        "slab": slab,
        "weather": {"cdd": c, "source": wsrc},
        "split_kwh": {"base": round(base - standby, 1), "cooling": round(cooling, 1), "standby": round(standby, 1)},
        "fairness": {"expected_kwh": round(exp, 1), "score": score,
                     "beats_baseline": bool(score and score < 1.0)},
        "reward": reward(score, pin, kwh, verified),
        "confidence": "estimate" if est else ("custom" if origin == "custom" else "regulator"), "kwh_range": rng,
        "offer": solar_or_kit(kwh, mbill, renter),
        "nudge": polish(nudge(slab, lang, est), lang), "lang": lang, "verified": verified,
    }
