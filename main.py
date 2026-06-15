from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from travel_ai_agent.graphs.main_graph import travel_agent

while True:
    user_input = input("Bạn: ")
    if user_input.lower() in ["quit", "exit"]:
        break
    result = travel_agent.invoke({"messages": [("user", user_input)]})
    print("AI:", result["messages"][-1].content)
