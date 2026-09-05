from travel_ai_agent.state.agent_state import AgentState


def route_by_intent(state: AgentState) -> str:
    """Sau classify_intent: travel/follow_up → planner, còn lại → chitchat."""
    intent = state.get("intent", "chitchat")
    if intent in ("travel", "follow_up"):
        return "planner"
    return "chitchat"


def route_after_planner(state: AgentState) -> str:
    """Sau planner: có plan → decision, thiếu info (plan None) → END."""
    if not state.get("plan"):
        return "__end__"
    return "decision"
