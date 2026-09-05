"""Graph topology: 5 node, không còn supervisor / agent nodes."""
from langgraph.checkpoint.memory import MemorySaver

from travel_ai_agent.graphs.main_graph import travel_agent


def test_graph_has_lean_node_set():
    compiled = travel_agent.compile(checkpointer=MemorySaver())
    nodes = set(compiled.get_graph().nodes)
    assert {"classify_intent", "chitchat", "planner", "decision", "respond"} <= nodes
    for gone in ("supervisor", "flight_agent", "hotel_agent", "weather_agent", "info_agent", "follow_up", "out_of_scope", "reflect"):
        assert gone not in nodes
