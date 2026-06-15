from travel_ai_agent.providers.gateway import fetch_destination_info


def info_agent_node(state: dict) -> dict:
    constraints = state.get("plan", {}).get("constraints", {})
    destination = constraints.get("destination_name") or constraints.get("destination", "")
    return {
        "search_info": fetch_destination_info(str(destination), constraints.get("days"), state.get("session_id")),
        "current_step": "info_agent",
        "completed_agents": state.get("completed_agents", []) + ["info_agent"],
    }
