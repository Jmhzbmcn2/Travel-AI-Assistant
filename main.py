from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langgraph.checkpoint.memory import MemorySaver

from travel_ai_agent.graphs.main_graph import travel_agent

agent = travel_agent.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "cli"}}

while True:
    user_input = input("Bạn: ")
    if user_input.lower() in ["quit", "exit"]:
        break
    result = agent.invoke(
        {"messages": [("user", user_input)], "session_id": "cli"},
        config,
    )
    print("AI:", result["messages"][-1].content)
