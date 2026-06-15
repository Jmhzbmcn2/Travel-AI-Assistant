from __future__ import annotations

from travel_ai_agent.api.services.session_store import SessionStore


REQUEST_LIMIT_PER_SESSION = 60
TOOL_LIMITS = {
    "flight_search": 3,
    "hotel_search": 3,
    "places_search": 2,
    "weather": 2,
    "reviews": 10,
    "routes": 20,
}


def request_allowed(store: SessionStore, session_id: str) -> bool:
    owner_id = store.get_session_owner(session_id) or "system"
    return store.usage_count(session_id, owner_id, "request") < REQUEST_LIMIT_PER_SESSION


def tool_allowed(store: SessionStore, session_id: str, tool_name: str) -> bool:
    owner_id = store.get_session_owner(session_id) or "system"
    return store.usage_count(session_id, owner_id, "tool_call", tool_name) < TOOL_LIMITS.get(tool_name, 3)


def record_tool_call(store: SessionStore, session_id: str, tool_name: str, **metadata) -> None:
    if not tool_allowed(store, session_id, tool_name):
        owner_id = store.get_session_owner(session_id) or "system"
        store.add_usage_event(session_id, owner_id, "blocked", tool_name, {"reason": "tool_budget_exceeded"})
        raise RuntimeError(f"Tool budget exceeded for {tool_name}")
    owner_id = store.get_session_owner(session_id) or "system"
    store.add_usage_event(session_id, owner_id, "tool_call", tool_name, metadata)
