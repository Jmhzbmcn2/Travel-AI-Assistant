from langchain_core.messages import AIMessage

from travel_ai_agent.state.agent_state import AgentState
from travel_ai_agent.config.prompts import CHITCHAT_PROMPT
from travel_ai_agent.core.llm_service import LLMs

OUT_OF_SCOPE_REPLY = (
    "Mình là trợ lý du lịch. Mình có thể giúp bạn lập lịch trình, tìm vé, "
    "khách sạn, thời tiết và thông tin điểm đến."
)


def chitchat_node(state: AgentState) -> dict:
    """Trả lời câu hỏi không liên quan travel. Out-of-scope → câu từ chối cố định."""
    if state.get("intent") == "out_of_scope":
        return {"messages": [AIMessage(content=OUT_OF_SCOPE_REPLY)], "current_step": "chitchat"}

    user_message = state["messages"][-1].content
    llm = LLMs()
    prompt = CHITCHAT_PROMPT.format(user_message=user_message)
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response)], "current_step": "chitchat"}
