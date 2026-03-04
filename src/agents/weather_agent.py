"""
Weather Agent — sub-agent chuyên xem thời tiết.
Sử dụng create_react_agent với tool get_weather.
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools.weather_search import get_weather
from src.services.llm_service import get_llm
from config.prompts import WEATHER_AGENT_PROMPT

weather_react_agent = create_react_agent(
    model=get_llm(),
    tools=[get_weather],
    prompt=WEATHER_AGENT_PROMPT,
)


def weather_agent_node(state: dict) -> dict:
    """Wrap weather react agent thành graph node."""
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}
    # Dùng destination_name (tên thật) thay vì destination (IATA code)
    destination = constraints.get("destination_name", constraints.get("destination", "N/A"))

    task_msg = f"Tra cứu thời tiết tại {destination}."

    print(f"[WEATHER_AGENT] Task: {task_msg}")

    result = weather_react_agent.invoke(
        {"messages": [HumanMessage(content=task_msg)]}
    )

    weather_info = result["messages"][-1].content if result["messages"] else ""
    print(f"[WEATHER_AGENT] Result: {weather_info[:100]}...")

    return {
        "weather_info": weather_info,
        "current_step": "weather_agent",
        "completed_agents": state.get("completed_agents", []) + ["weather_agent"],
    }
