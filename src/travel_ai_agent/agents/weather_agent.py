from travel_ai_agent.providers.gateway import fetch_weather


def weather_agent_node(state: dict) -> dict:
    constraints = state.get("plan", {}).get("constraints", {})
    destination = constraints.get("destination_name") or constraints.get("destination", "")
    return {
        "weather_info": fetch_weather(str(destination), state.get("session_id")),
        "current_step": "weather_agent",
        "completed_agents": state.get("completed_agents", []) + ["weather_agent"],
    }
