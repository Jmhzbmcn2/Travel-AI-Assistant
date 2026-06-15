from __future__ import annotations

from typing import Any

from travel_ai_agent.config.constants import CITY_IATA
from travel_ai_agent.schemas import TripPlan


def _to_iata(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) == 3 and value.isupper():
        return value
    lowered = value.lower().strip()
    for city, code in CITY_IATA.items():
        if city == lowered or city in lowered or lowered in city:
            return code
    return value


def trip_plan_from_graph_plan(graph_plan: dict[str, Any]) -> TripPlan:
    constraints = graph_plan.get("constraints", {}) if isinstance(graph_plan, dict) else {}
    return TripPlan(
        origin=constraints.get("origin_name") or constraints.get("origin"),
        destination=constraints.get("destination_name") or constraints.get("destination"),
        departure_date=constraints.get("departure_date"),
        return_date=constraints.get("return_date"),
        days=constraints.get("days"),
        nights=constraints.get("nights"),
        travelers=constraints.get("travelers") or constraints.get("passengers") or 1,
        budget_total=constraints.get("budget_total") or constraints.get("budget"),
        budget_per_person=constraints.get("budget_per_person"),
        preferences=constraints.get("preferences", []),
        comfort_level=constraints.get("comfort_level"),
        trip_type=constraints.get("trip_type"),
        must_have=constraints.get("must_have", []),
        avoid=constraints.get("avoid", []),
        special_requirements=constraints.get("special_requirements", []),
        steps=graph_plan.get("steps", []),
        goal=graph_plan.get("goal", ""),
    )


def graph_plan_from_trip_plan(plan: TripPlan) -> dict[str, Any]:
    constraints = plan.model_dump(
        mode="json",
        exclude={"steps", "goal", "version"},
        exclude_none=True,
    )
    if plan.origin:
        constraints["origin_name"] = plan.origin
        constraints["origin"] = _to_iata(plan.origin)
    if plan.destination:
        constraints["destination_name"] = plan.destination
        constraints["destination"] = _to_iata(plan.destination)
    constraints["budget"] = plan.budget_total
    return {
        "steps": plan.steps,
        "constraints": constraints,
        "goal": plan.goal,
    }
