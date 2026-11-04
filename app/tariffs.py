"""Tariff records for every Indian state. Sources, in order: data/tariffs.json (curated), data/tariffs_cache.json
(downloaded from TARIFF_REGISTRY_URL, refreshed daily), then per-request custom rates. A record can have several
versions with an "effective" date; the newest one already in force is used, so April rollovers need no deploy.
States with no record raise TariffNotLoaded instead of guessing."""
import json, os, threading
from datetime import date
from pathlib import Path
from urllib.request import urlopen

DATA = Path(__file__).parent.parent / "data"
TARIFFS: dict = {}            # state code -> active tariff (rebuilt in place by rebuild())
_RAW: dict = {}               # state code -> list of versions
_lock = threading.Lock()

STATES = {  # code: (name, capital lat, lon, regulator) - coordinates only used for weather
 "AP": ("Andhra Pradesh", 16.51, 80.52, "APERC"), "AR": ("Arunachal Pradesh", 27.08, 93.62, "APSERC"),
 "AS": ("Assam", 26.14, 91.74, "AERC"), "BR": ("Bihar", 25.59, 85.14, "BERC"), "CG": ("Chhattisgarh", 21.25, 81.63, "CSERC"),
 "GA": ("Goa", 15.50, 73.83, "JERC (Goa & UTs)"), "GJ": ("Gujarat", 23.22, 72.65, "GERC"), "HR": ("Haryana", 30.73, 76.78, "HERC"),
 "HP": ("Himachal Pradesh", 31.10, 77.17, "HPERC"), "JH": ("Jharkhand", 23.34, 85.31, "JSERC"), "KA": ("Karnataka", 12.97, 77.59, "KERC"),
 "KL": ("Kerala", 8.52, 76.94, "KSERC"), "MP": ("Madhya Pradesh", 23.26, 77.41, "MPERC"), "MH": ("Maharashtra", 19.08, 72.88, "MERC"),
 "MN": ("Manipur", 24.82, 93.94, "JERC (Manipur & Mizoram)"), "ML": ("Meghalaya", 25.57, 91.88, "MSERC"),
 "MZ": ("Mizoram", 23.73, 92.72, "JERC (Manipur & Mizoram)"), "NL": ("Nagaland", 25.67, 94.11, "NERC"), "OD": ("Odisha", 20.30, 85.82, "OERC"),
 "PB": ("Punjab", 30.73, 76.78, "PSERC"), "RJ": ("Rajasthan", 26.91, 75.79, "RERC"), "SK": ("Sikkim", 27.33, 88.61, "SSERC"),
 "TN": ("Tamil Nadu", 13.08, 80.27, "TNERC"), "TG": ("Telangana", 17.39, 78.49, "TGERC"), "TR": ("Tripura", 23.83, 91.28, "TERC"),
 "UP": ("Uttar Pradesh", 26.85, 80.95, "UPERC"), "UK": ("Uttarakhand", 30.32, 78.03, "UERC"), "WB": ("West Bengal", 22.57, 88.36, "WBERC"),
 "AN": ("Andaman & Nicobar Islands", 11.62, 92.73, "JERC (Goa & UTs)"), "CH": ("Chandigarh", 30.73, 76.78, "JERC (Goa & UTs)"),
 "DD": ("Dadra & Nagar Haveli and Daman & Diu", 20.40, 72.83, "JERC (Goa & UTs)"), "DL": ("Delhi", 28.61, 77.21, "DERC"),
 "JK": ("Jammu & Kashmir", 34.08, 74.80, "JERC (J&K and Ladakh)"), "LA": ("Ladakh", 34.15, 77.58, "JERC (J&K and Ladakh)"),
 "LD": ("Lakshadweep", 10.57, 72.64, "JERC (Goa & UTs)"), "PY": ("Puducherry", 11.93, 79.83, "JERC (Goa & UTs)")}
# Approximate: PIN prefix -> state. Postal circles don't follow borders, so 3-digit overrides go first and
# the live India Post lookup (see _pin_lookup) is preferred whenever it is reachable.
_P = {"11": "DL", "12": "HR", "13": "HR", "14": "PB", "15": "PB", "16": "PB", "17": "HP", "18": "JK", "19": "JK",
      **{p: "UP" for p in "20 21 22 23 24 25 26 27 28".split()}, **{p: "RJ" for p in "30 31 32 33 34".split()},
      **{p: "GJ" for p in "36 37 38 39".split()}, **{p: "MH" for p in "40 41 42 43 44".split()},
      **{p: "MP" for p in "45 46 47 48".split()}, "49": "CG", "50": "TG", "51": "AP", "52": "AP", "53": "AP",
      **{p: "KA" for p in "56 57 58 59".split()}, **{p: "TN" for p in "60 61 62 63 64".split()},
      "67": "KL", "68": "KL", "69": "KL", **{p: "WB" for p in "70 71 72 73 74".split()},
      "75": "OD", "76": "OD", "77": "OD", "78": "AS", "79": "AR", **{p: "BR" for p in "80 81 82 83 84 85".split()}}
_P3 = {"403": "GA", "160": "CH", "194": "LA", "737": "SK", "744": "AN", "793": "ML", "794": "ML", "795": "MN", "796": "MZ",
       "797": "NL", "798": "NL", "799": "TR", **{p: "UK" for p in "246 248 249 262 263".split()},
       **{p: "JH" for p in "814 815 816 826 827 828 829 831 832 833 834 835".split()}}

class TariffNotLoaded(Exception): ...

# Fallback BRACKET for states with no record. These are assumptions based on the rough Rs 3-12 per-unit range
# reported across states, NOT regulator data. Cheap rates give the most units, dear rates the fewest.
FALLBACK_LOW = {"slabs": [(100, 3.5), (300, 5.0), (None, 6.5)], "telescopic": True, "fixed_charge": 40.0, "duty": 0.05, "fppa_per_kwh": 0.0, "billing_days": 30}
FALLBACK_HIGH = {"slabs": [(100, 5.0), (300, 8.0), (None, 10.5)], "telescopic": True, "fixed_charge": 100.0, "duty": 0.10, "fppa_per_kwh": 0.0, "billing_days": 30}

def clean_tariff(raw: dict) -> dict:
    """Validate and normalise a tariff (registry entry, submission or custom rates). Raises ValueError."""
    try:
        slabs = [(None if u is None else float(u), float(r)) for u, r in raw["slabs"]]
        t = {**raw, "slabs": slabs, "telescopic": bool(raw.get("telescopic", True)),
             "fixed_charge": float(raw.get("fixed_charge", 0)), "duty": float(raw.get("duty", 0)),
             "fppa_per_kwh": float(raw.get("fppa_per_kwh", 0)), "billing_days": int(raw.get("billing_days", 30))}
    except (KeyError, TypeError, ValueError):
        raise ValueError("Rates need slabs like [[50, 3.05], [null, 5.20]] plus fixed charge, duty and fuel surcharge")
    bounds = [u for u, _ in slabs[:-1]]
    if not 1 <= len(slabs) <= 8 or slabs[-1][0] is not None or None in bounds:
        raise ValueError("Use 1 to 8 slabs; the last one must have no upper limit")
    if any(b <= a for a, b in zip(bounds, bounds[1:])) or any(b <= 0 for b in bounds):
        raise ValueError("Slab limits must be increasing")
    if not all(0 <= r <= 30 for _, r in slabs): raise ValueError("Rates must be between 0 and 30 rupees per unit")
    if not (0 <= t["fixed_charge"] <= 5000 and 0 <= t["duty"] <= 0.5 and 0 <= t["fppa_per_kwh"] <= 15):
        raise ValueError("Fixed charge, duty (as a fraction like 0.15) or fuel surcharge out of range")
    return t

def rebuild(today: str | None = None):
    today = today or date.today().isoformat()
    with _lock:
        new = {}
        for code, versions in _RAW.items():
            live = [v for v in versions if v.get("effective", "0000") <= today]
            if live: new[code] = max(live, key=lambda v: v.get("effective", ""))
        TARIFFS.clear(); TARIFFS.update(new)

def _merge(data: dict) -> int:
    n = 0
    for code, v in data.items():
        for item in (v if isinstance(v, list) else [v]):
            try: t = clean_tariff(item)
            except ValueError: continue                       # skip bad records, keep the rest
            vs = [x for x in _RAW.setdefault(code, []) if x.get("effective") != t.get("effective")]
            _RAW[code] = vs + [t]; n += 1
    return n

def load():
    for name in ("tariffs.json", "tariffs_cache.json"):
        f = DATA / name
        if f.exists(): _merge(json.loads(f.read_text()))
    rebuild()

def refresh() -> str:
    """Pull the shared registry (any JSON file with the same shape as tariffs.json) and cache it."""
    url = os.getenv("TARIFF_REGISTRY_URL")
    if not url: return "no registry configured"
    with urlopen(url, timeout=15) as r: data = json.load(r)
    n = _merge(data); (DATA / "tariffs_cache.json").write_text(json.dumps(data)); rebuild()
    return f"merged {n} records"

_PIN_CACHE: dict = {}
_NAME_TO_CODE = {n.lower().replace("&", "and"): c for c, (n, *_ ) in STATES.items()}
_NAME_TO_CODE.update({"jammu and kashmir": "JK", "ladakh": "JK", "orissa": "OD", "pondicherry": "PY", "puducherry": "PY"})

def _pin_lookup(pin: str) -> str:
    """Exact state from India Post's directory (api.postalpincode.in), cached. Falls back to the prefix table
    when offline, rate limited or unknown. Set PIN_LOOKUP=off to disable."""
    if os.getenv("PIN_LOOKUP") == "off": return ""
    if pin in _PIN_CACHE: return _PIN_CACHE[pin]
    try:
        with urlopen(f"https://api.postalpincode.in/pincode/{pin}", timeout=3) as r:
            offices = json.load(r)[0].get("PostOffice") or []
        name = (offices[0]["State"] if offices else "").lower().replace("&", "and")
        code = _NAME_TO_CODE.get(name, "")
    except Exception:
        return ""                                   # do not cache failures
    _PIN_CACHE[pin] = code
    return code

def state_for_pin(pin: str) -> str:
    return _pin_lookup(pin) or _P3.get(pin[:3]) or _P.get(pin[:2], "")

def state_name(code: str) -> str:
    return STATES.get(code, (code or "an unrecognised region",))[0]

def regulator_for(code: str) -> str:
    return STATES.get(code, ("", 0, 0, "the state electricity regulator"))[3]

def coords_for(code: str) -> tuple[float, float]:
    t = TARIFFS.get(code, {}); s = STATES.get(code)
    return (t["lat"], t["lon"]) if "lat" in t else ((s[1], s[2]) if s else (22.5, 79.0))

def tariff_key(pin: str, state: str | None = None) -> str:
    code = state or state_for_pin(pin)
    if code not in TARIFFS:
        raise TariffNotLoaded(f"Rates for {state_name(code)} aren't loaded yet. Enter your own rates from your bill to continue.")
    return code

load()
