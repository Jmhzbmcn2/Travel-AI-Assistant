"""Planner Agent: extract a typed TripPlan before provider calls.

- Đọc plan cũ trong state để LLM enrich, không reset giữa các turn.
- Sau khi tạo TripPlan, kiểm tra `missing_required_fields()`.
- Thiếu field → trả AIMessage hỏi lại (template tiếng Việt deterministic);
  lưu draft vào state["plan_draft"] để turn sau enrich tiếp.
- Đủ field → ghi TripPlan (model_dump) vào state["plan"].
"""
from datetime import datetime

from langchain_core.messages import AIMessage

from travel_ai_agent.config.prompts import PLANNER_SYSTEM_PROMPT, build_missing_fields_question
from travel_ai_agent.schemas import TripPlan
from travel_ai_agent.core.llm_service import get_llm


def _merge_plans(previous: TripPlan | None, new: TripPlan) -> TripPlan:
    """Merge plan mới vào plan cũ; giữ field cũ khi plan mới để trống.

    Field list: union + dedupe để không mất preferences/must_have/avoid user
    đã nêu các turn trước.
    """
    if previous is None:
        return new
    prev_dump = previous.model_dump()
    new_dump = new.model_dump()
    merged: dict = {}
    for key, new_value in new_dump.items():
        prev_value = prev_dump.get(key)
        if new_value in (None, "", [], {}):
            merged[key] = prev_value
        elif isinstance(new_value, list) and isinstance(prev_value, list):
            seen: set = set()
            combined: list = []
            for item in (*prev_value, *new_value):
                key_item = item if isinstance(item, (str, int, float, bool)) else repr(item)
                if key_item not in seen:
                    seen.add(key_item)
                    combined.append(item)
            merged[key] = combined
        else:
            merged[key] = new_value
    try:
        return TripPlan.model_validate(merged)
    except Exception:
        return new


def _trip_plan_from_state(state: dict) -> TripPlan | None:
    """Reconstruct TripPlan from prior turn's draft or confirmed plan."""
    for key in ("plan_draft", "plan"):
        raw = state.get(key)
        if raw:
            try:
                return TripPlan.model_validate(raw)
            except Exception:
                pass
    return None


def planner_node(state: dict) -> dict:
    user_message = state["messages"][-1].content
    recent_messages = state["messages"][-6:]
    previous_plan = _trip_plan_from_state(state)

    llm = get_llm().with_structured_output(TripPlan)
    try:
        plan = llm.invoke(
            [
                ("system", PLANNER_SYSTEM_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"))),
                *recent_messages,
            ]
        )
        plan.goal = plan.goal or user_message
    except Exception as exc:
        print(f"[PLANNER] Typed extraction failed: {exc}")
        plan = TripPlan(goal=user_message)

    plan = _merge_plans(previous_plan, plan)

    missing = plan.missing_required_fields()
    if missing:
        question = build_missing_fields_question(plan.model_dump(mode="json"), missing)
        print(f"[PLANNER] Missing required fields → asking user: {missing}")
        return {
            "messages": [AIMessage(content=question)],
            "plan": None,                       # route_after_planner → END
            "plan_draft": plan.model_dump(mode="json"),
            "current_step": "planner",
        }

    return {
        "plan": plan.model_dump(mode="json"),
        "plan_draft": None,
        "current_step": "planner",
    }
