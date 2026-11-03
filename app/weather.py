import json, urllib.request

def daily_temps(lat: float, lon: float, days: int = 30) -> tuple[list[float], str]:
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_mean&past_days={days}&forecast_days=1&timezone=Asia%2FKolkata")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            temps = json.load(r)["daily"]["temperature_2m_mean"]
        return [t for t in temps if t is not None], "open-meteo"
    except Exception:
        return [33.0] * days, "fallback"      # offline demo mode

def cdd(temps: list[float], base: float = 24.0) -> float:
    return round(sum(max(0.0, t - base) for t in temps), 1)
