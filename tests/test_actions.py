import pytest
from datetime import date
from travel_ai_agent.decision.actions import optimize_day, execute_trip_action
from travel_ai_agent.api.schemas.trip import TripActionRequest
from travel_ai_agent.schemas.domain import (
    DecisionInput, DecisionOutput, TripPlan, PlaceOption, RouteSegment,
    ItineraryDay, ItineraryItem, HotelOption
)

def _plan():
    return TripPlan(origin="SGN", destination="PQC", days=1, travelers=2, budget_total=10000000, comfort_level="medium")

def _places():
    return [
        PlaceOption(id="p1", title="A", name="A", provider="test", category="attraction", lat=10.0, lng=100.0, price_level=1),
        PlaceOption(id="p2", title="B", name="B", provider="test", category="attraction", lat=10.2, lng=100.2, price_level=1),
        PlaceOption(id="p3", title="C", name="C", provider="test", category="attraction", lat=10.1, lng=100.1, price_level=1),
    ]

def _hotel():
    return HotelOption(id="h1", name="Hotel", provider="test", lat=10.0, lng=100.0, price_per_night=500000, data_mode="fixture")

def _routes():
    return [
        RouteSegment(from_place_id="h1", to_place_id="p1", provider="test", distance_km=0, duration_minutes=0, data_mode="fixture"),
        RouteSegment(from_place_id="p1", to_place_id="p2", provider="test", distance_km=20, duration_minutes=30, data_mode="fixture"),
        RouteSegment(from_place_id="p2", to_place_id="p3", provider="test", distance_km=10, duration_minutes=15, data_mode="fixture"),
        RouteSegment(from_place_id="p3", to_place_id="p2", provider="test", distance_km=10, duration_minutes=15, data_mode="fixture"),
        RouteSegment(from_place_id="p1", to_place_id="p3", provider="test", distance_km=10, duration_minutes=15, data_mode="fixture"),
        RouteSegment(from_place_id="p3", to_place_id="h1", provider="test", distance_km=10, duration_minutes=15, data_mode="fixture"),
        RouteSegment(from_place_id="p2", to_place_id="h1", provider="test", distance_km=20, duration_minutes=30, data_mode="fixture"),
    ]

import pytest

@pytest.mark.asyncio
async def test_optimize_day_reduces_travel_time():
    # Setup bad order: Hotel -> A -> B -> C (A=10.0, B=10.2, C=10.1)
    # distance H->A: 0, A->B: 30m, B->C: 15m. Total 45m.
    # Wait, optimal order from H(10.0) -> A(10.0) -> C(10.1) -> B(10.2).
    # travel time H->A (0) + A->C (15) + C->B (15) = 30m.
    plan = _plan()
    places = _places()
    hotel = _hotel()
    routes = _routes()
    
    bad_items = [
        ItineraryItem(place_id="p1", title="A", estimated_visit_minutes=60, category="attraction"),
        ItineraryItem(place_id="p2", title="B", estimated_visit_minutes=60, category="attraction"),
        ItineraryItem(place_id="p3", title="C", estimated_visit_minutes=60, category="attraction"),
    ]
    
    day = ItineraryDay(day=1, date=date(2026, 7, 10), items=bad_items, travel_minutes=45)
    
    data = DecisionInput(
        trip_plan=plan,
        place_options=places,
        hotel_options=[hotel],
        route_segments=routes,
        itinerary=[day]
    )
    
    from travel_ai_agent.schemas.domain import CostBreakdown
    decision = DecisionOutput(budget_status="unknown", total_cost=0, total_cost_per_person=0, feasibility_score=1.0, comfort_score=1.0, value_score=1.0, cost_breakdown=CostBreakdown(), itinerary=[day])
    
    req = TripActionRequest(action="optimize_day", target_day=1)
    res = await execute_trip_action(req, data, decision, session_id="test_session")
    
    assert res.status == "success"
    assert res.before_summary["travel_minutes"] == 45
    assert res.after_summary["travel_minutes"] == 30
    assert res.decision is not None
    
    # Check new order
    new_day = res.decision.itinerary[0]
    assert new_day.items[0].place_id == "p1"
    assert new_day.items[1].place_id == "p3"
    assert new_day.items[2].place_id == "p2"

@pytest.mark.asyncio
async def test_replace_place_success():
    plan = _plan()
    places = _places()
    # Add an unused alternative
    places.append(PlaceOption(id="p4", title="D", name="D", provider="test", category="attraction", lat=10.3, lng=100.3, price_level=1, place_match_status="verified", confidence="high"))
    hotel = _hotel()
    routes = _routes()
    
    bad_items = [
        ItineraryItem(place_id="p1", title="A", estimated_visit_minutes=60, category="attraction"),
    ]
    
    day = ItineraryDay(day=1, date=date(2026, 7, 10), items=bad_items, travel_minutes=45)
    
    data = DecisionInput(
        trip_plan=plan,
        place_options=places,
        hotel_options=[hotel],
        route_segments=routes,
        itinerary=[day]
    )
    
    from travel_ai_agent.schemas.domain import CostBreakdown
    decision = DecisionOutput(budget_status="unknown", total_cost=0, total_cost_per_person=0, feasibility_score=1.0, comfort_score=1.0, value_score=1.0, cost_breakdown=CostBreakdown(), itinerary=[day])
    
    req = TripActionRequest(action="replace_place", target_place_id="p1")
    
    # Mock fetch_routes to not fail since we test logic
    import travel_ai_agent.providers.gateway as gateway
    original_fetch = gateway.fetch_routes
    gateway.fetch_routes = lambda sq, sid: []
    
    try:
        res = await execute_trip_action(req, data, decision, session_id="test_session")
        assert res.status == "success"
        assert res.before_summary["replaced"] == "A"
        assert res.after_summary["replacement"] == "D"
        new_day = res.decision.itinerary[0]
        assert new_day.items[0].place_id == "p4"
    finally:
        gateway.fetch_routes = original_fetch
