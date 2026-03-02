from src.state.agent_state import AgentState
from config.prompts import RESPONSE_PROMPT
from src.services.llm_service import LLMs
import json
from langchain_core.messages import AIMessage


def response_node(agent_state: AgentState) -> dict:
    try: 
        user_request = agent_state["user_request"]
        ranked_deals = agent_state["ranked_deals"]

        llm = LLMs()
        
        # Tạo travel info string cho response
        travel_info = (
            f"- Điểm đi: {user_request.get('origin', 'N/A')}\n"
            f"- Điểm đến: {user_request.get('destination', 'N/A')}\n"
            f"- Ngày bay: {user_request.get('departure_date', 'N/A')}\n"
            f"- Ngày về: {user_request.get('return_date', 'Không có')}\n"
            f"- Số hành khách: {user_request.get('passengers', 1)}"
        )
        
        prompt = RESPONSE_PROMPT.format(
            analysis=ranked_deals,
            travel_info=travel_info
        )

        print(f"[RESPONSE] Generating final response...")
        response = llm.invoke(prompt)
        return {
            "messages": [AIMessage(content=response)],  
            "current_step": "response"
        }
    except Exception as e:
        return {"error": str(e), "current_step": "response"}    