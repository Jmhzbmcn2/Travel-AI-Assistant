from __future__ import annotations

from datetime import date

from travel_ai_agent.api.services.trip_service import trip_plan_from_graph_plan
from travel_ai_agent.decision import build_decision, build_itinerary_order, enrich_itinerary_routes
from travel_ai_agent.providers import normalize_flights, normalize_hotels
from travel_ai_agent.providers.gateway import fetch_hotel_reviews, fetch_places, fetch_routes, fetch_weather_forecasts
from travel_ai_agent.schemas import DecisionInput


def decision_node(state: dict) -> dict:
    plan = trip_plan_from_graph_plan(state.get("plan", {}))
    session_id = state.get("session_id")
    flights = normalize_flights(state.get("flight_results", []))
    hotels = normalize_hotels(state.get("hotel_results", []))
    places = fetch_places(plan.destination or "", plan.preferences, session_id)
    
    # S1-05 & S1-06: Build itinerary order first with hotel anchor
    hotel_anchor = hotels[0] if hotels else None
    ordered_clusters = build_itinerary_order(plan, places, hotel_anchor)
    
    # Fetch routes only for the required ordered places
    routes = []
    for day_places in ordered_clusters:
        if len(day_places) > 1:
            routes.extend(fetch_routes(day_places, session_id))

    # Multi-day weather forecasts
    start_date = (plan.departure_date or date.today()).isoformat()
    days = plan.days or 1
    weather_forecasts = fetch_weather_forecasts(
        plan.destination or "",
        start_date,
        days,
        session_id,
    )

    # Reviews from provider (SerpAPI with heuristic fallback)
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
        "current_step": "decision",
        "completed_agents": state.get("completed_agents", []) + ["decision"],
    }
