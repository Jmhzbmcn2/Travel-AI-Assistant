from __future__ import annotations

import asyncio
from datetime import date

from travel_ai_agent.api.services.trip_service import to_iata
from travel_ai_agent.decision import build_decision, build_itinerary_order, enrich_itinerary_routes
from travel_ai_agent.providers import normalize_flights, normalize_hotels
from travel_ai_agent.providers.gateway import (
    fetch_flights,
    fetch_hotel_reviews,
    fetch_hotels,
    fetch_places,
    fetch_routes,
    fetch_weather_forecasts,
)
from travel_ai_agent.schemas import DecisionInput, TripPlan


async def decision_node(state: dict) -> dict:
    """Fetch dữ liệu du lịch rồi chạy Decision Engine.

    Gộp vai trò của các agent cũ: gọi flights + hotels song song, phần
    places/routes/weather/reviews chạy sau khi đã có itinerary order.
    """
    plan = TripPlan.model_validate(state.get("plan") or {})
    session_id = state.get("session_id")

    departure = plan.departure_date.isoformat() if plan.departure_date else ""
    return_date = plan.return_date.isoformat() if plan.return_date else ""
    nights = plan.nights if plan.nights is not None else max((plan.days or 1) - 1, 1)

    flights_raw, hotels_raw = await asyncio.gather(
        asyncio.to_thread(
            fetch_flights,
            to_iata(plan.origin) or "",
            to_iata(plan.destination) or "",
            departure,
            return_date,
            session_id,
        ),
        asyncio.to_thread(
            fetch_hotels,
            plan.destination or "",
            departure,
            nights,
            session_id,
        ),
    )
    flights = normalize_flights(flights_raw)
    hotels = normalize_hotels(hotels_raw)

    places = fetch_places(plan.destination or "", plan.preferences, session_id)

    hotel_anchor = hotels[0] if hotels else None
    ordered_clusters = build_itinerary_order(plan, places, hotel_anchor)

    routes = []
    for day_places in ordered_clusters:
        if len(day_places) > 1:
            routes.extend(fetch_routes(day_places, session_id))

    start_date = (plan.departure_date or date.today()).isoformat()
    weather_forecasts = fetch_weather_forecasts(plan.destination or "", start_date, plan.days or 1, session_id)
    reviews = fetch_hotel_reviews(hotels, session_id)

    itinerary = enrich_itinerary_routes(plan, ordered_clusters, routes, flights)
    decision = build_decision(
        DecisionInput(
            trip_plan=plan,
            flight_options=flights,
            hotel_options=hotels,
            place_options=places,
            route_segments=routes,
            weather_forecasts=weather_forecasts,
            review_summaries=reviews,
            itinerary=itinerary,
        )
    )

    return {
        "decision_output": decision.model_dump(mode="json"),
        "flight_options": [item.model_dump(mode="json") for item in flights],
        "hotel_options": [item.model_dump(mode="json") for item in hotels],
        "place_options": [item.model_dump(mode="json") for item in places],
        "route_segments": [item.model_dump(mode="json") for item in routes],
        "weather_forecasts": [item.model_dump(mode="json") for item in weather_forecasts],
        "review_summaries": [item.model_dump(mode="json") for item in reviews],
        "current_step": "decision",
    }
