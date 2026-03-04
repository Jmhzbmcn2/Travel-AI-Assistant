"""
Weather tool — tra cứu thời tiết thật qua OpenWeatherMap API.
"""
from langchain_core.tools import tool
from config.settings import OPENWEATHERMAP_API_KEY
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