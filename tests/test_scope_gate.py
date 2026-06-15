from langchain_core.messages import HumanMessage

from travel_ai_agent.nodes.classify_intent_node import classify_intent_node


def test_scope_gate_blocks_code_without_llm():
    result = classify_intent_node({"messages": [HumanMessage(content="write code in Python")]})
    assert result["intent"] == "out_of_scope"


def test_scope_gate_routes_travel_without_llm():
    result = classify_intent_node({"messages": [HumanMessage(content="plan a flight and hotel trip")]})
    assert result["intent"] == "travel"
