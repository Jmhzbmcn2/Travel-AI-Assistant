"""Tests for the coverage gate — verifies that fixture/missing critical data blocks recommendations."""
from datetime import date

from travel_ai_agent.decision import build_decision, evaluate_coverage
from travel_ai_agent.decision.coverage import CoverageResult
from travel_ai_agent.schemas import (
    DecisionInput,
    FlightOption,
    HotelOption,
    ItineraryDay,
    ItineraryItem,
    PlaceOption,
    RouteSegment,
    TripPlan,
)


def _base_plan(**overrides) -> TripPlan:
    defaults = dict(
        origin="Ho Chi Minh",
        destination="Da Nang",
        days=3,
        travelers=2,
        budget_total=8_000_000,
        preferences=["bien", "an ngon"],
        comfort_level="medium",
        currency="VND",
    )
    defaults.update(overrides)
    return TripPlan(**defaults)


def _live_flights() -> list[FlightOption]:
    return [
        FlightOption(id="f1", provider="serpapi", data_mode="live", airline="VietJet", price=1_500_000),
        FlightOption(id="f2", provider="serpapi", data_mode="live", airline="VNA", price=2_200_000),
    ]


def _fixture_flights() -> list[FlightOption]:
    return [
        FlightOption(id="f1", provider="fixture", data_mode="fixture", airline="Fixture Air", price=1_600_000),
    ]


def _live_hotels() -> list[HotelOption]:
    return [
        HotelOption(id="h1", provider="serpapi", data_mode="live", name="Beach Hotel", price_per_night=800_000, rating=4.2),
        HotelOption(id="h2", provider="serpapi", data_mode="live", name="Comfort Hotel", price_per_night=1_200_000, rating=4.6),
    ]


def _fixture_hotels() -> list[HotelOption]:
    return [
        HotelOption(id="h1", provider="fixture", data_mode="fixture", name="Fixture Hotel", price_per_night=850_000, rating=4.0),
    ]


def _live_routes() -> list[RouteSegment]:
    return [
        RouteSegment(provider="serpapi", data_mode="live", from_place_id="p1", to_place_id="p2", distance_km=10, duration_minutes=25),
    ]


def _places_with_gps() -> list[PlaceOption]:
    return [
        PlaceOption(id="p1", provider="serpapi", data_mode="live", name="Beach", category="beach", lat=16.05, lng=108.22, place_match_status="verified"),
        PlaceOption(id="p2", provider="serpapi", data_mode="live", name="Market", category="food", lat=16.06, lng=108.23, place_match_status="verified"),
    ]


def _itinerary() -> list[ItineraryDay]:
    return [
        ItineraryDay(day=1, date=date(2026, 7, 10), items=[ItineraryItem(title="Beach"), ItineraryItem(title="Market")]),
    ]


# ── Test 1: All live data, domestic Vietnam → verified + recommended ──
def test_all_live_domestic_verified():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        route_segments=_live_routes(),
        place_options=_places_with_gps(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "verified"
    assert coverage.confidence in ("high", "medium")
    assert len(coverage.blocking_reasons) == 0

    decision = build_decision(data)
    assert decision.decision_status == "recommended"
    assert decision.recommended_option is not None
    assert decision.coverage_status == "verified"


# ── Test 2: Fixture flights → draft_only, no recommendation ──
def test_fixture_flights_blocks_recommendation():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_fixture_flights(),
        hotel_options=_live_hotels(),
        route_segments=_live_routes(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert any("chuyến bay" in r for r in coverage.blocking_reasons)

    decision = build_decision(data)
    assert decision.decision_status != "recommended"
    assert decision.recommended_option is None


# ── Test 3: Missing hotels → draft_only, no recommendation ──
def test_missing_hotels_blocks_recommendation():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_live_flights(),
        hotel_options=[],
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert any("khách sạn" in r for r in coverage.blocking_reasons)

    decision = build_decision(data)
    assert decision.decision_status != "recommended"
    assert decision.recommended_option is None


# ── Test 4: Fixture routes but has GPS → still can verify with GPS fallback ──
def test_fixture_routes_with_gps_fallback():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        route_segments=[],
        place_options=_places_with_gps(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    # GPS fallback means route requirement is met
    assert coverage.status == "estimated"
    assert coverage.confidence == "medium"  # medium because no live routes


# ── Test 5: International destination (USD) → unsupported ──
def test_international_unsupported():
    data = DecisionInput(
        trip_plan=_base_plan(currency="USD", destination="Tokyo"),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "unsupported"

    decision = build_decision(data)
    assert decision.decision_status == "insufficient_data"
    assert decision.recommended_option is None


# ── Test 6: Days > 5 → draft_only (outside verified coverage) ──
def test_days_out_of_bounds():
    data = DecisionInput(
        trip_plan=_base_plan(days=7),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        route_segments=_live_routes(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert any("ngày" in r for r in coverage.blocking_reasons)


# ── Test 7: Travelers > 4 → draft_only ──
def test_travelers_out_of_bounds():
    data = DecisionInput(
        trip_plan=_base_plan(travelers=6),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        route_segments=_live_routes(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert any("người" in r for r in coverage.blocking_reasons)


# ── Test 8: All fixture data → draft_only, insufficient confidence ──
def test_all_fixture_insufficient():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_fixture_flights(),
        hotel_options=_fixture_hotels(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert coverage.confidence == "insufficient"

    decision = build_decision(data)
    assert decision.recommended_option is None
    assert decision.decision_status in ("needs_revision", "insufficient_data")


# ── Test 9: Empty flights AND hotels → insufficient_data ──
def test_no_data_insufficient():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=[],
        hotel_options=[],
        itinerary=_itinerary(),
    )
    decision = build_decision(data)
    assert decision.decision_status == "insufficient_data"
    assert decision.recommended_option is None
    assert len(decision.options) == 0


# ── Test 10: Mixed — live flights, fixture hotels → draft_only ──
def test_mixed_live_fixture():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_live_flights(),
        hotel_options=_fixture_hotels(),
        route_segments=_live_routes(),
        itinerary=_itinerary(),
    )
    coverage = evaluate_coverage(data)
    assert coverage.status == "draft_only"
    assert any("khách sạn" in r for r in coverage.blocking_reasons)

    decision = build_decision(data)
    assert decision.recommended_option is None
    assert decision.decision_status == "needs_revision"
    # Should still have options for informational purposes
    assert len(decision.options) > 0


# ── Test 11: Decision output always has rule_version and coverage fields ──
def test_decision_output_has_trust_fields():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_live_flights(),
        hotel_options=_live_hotels(),
        route_segments=_live_routes(),
        place_options=_places_with_gps(),
        itinerary=_itinerary(),
    )
    decision = build_decision(data)
    assert decision.rule_version == "v1.0"
    assert decision.coverage_status in ("verified", "draft_only", "unsupported")
    assert decision.decision_status in ("recommended", "needs_revision", "insufficient_data")
    assert decision.confidence in ("high", "medium", "insufficient")
    assert isinstance(decision.blocking_reasons, list)
    assert isinstance(decision.data_freshness, dict)


# ── Test 12: Booking links only for verified recommendations ──
def test_no_booking_links_for_draft():
    data = DecisionInput(
        trip_plan=_base_plan(),
        flight_options=_fixture_flights(),
        hotel_options=_fixture_hotels(),
        itinerary=_itinerary(),
    )
    decision = build_decision(data)
    assert decision.booking_links == []
    assert decision.why_recommended == []
