import hashlib, math

GEN_KWH_PER_KW_YR, COST_PER_KW, ROOF_SQFT_PER_KW = 1450, 48000, 95   # placeholders: verify vs GEDA/MNRE
LOAN_RATE, LOAN_YEARS = 0.07, 7

def subsidy(kw: float) -> int:
    """PM Surya Ghar: 30k/kW up to 2 kW, 18k for the 3rd kW, capped at 78k. Verify current scheme."""
    return int(min(kw, 2) * 30000 + max(0.0, min(kw, 3) - 2) * 18000)

def solar_or_kit(monthly_kwh: float, monthly_bill: float, renter: bool) -> dict:
    if renter:
        return {"type": "kit", "items": ["BLDC ceiling fan", "Smart AC saver plug"],
                "est_saving_rs": round(monthly_bill * 0.10)}      # placeholder estimate
    kw = min(10.0, max(1.0, math.ceil(monthly_kwh * 12 / GEN_KWH_PER_KW_YR * 2) / 2))
    gross = round(kw * COST_PER_KW); sub = subsidy(kw); net = gross - sub
    r, n = LOAN_RATE / 12, LOAN_YEARS * 12
    emi = round(net * r / (1 - (1 + r) ** -n))
    return {"type": "solar", "kw": kw, "roof_sqft": round(kw * ROOF_SQFT_PER_KW), "gross": gross,
            "subsidy": sub, "net": net, "emi": emi, "monthly_saving": round(monthly_bill - emi),
            "vendors": ["Vendor A (placeholder)", "Vendor B (placeholder)", "Vendor C (placeholder)"]}

def reward(score, pin: str, kwh: float, verified: bool = False):
    """Scratch-card prize. Only households beating their size-adjusted baseline get one."""
    if score is None or score >= 1.0:
        return None
    pool = ["₹100 off a BLDC fan", "₹50 bill cashback"] if score < 0.8 else ["₹50 bill cashback", "LED bulb voucher"]
    h = int(hashlib.sha256(f"{pin}{kwh}".encode()).hexdigest(), 16)   # deterministic: no re-rolling
    return {"label": pool[h % len(pool)], "preview_only": not verified}

NUDGE = {   # have a native speaker review hi/gu before the demo
 "over": {"en": "You went {over} units past the {cliff}-unit slab and paid about ₹{pen} extra. Run the AC at 24 degrees with the fan on to stay under it.",
          "hi": "आपने {cliff} यूनिट की सीमा से {over} यूनिट ज़्यादा बिजली जलाई और लगभग ₹{pen} ज़्यादा दिए। AC 24 डिग्री पर और पंखा चलाकर रखें।",
          "gu": "તમે {cliff} યુનિટની મર્યાદા કરતાં {over} યુનિટ વધુ વાપર્યા અને લગભગ ₹{pen} વધુ ચૂકવ્યા. AC 24 ડિગ્રી પર અને પંખો ચાલુ રાખો."},
 "ok":   {"en": "You stayed under the {cliff}-unit slab. Well done.",
          "hi": "आप {cliff} यूनिट की सीमा के अंदर रहे। बहुत बढ़िया।",
          "gu": "તમે {cliff} યુનિટની મર્યાદાની અંદર રહ્યા. સરસ!"}}

NUDGE["est"] = {"en": "These are estimates because we don't have verified rates for your state. Enter the slabs from your bill for an exact result.",
                "hi": "ये अनुमान हैं क्योंकि आपके राज्य की पक्की दरें हमारे पास नहीं हैं। सही नतीजे के लिए अपने बिल की दरें डालें।",
                "gu": "આ અંદાજ છે કારણ કે તમારા રાજ્યના ચકાસેલા દર અમારી પાસે નથી. ચોક્કસ પરિણામ માટે તમારા બિલના દર દાખલ કરો."}

def nudge(slab: dict, lang: str, estimate: bool = False) -> str:
    k = "est" if estimate else ("over" if slab["units_over"] else "ok")
    return NUDGE[k].get(lang, NUDGE[k]["en"]).format(over=slab["units_over"], cliff=slab["cliff_kwh"], pen=slab["penalty_rs"])

# Synthetic society ranking (fairness score = actual / expected for household size). Replace with real data.
SOCIETIES = [("Sector 21, Gandhinagar", 0.74), ("Satellite, Ahmedabad", 0.86), ("Kalawad Road, Rajkot", 0.93),
             ("Navrangpura, Ahmedabad", 1.04), ("Sector 7, Gandhinagar", 1.12), ("Alkapuri, Vadodara", 1.21)]

def leaderboard(score):
    rows = [{"name": n, "score": s} for n, s in SOCIETIES]
    if score is not None:
        rows.append({"name": "You", "score": score, "you": True})
    return sorted(rows, key=lambda r: r["score"])

# Synthetic admin data: (PIN, area, households, avg kWh/person/month, solar readiness 0-100)
ADMIN = [("380001", "Ahmedabad Central", 82000, 71, 78), ("382010", "Gandhinagar", 41000, 66, 84),
         ("360001", "Rajkot", 56000, 63, 80), ("390001", "Vadodara", 61000, 69, 76), ("395001", "Surat", 94000, 74, 72)]
ADMIN_CONST = {"slab3_share": 0.30, "kw": 3, "peak_coincidence": 0.6, "co2_kg_per_kwh": 0.82, "gen_kwh_per_kw_yr": GEN_KWH_PER_KW_YR}
