"""
Planner Agent — phân rã yêu cầu phức tạp thành plan thực thi.
Sử dụng structured output để tạo TripPlan.
"""
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from src.services.llm_service import get_llm
from config.constants import CITY_IATA, IATA_CITY
from config.prompts import PLANNER_SYSTEM_PROMPT
from datetime import datetime, timedelta


class TripPlan(BaseModel):
    """Kế hoạch thực thi được tạo bởi Planner."""
    steps: list[str] = Field(
        description="Danh sách các bước cần thực hiện, ví dụ: "
                    '["find_flights", "find_hotels", "check_weather"]'
    )
    constraints: dict = Field(
        description="Các ràng buộc: budget, days, origin, destination, departure_date, v.v."
    )
    goal: str = Field(
        description="Mô tả mục tiêu tổng thể của trip"
    )


def _to_iata(city_name: str) -> str:
    """Convert Vietnamese city name to IATA code."""
    if not city_name:
        return city_name
    if len(city_name) == 3 and city_name.isupper():
        return city_name
    key = city_name.lower().strip()
    if key in CITY_IATA:
        return CITY_IATA[key]
    for city, code in CITY_IATA.items():
        if city in key or key in city:
            return code
    return city_name


def _iata_to_city(code: str) -> str:
    """Reverse IATA code → Vietnamese city name."""
    return IATA_CITY.get(code, code)


STEP_LABELS = {
    "find_flights": "✈️ Tìm vé máy bay",
    "find_hotels": "🏨 Tìm khách sạn",
    "check_weather": "🌤️ Tra cứu thời tiết",
    "search_info": "🔍 Tìm kiếm thông tin du lịch",
}


def planner_node(state: dict) -> dict:
    """Phân rã yêu cầu phức tạp thành các bước cụ thể."""
    user_message = state["messages"][-1].content
    current_date = datetime.now().strftime("%Y-%m-%d")

    print(f"[PLANNER] Planning for: {user_message}")

    llm = get_llm().with_structured_output(TripPlan)

    # Lấy conversation history gần đây để hiểu context
    # (ví dụ: user nói "Có" → planner cần biết AI vừa hỏi gì)
    recent_messages = state["messages"][-6:]

    try:
        plan = llm.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT.format(
                current_date=current_date
            )),
            *recent_messages,  # Gửi context, không chỉ message cuối
        ])

        plan_dict = plan.model_dump()
        constraints = plan_dict.get("constraints", {})
        steps = plan_dict.get("steps", [])

        # ── Kiểm tra thiếu info quan trọng ────────────────
        needs_flights_or_hotels = any(
            s in steps for s in ["find_flights", "find_hotels"]
        )
        has_destination = bool(constraints.get("destination"))

        if needs_flights_or_hotels and not has_destination:
            # Thiếu thông tin quan trọng → hỏi lại user
            missing = []
            if not constraints.get("destination"):
                missing.append("điểm đến")
            if not constraints.get("origin"):
                missing.append("điểm đi")

            ask_msg = (
                f"Bạn muốn tìm vé máy bay, nhưng mình cần thêm thông tin:\n\n"
                f"📌 Thiếu: **{', '.join(missing)}**\n\n"
                f"Ví dụ: *\"Tìm vé rẻ nhất từ HCM đi Đà Nẵng ngày 15/3\"*\n\n"
                f"Bạn bổ sung giúp mình nhé!"
            )
            print(f"[PLANNER] Missing info: {missing} → asking user")

            from langchain_core.messages import AIMessage
            return {
                "messages": [AIMessage(content=ask_msg)],
                "current_step": "planner",
            }

        # ── Origin: lưu tên gốc → convert IATA ───────────
        if constraints.get("origin"):
            raw = str(constraints["origin"])
            if len(raw) == 3 and raw.isupper():
                constraints["origin_name"] = _iata_to_city(raw)
            else:
                constraints["origin_name"] = raw
            constraints["origin"] = _to_iata(raw)

        # ── Destination ───────────────────────────────────
        if constraints.get("destination"):
            raw = str(constraints["destination"])
            if len(raw) == 3 and raw.isupper():
                constraints["destination_name"] = _iata_to_city(raw)
            else:
                constraints["destination_name"] = raw
            constraints["destination"] = _to_iata(raw)

        # ── Fallback date ─────────────────────────────────
        if not constraints.get("departure_date") and any(
            s in steps for s in ["find_flights", "find_hotels"]
        ):
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            constraints["departure_date"] = tomorrow
            print(f"[PLANNER] No date specified, using tomorrow: {tomorrow}")

        plan_dict["constraints"] = constraints

        print(f"[PLANNER] Plan: {plan_dict}")

        return {
            "plan": plan_dict,
            "current_step_index": 0,
            "current_step": "planner",
        }

    except Exception as e:
        print(f"[PLANNER] Error: {e}")
        return {
            "plan": {
                "steps": ["find_flights"],
                "constraints": {},
                "goal": user_message,
            },
            "current_step_index": 0,
            "current_step": "planner",
        }
