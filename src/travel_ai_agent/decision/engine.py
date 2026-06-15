from __future__ import annotations

from travel_ai_agent.decision.coverage import RULE_VERSION, evaluate_coverage
from travel_ai_agent.schemas import (
    CostBreakdown,
    DecisionInput,
    DecisionOutput,
    FlightOption,
    HotelOption,
    ItineraryDay,
    PlaceOption,
    RankedOption,
    Risk,
    RouteSegment,
)


from travel_ai_agent.decision.cost_rules import COST_RULES_V1

PRIORITY_PRESETS = {
    "cheapest": {"cost": 0.7, "feasibility": 0.2, "comfort": 0.1},
    "less_travel": {"cost": 0.3, "feasibility": 0.5, "comfort": 0.2},
    "comfortable": {"cost": 0.2, "feasibility": 0.3, "comfort": 0.5},
}

def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _cost_breakdown(data: DecisionInput, flight: FlightOption | None, hotel_price: float) -> tuple[CostBreakdown, list[str]]:
    plan = data.trip_plan
    
    # Allow dynamic cost_rules to override defaults, but default to COST_RULES_V1
    food_per_person_day = data.cost_rules.get("food_per_person_day", COST_RULES_V1["per_person_day"]["food"])
    local_transport_per_day = data.cost_rules.get("local_transport_per_day", COST_RULES_V1["per_day"]["local_transport"])
    buffer_rate = data.cost_rules.get("buffer_rate", COST_RULES_V1["buffer_rate"])

    days = plan.days or 1
    nights = plan.nights if plan.nights is not None else max(days - 1, 0)
    tickets = sum(place.estimated_cost for place in data.place_options) * plan.travelers

    flight_price = flight.price if flight else 0
    flight_assumptions = []
    
    if flight and flight.price_scope == "one_way_per_traveler" and plan.return_date:
        flight_price = flight_price * 2
        flight_assumptions.append("Giá vé khứ hồi được ước tính = giá một chiều × 2.")

    subtotal = (
        flight_price * plan.travelers
        + hotel_price * nights
        + food_per_person_day * days * plan.travelers
        + local_transport_per_day * days
        + tickets
    )
    
    breakdown = CostBreakdown(
        flights=round(flight_price * plan.travelers),
        hotels=round(hotel_price * nights),
        food=round(food_per_person_day * days * plan.travelers),
        local_transport=round(local_transport_per_day * days),
        tickets=round(tickets),
        buffer=round(subtotal * buffer_rate),
    )
    return breakdown, flight_assumptions


def _budget_status(total: float, budget: float | None) -> str:
    if not budget:
        return "unknown"
    ratio = total / budget
    if ratio <= 0.9:
        return "under_budget"
    if ratio <= 1:
        return "near_limit"
    if ratio <= 1.1:
        return "slightly_over"
    return "over_budget"


def _feasibility_score(data: DecisionInput) -> float:
    score = 1.0
    for day in data.itinerary:
        warnings_count = sum(1 for e in day.evidence if e.type == "warning")
        score -= warnings_count * 0.1
    return _clamp(score)


def _comfort_score(hotel: HotelOption | None, data: DecisionInput) -> float:
    score = 0.55
    if hotel and hotel.rating is not None:
        score += (hotel.rating - 3.0) / 5
    if hotel and hotel.distance_to_center_km is not None:
        score -= min(0.2, hotel.distance_to_center_km / 50)
    if data.trip_plan.comfort_level == "comfortable":
        score += 0.05
    return _clamp(score)


def _flight_tradeoffs(flight: FlightOption) -> list[str]:
    """Generate tradeoff tags for a flight option."""
    tradeoffs: list[str] = []
    dep = flight.departure_time
    if dep:
        try:
            hour = int(dep.split(":")[0])
            if hour < 7:
                tradeoffs.append("early_morning")
            elif hour >= 22:
                tradeoffs.append("red_eye")
            elif hour >= 18:
                tradeoffs.append("evening_flight")
        except (ValueError, IndexError):
            pass
    if flight.stops > 0:
        tradeoffs.append(f"{flight.stops}_stop{'s' if flight.stops > 1 else ''}")
    if flight.duration_minutes > 180:
        tradeoffs.append("long_flight")
    if flight.price > 3_000_000:
        tradeoffs.append("higher_price")
    elif flight.price < 1_500_000:
        tradeoffs.append("budget_price")
    return tradeoffs


def _build_option(
    option_id: str,
    data: DecisionInput,
    flight_index: int,
    hotel_index: int,
    feasibility: float,
) -> RankedOption:
    flight = data.flight_options[flight_index] if data.flight_options else None
    hotel = data.hotel_options[hotel_index] if data.hotel_options else None
    costs, flight_assumptions = _cost_breakdown(data, flight, hotel.price_per_night if hotel else 0)
    budget = data.trip_plan.budget_total
    cost_score = _clamp(1 - max(0, costs.total - (budget or costs.total)) / max(costs.total, 1))
    comfort = _comfort_score(hotel, data)
    weights = PRIORITY_PRESETS.get(data.trip_plan.priority, PRIORITY_PRESETS["cheapest"])
    value = _clamp(cost_score * weights["cost"] + feasibility * weights["feasibility"] + comfort * weights["comfort"])

    tradeoffs: list[str] = []
    if flight:
        tradeoffs.extend(_flight_tradeoffs(flight))
    if hotel and hotel.rating is not None and hotel.rating < 3.5:
        tradeoffs.append("low_hotel_rating")
    if hotel and hotel.distance_to_center_km is not None and hotel.distance_to_center_km > 5:
        tradeoffs.append("far_from_center")

    if feasibility >= 0.8:
        feasibility_status = "Khả thi"
    elif feasibility >= 0.5:
        feasibility_status = "Khả thi có điều kiện"
    else:
        feasibility_status = "Cần chỉnh sửa"

    if comfort >= 0.7:
        comfort_status = "Rất thoải mái"
    elif comfort >= 0.5:
        comfort_status = "Thoải mái"
    else:
        comfort_status = "Cơ bản"

    reasons = [
        f"Chi phí ước tính {costs.total:,.0f} {data.trip_plan.currency}.",
        f"Mức độ khả thi: {feasibility_status}. Mức độ thoải mái: {comfort_status}.",
    ]
    return RankedOption(
        id=option_id,
        flight_id=flight.id if flight else None,
        hotel_id=hotel.id if hotel else None,
        total_cost=costs.total,
        cost_score=cost_score,
        feasibility_score=feasibility,
        comfort_score=comfort,
        value_score=value,
        feasibility_status=feasibility_status,
        comfort_status=comfort_status,
        cost_breakdown=costs,
        tradeoffs=tradeoffs,
        reasons=reasons,
    )


def _cross_compare_reasons(recommended: RankedOption, all_options: list[RankedOption], currency: str) -> list[str]:
    """Generate why_recommended comparing recommended to other options."""
    reasons = list(recommended.reasons)
    for other in all_options:
        if other.id == recommended.id:
            continue
        cost_diff = other.total_cost - recommended.total_cost

        if cost_diff > recommended.total_cost * 0.01:
            reasons.append(
                f"Phương án {recommended.id} giúp tiết kiệm chi phí hơn so với {other.id} "
                f"(khoảng {abs(cost_diff):,.0f} {currency})."
            )
        elif cost_diff < -recommended.total_cost * 0.01:
            # Recommended is more expensive — explain the value tradeoff
            comfort_diff = recommended.comfort_score - other.comfort_score
            feasibility_diff = recommended.feasibility_score - other.feasibility_score
            tradeoff_parts: list[str] = []
            if comfort_diff > 0.05:
                tradeoff_parts.append("có thời gian nghỉ ngơi thoải mái hơn")
            if feasibility_diff > 0.05:
                tradeoff_parts.append("lộ trình khả thi hơn")
            tradeoff_text = " và ".join(tradeoff_parts) if tradeoff_parts else "đem lại trải nghiệm tốt hơn"
            reasons.append(
                f"Phương án {recommended.id} có chi phí cao hơn {other.id} một chút "
                f"nhưng đổi lại {tradeoff_text}."
            )
    return reasons





def _risks(data: DecisionInput, total: float, status: str) -> list[Risk]:
    risks: list[Risk] = []
    if status in {"near_limit", "slightly_over", "over_budget"}:
        severity = "high" if status == "over_budget" else "medium"
        risks.append(Risk(type="budget_tight", severity=severity, message="Ngân sách đang sát hoặc vượt mức dự kiến."))
    for day in data.itinerary:
        if day.evidence:
            risks.append(
                Risk(
                    type="day_too_dense",
                    severity="medium",
                    message=f"Ngày {day.day} có lịch trình dày hoặc vi phạm rule di chuyển.",
                    recommendation="Kiểm tra lại evidence chi tiết của ngày để điều chỉnh.",
                    target_day=day.day,
                    suggested_action="optimize_day",
                )
            )
    # Weather + outdoor mismatch
    for day in data.itinerary:
        day_weather = next((w for w in data.weather_forecasts if w.date == day.date), None)
        if day_weather and day_weather.rain_probability >= 0.6:
            outdoor_items = [item for item in day.items if item.outdoor]
            if outdoor_items:
                names = ", ".join(item.title for item in outdoor_items[:3])
                risks.append(
                    Risk(
                        type="weather_outdoor_mismatch",
                        severity="medium",
                        message=f"Ngày {day.day}: mưa {day_weather.rain_probability:.0%} nhưng có hoạt động ngoài trời ({names}).",
                        recommendation="Dời hoạt động ngoài trời sang ngày khác hoặc chuẩn bị phương án trong nhà.",
                        target_day=day.day,
                        target_place_id=outdoor_items[0].place_id if outdoor_items else None,
                        suggested_action="replace_place",
                    )
                )
            else:
                risks.append(Risk(type="bad_weather", severity="medium", message=f"Khả năng mưa cao tại {day_weather.location} ngày {day_weather.date}.", target_day=day.day))



    # Distance too high per day
    for day in data.itinerary:
        if day.travel_minutes > 0:
            # Estimate km from travel_minutes (avg 30km/h city driving)
            est_km = day.travel_minutes * 30 / 60
            if est_km > 60:
                risks.append(
                    Risk(
                        type="distance_too_high",
                        severity="medium",
                        message=f"Ngày {day.day} ước tính di chuyển ~{est_km:.0f} km — kiểm tra lại tuyến.",
                        recommendation="Gộp các điểm gần nhau hoặc bỏ điểm xa nhất.",
                        target_day=day.day,
                        suggested_action="optimize_day",
                    )
                )

    for review in data.review_summaries:
        if review.confidence == "low" or review.risk_flags:
            hotel_name = next((h.name for h in data.hotel_options if h.id == review.target_id), None)
            place_name = next((p.name for p in data.place_options if p.id == review.target_id), None)
            target_name = hotel_name or place_name or review.target_id
            risks.append(
                Risk(
                    type="weak_reviews",
                    severity="medium",
                    message=f"Dữ liệu đánh giá cho '{target_name}' có độ tin cậy thấp hoặc có phản hồi tiêu cực.",
                    target_place_id=review.target_id if not hotel_name else None,
                    suggested_action="replace_place" if not hotel_name else None,
                )
            )
    if any(record.data_mode == "fixture" for group in [
        data.flight_options,
        data.hotel_options,
        data.place_options,
        data.route_segments,
        data.weather_forecasts,
        data.review_summaries,
    ] for record in group):
        risks.append(Risk(type="fixture_data", severity="low", message="Một phần dữ liệu đang dùng fixture để demo."))
    if not data.route_segments:
        risks.append(Risk(type="missing_routes", severity="medium", message="Chưa có dữ liệu tuyến đường để xác minh thời gian di chuyển."))
    return risks


def build_decision(data: DecisionInput) -> DecisionOutput:
    # ── Step 1: Evaluate coverage ─────────────────────
    coverage = evaluate_coverage(data)

    flights = sorted(data.flight_options, key=lambda item: item.price)
    hotels = sorted(data.hotel_options, key=lambda item: item.price_per_night)
    comfortable_hotels = sorted(data.hotel_options, key=lambda item: (item.rating or 0, -(item.distance_to_center_km or 0)), reverse=True)
    normalized = data.model_copy(update={"flight_options": flights, "hotel_options": hotels})
    feasibility = _feasibility_score(normalized)

    # ── Step 2: Build options if possible ──────────────
    options: list[RankedOption] = []
    if flights and hotels:
        cheapest_opt = _build_option("cheapest", normalized, 0, 0, feasibility)
        options.append(cheapest_opt)
        
        balanced_opt = _build_option("balanced", normalized, min(1, max(len(flights) - 1, 0)), min(1, max(len(hotels) - 1, 0)), feasibility)
        
        def is_meaningful(opt: RankedOption, reference: RankedOption) -> bool:
            if not opt or not reference:
                return False
            cost_diff_ratio = abs(opt.total_cost - reference.total_cost) / max(reference.total_cost, 1)
            comfort_diff = opt.comfort_status != reference.comfort_status
            feasibility_diff = opt.feasibility_status != reference.feasibility_status
            tradeoff_diff = set(opt.tradeoffs) != set(reference.tradeoffs)
            return cost_diff_ratio >= 0.03 or comfort_diff or feasibility_diff or tradeoff_diff

        if is_meaningful(balanced_opt, cheapest_opt):
            options.append(balanced_opt)
            
        if comfortable_hotels:
            comfortable_index = hotels.index(comfortable_hotels[0])
            comfortable_opt = _build_option("comfortable", normalized, min(1, max(len(flights) - 1, 0)), comfortable_index, feasibility)
            
            if all(is_meaningful(comfortable_opt, accepted) for accepted in options):
                options.append(comfortable_opt)

    # ── Step 3: Determine recommendation ──────────────
    can_recommend = (
        coverage.status in ("verified", "estimated")
        and coverage.confidence in ("high", "medium")
        and options
    )

    if can_recommend:
        recommended = max(options, key=lambda item: item.value_score)
        decision_status = "recommended"
    else:
        recommended = max(options, key=lambda item: item.value_score) if options else None
        if coverage.status == "unsupported":
            decision_status = "insufficient_data"
        elif not options:
            decision_status = "insufficient_data"
        else:
            decision_status = "needs_revision"

    # ── Step 4: Build output ──────────────────────────
    if recommended:
        costs = recommended.cost_breakdown
    elif options:
        costs = options[0].cost_breakdown
    else:
        # Pass None for flight to _cost_breakdown to get base costs
        costs, _ = _cost_breakdown(normalized, None, 0)

    budget = normalized.trip_plan.budget_total
    status = _budget_status(costs.total, budget)

    assumptions = list(COST_RULES_V1["assumptions"])
    
    # Re-evaluate flight assumptions for the recommended/first option
    if recommended and recommended.flight_id:
        rec_flight = next((f for f in normalized.flight_options if f.id == recommended.flight_id), None)
        _, f_assump = _cost_breakdown(normalized, rec_flight, 0)
        assumptions.extend(f_assump)
    elif options and options[0].flight_id:
        rec_flight = next((f for f in normalized.flight_options if f.id == options[0].flight_id), None)
        _, f_assump = _cost_breakdown(normalized, rec_flight, 0)
        assumptions.extend(f_assump)

    assumptions.extend(
        assumption
        for group in [
            normalized.flight_options,
            normalized.hotel_options,
            normalized.place_options,
            normalized.route_segments,
            normalized.weather_forecasts,
        ]
        for record in group
        for assumption in record.assumptions
        if assumption not in assumptions
    )

    weather_dates = {w.date for w in normalized.weather_forecasts}
    for day in normalized.itinerary:
        if day.date and day.date not in weather_dates:
            missing_weather_assump = "Dữ liệu thời tiết không có sẵn cho toàn bộ chuyến đi, bỏ qua kiểm tra rủi ro thời tiết."
            if missing_weather_assump not in assumptions:
                assumptions.append(missing_weather_assump)

    # Only provide booking links and why_recommended for verified recommendations
    booking_links: list[str] = []
    why_recommended: list[str] = []
    if can_recommend and recommended:
        booking_links = [
            link
            for link in [
                next((item.booking_url for item in normalized.flight_options if item.id == recommended.flight_id), None),
                next((item.booking_url for item in normalized.hotel_options if item.id == recommended.hotel_id), None),
            ]
            if link
        ]
        why_recommended = _cross_compare_reasons(recommended, options, normalized.trip_plan.currency)

    return DecisionOutput(
        recommended_option=recommended.id if can_recommend and recommended else None,
        budget_status=status,
        total_cost=costs.total,
        total_cost_per_person=round(costs.total / max(normalized.trip_plan.travelers, 1)),
        budget_delta=round(costs.total - budget) if budget else None,
        feasibility_score=recommended.feasibility_score if recommended else feasibility,
        comfort_score=recommended.comfort_score if recommended else 0.0,
        value_score=recommended.value_score if recommended else 0.0,
        cost_breakdown=costs,
        options=options,
        itinerary=normalized.itinerary,
        risks=_risks(normalized, costs.total, status),
        assumptions=assumptions,
        why_recommended=why_recommended,
        booking_links=booking_links,
        # Coverage & trust fields
        coverage_status=coverage.status,
        decision_status=decision_status,
        confidence=coverage.confidence,
        blocking_reasons=coverage.blocking_reasons,
        rule_version=COST_RULES_V1["version"],
        data_freshness=coverage.data_freshness,
    )
