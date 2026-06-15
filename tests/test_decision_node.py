"""Test decision_node returns structured output — updated for Sprint 1 coverage gate."""
from travel_ai_agent.nodes import decision_node as decision_module
from travel_ai_agent.providers import fixture_places, fixture_routes


def test_decision_node_returns_structured_output(monkeypatch):
    """Decision node with fixture data should return structured output but NOT recommend."""
    places = fixture_places("Da Nang")
    monkeypatch.setattr(decision_module, "fetch_places", lambda destination, preferences, session_id: places)
    monkeypatch.setattr(decision_module, "fetch_routes", lambda items, session_id: fixture_routes(items))
    monkeypatch.setattr(decision_module, "fetch_weather_forecasts", lambda dest, start, days, sid: [])
    monkeypatch.setattr(decision_module, "fetch_hotel_reviews", lambda hotels, sid: [])
    result = decision_module.decision_node(
        {
            "plan": {
                "goal": "Da Nang trip",
                "steps": [],
                "constraints": {
                    "destination": "Da Nang",
                    "days": 3,
                    "travelers": 2,
                    "budget": 8_000_000,
                    "preferences": ["bien"],
                    "comfort_level": "medium",
                },
            },
            "flight_results": [{"airline": "Demo", "price": 1_500_000, "data_mode": "fixture"}],
            "hotel_results": [{"name": "Demo Hotel", "price": 800_000, "rating": 4.5, "data_mode": "fixture"}],
        }
    )

    assert result["decision_output"]["total_cost"] > 0
    # Sprint 1: fixture data → no recommendation
    assert result["decision_output"]["recommended_option"] is None
    assert result["decision_output"]["decision_status"] in ("needs_revision", "insufficient_data")
    assert result["decision_output"]["coverage_status"] == "draft_only"
