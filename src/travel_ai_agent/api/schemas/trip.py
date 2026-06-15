from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from travel_ai_agent.schemas import DecisionOutput, TripPlan


class TripPlanPatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    days: int | None = None
    nights: int | None = None
    travelers: int | None = None
    budget_total: float | None = None
    budget_per_person: float | None = None
    currency: str | None = None
    comfort_level: str | None = None
    priority: str | None = None
    preferences: list[str] | None = None
    constraints: dict | None = None
    trip_type: str | None = None
    must_have: list[str] | None = None
    avoid: list[str] | None = None
    special_requirements: list[str] | None = None
    steps: list[str] | None = None
    goal: str | None = None


class TripWorkspaceResponse(BaseModel):
    session_id: str
    plan: TripPlan | None = None
    decision: DecisionOutput | None = None
    status: str = "empty"
    missing_fields: list[str] = []
    metadata: dict[str, Any] = {}

class TripActionRequest(BaseModel):
    action: Literal["optimize_day", "replace_place"]
    target_day: int | None = None
    target_place_id: str | None = None

class TripActionResponse(BaseModel):
    status: str
    message: str | None = None
    before_summary: dict[str, Any] | None = None
    after_summary: dict[str, Any] | None = None
    decision: DecisionOutput | None = None
