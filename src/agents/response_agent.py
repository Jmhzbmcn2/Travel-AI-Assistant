"""
Response Agent — tổng hợp tất cả kết quả và trả lời user.
"""
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from src.services.llm_service import get_llm
from config.prompts import RESPONSE_AGENT_PROMPT
import json


def response_agent_node(state: dict) -> dict:
    """Tổng hợp tất cả kết quả và tạo response cuối cùng."""
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}
    flight_results = state.get("flight_results", [])
    hotel_results = state.get("hotel_results", [])
    weather_info = state.get("weather_info", "")

    # Xây dựng context cho LLM
    context_parts = [f"**Mục tiêu**: {plan.get('goal', 'N/A')}"]

    if constraints:
        context_parts.append(f"**Thông tin chuyến đi**: {json.dumps(constraints, ensure_ascii=False)}")

    if flight_results:
        # Chỉ gửi top 5
        top_flights = flight_results[:5]
        context_parts.append(
            f"**Kết quả vé máy bay** ({len(flight_results)} vé):\n"
            f"{json.dumps(top_flights, ensure_ascii=False, indent=2)}"
        )
    else:
        context_parts.append("**Vé máy bay**: Không tìm thấy kết quả")

    if hotel_results:
        top_hotels = hotel_results[:5]
        context_parts.append(
            f"**Kết quả khách sạn** ({len(hotel_results)} KS):\n"
            f"{json.dumps(top_hotels, ensure_ascii=False, indent=2)}"
        )

    if weather_info:
        context_parts.append(f"**Thời tiết**: {weather_info}")

    search_info = state.get("search_info", "")
    if search_info:
        context_parts.append(f"**Thông tin du lịch (từ web)**: {search_info}")

    if constraints.get("budget"):
        context_parts.append(f"**Budget**: {constraints['budget']} VND")

    context = "\n\n".join(context_parts)

    print(f"[RESPONSE_AGENT] Generating final response...")

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=RESPONSE_AGENT_PROMPT),
        HumanMessage(content=context),
    ])

    return {
        "messages": [AIMessage(content=response.content)],
        "current_step": "respond",
    }
