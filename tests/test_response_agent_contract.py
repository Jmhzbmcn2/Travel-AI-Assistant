"""Tests for response agent contract — ensures no raw data leaks."""
from unittest.mock import MagicMock, patch

from travel_ai_agent.agents.response_agent import response_agent_node


def _make_state(decision_output=None, flight_results=None, hotel_results=None, weather_info=None):
    return {
        "messages": [],
        "plan": {
            "steps": ["find_flights"],
            "constraints": {"origin": "Ho Chi Minh", "destination": "Da Nang", "departure_date": "2026-07-10"},
            "goal": "Test trip",
        },
        "decision_output": decision_output,
        "flight_results": flight_results or [{"airline": "PRIVATE_RAW", "price": 999}],
        "hotel_results": hotel_results or [{"name": "PRIVATE_RAW_HOTEL", "price": 111}],
        "weather_info": weather_info or '{"status": "success", "PRIVATE_WEATHER_DATA": "raw"}',
        "notes": ["OK note"],
        "session_id": "test-session",
        "completed_agents": [],
    }


@patch("travel_ai_agent.agents.response_agent.get_llm")
def test_response_agent_does_not_leak_raw_flight_data(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Tổng hợp chuyến đi")
    mock_get_llm.return_value = mock_llm

    state = _make_state()
    response_agent_node(state)

    prompt_text = mock_llm.invoke.call_args[0][0][-1].content
    assert "PRIVATE_RAW" not in prompt_text
    assert "PRIVATE_RAW_HOTEL" not in prompt_text
    assert "PRIVATE_WEATHER_DATA" not in prompt_text


@patch("travel_ai_agent.agents.response_agent.get_llm")
def test_response_agent_includes_decision_output(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Phương án khuyến nghị")
    mock_get_llm.return_value = mock_llm

    decision = {
        "recommended_option": "balanced",
        "total_cost": 5_000_000,
        "budget_status": "under_budget",
        "options": [],
        "risks": [],
    }
    state = _make_state(decision_output=decision)
    response_agent_node(state)

    prompt_text = mock_llm.invoke.call_args[0][0][-1].content
    assert "DECISION_OUTPUT" in prompt_text or "5000000" in prompt_text or "5,000,000" in prompt_text


@patch("travel_ai_agent.agents.response_agent.get_llm")
def test_response_agent_returns_ai_message(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Kết quả cuối")
    mock_get_llm.return_value = mock_llm

    state = _make_state()
    result = response_agent_node(state)

    assert "messages" in result
    assert result["messages"][0].content == "Kết quả cuối"
