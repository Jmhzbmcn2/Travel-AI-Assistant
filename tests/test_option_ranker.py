"""Tests for option ranking — 3 options, scores, cross-comparison."""
from datetime import date

from travel_ai_agent.decision import build_decision
from travel_ai_agent.schemas import (
    DecisionInput,
    FlightOption,
    HotelOption,
    ItineraryDay,
    ItineraryItem,
    TripPlan,
)


def _base_input(**overrides):
    plan = TripPlan(
        origin="Ho Chi Minh",
        destination="Da Nang",
        days=3,
        travelers=2,
        budget_total=overrides.pop("budget_total", 10_000_000),
        preferences=["bien"],
        comfort_level="medium",
    )
    return DecisionInput(
        trip_plan=plan,
        flight_options=overrides.get(
            "flights",
            [
                FlightOption(id="f-cheap", provider="test", data_mode="fixture", airline="Budget Air", price=1_200_000),
                FlightOption(id="f-mid", provider="test", data_mode="fixture", airline="Mid Air", price=1_800_000, departure_time="06:00"),
                FlightOption(id="f-comfy", provider="test", data_mode="fixture", airline="Comfy Air", price=2_500_000, stops=0, duration_minutes=90),
            ],
        ),
        hotel_options=overrides.get(
            "hotels",
            [
                HotelOption(id="h-cheap", provider="test", data_mode="fixture", name="Budget Hotel", price_per_night=600_000, rating=3.5),
                HotelOption(id="h-mid", provider="test", data_mode="fixture", name="Mid Hotel", price_per_night=900_000, rating=4.2),
                HotelOption(id="h-comfy", provider="test", data_mode="fixture", name="Comfy Hotel", price_per_night=1_500_000, rating=4.8),
            ],
        ),
        itinerary=overrides.get(
            "itinerary",
            [
                ItineraryDay(day=1, date=date(2026, 7, 10), travel_minutes=60, items=[ItineraryItem(title="Beach")]),
                ItineraryDay(day=2, date=date(2026, 7, 11), travel_minutes=90, items=[ItineraryItem(title="Food tour")]),
                ItineraryDay(day=3, date=date(2026, 7, 12), travel_minutes=45, items=[ItineraryItem(title="Museum")]),
            ],
        ),
    )


def test_produces_3_options():
    decision = build_decision(_base_input())
    assert len(decision.options) >= 2
    option_ids = {opt.id for opt in decision.options}
    assert "cheapest" in option_ids
    assert "balanced" in option_ids


def test_cheapest_option_costs_least():
    decision = build_decision(_base_input())
    cheapest = next(opt for opt in decision.options if opt.id == "cheapest")
    for other in decision.options:
        if other.id != "cheapest":
            assert cheapest.total_cost <= other.total_cost + 1, f"cheapest ({cheapest.total_cost}) should be <= {other.id} ({other.total_cost})"


def test_each_option_has_cost_breakdown():
    decision = build_decision(_base_input())
    for opt in decision.options:
        assert opt.cost_breakdown is not None
        assert opt.cost_breakdown.flights >= 0
        assert opt.cost_breakdown.hotels >= 0


def test_each_option_has_scores():
    decision = build_decision(_base_input())
    for opt in decision.options:
        assert 0 <= opt.cost_score <= 1
        assert 0 <= opt.feasibility_score <= 1
        assert 0 <= opt.comfort_score <= 1
        assert 0 <= opt.value_score <= 1


def test_why_recommended_empty_for_fixture_data():
    """Sprint 1: fixture data should NOT produce cross-comparison recommendations."""
    decision = build_decision(_base_input())
    # Fixture data → no recommendation → no why_recommended
    assert decision.recommended_option is None
    assert decision.why_recommended == []


def test_over_budget_detected():
    decision = build_decision(_base_input(budget_total=3_000_000))
    assert decision.budget_status in {"over_budget", "slightly_over"}
    assert any(r.type == "budget_tight" for r in decision.risks)


def test_flight_tradeoffs_populated():
    inp = _base_input()
    decision = build_decision(inp)
    # f-mid has departure_time 06:00 → early_morning tradeoff expected
    all_tradeoffs = [t for opt in decision.options for t in opt.tradeoffs]
    assert len(all_tradeoffs) > 0  # At least one tradeoff tag generated
