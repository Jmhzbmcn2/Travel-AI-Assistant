from src.state.agent_state import AgentState
from src.nodes.classify_intent_node import classify_intent_node
from src.nodes.parser_node import parser_node
from src.nodes.search_node import search_node
from src.nodes.ranker_node import ranker_node
from src.nodes.response_node import response_node
from src.nodes.ask_user_node import ask_user_node
from src.nodes.chitchat_node import chitchat_node
from src.nodes.follow_up_node import follow_up_node
from src.edges.routing_edges import route_by_intent, should_search_or_ask
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

# Nodes
graph.add_node("classify_intent", classify_intent_node)
graph.add_node("parser", parser_node)
graph.add_node("search", search_node)
graph.add_node("ranker", ranker_node)
graph.add_node("response", response_node)
graph.add_node("ask_user", ask_user_node)
graph.add_node("chitchat", chitchat_node)
graph.add_node("follow_up", follow_up_node)

# Entry point → intent classifier
graph.set_entry_point("classify_intent")

# Intent routing: travel → parser, follow_up → follow_up, chitchat → chitchat
graph.add_conditional_edges(
    "classify_intent",
    route_by_intent,
    ["parser", "follow_up", "chitchat"]
)

# Chitchat → END, Follow-up → END
graph.add_edge("chitchat", END)
graph.add_edge("follow_up", END)

# Parser routing: đủ info → search, thiếu → ask_user
graph.add_conditional_edges(
    "parser",
    should_search_or_ask,
    ["search", "ask_user"]
)

graph.add_edge("ask_user", "parser")
graph.add_edge("search", "ranker")
graph.add_edge("ranker", "response")
graph.add_edge("response", END)

travel_agent = graph.compile()