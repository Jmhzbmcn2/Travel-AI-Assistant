from __future__ import annotations

from travel_ai_agent.config.constants import CITY_IATA


def to_iata(value: str | None) -> str | None:
    """Chuyển tên thành phố tiếng Việt → mã IATA cho provider chuyến bay."""
    if not value:
        return value
    if len(value) == 3 and value.isupper():
        return value
    lowered = value.lower().strip()
    for city, code in CITY_IATA.items():
        if city == lowered or city in lowered or lowered in city:
            return code
    return value
