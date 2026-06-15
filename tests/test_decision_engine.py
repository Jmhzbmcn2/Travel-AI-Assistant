"""Tests for the decision engine — updated for Sprint 1 coverage gate."""
from datetime import date

from travel_ai_agent.decision import build_decision
from travel_ai_agent.schemas import DecisionEvidence, DecisionInput, FlightOption, HotelOption, ItineraryDay, ItineraryItem, PlaceOption, RouteSegment, TripPlan


def test_build_decision_is_deterministic_and_flags_dense_day():
    """Fixture data should be deterministic but should NOT produce a recommendation."""
    decision_input = DecisionInput(
        trip_plan=TripPlan(
            origin="Ho Chi Minh",
            destination="Da Nang",
            days=3,
            travelers=2,
            budget_total=8_000_000,
            preferences=["bien", "an ngon"],
            comfort_level="medium",
        ),
        flight_options=[
            FlightOption(id="f1", provider="fixture", data_mode="fixture", airline="Demo Air", price=1_500_000),
        ],
        hotel_options=[
            HotelOption(id="h1", provider="fixture", data_mode="fixture", name="Demo Hotel", price_per_night=800_000, rating=4.4),
        ],
        itinerary=[
            ItineraryDay(
                day=1,
                date=date(2026, 7, 10),
                travel_minutes=220,
                items=[ItineraryItem(title=f"Place {index}") for index in range(4)],
                evidence=[
                    DecisionEvidence(type="warning", rule="Test Rule", observed_value="Test", threshold="Test", recommendation="Test")
                ]
            )
        ],
    )

    first = build_decision(decision_input)
    second = build_decision(decision_input)

    # Deterministic
    assert first == second
    assert first.total_cost > 0
    assert len(first.options) >= 1
    assert any(risk.type == "day_too_dense" for risk in first.risks)
    assert any(risk.type == "fixture_data" for risk in first.risks)

    # Sprint 1: fixture data must NOT produce a recommendation
    assert first.recommended_option is None
    assert first.decision_status in ("needs_revision", "insufficient_data")
    assert first.coverage_status == "draft_only"
    assert first.booking_links == []
    assert first.why_recommended == []


def test_build_decision_with_live_data_produces_recommendation():
    """Live data within verified coverage should produce a recommendation."""
    decision_input = DecisionInput(
        trip_plan=TripPlan(
            origin="Ho Chi Minh",
            destination="Da Nang",
            days=3,
            travelers=2,
            budget_total=10_000_000,
            preferences=["bien"],
            comfort_level="medium",
        ),
        flight_options=[
            FlightOption(id="f1", provider="serpapi", data_mode="live", airline="VietJet", price=1_500_000),
            FlightOption(id="f2", provider="serpapi", data_mode="live", airline="VNA", price=2_200_000),
        ],
        hotel_options=[
            HotelOption(id="h1", provider="serpapi", data_mode="live", name="Beach Hotel", price_per_night=800_000, rating=4.2),
            HotelOption(id="h2", provider="serpapi", data_mode="live", name="Comfort Inn", price_per_night=1_200_000, rating=4.6),
        ],
        route_segments=[
            RouteSegment(from_place_id="p1", to_place_id="p2", distance_km=5.0, duration_minutes=15, provider="serpapi", data_mode="live"),
        ],
        place_options=[
            PlaceOption(id="p1", provider="serpapi", data_mode="live", name="Beach", category="beach", lat=16.05, lng=108.22, place_match_status="verified"),
            PlaceOption(id="p2", provider="serpapi", data_mode="live", name="Market", category="food", lat=16.06, lng=108.23, place_match_status="verified"),
        ],
        itinerary=[
            ItineraryDay(
                day=1,
                date=date(2026, 7, 10),
                items=[ItineraryItem(title="Beach"), ItineraryItem(title="Market")],
            )
        ],
    )

    result = build_decision(decision_input)

    assert result.decision_status == "recommended"
    assert result.recommended_option is not None
    assert result.coverage_status == "verified"
    assert result.total_cost > 0
    assert len(result.options) >= 2
