from __future__ import annotations
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from langgraph.graph.state import CompiledStateGraph

from travel_ai_agent.api.dependencies import get_graph, get_session_store
from travel_ai_agent.api.schemas.trip import TripPlanPatch, TripWorkspaceResponse, TripActionRequest, TripActionResponse
from travel_ai_agent.api.services.chat_service import get_graph_config
from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.api.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/trips", tags=["Trips"])


def _workspace(sid: str, store: SessionStore, owner_id: str) -> TripWorkspaceResponse:
    plan = store.get_trip(sid, owner_id)
    decision = store.get_decision(sid, owner_id)
    status = store.get_trip_status(sid, owner_id) or ("decided" if decision else "draft" if plan else "empty")
    return TripWorkspaceResponse(
        session_id=sid,
        plan=plan,
        decision=decision,
        status=status,
        missing_fields=plan.missing_required_fields() if plan else [],
    )


@router.get("/{session_id}", response_model=TripWorkspaceResponse)
async def get_trip(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> TripWorkspaceResponse:
    return _workspace(session_id, store, owner_id)


@router.patch("/{session_id}/plan", response_model=TripWorkspaceResponse)
async def patch_trip_plan(
    session_id: str,
    patch: TripPlanPatch,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
    owner_id: str = Depends(get_current_user),
) -> TripWorkspaceResponse:
    try:
        plan = store.patch_trip(session_id, owner_id, patch.model_dump(exclude_none=True))
        store.add_usage_event(session_id, owner_id, "plan_edited", "user_action", {})
    except KeyError:
        raise HTTPException(status_code=404, detail="Trip not found")
    await graph.aupdate_state(get_graph_config(session_id), {"plan": plan.model_dump(mode="json")})
    return _workspace(session_id, store, owner_id)


@router.get("/{session_id}/decision", response_model=TripWorkspaceResponse)
async def get_decision(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> TripWorkspaceResponse:
    return _workspace(session_id, store, owner_id)


from pydantic import BaseModel
from travel_ai_agent.schemas.domain import AnalyticsEventType

class DecisionFeedback(BaseModel):
    action: Literal["accepted", "rejected"]
    reason: str | None = None

@router.post("/{session_id}/decision/feedback")
async def decision_feedback(
    session_id: str,
    feedback: DecisionFeedback,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> dict[str, str]:
    decision = store.get_decision(session_id, owner_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    event_type: AnalyticsEventType = "recommendation_accepted" if feedback.action == "accepted" else "recommendation_rejected"
    store.add_usage_event(session_id, owner_id, event_type, "user_feedback", {"reason": feedback.reason})
    return {"status": "recorded"}


@router.post("/{session_id}/actions", response_model=TripActionResponse)
async def perform_trip_action(
    session_id: str,
    action_req: TripActionRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
    owner_id: str = Depends(get_current_user),
) -> TripActionResponse:
    plan = store.get_trip(session_id, owner_id)
    decision = store.get_decision(session_id, owner_id)
    if not plan or not decision:
        raise HTTPException(status_code=404, detail="Trip or decision not found")

    from travel_ai_agent.decision.actions import execute_trip_action
    
    try:
        # Fetch graph state to get options
        state = await graph.aget_state(get_graph_config(session_id))
        values = state.values
        
        from travel_ai_agent.schemas.domain import DecisionInput
        data_input = DecisionInput(
            trip_plan=plan,
            flight_options=values.get("flight_options", []),
            hotel_options=values.get("hotel_options", []),
            place_options=values.get("place_options", []),
            route_segments=values.get("route_segments", []),
            weather_forecasts=values.get("weather_forecasts", []),
            review_summaries=values.get("review_summaries", []),
            itinerary=decision.itinerary,
            cost_rules=values.get("cost_rules", {})
        )

        result = await execute_trip_action(action_req, data_input, decision, session_id)
        if result.decision:
            store.save_decision(session_id, owner_id, result.decision)
        store.add_usage_event(
            session_id, owner_id, "action_executed", "user_action", 
            {"action": action_req.action, "target_day": action_req.target_day}
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{session_id}/export.md", response_class=PlainTextResponse)
async def export_trip(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> str:
    plan = store.get_trip(session_id, owner_id)
    decision = store.get_decision(session_id, owner_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Trip not found")
    lines = [
        f"# Chuyến đi {plan.destination or ''}",
        "",
        f"- Số ngày: {plan.days or 'Chưa xác định'}",
        f"- Số người: {plan.travelers}",
        f"- Ngân sách: {plan.budget_total or 'Chưa xác định'} {plan.currency}",
    ]
    if decision:
        lines.extend([
            "",
            "## Khuyến nghị",
            f"- Phương án: {decision.recommended_option}",
            f"- Tổng chi phí ước tính: {decision.total_cost:,.0f} {plan.currency}",
            f"- Trạng thái ngân sách: {decision.budget_status}",
            "",
            "## Rủi ro và giả định",
        ])
        lines.extend(f"- {risk.message}" for risk in decision.risks)
        lines.extend(f"- {assumption}" for assumption in decision.assumptions)
    return "\n".join(lines)
