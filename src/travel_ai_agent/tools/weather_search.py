"""
Weather tool — tra cứu thời tiết thật qua OpenWeatherMap API.
"""
from langchain_core.tools import tool
from travel_ai_agent.config.settings import OPENWEATHERMAP_API_KEY
import requests
import json


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city using OpenWeatherMap API.

    Args:
        city: City name (e.g. "Da Nang", "Ha Noi", "Nha Trang")

    Returns:
        JSON string with weather data including temperature, humidity,
        description, wind speed, etc.
    """
    if not OPENWEATHERMAP_API_KEY:
        return json.dumps({
            "status": "error",
            "message": "OPENWEATHERMAP_API_KEY chưa được cấu hình trong .env"
        }, ensure_ascii=False)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",      # Celsius
        "lang": "vi",           # Tiếng Việt
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather = {
            "status": "success",
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "clouds": data["clouds"]["all"],
        }

        # Thêm mưa nếu có
        if "rain" in data:
            weather["rain_1h"] = data["rain"].get("1h", 0)
        if "snow" in data:
            weather["snow_1h"] = data["snow"].get("1h", 0)

        return json.dumps(weather, ensure_ascii=False)

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return json.dumps({
                "status": "error",
                "message": f"Không tìm thấy thành phố '{city}'. Thử tên tiếng Anh (VD: 'Da Nang')."
            }, ensure_ascii=False)
        return json.dumps({
            "status": "error",
            "message": f"HTTP error: {str(e)}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


def get_weather_forecast(city: str, days: int = 5) -> list[dict]:
    """Get multi-day weather forecast for a city.

    Uses OpenWeatherMap 5-day/3-hour forecast API, aggregated per day.
    Returns list of dicts with date, temp_min, temp_max, rain_probability, summary.
    """
    if not OPENWEATHERMAP_API_KEY:
        return []

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",
        "lang": "vi",
        "cnt": min(days * 8, 40),  # 8 entries per day (3-hour intervals)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Aggregate 3-hour entries into daily forecasts
        daily: dict[str, dict] = {}
        for entry in data.get("list", []):
            dt_text = entry["dt_txt"][:10]  # YYYY-MM-DD
            if dt_text not in daily:
                daily[dt_text] = {
                    "date": dt_text,
                    "temp_min": entry["main"]["temp_min"],
                    "temp_max": entry["main"]["temp_max"],
                    "rain_entries": 0,
                    "total_entries": 0,
                    "descriptions": [],
                }
            day = daily[dt_text]
            day["temp_min"] = min(day["temp_min"], entry["main"]["temp_min"])
            day["temp_max"] = max(day["temp_max"], entry["main"]["temp_max"])
            day["total_entries"] += 1
            weather_main = entry["weather"][0]["main"].lower() if entry.get("weather") else ""
            if weather_main in ("rain", "drizzle", "thunderstorm"):
                day["rain_entries"] += 1
            desc = entry["weather"][0]["description"] if entry.get("weather") else ""
            if desc and desc not in day["descriptions"]:
                day["descriptions"].append(desc)

        result = []
        for day_data in list(daily.values())[:days]:
            rain_prob = day_data["rain_entries"] / max(day_data["total_entries"], 1)
            result.append({
                "date": day_data["date"],
                "temp_min": round(day_data["temp_min"], 1),
                "temp_max": round(day_data["temp_max"], 1),
                "rain_probability": round(rain_prob, 2),
                "summary": ", ".join(day_data["descriptions"][:3]) or "Không có dữ liệu",
            })
        return result
    except Exception:
        return []