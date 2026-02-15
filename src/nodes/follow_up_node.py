from src.state.agent_state import AgentState
from config.prompts import FOLLOW_UP_PROMPT
from src.services.llm_service import LLMs
from langchain_core.messages import AIMessage
import json


def follow_up_node(state: AgentState) -> dict:
    """Trả lời câu hỏi follow-up dựa trên kết quả tìm kiếm trước đó."""
    user_message = state["messages"][-1].content
    flight_results = state.get("flight_results", [])
    hotel_results = state.get("hotel_results", [])

    # Nếu không có kết quả trước đó → thông báo cho user
    if not flight_results and not hotel_results:
        return {
            "messages": [AIMessage(
                content="Xin lỗi bạn, mình chưa có kết quả tìm kiếm nào trước đó. "
                        "Bạn hãy cho mình biết bạn muốn bay từ đâu đến đâu và ngày nào nhé! ✈️"
            )],
            "current_step": "follow_up"
        }

    llm = LLMs()
    prompt = FOLLOW_UP_PROMPT.format(
        flight_results=json.dumps(flight_results, ensure_ascii=False, indent=2),
        hotel_results=json.dumps(hotel_results, ensure_ascii=False, indent=2),
        user_message=user_message,
    )
    response = llm.invoke(prompt)
    return {
        "messages": [AIMessage(content=response)],
        "current_step": "follow_up"
    }
