from travel_ai_agent.state.agent_state import AgentState
from travel_ai_agent.config.prompts import CLASSIFY_INTENT_PROMPT
from travel_ai_agent.services.llm_service import LLMs


def classify_intent_node(state: AgentState) -> dict:
    """Phân loại intent của user: travel, follow_up hay chitchat."""
    user_message = state["messages"][-1].content
    lowered = user_message.lower()
    out_of_scope_markers = [
        "viết code", "lập trình", "bài tập", "chẩn đoán", "thuốc",
        "pháp luật", "chính trị", "hack", "prompt injection", "write code",
        "python code", "javascript", "programming", "medical advice", "legal advice",
    ]
    if any(marker in lowered for marker in out_of_scope_markers):
        return {"intent": "out_of_scope", "current_step": "classify_intent"}
    travel_markers = [
        "du lịch", "chuyến đi", "khách sạn", "vé máy bay", "thời tiết",
        "travel", "trip", "hotel", "flight", "weather",
    ]
    if any(marker in lowered for marker in travel_markers):
        return {"intent": "travel", "current_step": "classify_intent"}
    
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
    try:
        response = llm.invoke(prompt).strip().lower()
    except Exception as exc:
        print(f"[CLASSIFY] LLM unavailable, using safe chitchat fallback: {exc}")
        return {"intent": "chitchat", "current_step": "classify_intent"}

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

    
