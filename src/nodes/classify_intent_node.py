from src.state.agent_state import AgentState
from config.prompts import CLASSIFY_INTENT_PROMPT
from src.services.llm_service import LLMs


def classify_intent_node(state: AgentState) -> dict:
    """Phân loại intent của user: travel, follow_up hay chitchat."""
    user_message = state["messages"][-1].content
    
    # Lấy conversation history gần đây (tối đa 6 messages cuối)
    recent_messages = state["messages"][-6:]
    history_lines = []
    for msg in recent_messages:
        role = "User" if msg.type == "human" else "Assistant"
        history_lines.append(f"{role}: {msg.content[:200]}")
    conversation_history = "\n".join(history_lines) if history_lines else "(No history)"
    
    llm = LLMs()
    prompt = CLASSIFY_INTENT_PROMPT.format(
        user_message=user_message,
        conversation_history=conversation_history
    )
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

    