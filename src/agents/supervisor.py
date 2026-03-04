"""
Supervisor Agent — điều phối các sub-agents.
Nhìn vào plan + kết quả hiện tại → quyết định gọi agent nào tiếp.
Hỗ trợ Dynamic Replanning: apply plan modifications và re-run agents.
"""
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from src.services.llm_service import get_llm
from config.prompts import SUPERVISOR_SYSTEM_PROMPT
import json
import copy

# Mapping: plan step name → agent node name
STEP_TO_AGENT = {
    "find_flights": "flight_agent",
    "find_hotels": "hotel_agent",
    "check_weather": "weather_agent",
    "search_info": "info_agent",
}


class SupervisorDecision(BaseModel):
    """Quyết định của Supervisor: gọi agent nào tiếp."""
    next_agent: Literal[
        "flight_agent", "hotel_agent", "weather_agent", "info_agent",
        "reflect", "respond"
    ] = Field(description="Agent tiếp theo cần gọi")
    reasoning: str = Field(description="Lý do chọn agent này")


def supervisor_node(state: dict) -> dict:
    """Supervisor nhìn vào plan + kết quả hiện tại → quyết định bước tiếp.

    Sử dụng logic DETERMINISTIC trước, chỉ gọi LLM khi cần reflection/revision.
    Hỗ trợ Dynamic Replanning: khi revision, apply plan_modifications + reset agents.
    """
    plan = state.get("plan", {})
    steps = plan.get("steps", []) if isinstance(plan, dict) else []
    needs_revision = state.get("needs_revision", False)
    revision_count = state.get("revision_count", 0)
    completed_agents = state.get("completed_agents", [])

    print(f"[SUPERVISOR] Steps: {steps}, Completed: {completed_agents}, "
          f"Revision: {needs_revision}, Count: {revision_count}/3")

    # ── Nếu đã revision quá 3 lần → force respond ────
    if revision_count >= 3:
        print("[SUPERVISOR] Max revisions reached → respond")
        return {
            "next_agent": "respond",
            "reasoning": "Đã thử sửa 3 lần, trả kết quả tốt nhất hiện có.",
            "current_step": "supervisor",
        }

    # ── Nếu cần revision → DYNAMIC REPLAN ──
    if needs_revision:
        return _handle_replan(state, plan, completed_agents, revision_count)

    # ── DETERMINISTIC: tìm step tiếp theo chưa hoàn thành ────
    for step in steps:
        agent = STEP_TO_AGENT.get(step)
        if agent and agent not in completed_agents:
            print(f"[SUPERVISOR] Next step: {step} → {agent}")
            return {
                "next_agent": agent,
                "reasoning": f"Thực hiện bước '{step}' trong plan.",
                "current_step": "supervisor",
            }

    # ── Tất cả steps đã xong → reflect ────
    if "reflect" not in completed_agents:
        print("[SUPERVISOR] All steps done → reflect")
        return {
            "next_agent": "reflect",
            "reasoning": "Tất cả bước đã xong, kiểm tra chất lượng.",
            "current_step": "supervisor",
        }

    # ── Reflection cũng xong rồi → respond ────
    print("[SUPERVISOR] All done → respond")
    return {
        "next_agent": "respond",
        "reasoning": "Tất cả bước và reflection đã xong.",
        "current_step": "supervisor",
    }


def _handle_replan(state: dict, plan: dict, completed_agents: list, revision_count: int) -> dict:
    """Dynamic Replanning: sửa plan constraints + reset agents cần chạy lại."""
    plan_modifications = state.get("plan_modifications", {})
    agents_to_retry = state.get("agents_to_retry", [])
    reflection_issues = state.get("reflection_issues", [])

    print(f"[SUPERVISOR] 🔄 REPLAN: mods={plan_modifications}, retry={agents_to_retry}")
    print(f"[SUPERVISOR] Issues: {reflection_issues}")

    # ── 1. Apply plan modifications ──
    updated_plan = copy.deepcopy(plan)
    if plan_modifications:
        constraints = updated_plan.get("constraints", {})
        for key, value in plan_modifications.items():
            old_val = constraints.get(key)
            constraints[key] = value
            print(f"[SUPERVISOR] Plan constraint '{key}': {old_val} → {value}")
        updated_plan["constraints"] = constraints

    # ── 2. Reset agents cần chạy lại ──
    new_completed = [a for a in completed_agents if a not in agents_to_retry and a != "reflect"]

    # ── 3. Xóa kết quả cũ của agents bị reset ──
    clear_results = {}
    if "flight_agent" in agents_to_retry:
        clear_results["flight_results"] = []
    if "hotel_agent" in agents_to_retry:
        clear_results["hotel_results"] = []
    if "weather_agent" in agents_to_retry:
        clear_results["weather_info"] = ""

    # ── 4. Quyết định agent tiếp theo ──
    next_agent = "respond"
    reasoning = "Không có agent cần retry."

    if agents_to_retry:
        next_agent = agents_to_retry[0]
        reasoning = f"Replan: chạy lại {next_agent} với constraints mới — {reflection_issues}"
    else:
        # Không có agent cụ thể → dùng LLM quyết định
        return _llm_decide_replan(state, new_completed, revision_count, updated_plan, clear_results)

    result = {
        "next_agent": next_agent,
        "reasoning": reasoning,
        "current_step": "supervisor",
        "plan": updated_plan,
        "completed_agents": new_completed,
        "revision_count": revision_count + 1,
        "needs_revision": False,
        "plan_modifications": {},
        "agents_to_retry": [],
    }
    result.update(clear_results)
    return result


def _llm_decide_replan(state, completed_agents, revision_count, updated_plan, clear_results):
    """Fallback: dùng LLM quyết định replan khi reflection không chỉ rõ agents_to_retry."""
    reflection_issues = state.get("reflection_issues", [])
    suggested_fixes = state.get("suggested_fixes", [])

    summary = (
        f"Reflection issues: {reflection_issues}\n"
        f"Suggested fixes: {suggested_fixes}\n"
        f"Already completed: {completed_agents}\n"
        f"Updated plan: {json.dumps(updated_plan, ensure_ascii=False)}\n"
    )
    print(f"[SUPERVISOR] LLM deciding replan: {summary}")

    llm = get_llm().with_structured_output(SupervisorDecision)
    try:
        decision = llm.invoke([
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=summary),
        ])
        print(f"[SUPERVISOR] LLM decision: {decision.next_agent} — {decision.reasoning}")

        result = {
            "next_agent": decision.next_agent,
            "reasoning": decision.reasoning,
            "current_step": "supervisor",
            "plan": updated_plan,
            "completed_agents": completed_agents,
            "revision_count": revision_count + 1,
            "needs_revision": False,
        }
        result.update(clear_results)
        return result
    except Exception as e:
        print(f"[SUPERVISOR] LLM error: {e} → respond")
        return {
            "next_agent": "respond",
            "reasoning": f"Error: {str(e)}",
            "current_step": "supervisor",
        }


def route_supervisor(state: dict) -> str:
    """Route dựa trên quyết định của supervisor."""
    return state.get("next_agent", "respond")
