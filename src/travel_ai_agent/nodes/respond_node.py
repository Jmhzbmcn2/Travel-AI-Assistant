"""Response node — câu trả lời chat ngắn gọn bằng template deterministic.

Không gọi LLM. Chỉ đọc TripPlan + DecisionOutput trong state. Chi tiết đầy đủ
(lịch trình, chi phí, rủi ro) nằm ở workspace bên phải — chat chỉ nêu kết luận.
"""
from __future__ import annotations

from langchain_core.messages import AIMessage

from travel_ai_agent.schemas import DecisionOutput, TripPlan

_BUDGET_LABEL = {
    "under_budget": "dưới ngân sách",
    "near_limit": "sát ngân sách",
    "slightly_over": "hơi vượt ngân sách",
    "over_budget": "vượt ngân sách",
    "unknown": "chưa rõ ngân sách",
}
_OPTION_LABEL = {"cheapest": "Tiết kiệm", "balanced": "Cân bằng", "comfortable": "Thoải mái"}


def _vnd(amount: float | int | None) -> str:
    if amount is None:
        return "chưa xác định"
    return f"{round(amount):,}₫".replace(",", ".")


def _safe(model_cls, raw):
    if not raw:
        return None
    try:
        return model_cls.model_validate(raw)
    except Exception:
        return None


def _plan_summary(plan: TripPlan) -> str:
    bits = []
    if plan.destination:
        bits.append(f"đi {plan.destination}")
    if plan.days:
        bits.append(f"{plan.days} ngày")
    if plan.travelers and plan.travelers > 1:
        bits.append(f"{plan.travelers} người")
    if plan.budget_total:
        bits.append(f"ngân sách {_vnd(plan.budget_total)}")
    return "Chuyến đi " + ", ".join(bits) + "." if bits else "Chưa đủ thông tin để lên kế hoạch."


def _build_markdown(plan: TripPlan, decision: DecisionOutput | None) -> str:
    if decision is None:
        return _plan_summary(plan)

    budget = _BUDGET_LABEL.get(decision.budget_status, decision.budget_status)
    high_risks = sum(1 for r in decision.risks if r.severity == "high")
    blocks: list[str] = []

    if decision.decision_status == "recommended" and decision.recommended_option:
        opt = _OPTION_LABEL.get(decision.recommended_option, decision.recommended_option)
        blocks.append(
            f"**Đi được với {_vnd(decision.total_cost)}** theo phương án **{opt}** — {budget}."
        )
        for reason in decision.why_recommended[:2]:
            blocks.append(f"- {reason}")
        if high_risks:
            blocks.append(f"Còn {high_risks} điểm cần xử lý trước khi đặt chỗ — xem tab **Rủi ro** bên phải.")
        else:
            blocks.append("Lịch trình, chi phí và rủi ro chi tiết ở bảng bên phải.")
    elif decision.decision_status == "needs_revision":
        blocks.append(f"**Khả thi có điều kiện** — khoảng {_vnd(decision.total_cost)}, {budget}.")
        for r in decision.blocking_reasons[:2]:
            blocks.append(f"- {r}")
        blocks.append("Xem tab **Rủi ro** bên phải để xử lý, rồi mình chốt lại.")
    else:
        blocks.append("**Chưa đủ dữ liệu đã xác minh để đưa khuyến nghị.**")
        for r in decision.blocking_reasons[:3]:
            blocks.append(f"- {r}")
        blocks.append("Bổ sung thông tin còn thiếu ở bảng bên phải để mình thử lại.")

    return "\n".join(blocks)


def response_agent_node(state: dict) -> dict:
    plan = _safe(TripPlan, state.get("plan")) or TripPlan()
    decision = _safe(DecisionOutput, state.get("decision_output"))
    return {
        "messages": [AIMessage(content=_build_markdown(plan, decision))],
        "current_step": "respond",
    }
