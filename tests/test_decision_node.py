"""Test decision_node: async, gọi flights/hotels song song, ghi options vào state."""
import pytest

from travel_ai_agent.nodes import decision_node as decision_module
from travel_ai_agent.providers import fixture_places, fixture_routes
from travel_ai_agent.schemas import TripPlan


@pytest.mark.asyncio
async def test_decision_node_returns_structured_output(monkeypatch):
    """Fixture data → structured output nhưng KHÔNG recommend (coverage gate)."""
    places = fixture_places("Da Nang")
    calls: list[str] = []

    monkeypatch.setattr(decision_module, "fetch_flights", lambda *a, **k: calls.append("flights") or [
        {"airline": "Demo", "price": 1_500_000, "data_mode": "fixture"}
    ])
    monkeypatch.setattr(decision_module, "fetch_hotels", lambda *a, **k: calls.append("hotels") or [
        {"name": "Demo Hotel", "price": 800_000, "rating": 4.5, "data_mode": "fixture"}
    ])
    monkeypatch.setattr(decision_module, "fetch_places", lambda *a, **k: places)
    monkeypatch.setattr(decision_module, "fetch_routes", lambda items, session_id: fixture_routes(items))
    monkeypatch.setattr(decision_module, "fetch_weather_forecasts", lambda *a, **k: [])
    monkeypatch.setattr(decision_module, "fetch_hotel_reviews", lambda *a, **k: [])

    plan = TripPlan(
        destination="Da Nang", days=3, travelers=2, budget_total=8_000_000,
        preferences=["bien"], comfort_level="medium",
    )
    result = await decision_module.decision_node({"plan": plan.model_dump(mode="json"), "session_id": "t"})

    assert "flights" in calls and "hotels" in calls
    assert result["decision_output"]["total_cost"] > 0
    assert result["decision_output"]["recommended_option"] is None
    assert result["decision_output"]["decision_status"] in ("needs_revision", "insufficient_data")
    # options được ghi vào state cho trip actions
    assert len(result["flight_options"]) == 1
    assert len(result["hotel_options"]) == 1
    assert result["place_options"]
