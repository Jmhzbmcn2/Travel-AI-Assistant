from src.state.agent_state import AgentState
from config.prompts import CHITCHAT_PROMPT
from src.services.llm_service import LLMs
from langchain_core.messages import AIMessage


def chitchat_node(state: AgentState) -> dict:
    """Trả lời các câu hỏi chung (không liên quan travel)."""
    user_message = state["messages"][-1].content
    llm = LLMs()
    prompt = CHITCHAT_PROMPT.format(user_message=user_message)
    response = llm.invoke(prompt)
    return {
        "messages": [AIMessage(content=response)],
        "current_step": "chitchat"
    }
