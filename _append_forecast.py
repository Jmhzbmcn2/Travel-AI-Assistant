from pathlib import Path
p = Path("src/travel_ai_agent/tools/weather_search.py")
raw = p.read_bytes()
addition = '''

def get_weather_forecast(city: str, days: int = 5) -> dict:
    """Lấy dự báo thời tiết theo ngày qua OpenWeatherMap 5 day / 3 hour API.

    Returns dict {status, city, days:[{date, temp_min, temp_max, rain_probability, summary}]}.
    """
    from collections import defaultdict

    if not OPENWEATHERMAP_API_KEY:
        return {"status": "error", "message": "OPENWEATHERMAP_API_KEY missing", "days": []}

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": OPENWEATHERMAP_API_KEY, "units": "metric", "lang": "vi"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return {"status": "error", "message": str(exc), "days": []}

    buckets: dict = defaultdict(list)
    for entry in data.get("list", []):
        dt_txt = entry.get("dt_txt", "")
        if not dt_txt:
            continue
        buckets[dt_txt.split(" ")[0]].append(entry)

    out_days = []
    for day_key in sorted(buckets.keys())[: max(days, 1)]:
        entries = buckets[day_key]
        temps = [e["main"]["temp"] for e in entries if "main" in e]
        pops = [float(e.get("pop", 0.0)) for e in entries]
        descs = [e["weather"][0]["description"] for e in entries if e.get("weather")]
        summary = max(set(descs), key=descs.count) if descs else ""
        out_days.append({
            "date": day_key,
            "temp_min": round(min(temps), 1) if temps else None,
            "temp_max": round(max(temps), 1) if temps else None,
            "rain_probability": round(max(pops) if pops else 0.0, 2),
            "summary": summary,
        })

    return {"status": "success", "city": data.get("city", {}).get("name", city), "days": out_days}
'''
if b"def get_weather_forecast(" not in raw:
    p.write_bytes(raw + addition.replace("\n", "\r\n").encode("utf-8"))
    print("appended get_weather_forecast")
else:
    print("already present")
