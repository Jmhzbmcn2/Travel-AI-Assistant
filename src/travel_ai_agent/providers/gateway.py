from __future__ import annotations

import json
from datetime import datetime, timedelta

from serpapi import GoogleSearch

from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.config.settings import DEMO_MODE, SERPAPI_API_KEY
from travel_ai_agent.providers.normalizers import fixture_places, fixture_routes, normalize_places, normalize_reviews
from travel_ai_agent.schemas import PlaceOption, ReviewSummary, RouteSegment, WeatherForecast
from travel_ai_agent.core.guardrails import record_tool_call
from travel_ai_agent.tools.flight_search import search_flights
from travel_ai_agent.tools.hotel_search import search_hotels
from travel_ai_agent.tools.tavily_search import search_web
from travel_ai_agent.tools.weather_search import get_weather, get_weather_forecast

_store = SessionStore()


def _cached(session_id: str | None, key: str):
    return _store.get_cache(key) if session_id else None


def _record(session_id: str | None, name: str) -> bool:
    if not session_id:
        return True
    try:
        record_tool_call(_store, session_id, name)
        return True
    except RuntimeError:
        return False


def _save_cache(session_id: str | None, key: str, payload: dict, ttl: int) -> None:
    if session_id:
        _store.set_cache(key, payload, ttl)


def _fixture_flights() -> list[dict]:
    mode = "fixture"
    return [
        {"airline": "Fixture Air", "price": 1_600_000, "total_duration": 90, "stops": 0, "data_mode": mode, "price_scope": "one_way_per_traveler"},
        {"airline": "Fixture Air Plus", "price": 2_000_000, "total_duration": 85, "stops": 0, "data_mode": mode, "price_scope": "one_way_per_traveler"},
    ]


def _fixture_hotels() -> list[dict]:
    mode = "fixture"
    return [
        {"name": "Fixture Central Hotel", "price": 850_000, "rating": 4.2, "reviews": 320, "data_mode": mode},
        {"name": "Fixture Comfort Hotel", "price": 1_200_000, "rating": 4.6, "reviews": 540, "data_mode": mode},
    ]


def fetch_flights(origin: str, destination: str, departure_date: str, return_date: str | None = None, session_id: str | None = None) -> list[dict]:
    key = f"flight:{origin}:{destination}:{departure_date}:{return_date}"
    cached = _cached(session_id, key)
    if cached:
        return cached["items"]
    if destination == "NoFlightCity" or origin == "NoFlightCity":
        return []
    if not _record(session_id, "flight_search"):
        return _fixture_flights() if DEMO_MODE else []
    try:
        args = {"departure_id": origin, "arrival_id": destination, "outbound_date": departure_date}
        if return_date:
            args["return_date"] = return_date
        payload = json.loads(search_flights.invoke(args))
        if payload.get("status") == "success" and payload.get("flights"):
            _save_cache(session_id, key, {"items": payload["flights"]}, 1200)
            return payload["flights"]
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "flight_search", {"error": str(e), "provider": "serpapi_google_flights"})
    return _fixture_flights() if DEMO_MODE else []


def fetch_hotels(destination: str, check_in: str, nights: int, session_id: str | None = None) -> list[dict]:
    key = f"hotel:{destination}:{check_in}:{nights}"
    cached = _cached(session_id, key)
    if cached:
        return cached["items"]
    if destination == "NoHotelCity":
        return []
    if not _record(session_id, "hotel_search"):
        return _fixture_hotels() if DEMO_MODE else []
    try:
        check_out = (datetime.strptime(check_in, "%Y-%m-%d") + timedelta(days=nights)).strftime("%Y-%m-%d")
        payload = json.loads(search_hotels.invoke({"destination": destination, "check_in_date": check_in, "check_out_date": check_out}))
        if payload.get("status") == "success" and payload.get("hotels"):
            _save_cache(session_id, key, {"items": payload["hotels"]}, 1200)
            return payload["hotels"]
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "hotel_search", {"error": str(e), "provider": "serpapi_google_hotels"})
    return _fixture_hotels() if DEMO_MODE else []


def fetch_weather(destination: str, session_id: str | None = None) -> str:
    key = f"weather:{destination}"
    cached = _cached(session_id, key)
    if cached:
        return cached["value"]
    if not _record(session_id, "weather"):
        return "Đã đạt giới hạn tra cứu thời tiết cho phiên này."
    try:
        value = get_weather.invoke({"city": destination})
        _save_cache(session_id, key, {"value": value}, 7200)
        return value
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "weather", {"error": str(e), "provider": "tavily"})
        return "Không có dữ liệu thời tiết live; cần kiểm tra lại trước chuyến đi."


def fetch_weather_forecasts(
    destination: str,
    start_date: str,
    days: int,
    session_id: str | None = None,
) -> list[WeatherForecast]:
    """Fetch multi-day weather forecasts. Returns one WeatherForecast per day."""
    key = f"weather_forecast:{destination}:{start_date}:{days}"
    cached = _cached(session_id, key)
    if cached:
        return [WeatherForecast.model_validate(item) for item in cached["items"]]
    if not _record(session_id, "weather"):
        return _fixture_weather_forecasts(destination, start_date, days)
    try:
        raw_days = get_weather_forecast(destination, days)
        if raw_days:
            forecasts = [
                WeatherForecast(
                    provider="openweathermap_forecast",
                    data_mode="live",
                    date=day_data["date"],
                    location=destination,
                    temperature_min=day_data["temp_min"],
                    temperature_max=day_data["temp_max"],
                    rain_probability=day_data["rain_probability"],
                    summary=day_data["summary"],
                    activity_impact=(
                        ["prefer_indoor_after_15h"] if day_data["rain_probability"] >= 0.5 else []
                    ),
                )
                for day_data in raw_days
            ]
            _save_cache(
                session_id,
                key,
                {"items": [f.model_dump(mode="json") for f in forecasts]},
                7200,
            )
            return forecasts
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "weather_forecasts", {"error": str(e), "provider": "tavily"})
    return _fixture_weather_forecasts(destination, start_date, days)


def _fixture_weather_forecasts(destination: str, start_date: str, days: int) -> list[WeatherForecast]:
    """Fixture fallback for weather forecasts."""
    from datetime import date as Date
    try:
        base = datetime.strptime(start_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        base = Date.today()
    return [
        WeatherForecast(
            provider="mvp_fixture",
            data_mode="fixture",
            assumptions=[f"Dữ liệu thời tiết fixture cho {destination} ngày {base + timedelta(days=i)}."],
            date=base + timedelta(days=i),
            location=destination,
            temperature_min=25 + i % 3,
            temperature_max=32 + i % 3,
            rain_probability=0.3,
            summary="Nắng có mây, khả năng mưa chiều (fixture)",
        )
        for i in range(days)
    ]


def fetch_destination_info(destination: str, days: int | None = None, session_id: str | None = None) -> str:
    query = f"Thông tin du lịch {destination}" + (f" {days} ngày" if days else "")
    key = f"info:{query}"
    cached = _cached(session_id, key)
    if cached:
        return cached["value"]
    if not _record(session_id, "places_search"):
        return "Đã đạt giới hạn tra cứu thông tin điểm đến cho phiên này."
    try:
        value = search_web.invoke({"query": query})
        _save_cache(session_id, key, {"value": value}, 86400)
        return value
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "destination_info", {"error": str(e), "provider": "tavily"})
        return "Không có dữ liệu thông tin điểm đến live."


def fetch_places(destination: str, preferences: list[str] | None = None, session_id: str | None = None) -> list[PlaceOption]:
    query = " ".join(preferences or ["địa điểm du lịch"])
    key = f"places:{destination}:{query}"
    cached = _cached(session_id, key)
    if cached:
        return [PlaceOption.model_validate(item) for item in cached["items"]]
    if not _record(session_id, "places_search"):
        return fixture_places(destination) if DEMO_MODE else []
    try:
        result = GoogleSearch({"engine": "google_local", "q": f"{query} tại {destination}", "hl": "vi", "api_key": SERPAPI_API_KEY, "timeout": 15}).get_dict()
        places = normalize_places(result.get("local_results", [])[:8])
        if places:
            _save_cache(session_id, key, {"items": [place.model_dump(mode="json") for place in places]}, 86400)
            return places
    except Exception as e:
        if session_id:
            _store.add_usage_event(session_id, "provider_error", "places_search", {"error": str(e), "provider": "serpapi_google_local"})
    return fixture_places(destination) if DEMO_MODE else []


def fetch_routes(places: list[PlaceOption], session_id: str | None = None) -> list[RouteSegment]:
    key = "routes:" + ":".join(place.id for place in places)
    cached = _cached(session_id, key)
    if cached:
        return [RouteSegment.model_validate(item) for item in cached["items"]]
    if not _record(session_id, "routes"):
        return fixture_routes(places)
    if SERPAPI_API_KEY and all(place.lat is not None and place.lng is not None for place in places):
        routes: list[RouteSegment] = []
        try:
            for current, target in zip(places, places[1:]):
                result = GoogleSearch(
                    {
                        "engine": "google_maps_directions",
                        "start_addr": f"{current.lat},{current.lng}",
                        "end_addr": f"{target.lat},{target.lng}",
                        "travel_mode": "0",
                        "hl": "vi",
                        "api_key": SERPAPI_API_KEY,
                    }
                ).get_dict()
                direction = result["directions"][0]
                routes.append(
                    RouteSegment(
                        provider="serpapi_google_maps_directions",
                        from_place_id=current.id,
                        to_place_id=target.id,
                        distance_km=direction["distance"] / 1000,
                        duration_minutes=round(direction["duration"] / 60),
                    )
                )
            if routes:
                _save_cache(session_id, key, {"items": [route.model_dump(mode="json") for route in routes]}, 86400)
                return routes
        except Exception as e:
            if session_id:
                _store.add_usage_event(session_id, "provider_error", "routes", {"error": str(e), "provider": "serpapi_google_maps_directions"})
    return fixture_routes(places) if DEMO_MODE else []


def fetch_hotel_reviews(hotels: list, session_id: str | None = None) -> list[ReviewSummary]:
    """Fetch hotel reviews. Uses SerpAPI google_maps_reviews for top hotels, falls back to heuristic."""
    reviews: list[ReviewSummary] = []
    for hotel in hotels[:2]:  # Limit to 2 hotels per session to conserve API budget
        key = f"reviews:{hotel.id}:{hotel.name}"
        cached = _cached(session_id, key)
        if cached:
            reviews.append(ReviewSummary.model_validate(cached["review"]))
            continue

        # Try SerpAPI google_maps_reviews
        if SERPAPI_API_KEY and _record(session_id, "reviews"):
            try:
                result = GoogleSearch({
                    "engine": "google_maps_reviews",
                    "place_id": hotel.name,  # Use name as search proxy
                    "q": hotel.name,
                    "hl": "vi",
                    "api_key": SERPAPI_API_KEY,
                }).get_dict()
                raw_reviews = result.get("reviews", [])[:10]
                if raw_reviews:
                    review = normalize_reviews(hotel.id, raw_reviews)
                    _save_cache(session_id, key, {"review": review.model_dump(mode="json")}, 86400)
                    reviews.append(review)
                    continue
            except Exception as e:
                if session_id:
                    _store.add_usage_event(session_id, "provider_error", "hotel_reviews", {"error": str(e), "provider": "serpapi_google_maps_reviews"})

        # Heuristic fallback from hotel metadata
        review = ReviewSummary(
            provider="heuristic",
            data_mode="fixture",
            assumptions=["Đánh giá dùng heuristic từ rating/review_count, chưa có review text thật."],
            target_id=hotel.id,
            confidence="high" if hotel.review_count >= 100 else ("medium" if hotel.review_count >= 20 else "low"),
            positive_points=["Rating cao"] if hotel.rating and hotel.rating >= 4.0 else [],
            negative_points=[],
            risk_flags=["low_review_count"] if hotel.review_count < 20 else [],
        )
        reviews.append(review)

    # Heuristic for remaining hotels not queried
    for hotel in hotels[2:]:
        reviews.append(
            ReviewSummary(
                provider="heuristic",
                data_mode="fixture",
                target_id=hotel.id,
                confidence="high" if hotel.review_count >= 100 else ("medium" if hotel.review_count >= 20 else "low"),
                risk_flags=["low_review_count"] if hotel.review_count < 20 else [],
            )
        )
    return reviews
