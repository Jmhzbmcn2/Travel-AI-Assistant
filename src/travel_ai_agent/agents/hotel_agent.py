from travel_ai_agent.providers.gateway import fetch_hotels


def hotel_agent_node(state: dict) -> dict:
    constraints = state.get("plan", {}).get("constraints", {})
    destination = constraints.get("destination_name") or constraints.get("destination", "")
    days = int(constraints.get("days", 2))
    nights = max(1, days - 1)
    results = fetch_hotels(str(destination), str(constraints.get("departure_date", "")), nights, state.get("session_id"))
    return {
        "hotel_results": sorted(results, key=lambda item: item.get("price", 0))[:10],
        "current_step": "hotel_agent",
        "completed_agents": state.get("completed_agents", []) + ["hotel_agent"],
    }
