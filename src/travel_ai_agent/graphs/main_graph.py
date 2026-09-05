"""
Main Graph — lean pipeline.

  classify_intent
    ├── chitchat / out_of_scope → chitchat → END
    └── travel / follow_up      → planner ─┬→ (thiếu info) END
                                            └→ decision → respond → END

The graph is exported uncompiled; it is compiled with a checkpointer in
`api/dependencies.py` (AsyncSqliteSaver) or `main.py` (MemorySaver).
"""
from langgraph.graph import StateGraph, END

from travel_ai_agent.state.agent_state import AgentState
from travel_ai_agent.nodes.classify_intent_node import classify_intent_node
from travel_ai_agent.nodes.chitchat_node import chitchat_node
from travel_ai_agent.nodes.decision_node import decision_node
from travel_ai_agent.nodes.planner_node import planner_node
from travel_ai_agent.nodes.respond_node import response_agent_node
from travel_ai_agent.edges.routing_edges import route_by_intent, route_after_planner

graph = StateGraph(AgentState)

graph.add_node("classify_intent", classify_intent_node)
graph.add_node("chitchat", chitchat_node)
graph.add_node("planner", planner_node)
graph.add_node("decision", decision_node)
graph.add_node("respond", response_agent_node)

graph.set_entry_point("classify_intent")

graph.add_conditional_edges("classify_intent", route_by_intent, ["chitchat", "planner"])
graph.add_edge("chitchat", END)
graph.add_conditional_edges("planner", route_after_planner, {"decision": "decision", "__end__": END})
graph.add_edge("decision", "respond")
graph.add_edge("respond", END)

# Uncompiled — compiled with a checkpointer downstream.
travel_agent = graph
