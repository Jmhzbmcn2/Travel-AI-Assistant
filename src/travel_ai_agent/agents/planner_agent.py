"""Planner Agent: extract a typed TripPlan before provider calls.

Quy tắc (SPEC §10 Feature 2 + §14):
- Đọc plan cũ trong state để LLM enrich, không reset giữa các turn.
- Sau khi tạo TripPlan, kiểm tra `missing_required_fields()`.
- Nếu thiếu field → KHÔNG cho qua HITL: trả về AIMessage hỏi lại
  bằng template tiếng Việt deterministic; lưu draft plan vào state["plan_draft"]
  để turn sau enrich tiếp.
"""
from datetime import datetime

from langchain_core.messages import AIMessage

from travel_ai_agent.api.services.trip_service import (
    graph_plan_from_trip_plan,
    trip_plan_from_graph_plan,
)
from travel_ai_agent.config.prompts import (
    PLANNER_SYSTEM_PROMPT,
    build_missing_fields_question,
)
from travel_ai_agent.schemas import TripPlan
from travel_ai_agent.services.llm_service import get_llm


def _default_steps(plan: TripPlan) -> list[str]:
    if plan.steps:
        return plan.steps
    if plan.destination and (plan.days or plan.return_date):
        return ["find_flights", "find_hotels", "check_weather", "search_info"]
    return ["find_flights"] if plan.destination else []


def _merge_plans(previous: TripPlan | None, new: TripPlan) -> TripPlan:
    """Merge plan mới vào plan cũ; giữ field cũ khi plan mới để trống.

    Với field list, union + dedupe để không mất preferences/must_have/avoid
    user đã nêu các turn trước.
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
    draft = state.get("plan_draft")
    if draft:
        try:
            return TripPlan.model_validate(draft)
        except Exception:
            pass
    graph_plan = state.get("plan")
    if graph_plan:
        try:
            return trip_plan_from_graph_plan(graph_plan)
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
    plan.steps = _default_steps(plan)

    missing = plan.missing_required_fields()
    if missing:
        question = build_missing_fields_question(plan.model_dump(mode="json"), missing)
        print(f"[PLANNER] Missing required fields → asking user: {missing}")
        return {
            "messages": [AIMessage(content=question)],
            "plan": None,                       # route_after_planner → END (no HITL)
            "plan_draft": plan.model_dump(mode="json"),
            "current_step": "planner",
        }

    return {
        "plan": graph_plan_from_trip_plan(plan),
        "plan_draft": None,
        "current_step_index": 0,
        "current_step": "planner",
    }
