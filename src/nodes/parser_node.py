from src.state.agent_state import AgentState
from config.prompts import PARSER_PROMPT
from config.constants import CITY_IATA
from src.services.llm_service import LLMs
from datetime import datetime
import json
import re


def _to_iata(city_name: str) -> str:
    """Convert Vietnamese city name to IATA code."""
    if not city_name:
        return city_name
    # Nếu đã là IATA code (3 ký tự in hoa) → giữ nguyên
    if len(city_name) == 3 and city_name.isupper():
        return city_name
    # Tìm trong dict
    key = city_name.lower().strip()
    if key in CITY_IATA:
        return CITY_IATA[key]
    # Thử tìm gần đúng
    for city, code in CITY_IATA.items():
        if city in key or key in city:
            return code
    return city_name  # Trả về nguyên nếu không tìm thấy


def parser_node(agent_state: AgentState) -> dict:
    try:
        user_message = agent_state["messages"][-1].content
        llm = LLMs()
        current_date = datetime.now().strftime("%Y-%m-%d")
        prompt = PARSER_PROMPT.format(
            user_message=user_message,
            current_date=current_date
        )

        response = llm.invoke(prompt)
        print(f"[PARSER] LLM raw response:\n{response}")

        # Strip markdown code block nếu có
        cleaned = response.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        parsed_data = json.loads(cleaned)

        # Merge với user_request cũ (nếu có) — giữ lại info đã parse trước đó
        previous_request = agent_state.get("user_request", {})
        if previous_request:
            for key, value in previous_request.items():
                if value and not parsed_data.get(key):
                    parsed_data[key] = value

        # Convert city names → IATA codes
        if parsed_data.get("origin"):
            parsed_data["origin"] = _to_iata(parsed_data["origin"])
        if parsed_data.get("destination"):
            parsed_data["destination"] = _to_iata(parsed_data["destination"])

        print(f"[PARSER] Parsed data: {parsed_data}")

        required = ["origin", "destination", "departure_date"]
        missing = [field for field in required if not parsed_data.get(field)]

        print(f"[PARSER] Missing fields: {missing}")

        return {
            "user_request": parsed_data,
            "missing_fields": missing,
            "current_step": "parser"
        }

    except Exception as e:
        # print(f"[DEBUG parser] ERROR: {e}")
        return {
            "error": str(e),
            "current_step": "parser",
            "missing_fields": ["origin", "destination", "departure_date"]
        }