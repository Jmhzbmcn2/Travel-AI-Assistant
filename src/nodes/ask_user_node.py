from src.state.agent_state import AgentState
from config.prompts import MISSING_INFO_PROMPT
from src.services.llm_service import LLMs
from langchain_core.messages import AIMessage

def ask_user_node(state: AgentState) -> dict:
    """Hỏi user bổ sung thông tin còn thiếu."""
    llm = LLMs()
    prompt = MISSING_INFO_PROMPT.format(
        parsed_info=state.get("user_request", {}),
        missing_fields=state.get("missing_fields", [])
    )
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response)]}
