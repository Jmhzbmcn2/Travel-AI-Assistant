COST_RULES_V1 = {
    "version": "v1.0",
    "per_person_day": {
        "food": 350_000,          # VND per person per day
    },
    "per_day": {
        "local_transport": 300_000,  # VND per day for group
    },
    "per_night": {},               # Hotel costs handled by provider data
    "fixed": {},                   # No fixed trip costs in v1
    "buffer_rate": 0.10,
    "assumptions": [
        "Chi phí ăn uống: 350.000₫/người/ngày (3 bữa cơ bản).",
        "Di chuyển nội thành: 300.000₫/ngày (taxi/grab).",
        "Dự phòng: 10% tổng chi phí.",
    ],
}
