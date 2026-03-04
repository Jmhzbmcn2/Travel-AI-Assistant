"""
Hotel Agent — sub-agent chuyên tìm khách sạn.
Sử dụng create_react_agent với tool search_hotels.
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools.hotel_search import search_hotels
from src.services.llm_service import get_llm
from config.prompts import HOTEL_AGENT_PROMPT
from datetime import datetime, timedelta
import json

hotel_react_agent = create_react_agent(
    model=get_llm(),
    tools=[search_hotels],
    prompt=HOTEL_AGENT_PROMPT,
)


def hotel_agent_node(state: dict) -> dict:
    """Wrap hotel react agent thành graph node."""
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}

    # Dùng destination_name (tên thật) thay vì destination (IATA code)
    destination = constraints.get("destination_name", constraints.get("destination", "N/A"))
    check_in = constraints.get("departure_date", "N/A")
    days = constraints.get("days", 2)

    # Tính check_out từ check_in + days
    check_out = check_in
    try:
        dep = datetime.strptime(check_in, "%Y-%m-%d")
        check_out = (dep + timedelta(days=days)).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    task_msg = (
        f"Tìm khách sạn tại {destination} "
        f"từ ngày {check_in} đến {check_out}."
    )
    if constraints.get("budget"):
        task_msg += f" Budget tối đa: {constraints['budget']} VND cho toàn bộ trip."

    print(f"[HOTEL_AGENT] Task: {task_msg}")

    result = hotel_react_agent.invoke(
        {"messages": [HumanMessage(content=task_msg)]}
    )

    # Trích xuất hotel_results
    hotel_results = []
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and "hotels" in data:
                    hotel_results = data["hotels"]
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    if hotel_results:
        hotel_results = sorted(hotel_results, key=lambda x: x.get("price", 0))[:10]

    print(f"[HOTEL_AGENT] Found {len(hotel_results)} hotels")

    return {
        "hotel_results": hotel_results,
        "current_step": "hotel_agent",
        "completed_agents": state.get("completed_agents", []) + ["hotel_agent"],
    }
