"""
Main Graph — Multi-Agent Supervisor architecture + Checkpointer + HITL.

HITL: interrupt_before trên human_confirm node — user xác nhận plan
      trước khi supervisor dispatch agents.

Flow:
  classify_intent
    ├── chitchat    → END
    ├── follow_up   → END
    └── travel      → planner → [INTERRUPT] human_confirm → supervisor ─┬→ ...agents...
                                                                         ├→ reflect → supervisor/respond
                                                                         └→ respond → END
"""
from src.state.agent_state import AgentState
from src.nodes.classify_intent_node import classify_intent_node
from src.nodes.chitchat_node import chitchat_node
from src.nodes.follow_up_node import follow_up_node

# Multi-agent imports
from src.agents.planner_agent import planner_node
from src.agents.supervisor import supervisor_node, route_supervisor
from src.agents.flight_agent import flight_agent_node
from src.agents.hotel_agent import hotel_agent_node
from src.agents.weather_agent import weather_agent_node
from src.agents.info_agent import info_agent_node
from src.agents.reflection import reflection_node, route_after_reflection
from src.agents.response_agent import response_agent_node

from src.edges.routing_edges import route_by_intent
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# ── Build graph ───────────────────────────────────────
graph = StateGraph(AgentState)


# ── Human confirm node (HITL gate) ────────────────────
def human_confirm_node(state: dict) -> dict:
    """Gate node: chỉ chạy 1 lần sau planner.
    interrupt_before sẽ dừng TRƯỚC node này → user confirm
    Khi resume, node này pass-through → tiếp tục tới supervisor.
    """
    print("[HUMAN_CONFIRM] User confirmed plan. Proceeding to supervisor.")
    return {}


# Nodes — shared
graph.add_node("classify_intent", classify_intent_node)
graph.add_node("chitchat", chitchat_node)
graph.add_node("follow_up", follow_up_node)

# Nodes — multi-agent
graph.add_node("planner", planner_node)
graph.add_node("human_confirm", human_confirm_node)  # HITL gate
graph.add_node("supervisor", supervisor_node)
graph.add_node("flight_agent", flight_agent_node)
graph.add_node("hotel_agent", hotel_agent_node)
graph.add_node("weather_agent", weather_agent_node)
graph.add_node("info_agent", info_agent_node)
graph.add_node("reflect", reflection_node)
graph.add_node("respond", response_agent_node)

# ── Entry point ───────────────────────────────────────
graph.set_entry_point("classify_intent")

# ── Intent routing ────────────────────────────────────
graph.add_conditional_edges(
    "classify_intent",
    route_by_intent,
    ["planner", "follow_up", "chitchat"],
)

# ── Simple flows → END ───────────────────────────────
graph.add_edge("chitchat", END)
graph.add_edge("follow_up", END)

# ── Multi-agent flow ─────────────────────────────────
# Planner → Human Confirm (HITL gate) → Supervisor
# Nếu planner thiếu info → trả message hỏi lại → END
def route_after_planner(state: dict) -> str:
    """Route sau planner: có plan → confirm, thiếu info → END."""
    plan = state.get("plan")
    if not plan:
        # Planner trả AIMessage hỏi lại → END
        return "__end__"
    return "human_confirm"

graph.add_conditional_edges("planner", route_after_planner, {
    "human_confirm": "human_confirm",
    "__end__": END,
})
graph.add_edge("human_confirm", "supervisor")

# Supervisor → routes to agents / reflect / respond
graph.add_conditional_edges("supervisor", route_supervisor, {
    "flight_agent": "flight_agent",
    "hotel_agent": "hotel_agent",
    "weather_agent": "weather_agent",
    "info_agent": "info_agent",
    "reflect": "reflect",
    "respond": "respond",
})

# Agents → back to Supervisor (loop, NO interrupt)
graph.add_edge("flight_agent", "supervisor")
graph.add_edge("hotel_agent", "supervisor")
graph.add_edge("weather_agent", "supervisor")
graph.add_edge("info_agent", "supervisor")

# Reflection → Supervisor (needs fix) OR Respond (OK)
graph.add_conditional_edges("reflect", route_after_reflection, {
    "supervisor": "supervisor",
    "respond": "respond",
})

# Respond → END
graph.add_edge("respond", END)

# ── Compile with Checkpointer + HITL ─────────────────
# interrupt_before=["human_confirm"]: chỉ dừng 1 lần
# (planner → STOP → user confirm → human_confirm → supervisor → agents...)
memory = MemorySaver()
travel_agent = graph.compile(
    checkpointer=memory,
    interrupt_before=["human_confirm"],
)