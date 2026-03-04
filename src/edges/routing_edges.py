from src.state.agent_state import AgentState


def route_by_intent(state: AgentState) -> str:
    """Sau classify_intent: travel → planner, follow_up → follow_up, chitchat → chitchat."""
    intent = state.get("intent", "chitchat")
    if intent == "travel":
        return "planner"
    if intent == "follow_up":
        return "follow_up"
    return "chitchat"


def should_search_or_ask(state: AgentState) -> str:
    """Sau parser: đủ info → search, thiếu → hỏi lại."""
    if state.get("missing_fields"):
        return "ask_user"
    return "search"