"""Tests for risk detection — weather mismatch, route backtracking, distance, budget."""
from datetime import date

from travel_ai_agent.decision import build_decision
from travel_ai_agent.decision.itinerary import _check_route_backtracking_day
from travel_ai_agent.schemas import (
    DecisionEvidence,
    DecisionInput,
    FlightOption,
    HotelOption,
    ItineraryDay,
    ItineraryItem,
    PlaceOption,
    TripPlan,
    WeatherForecast,
)


def _plan():
    return TripPlan(
        origin="Ho Chi Minh",
        destination="Da Nang",
        days=2,
        travelers=1,
        budget_total=10_000_000,
        comfort_level="medium",
    )


def _flights():
    return [FlightOption(id="f1", provider="test", data_mode="fixture", airline="Test", price=1_500_000)]


def _hotels():
    return [HotelOption(id="h1", provider="test", data_mode="fixture", name="Test Hotel", price_per_night=800_000, rating=4.0)]


def test_weather_outdoor_mismatch_risk():
    itinerary = [
        ItineraryDay(
            day=1,
            date=date(2026, 7, 10),
            items=[ItineraryItem(title="Beach Day", outdoor=True)],
        ),
    ]
    weather = [
        WeatherForecast(
            provider="test",
            date=date(2026, 7, 10),
            location="Da Nang",
            rain_probability=0.8,
            summary="Mưa lớn",
        ),
    ]
    decision = build_decision(
        DecisionInput(
            trip_plan=_plan(),
            flight_options=_flights(),
            hotel_options=_hotels(),
            weather_forecasts=weather,
            itinerary=itinerary,
        )
    )
    assert any(r.type == "weather_outdoor_mismatch" for r in decision.risks)
    risk = next(r for r in decision.risks if r.type == "weather_outdoor_mismatch")
    assert risk.target_day == 1
    assert risk.target_place_id is None # Not provided in test items
    assert risk.suggested_action == "replace_place"


def test_no_weather_risk_for_indoor_items():
    itinerary = [
        ItineraryDay(
            day=1,
            date=date(2026, 7, 10),
            items=[ItineraryItem(title="Museum", outdoor=False)],
        ),
    ]
    weather = [
        WeatherForecast(
            provider="test",
            date=date(2026, 7, 10),
            location="Da Nang",
            rain_probability=0.9,
            summary="Mưa rất lớn",
        ),
    ]
    decision = build_decision(
        DecisionInput(
            trip_plan=_plan(),
            flight_options=_flights(),
            hotel_options=_hotels(),
            weather_forecasts=weather,
            itinerary=itinerary,
        )
    )
    assert not any(r.type == "weather_outdoor_mismatch" for r in decision.risks)


def test_distance_too_high_risk():
    # travel_minutes 250 => est ~125km > 60km threshold
    itinerary = [
        ItineraryDay(
            day=1,
            date=date(2026, 7, 10),
            travel_minutes=250,
            items=[ItineraryItem(title="Far place")],
        ),
    ]
    decision = build_decision(
        DecisionInput(
            trip_plan=_plan(),
            flight_options=_flights(),
            hotel_options=_hotels(),
            itinerary=itinerary,
        )
    )
    assert any(r.type == "distance_too_high" for r in decision.risks)


def test_route_backtracking_risk():
    # Places that backtrack: p0 far, p1 farther, p2 close to p0
    places = [
        PlaceOption(id="p0", provider="test", name="Start", category="attraction", lat=16.0, lng=108.0),
        PlaceOption(id="p1", provider="test", name="Far", category="attraction", lat=16.1, lng=108.2),
        PlaceOption(id="p2", provider="test", name="Back", category="attraction", lat=16.01, lng=108.01),
    ]
    backtracking = _check_route_backtracking_day(places)
    assert len(backtracking) > 0
    assert "Back" in backtracking


def test_day_too_dense_risk():
    itinerary = [
        ItineraryDay(
            day=1,
            date=date(2026, 7, 10),
            travel_minutes=200,
            items=[ItineraryItem(title=f"Place {i}") for i in range(5)],
            evidence=[
                DecisionEvidence(type="warning", rule="Test Rule", observed_value="Test", threshold="Test", recommendation="Test")
            ],
        ),
    ]
    decision = build_decision(
        DecisionInput(
            trip_plan=_plan(),
            flight_options=_flights(),
            hotel_options=_hotels(),
            itinerary=itinerary,
        )
    )
    assert any(r.type == "day_too_dense" for r in decision.risks)


def test_budget_tight_risk_when_over():
    plan = TripPlan(
        origin="Ho Chi Minh",
        destination="Da Nang",
        days=2,
        travelers=1,
        budget_total=2_000_000,  # Very low budget
        comfort_level="medium",
    )
    decision = build_decision(
        DecisionInput(
            trip_plan=plan,
            flight_options=_flights(),
            hotel_options=_hotels(),
            itinerary=[ItineraryDay(day=1, date=date(2026, 7, 10), items=[])],
        )
    )
    assert any(r.type == "budget_tight" for r in decision.risks)
