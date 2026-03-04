"""
Reflection Node — kiểm tra chất lượng kết quả tổng thể.
Phát hiện vấn đề (budget vượt, thiếu info, inconsistency) và đề xuất sửa.
Hỗ trợ Dynamic Replanning: đề xuất plan_modifications cụ thể.
"""
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.services.llm_service import get_llm
from config.prompts import REFLECTION_SYSTEM_PROMPT
import json

MAX_REVISIONS = 3


class ReflectionResult(BaseModel):
    """Kết quả kiểm tra chất lượng."""
    is_satisfactory: bool = Field(description="Kết quả có đạt yêu cầu không")
    issues: list[str] = Field(
        default_factory=list,
        description="Danh sách vấn đề phát hiện"
    )
    suggested_fixes: list[str] = Field(
        default_factory=list,
        description="Đề xuất cách sửa bằng text"
    )
    plan_modifications: dict = Field(
        default_factory=dict,
        description="Thay đổi constraints cụ thể. VD: {\"days\": 2}"
    )
    agents_to_retry: list[str] = Field(
        default_factory=list,
        description="Agents cần chạy lại. VD: [\"hotel_agent\"]"
    )


def reflection_node(state: dict) -> dict:
    """Kiểm tra kết quả tổng thể, phát hiện vấn đề."""
    plan = state.get("plan", {})
    constraints = plan.get("constraints", {}) if isinstance(plan, dict) else {}
    steps = plan.get("steps", []) if isinstance(plan, dict) else []
    flight_results = state.get("flight_results", [])
    hotel_results = state.get("hotel_results", [])
    weather_info = state.get("weather_info", "")
    revision_count = state.get("revision_count", 0)

    # Nếu đã revision quá nhiều lần → force pass
    if revision_count >= MAX_REVISIONS:
        print(f"[REFLECTION] Max revisions ({MAX_REVISIONS}) reached → auto-pass")
        return {
            "needs_revision": False,
            "current_step": "reflect",
        }

    # Tạo summary cho reflection
    summary = (
        f"Plan goal: {plan.get('goal', 'N/A')}\n"
        f"Plan steps: {steps}\n"
        f"Current constraints: {json.dumps(constraints, ensure_ascii=False)}\n"
        f"Budget constraint: {constraints.get('budget', 'Không giới hạn')}\n"
        f"Days: {constraints.get('days', 'N/A')}\n"
        f"Flights found: {len(flight_results)}\n"
        f"Hotels found: {len(hotel_results)}\n"
        f"Weather info: {'Có' if weather_info else 'Chưa có'}\n"
    )

    if flight_results:
        cheapest = min(flight_results, key=lambda x: x.get("price", 0))
        summary += f"Cheapest flight: {cheapest.get('price', 'N/A')} VND\n"
    if hotel_results:
        cheapest_hotel = min(hotel_results, key=lambda x: x.get("price", 0))
        summary += f"Cheapest hotel: {cheapest_hotel.get('price', 'N/A')} VND/đêm\n"

    if flight_results and hotel_results:
        min_flight = min(f.get("price", 0) for f in flight_results)
        min_hotel = min(h.get("price", 0) for h in hotel_results)
        days = constraints.get("days", 1)
        total = min_flight + (min_hotel * days)
        summary += f"Estimated total: {total} VND (cheapest flight + cheapest hotel × {days} đêm)\n"

    print(f"[REFLECTION] Checking:\n{summary}")

    llm = get_llm().with_structured_output(ReflectionResult)

    try:
        result = llm.invoke([
            SystemMessage(content=REFLECTION_SYSTEM_PROMPT),
            HumanMessage(content=summary),
        ])

        print(f"[REFLECTION] Satisfactory: {result.is_satisfactory}")
        if result.issues:
            print(f"[REFLECTION] Issues: {result.issues}")
        if result.plan_modifications:
            print(f"[REFLECTION] Plan mods: {result.plan_modifications}")

        if not result.is_satisfactory:
            return {
                "reflection_issues": result.issues,
                "suggested_fixes": result.suggested_fixes,
                "plan_modifications": result.plan_modifications,
                "agents_to_retry": result.agents_to_retry,
                "needs_revision": True,
                "current_step": "reflect",
                "completed_agents": state.get("completed_agents", []) + ["reflect"],
            }

        return {
            "needs_revision": False,
            "reflection_issues": [],
            "suggested_fixes": [],
            "plan_modifications": {},
            "agents_to_retry": [],
            "current_step": "reflect",
            "completed_agents": state.get("completed_agents", []) + ["reflect"],
        }

    except Exception as e:
        print(f"[REFLECTION] Error: {e} → auto-pass")
        return {
            "needs_revision": False,
            "current_step": "reflect",
            "completed_agents": state.get("completed_agents", []) + ["reflect"],
        }


def route_after_reflection(state: dict) -> str:
    """Route sau reflection: cần sửa → supervisor, OK → respond."""
    if state.get("needs_revision"):
        return "supervisor"
    return "respond"
