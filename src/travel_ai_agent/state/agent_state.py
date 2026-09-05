"""
Agent State — the central data structure shared across all graph nodes.

Flow: classify_intent -> {chitchat | planner} -> {END | decision} -> respond -> END
"""
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # ── Core ──────────────────────────────────────────
    messages: Annotated[list, add_messages]
    intent: str
    current_step: str
    error: str | None
    session_id: str

    # ── Planner ───────────────────────────────────────
    plan: dict          # TripPlan.model_dump(mode="json")
    plan_draft: dict     # Draft TripPlan retained across turns when required fields are missing

    # ── Decision node output ──────────────────────────
    decision_output: dict                    # DecisionOutput.model_dump(mode="json")
    flight_options: list[dict[str, Any]]      # normalized, kept for trip actions
    hotel_options: list[dict[str, Any]]
    place_options: list[dict[str, Any]]
    route_segments: list[dict[str, Any]]
    weather_forecasts: list[dict[str, Any]]
    review_summaries: list[dict[str, Any]]
