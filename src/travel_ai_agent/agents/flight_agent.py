from travel_ai_agent.providers.gateway import fetch_flights


def flight_agent_node(state: dict) -> dict:
    constraints = state.get("plan", {}).get("constraints", {})
    results = fetch_flights(
        str(constraints.get("origin", "")),
        str(constraints.get("destination", "")),
        str(constraints.get("departure_date", "")),
        str(constraints.get("return_date", "")),
        state.get("session_id"),
    )
    return {
        "flight_results": sorted(results, key=lambda item: item.get("price", 0))[:10],
        "current_step": "flight_agent",
        "completed_agents": state.get("completed_agents", []) + ["flight_agent"],
    }
