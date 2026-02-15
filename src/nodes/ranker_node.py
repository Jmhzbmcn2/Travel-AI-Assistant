from src.state.agent_state import AgentState
from config.prompts import RANKER_PROMPT
from src.services.llm_service import LLMs
import json

def ranker_node(agent_state: AgentState) -> dict:
    try:
        user_request = agent_state["user_request"]
        flight_results = agent_state.get("flight_results", [])
        hotel_results = agent_state.get("hotel_results", [])

        print(f"[RANKER] Analyzing {len(flight_results)} flights, {len(hotel_results)} hotels")

        llm = LLMs()
        prompt = RANKER_PROMPT.format(
            budget=user_request.get("budget", "Không giới hạn"),
            currency=user_request.get("currency", "VND"),
            flight_results=json.dumps(flight_results, ensure_ascii=False, indent=2),
            hotel_results=json.dumps(hotel_results, ensure_ascii=False, indent=2),
        )

        response = llm.invoke(prompt)
        return {
            "ranked_deals": response,
            "current_step": "ranker"
        }
    except Exception as e:
        return {"error": str(e), "current_step": "ranker"}