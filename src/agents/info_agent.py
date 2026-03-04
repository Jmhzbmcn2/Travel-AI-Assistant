"""
Info Agent — sub-agent tìm kiếm thông tin du lịch từ web.
Sử dụng create_react_agent với tool search_web (Tavily).
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools.tavily_search import search_web
from src.services.llm_service import get_llm

INFO_AGENT_PROMPT = """Bạn là trợ lý tìm kiếm thông tin du lịch.

Khi nhận được câu hỏi, hãy:
1. Dùng tool search_web để tìm thông tin liên quan
2. Tóm tắt kết quả bằng tiếng Việt, ngắn gọn và hữu ích
3. Trích dẫn nguồn nếu có

Trả lời bằng tiếng Việt."""

info_react_agent = create_react_agent(
    model=get_llm(),
    tools=[search_web],
    prompt=INFO_AGENT_PROMPT,
)


def info_agent_node(state: dict) -> dict:
    """Wrap info react agent thành graph node."""
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}
    goal = plan.get("goal", "")

    destination = constraints.get("destination_name", constraints.get("destination", ""))
    days = constraints.get("days", "")

    # Tạo search query từ plan
    if destination:
        task_msg = f"Tìm kiếm thông tin du lịch {destination}"
        if days:
            task_msg += f" {days} ngày"
        task_msg += ". Bao gồm: địa điểm nổi bật, ẩm thực, kinh nghiệm đi lại, lưu ý."
    else:
        task_msg = f"Tìm thông tin du lịch: {goal}"

    print(f"[INFO_AGENT] Task: {task_msg}")

    result = info_react_agent.invoke(
        {"messages": [HumanMessage(content=task_msg)]}
    )

    info_result = result["messages"][-1].content if result["messages"] else ""
    print(f"[INFO_AGENT] Result: {info_result[:100]}...")

    return {
        "search_info": info_result,
        "current_step": "info_agent",
        "completed_agents": state.get("completed_agents", []) + ["info_agent"],
    }
