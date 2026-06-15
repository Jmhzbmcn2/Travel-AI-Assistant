"""Response Agent — giải thích DecisionOutput cho user (SPEC §14).

Quy tắc:
- KHÔNG nhận raw provider payload (flight_results, hotel_results, weather_info,
  search_info JSON web). Chỉ nhận:
    - TripPlan (normalized)
    - DecisionOutput (authoritative cost/score/risk/itinerary)
    - notes ngắn đã được trích lọc (string thuần)
- LLM chỉ giải thích DecisionOutput, KHÔNG sinh giá, thời gian bay, hoặc đánh
  giá mới.
"""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_ai_agent.api.services.trip_service import trip_plan_from_graph_plan
from travel_ai_agent.config.prompts import RESPONSE_AGENT_PROMPT
from travel_ai_agent.schemas import DecisionOutput, TripPlan
from travel_ai_agent.services.llm_service import get_llm


def _safe_trip_plan(state: dict) -> TripPlan | None:
    plan_dict = state.get("plan")
    if not plan_dict:
        return None
    try:
        return trip_plan_from_graph_plan(plan_dict)
    except Exception:
        return None


def _safe_decision(state: dict) -> DecisionOutput | None:
    raw = state.get("decision_output")
    if not raw:
        return None
    try:
        return DecisionOutput.model_validate(raw)
    except Exception:
        return None


def _summarize_notes(state: dict) -> list[str]:
    """Trích ghi chú ngôn ngữ tự nhiên ngắn, KHÔNG truyền raw JSON."""
    notes: list[str] = []
    search_info = state.get("search_info")
    if isinstance(search_info, str) and search_info.strip():
        joined = " ".join(line.strip() for line in search_info.splitlines() if line.strip())
        if joined:
            notes.append("Ghi chú điểm đến: " + joined[:600])
    weather_info = state.get("weather_info")
    if isinstance(weather_info, str) and weather_info.strip() and not weather_info.lstrip().startswith("{"):
        notes.append("Ghi chú thời tiết: " + weather_info.strip()[:200])
    return notes


def _format_context(trip_plan: TripPlan | None, decision: DecisionOutput | None, notes: list[str]) -> str:
    parts: list[str] = []
    if trip_plan:
        parts.append(
            "## TRIP_PLAN (normalized)\n"
            + json.dumps(trip_plan.model_dump(mode="json"), ensure_ascii=False, indent=2)
        )
    else:
        parts.append("## TRIP_PLAN: (chưa có)")

    if decision:
        parts.append(
            "## DECISION_OUTPUT (authoritative — KHÔNG sinh số mới ngoài payload này)\n"
            + json.dumps(decision.model_dump(mode="json"), ensure_ascii=False, indent=2)
        )
    else:
        parts.append("## DECISION_OUTPUT: (chưa có — chỉ tóm tắt trip plan, không bịa số)")

    if notes:
        parts.append("## NOTES\n" + "\n".join(f"- {note}" for note in notes))

    return "\n\n".join(parts)


def response_agent_node(state: dict) -> dict:
    trip_plan = _safe_trip_plan(state)
    decision = _safe_decision(state)
    notes = _summarize_notes(state)

    context = _format_context(trip_plan, decision, notes)
    print(
        f"[RESPONSE_AGENT] Generating final response "
        f"(plan={'yes' if trip_plan else 'no'}, decision={'yes' if decision else 'no'}, notes={len(notes)})"
    )

    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=RESPONSE_AGENT_PROMPT),
            HumanMessage(content=context),
        ]
    )

    return {
        "messages": [AIMessage(content=response.content)],
        "current_step": "respond",
    }
