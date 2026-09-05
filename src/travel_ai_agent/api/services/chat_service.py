"""
Chat service — business logic for graph invocation and result processing.
"""
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph


def get_graph_config(sid: str) -> dict:
    """Tạo config cho graph invocation với thread_id."""
    return {"configurable": {"thread_id": sid}}


def build_graph_input(message: str, sid: str) -> dict:
    """Xây dựng input cho LangGraph."""
    return {"messages": [HumanMessage(content=message)], "session_id": sid}


async def process_graph_result(graph: CompiledStateGraph, sid: str) -> dict:
    """Đọc kết quả cuối từ graph state (không còn interrupt trong luồng MVP)."""
    snapshot = await graph.aget_state(get_graph_config(sid))
    state_values = snapshot.values or {}
    return {
        "type": "done",
        "message": "",
        "decision": state_values.get("decision_output"),
        "plan": state_values.get("plan"),
        "plan_draft": state_values.get("plan_draft"),
    }


async def invoke_graph(
    graph: CompiledStateGraph, sid: str, message: str
) -> tuple[Any, dict]:
    """Invoke graph với user message và trả về (result, processed)."""
    result = await graph.ainvoke(
        build_graph_input(message, sid),
        get_graph_config(sid),
    )

    # Lấy AI message từ result nếu có
    processed = await process_graph_result(graph, sid)
    if processed["type"] == "done" and result:
        if isinstance(result, dict) and result.get("messages"):
            processed["message"] = result["messages"][-1].content

    return result, processed


async def resume_graph(graph: CompiledStateGraph, sid: str) -> tuple[Any, dict]:
    """Resume graph sau interrupt (HITL) và trả về (result, processed)."""
    result = await graph.ainvoke(
        None,
        get_graph_config(sid),
    )

    processed = await process_graph_result(graph, sid)
    if processed["type"] == "done" and result:
        if isinstance(result, dict) and result.get("messages"):
            processed["message"] = result["messages"][-1].content

    return result, processed
