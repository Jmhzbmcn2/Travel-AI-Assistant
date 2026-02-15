from src.state.agent_state import AgentState
from config.prompts import CLASSIFY_INTENT_PROMPT
from src.services.llm_service import LLMs


def classify_intent_node(state: AgentState) -> dict:
    """Phân loại intent của user: travel hay chitchat."""
    user_message = state["messages"][-1].content
    llm = LLMs()
    prompt = CLASSIFY_INTENT_PROMPT.format(user_message=user_message)
    response = llm.invoke(prompt).strip().lower()

    # Đảm bảo chỉ trả về "travel", "follow_up", hoặc "chitchat"
    if "follow_up" in response:
        intent = "follow_up"
    elif "travel" in response:
        intent = "travel"
    else:
        intent = "chitchat"

    print(f"[CLASSIFY] User: {user_message[:80]}...")
    print(f"[CLASSIFY] Intent: {intent}")
    return {"intent": intent, "current_step": "classify_intent"}

    