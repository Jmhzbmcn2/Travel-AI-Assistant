from typing import Optional
from pydantic import ValidationError
import pytest
from travel_ai_agent.decision.engine import _cost_breakdown
from travel_ai_agent.schemas.domain import DecisionInput, FlightOption, HotelOption, TripPlan
from travel_ai_agent.decision.cost_rules import COST_RULES_V1

def make_flight(price: float, scope: str = "one_way_per_traveler") -> FlightOption:
    return FlightOption(
        id="f1",
        provider="fixture",
        airline="Air",
        price=price,
        price_scope=scope,
    )

def make_hotel(price: float) -> HotelOption:
    return HotelOption(
        id="h1",
        provider="fixture",
        name="Hotel",
        price_per_night=price,
    )

def make_input(travelers: int, days: int, return_date: Optional[str] = None) -> DecisionInput:
    plan = TripPlan(
        destination="SGN",
        travelers=travelers,
        days=days,
        return_date=return_date,
        budget_total=None,
    )
    return DecisionInput(trip_plan=plan)

@pytest.mark.parametrize(
    "scenario_name, travelers, days, return_date, flight_price, flight_scope, hotel_price, expected_flight_total, expected_hotel_total",
    [
        # 1. Solo 3-day one-way
        ("Solo 3-day one-way", 1, 3, None, 1_500_000, "one_way_per_traveler", 800_000, 1_500_000, 1_600_000),
        
        # 2. Solo 3-day round-trip
        ("Solo 3-day round-trip", 1, 3, "2026-10-03", 3_000_000, "round_trip_per_traveler", 800_000, 3_000_000, 1_600_000),
        
        # 3. Couple 3-day one-way
        ("Couple 3-day one-way", 2, 3, None, 1_500_000, "one_way_per_traveler", 800_000, 3_000_000, 1_600_000),
        
        # 4. Couple 5-day round-trip
        ("Couple 5-day round-trip", 2, 5, "2026-10-05", 2_500_000, "round_trip_per_traveler", 1_000_000, 5_000_000, 4_000_000),
        
        # 5. Group 4p 2-day one-way
        ("Group 4p 2-day", 4, 2, None, 1_200_000, "one_way_per_traveler", 600_000, 4_800_000, 600_000),
        
        # 6. One-way only on round-trip plan (should double the flight price)
        ("One-way only on round-trip", 2, 3, "2026-10-03", 1_500_000, "one_way_per_traveler", 800_000, 6_000_000, 1_600_000),
        
        # 7. Missing flights (no flight provided)
        ("Missing flights", 1, 3, None, None, None, 800_000, 0, 1_600_000),
        
        # 8. Missing hotels (no hotel provided)
        ("Missing hotels", 1, 3, None, 1_500_000, "one_way_per_traveler", None, 1_500_000, 0),
        
        # 9. Both missing
        ("Both missing", 1, 3, None, None, None, None, 0, 0),
    ]
)
def test_golden_costs(scenario_name, travelers, days, return_date, flight_price, flight_scope, hotel_price, expected_flight_total, expected_hotel_total):
    data = make_input(travelers, days, return_date)
    flight = make_flight(flight_price, flight_scope) if flight_price is not None else None
    h_price = hotel_price if hotel_price is not None else 0
    
    costs, assumptions = _cost_breakdown(data, flight, h_price)
    
    assert costs.flights == expected_flight_total, f"{scenario_name}: flights mismatch"
    assert costs.hotels == expected_hotel_total, f"{scenario_name}: hotels mismatch"
    
    expected_food = COST_RULES_V1["per_person_day"]["food"] * days * travelers
    assert costs.food == expected_food, f"{scenario_name}: food mismatch"
    
    expected_transport = COST_RULES_V1["per_day"]["local_transport"] * days
    assert costs.local_transport == expected_transport, f"{scenario_name}: transport mismatch"
    
    subtotal = costs.flights + costs.hotels + costs.food + costs.local_transport + costs.tickets
    expected_buffer = round(subtotal * COST_RULES_V1["buffer_rate"])
    assert costs.buffer == expected_buffer, f"{scenario_name}: buffer mismatch"
    
    if scenario_name == "One-way only on round-trip":
        assert len(assumptions) > 0
        assert "Giá vé khứ hồi được ước tính = giá một chiều × 2." in assumptions[0]

def test_budget_exceeded():
    from travel_ai_agent.decision.engine import build_decision
    plan = TripPlan(
        destination="SGN",
        travelers=2,
        days=5,
        return_date="2026-10-05",
        budget_total=10_000_000, # Very low budget for 5 days
        currency="VND",
        comfort_level="medium",
    )
    data = DecisionInput(trip_plan=plan)
    data.flight_options = [make_flight(2_500_000, "round_trip_per_traveler")]
    data.hotel_options = [make_hotel(1_500_000)]
    
    decision = build_decision(data)
    assert decision.budget_status == "over_budget"
