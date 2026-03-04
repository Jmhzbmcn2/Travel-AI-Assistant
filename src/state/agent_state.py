"""
Agent State — the central data structure shared across all graph nodes.
"""
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class UserRequest(TypedDict, total=False):
    """Parsed travel request from the user."""
    origin: str | None
    destination: str | None
    departure_date: str | None
    return_date: str | None
    budget: float | None
    currency: str
    passengers: int
    trip_type: str
    hotel_needed: bool


class AgentState(TypedDict, total=False):
    """
    Main state flowing through the LangGraph.

    Pipeline fields (kept for backward-compat):
      messages, user_request, search_type, flight_results, hotel_results,
      ranked_deals, missing_fields, current_step, intent, error

    Multi-agent fields (Upgrade #1):
      plan, current_step_index, next_agent, reasoning,
      weather_info, reflection_issues, suggested_fixes,
      needs_revision, revision_count
    """
    # ── Core ──────────────────────────────────────────
    messages: Annotated[list, add_messages]
    intent: str
    current_step: str
    error: str | None

    # ── Pipeline (legacy) ─────────────────────────────
    user_request: UserRequest
    search_type: str
    flight_results: list[dict[str, Any]]
    hotel_results: list[dict[str, Any]]
    ranked_deals: str
    missing_fields: list[str]

    # ── Multi-Agent: Planner ──────────────────────────
    plan: dict                  # {"steps": [...], "constraints": {...}, "goal": "..."}
    current_step_index: int     # which step in the plan we're on

    # ── Multi-Agent: Supervisor ───────────────────────
    next_agent: str             # which agent the supervisor chose
    reasoning: str              # why the supervisor chose that agent
    completed_agents: list[str] # agents that have already been called

    # ── Multi-Agent: Agent results ────────────────────
    weather_info: str           # weather agent output
    search_info: str            # info agent output (Tavily search)

    # ── Multi-Agent: Reflection ───────────────────────
    reflection_issues: list[str]
    suggested_fixes: list[str]
    needs_revision: bool
    revision_count: int         # cap at MAX_REVISIONS to prevent infinite loop
    plan_modifications: dict    # concrete constraint changes from reflection
    agents_to_retry: list[str]  # which agents to re-run after replan