"""Coverage evaluator — determines if a trip has sufficient verified data for recommendation.

Verified coverage v1:
- Domestic Vietnam, single destination
- 2–5 days, 1–4 travelers, VND currency
- At least 1 live flight, 1 live hotel
- Route data live OR places have GPS for Haversine fallback
- No fixture data in critical categories (flights, hotels)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from travel_ai_agent.schemas.domain import (
    CoverageStatus,
    DecisionConfidence,
    DecisionInput,
)

RULE_VERSION = "v1.0"


@dataclass
class CoverageResult:
    status: CoverageStatus
    confidence: DecisionConfidence
    blocking_reasons: list[str] = field(default_factory=list)
    data_freshness: dict[str, str] = field(default_factory=dict)


def _has_live_data(records: list, category: str) -> tuple[bool, str | None]:
    """Check if any record in the list is live (not fixture/missing)."""
    if not records:
        return False, f"Không có dữ liệu {category}."
    live = [r for r in records if getattr(r, "data_mode", "missing") == "live"]
    if not live:
        return False, f"Dữ liệu {category} đang dùng fixture — chưa xác minh được."
    return True, None


def _check_domestic_vietnam(data: DecisionInput) -> tuple[bool, str | None]:
    """Check if trip is domestic Vietnam using currency heuristic."""
    plan = data.trip_plan
    if plan.currency != "VND":
        return False, f"Chưa hỗ trợ đơn vị tiền tệ {plan.currency} — chỉ hỗ trợ VND cho verified coverage."
    return True, None


def _check_price_scope(data: DecisionInput) -> str | None:
    """Check if trip plan requires round trip but flights are one-way only."""
    if data.trip_plan.return_date and data.flight_options:
        all_one_way = all(f.price_scope == "one_way_per_traveler" for f in data.flight_options)
        if all_one_way:
            return "Trip yêu cầu khứ hồi nhưng chỉ có giá vé một chiều — chi phí ước tính chưa đầy đủ."
    return None



def _check_parameter_bounds(data: DecisionInput) -> list[str]:
    """Check if trip parameters are within verified coverage bounds."""
    plan = data.trip_plan
    reasons: list[str] = []
    days = plan.days
    if days is not None and (days < 2 or days > 5):
        reasons.append(f"Số ngày ({days}) ngoài phạm vi verified (2–5 ngày).")
    travelers = plan.travelers
    if travelers < 1 or travelers > 4:
        reasons.append(f"Số người ({travelers}) ngoài phạm vi verified (1–4 người).")
    if not plan.destination:
        reasons.append("Chưa có điểm đến.")
    return reasons


def _check_places_have_gps(data: DecisionInput) -> bool:
    """Check if places have GPS coordinates for Haversine fallback."""
    return any(
        p.lat is not None and p.lng is not None
        for p in data.place_options
    )


def _build_data_freshness(data: DecisionInput) -> dict[str, str]:
    """Extract retrieval timestamps from provider records."""
    freshness: dict[str, str] = {}
    if data.flight_options:
        live_flights = [f for f in data.flight_options if f.data_mode == "live"]
        if live_flights:
            freshness["flights"] = live_flights[0].retrieved_at.isoformat()
    if data.hotel_options:
        live_hotels = [h for h in data.hotel_options if h.data_mode == "live"]
        if live_hotels:
            freshness["hotels"] = live_hotels[0].retrieved_at.isoformat()
    if data.route_segments:
        live_routes = [r for r in data.route_segments if r.data_mode == "live"]
        if live_routes:
            freshness["routes"] = live_routes[0].retrieved_at.isoformat()
    if data.weather_forecasts:
        live_weather = [w for w in data.weather_forecasts if w.data_mode == "live"]
        if live_weather:
            freshness["weather"] = live_weather[0].retrieved_at.isoformat()
    return freshness


def evaluate_coverage(data: DecisionInput) -> CoverageResult:
    """Evaluate whether the trip data meets verified coverage criteria.

    Returns a CoverageResult with status, confidence, and blocking reasons.
    """
    blocking: list[str] = []
    freshness = _build_data_freshness(data)

    # 1. Check domestic Vietnam
    is_domestic, reason = _check_domestic_vietnam(data)
    if not is_domestic:
        blocking.append(reason)
        return CoverageResult(
            status="unsupported",
            confidence="insufficient",
            blocking_reasons=blocking,
            data_freshness=freshness,
        )

    # 2. Check parameter bounds
    param_issues = _check_parameter_bounds(data)
    if param_issues:
        blocking.extend(param_issues)

    # 3. Check critical data: flights
    has_live_flights, flight_reason = _has_live_data(data.flight_options, "chuyến bay")
    if not has_live_flights and flight_reason:
        blocking.append(flight_reason)

    # 4. Check critical data: hotels
    has_live_hotels, hotel_reason = _has_live_data(data.hotel_options, "khách sạn")
    if not has_live_hotels and hotel_reason:
        blocking.append(hotel_reason)

    # 5. Check route data: live routes OR GPS fallback
    has_live_routes, _ = _has_live_data(data.route_segments, "tuyến đường")
    has_gps = _check_places_have_gps(data)
    if not has_live_routes and not has_gps:
        blocking.append("Chưa có dữ liệu tuyến đường và không có tọa độ GPS để ước tính.")

    # 6. Check price scope for round trips
    price_scope_issue = _check_price_scope(data)
    if price_scope_issue:
        blocking.append(price_scope_issue)

    # 7. Check unverified places
    if data.place_options:
        unverified_places = [p.name for p in data.place_options if getattr(p, "place_match_status", "") == "unverified"]
        if unverified_places:
            names = ", ".join(unverified_places[:3])
            blocking.append(f"Có địa điểm chưa được xác minh: {names}.")


    # Determine status
    if not blocking:
        return CoverageResult(
            status="verified" if has_live_routes else "estimated",
            confidence="high" if has_live_routes else "medium",
            blocking_reasons=[],
            data_freshness=freshness,
        )

    # Check if it's draft_only vs unsupported
    # Unsupported: no destination or currency mismatch (already handled above)
    # Draft_only: has some data but not enough for verified
    has_any_data = bool(data.flight_options or data.hotel_options)
    if has_any_data or param_issues:
        return CoverageResult(
            status="draft_only",
            confidence="insufficient" if not (has_live_flights or has_live_hotels) else "medium",
            blocking_reasons=blocking,
            data_freshness=freshness,
        )

    return CoverageResult(
        status="draft_only",
        confidence="insufficient",
        blocking_reasons=blocking,
        data_freshness=freshness,
    )
