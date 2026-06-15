from langchain_core.messages import AIMessage


def out_of_scope_node(state: dict) -> dict:
    return {
        "messages": [AIMessage(content="Mình là trợ lý du lịch. Mình có thể giúp bạn lập lịch trình, tìm vé, khách sạn, thời tiết và thông tin điểm đến.")],
        "current_step": "out_of_scope",
    }
