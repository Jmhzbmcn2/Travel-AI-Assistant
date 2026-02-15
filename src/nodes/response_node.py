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
        prompt = RESPONSE_PROMPT.format(analysis=ranked_deals)

        print(f"[RESPONSE] Generating final response...")
        response = llm.invoke(prompt)
        return {
            "messages": [AIMessage(content=response)],  
            "current_step": "response"
        }
    except Exception as e:
        return {"error": str(e), "current_step": "response"}    