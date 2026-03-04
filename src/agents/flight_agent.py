"""
Flight Agent — sub-agent chuyên tìm vé máy bay.
Sử dụng create_react_agent với tool search_flights.
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools.flight_search import search_flights
from src.services.llm_service import get_llm
from config.prompts import FLIGHT_AGENT_PROMPT
import json

# Tạo react agent với tool search_flights
flight_react_agent = create_react_agent(
    model=get_llm(),
    tools=[search_flights],
    prompt=FLIGHT_AGENT_PROMPT,
)


def flight_agent_node(state: dict) -> dict:
    """Wrap flight react agent thành graph node."""
    # Xây dựng message cho agent từ plan constraints
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}

    task_msg = (
        f"Tìm vé máy bay từ {constraints.get('origin', 'N/A')} "
        f"đến {constraints.get('destination', 'N/A')} "
        f"ngày {constraints.get('departure_date', 'N/A')}."
    )
    if constraints.get("budget"):
        task_msg += f" Budget tối đa: {constraints['budget']} VND."

    print(f"[FLIGHT_AGENT] Task: {task_msg}")

    result = flight_react_agent.invoke(
        {"messages": [HumanMessage(content=task_msg)]}
    )

    # Trích xuất flight_results từ kết quả agent
    flight_results = []
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and "flights" in data:
                    flight_results = data["flights"]
                    break
            except (json.JSONDecodeError, TypeError):
                continue

    # Sắp xếp theo giá
    if flight_results:
        flight_results = sorted(flight_results, key=lambda x: x.get("price", 0))[:10]

    # Lấy message cuối cùng của agent làm summary
    agent_summary = result["messages"][-1].content if result["messages"] else ""
    print(f"[FLIGHT_AGENT] Found {len(flight_results)} flights")

    return {
        "flight_results": flight_results,
        "current_step": "flight_agent",
        "completed_agents": state.get("completed_agents", []) + ["flight_agent"],
    }
