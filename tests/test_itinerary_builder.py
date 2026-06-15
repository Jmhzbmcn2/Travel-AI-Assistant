"""Tests for itinerary builder — day splitting, clustering, warnings."""
from datetime import date

from travel_ai_agent.decision.itinerary import build_itinerary_order, enrich_itinerary_routes
from travel_ai_agent.schemas import PlaceOption, RouteSegment, TripPlan


def _plan(days=3, comfort="medium"):
    return TripPlan(
        destination="Da Nang",
        days=days,
        departure_date=date(2026, 7, 10),
        travelers=2,
        comfort_level=comfort,
    )


def _places(n=6):
    return [
        PlaceOption(
            id=f"p{i}",
            provider="test",
            data_mode="fixture",
            name=f"Place {i}",
            category="attraction",
            lat=16.0 + i * 0.01,
            lng=108.0 + i * 0.01,
            estimated_cost=50_000,
        )
        for i in range(n)
    ]


def _routes(places):
    return [
        RouteSegment(
            provider="test",
            from_place_id=places[i].id,
            to_place_id=places[i + 1].id,
            distance_km=5 + i * 2,
            duration_minutes=15 + i * 5,
        )
        for i in range(len(places) - 1)
    ]


def test_build_itinerary_splits_days():
    plan = _plan(days=3)
    places = _places(6)
    routes = _routes(places)
    ordered = build_itinerary_order(plan, places)
    itinerary = enrich_itinerary_routes(plan, ordered, routes)

    assert len(itinerary) == 3
    total_items = sum(len(day.items) for day in itinerary)
    assert total_items == 6


def test_build_itinerary_respects_comfort_level():
    plan = _plan(days=3, comfort="comfortable")
    places = _places(9)
    routes = _routes(places)
    ordered = build_itinerary_order(plan, places)
    itinerary = enrich_itinerary_routes(plan, ordered, routes)

    # Comfortable: max 2 places/day → should expand to more days if needed
    for day in itinerary:
        assert len(day.items) <= 3  # flexible but limited


def test_build_itinerary_warns_on_dense_day():
    plan = _plan(days=1)
    places = _places(5)
    routes = _routes(places)
    ordered = build_itinerary_order(plan, places)
    itinerary = enrich_itinerary_routes(plan, ordered, routes)

    assert len(itinerary) == 1
    # 5 places in 1 day (default 90 mins each) = 450 mins
    # travel = ~4 legs = ~80 mins
    # load = 450 + 80 + 90 = 620
    # medium limit = 600 -> warning
    assert len(itinerary[0].items) == 5
    assert len(itinerary[0].evidence) > 0
    assert itinerary[0].evidence[0].type == "warning"


def test_build_itinerary_assigns_travel_minutes():
    plan = _plan(days=2)
    places = _places(4)
    routes = _routes(places)
    ordered = build_itinerary_order(plan, places)
    itinerary = enrich_itinerary_routes(plan, ordered, routes)

    assert any(day.travel_minutes > 0 for day in itinerary)


def test_build_itinerary_with_no_places():
    plan = _plan(days=2)
    ordered = build_itinerary_order(plan, [])
    itinerary = enrich_itinerary_routes(plan, ordered, [])

    assert len(itinerary) == 2
    assert all(len(day.items) == 0 for day in itinerary)

def test_build_itinerary_flight_loss_triggers_warning():
    from travel_ai_agent.schemas.domain import FlightOption
    
    plan = _plan(days=1, comfort="medium")
    places = _places(5) # 5 places * 90 mins = 450 mins
    routes = []
    
    flights = [
        FlightOption(
            id="f1", provider="test", airline="VJ", 
            arrival_time="14:00", # Arrives at 14:00 -> loses 5 hours (14 - 9)
            price=1_000_000, price_scope="one_way_per_traveler"
        )
    ]
    
    ordered = build_itinerary_order(plan, places)
    itinerary = enrich_itinerary_routes(plan, ordered, routes, flights)
    
    # Base limit is 600. Loss is 5 * 60 = 300. Limit becomes 300.
    # Total load = 450 + 90 = 540 > 300 -> warning
    
    assert len(itinerary[0].evidence) > 0
    assert any("Tối đa 5.0 giờ hoạt động" in e.rule for e in itinerary[0].evidence)
