"""
Chat service — business logic for graph invocation and result processing.
"""
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from backend.utils.plan_builder import build_plan_message


def get_graph_config(sid: str) -> dict:
    """Tạo config cho graph invocation với thread_id."""
    return {"configurable": {"thread_id": sid}}


def build_graph_input(message: str) -> dict:
    """Xây dựng input cho LangGraph."""
    return {"messages": [HumanMessage(content=message)]}


def process_graph_result(graph: CompiledStateGraph, sid: str) -> dict:
    """Xử lý kết quả từ graph: normal completion hoặc interrupt."""
    snapshot = graph.get_state(get_graph_config(sid))

    if snapshot.next:
        # Graph bị interrupt_before — đọc plan từ state
        state_values = snapshot.values or {}
        plan = state_values.get("plan", {})
        message = build_plan_message(plan)

        return {
            "type": "interrupt",
            "data": {"plan": plan, "type": "plan_confirmation"},
            "message": message,
            "waiting_for": list(snapshot.next),
        }

    # Normal completion — lấy AI message cuối cùng
    return {
        "type": "done",
        "message": "",
    }


async def invoke_graph(
    graph: CompiledStateGraph, sid: str, message: str
) -> tuple[Any, dict]:
    """Invoke graph với user message và trả về (result, processed)."""
    result = await asyncio.to_thread(
        graph.invoke,
        build_graph_input(message),
        get_graph_config(sid),
    )

    # Lấy AI message từ result nếu có
    processed = process_graph_result(graph, sid)
    if processed["type"] == "done" and result:
        if isinstance(result, dict) and result.get("messages"):
            processed["message"] = result["messages"][-1].content

    return result, processed


async def resume_graph(graph: CompiledStateGraph, sid: str) -> tuple[Any, dict]:
    """Resume graph sau interrupt (HITL) và trả về (result, processed)."""
    result = await asyncio.to_thread(
        graph.invoke,
        None,
        get_graph_config(sid),
    )

    processed = process_graph_result(graph, sid)
    if processed["type"] == "done" and result:
        if isinstance(result, dict) and result.get("messages"):
            processed["message"] = result["messages"][-1].content

    return result, processed
