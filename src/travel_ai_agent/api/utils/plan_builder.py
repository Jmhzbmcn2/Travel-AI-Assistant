"""
Plan message builder — tạo message xác nhận kế hoạch cho user.
"""

STEP_LABELS: dict[str, str] = {
    "find_flights": "✈️ Tìm vé máy bay",
    "find_hotels": "🏨 Tìm khách sạn",
    "check_weather": "🌤️ Tra cứu thời tiết",
    "search_info": "🔍 Tìm kiếm thông tin du lịch",
}


def build_plan_message(plan: dict) -> str:
    """Tạo message confirm đẹp từ plan data."""
    if not plan:
        return "Xác nhận kế hoạch?"

    constraints = plan.get("constraints", {})
    steps = plan.get("steps", [])
    goal = plan.get("goal", "")

    parts = [f"📋 **Kế hoạch:** {goal}\n"]

    if constraints.get("destination_name") or constraints.get("destination"):
        dest = constraints.get("destination_name", constraints.get("destination", ""))
        parts.append(f"📍 Điểm đến: {dest}")
    if constraints.get("origin_name") or constraints.get("origin"):
        origin = constraints.get("origin_name", constraints.get("origin", ""))
        parts.append(f"🛫 Điểm đi: {origin}")
    if constraints.get("departure_date"):
        parts.append(f"📅 Ngày: {constraints['departure_date']}")
    if constraints.get("days"):
        parts.append(f"⏱️ Số ngày: {constraints['days']}")
    if constraints.get("budget"):
        parts.append(f"💰 Budget: {constraints['budget']:,} VND")

    parts.append("\n**Các bước:**")
    for i, step in enumerate(steps):
        label = STEP_LABELS.get(step, step)
        parts.append(f"  {i + 1}. {label}")

    parts.append("\nBạn xác nhận kế hoạch này không?")
    return "\n".join(parts)
