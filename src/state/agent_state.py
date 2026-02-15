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
    - messages: conversation history (auto-appended via add_messages)
    - user_request: parsed travel request
    - search_type: what to search — "flights", "hotels", or "both"
    - flight_results: list of flight options from API
    - hotel_results: list of hotel options from API
    - ranked_deals: LLM analysis & ranking of results
    - missing_fields: fields still needed from the user
    - current_step: current node in the flow
    - error: error message if something goes wrong
    """
    messages: Annotated[list, add_messages]
    user_request: UserRequest
    search_type: str
    flight_results: list[dict[str, Any]]
    hotel_results: list[dict[str, Any]]
    ranked_deals: str
    missing_fields: list[str]
    current_step: str
    intent: str
    error: str | None