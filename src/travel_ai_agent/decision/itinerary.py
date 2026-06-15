"""Per-day itinerary builder for the Decision Engine.

Phân bố places theo cụm địa lý (greedy nearest-neighbor), tôn trọng comfort_level:
- budget / medium: tối đa 3 places/ngày
- comfortable: tối đa 2 places/ngày

Tính travel_minutes mỗi ngày bằng cách cộng route segments giữa các place
trong cùng ngày (dùng route_segments lookup) hoặc ước lượng theo khoảng cách
Haversine khi không có route.
"""
from __future__ import annotations

import math
from datetime import timedelta

from travel_ai_agent.schemas import (
    DecisionEvidence,
    FlightOption,
    ItineraryDay,
    ItineraryItem,
    ItineraryLeg,
    PlaceOption,
    RouteSegment,
    TripPlan,
    HotelOption,
)


def _places_per_day(comfort_level: str | None) -> int:
    if comfort_level == "comfortable":
        return 2
    return 3


def _haversine_km(a: PlaceOption, b: PlaceOption) -> float | None:
    if a.lat is None or a.lng is None or b.lat is None or b.lng is None:
        return None
    r = 6371.0
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlng = math.radians(b.lng - a.lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _route_lookup(routes: list[RouteSegment]) -> dict[tuple[str, str], RouteSegment]:
    lookup: dict[tuple[str, str], RouteSegment] = {}
    for route in routes:
        lookup[(route.from_place_id, route.to_place_id)] = route
        lookup[(route.to_place_id, route.from_place_id)] = route
    return lookup


def _segment_minutes(a: PlaceOption, b: PlaceOption, lookup: dict[tuple[str, str], RouteSegment]) -> int:
    route = lookup.get((a.id, b.id))
    if route and route.duration_minutes:
        return int(route.duration_minutes)
    distance = _haversine_km(a, b)
    if distance is None:
        return 20  # default fallback per leg
    # Assume city driving avg 25 km/h
    return max(10, int(distance / 25 * 60))


def _segment_km(a: PlaceOption, b: PlaceOption, lookup: dict[tuple[str, str], RouteSegment]) -> float:
    route = lookup.get((a.id, b.id))
    if route and route.distance_km:
        return float(route.distance_km)
    distance = _haversine_km(a, b)
    return distance if distance is not None else 5.0


def _cluster_by_proximity(places: list[PlaceOption], days: int, per_day: int, is_food_tour: bool) -> list[list[PlaceOption]]:
    if not places or days <= 0:
        return [[] for _ in range(max(days, 0))]

    priority_rank = {"must_go": 0, "recommended": 1, "optional": 2}
    remaining = sorted(places, key=lambda place: priority_rank.get(place.priority, 1))
    
    # Build a continuous chain
    ordered: list[PlaceOption] = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        next_idx = 0
        best_distance = float("inf")
        for index, candidate in enumerate(remaining):
            distance = _haversine_km(last, candidate)
            distance = distance if distance is not None else 100.0
            if distance < best_distance:
                best_distance = distance
                next_idx = index
        ordered.append(remaining.pop(next_idx))

    # Group into chunks geographically (by dividing the chain evenly)
    chunks: list[list[PlaceOption]] = [[] for _ in range(days)]
    base_count = len(ordered) // days
    extra = len(ordered) % days
    
    idx = 0
    for day in range(days):
        count = base_count + (1 if day < extra else 0)
        for _ in range(count):
            if idx < len(ordered):
                chunks[day].append(ordered[idx])
                idx += 1

    # Balance each chunk
    balanced_chunks = []
    for chunk in chunks:
        if not chunk:
            balanced_chunks.append([])
            continue
            
        if not is_food_tour:
            # Enforce max 2 food places
            food_count = 0
            filtered = []
            for p in chunk:
                if p.category == "food":
                    if food_count < 2:
                        filtered.append(p)
                        food_count += 1
                else:
                    filtered.append(p)
            chunk = filtered
            
        # Reorder to avoid consecutive food
        reordered = [chunk.pop(0)]
        while chunk:
            last_cat = reordered[-1].category
            best_idx = 0
            best_score = float("inf")
            for i, cand in enumerate(chunk):
                dist = _haversine_km(reordered[-1], cand) or 10.0
                penalty = 1000.0 if last_cat == "food" and cand.category == "food" else 0.0
                if dist + penalty < best_score:
                    best_score = dist + penalty
                    best_idx = i
            reordered.append(chunk.pop(best_idx))
            
        balanced_chunks.append(reordered)
        
    return balanced_chunks



def _calculate_flight_time_loss(day_index: int, total_days: int, flights: list[FlightOption] | None) -> int:
    """Calculate minutes lost from a standard day due to flight schedules."""
    if not flights:
        return 0
    # Simplistic heuristic:
    # If first day, and flight arrives later than 09:00, we lose those morning minutes.
    if day_index == 0:
        # Assuming we take the first flight in the list as the outbound
        f = flights[0]
        if f.arrival_time:
            try:
                hour = int(f.arrival_time.split(":")[0])
                if hour > 9:
                    return (hour - 9) * 60
            except (ValueError, IndexError):
                pass
    # If last day, and flight departs before 18:00, we lose those evening minutes.
    if day_index == total_days - 1 and day_index > 0:
        # Simplistic: use second flight if round trip, or just first if one-way
        f = flights[-1] if len(flights) > 1 else flights[0]
        if f.departure_time:
            try:
                hour = int(f.departure_time.split(":")[0])
                if hour < 18:
                    return (18 - hour) * 60
            except (ValueError, IndexError):
                pass
    return 0


def _check_route_backtracking_day(day_places: list[PlaceOption]) -> list[str]:
    """Check if the itinerary backtracks significantly (revisits area) and return problematic place names."""
    if len(day_places) < 3:
        return []
    geo_places = [(p, p.lat, p.lng) for p in day_places if p.lat is not None and p.lng is not None]
    if len(geo_places) < 3:
        return []
    
    backtracking_places = []
    for i in range(2, len(geo_places)):
        curr_lat, curr_lng = geo_places[i][1], geo_places[i][2]
        prev_lat, prev_lng = geo_places[i - 1][1], geo_places[i - 1][2]
        start_lat, start_lng = geo_places[0][1], geo_places[0][2]
        dist_curr_to_start = abs(curr_lat - start_lat) + abs(curr_lng - start_lng)
        dist_prev_to_start = abs(prev_lat - start_lat) + abs(prev_lng - start_lng)
        if dist_curr_to_start < dist_prev_to_start * 0.5:
            backtracking_places.append(geo_places[i][0].name)
    return backtracking_places


def build_itinerary_order(
    plan: TripPlan,
    places: list[PlaceOption],
    hotel: HotelOption | None = None,
) -> list[list[PlaceOption]]:
    """Build the sequential order of places for each day without fetching routes."""
    days = plan.days or 1
    per_day = _places_per_day(plan.comfort_level)
    
    trip_theme = (plan.trip_type or "").lower()
    prefs = " ".join(plan.preferences).lower()
    is_food_tour = "food" in trip_theme or "food" in prefs or "ẩm thực" in prefs or "hải sản" in prefs
    
    clusters = _cluster_by_proximity(places, days, per_day, is_food_tour)
    
    hotel_place = None
    if hotel:
        hotel_place = PlaceOption(
            id=hotel.id,
            name=hotel.name,
            provider=hotel.provider,
            category="hotel",
            lat=hotel.lat,
            lng=hotel.lng,
            provider_place_id=hotel.provider_place_id,
            place_match_status="verified" if hotel.provider_place_id else "unverified"
        )
        
    ordered_clusters: list[list[PlaceOption]] = []
    for day_index in range(days):
        day_places = clusters[day_index] if day_index < len(clusters) else []
        if hotel_place and day_places:
            day_places = [hotel_place] + day_places + [hotel_place]
        ordered_clusters.append(day_places)
        
    return ordered_clusters


def enrich_itinerary_routes(
    plan: TripPlan,
    ordered_clusters: list[list[PlaceOption]],
    routes: list[RouteSegment],
    flights: list[FlightOption] | None = None,
) -> list[ItineraryDay]:
    """Take ordered places and route segments to build the final ItineraryDay objects."""
    days = plan.days or 1
    route_lookup = _route_lookup(routes)

    load_limits = {
        "comfortable": 480, # 8 hours
        "medium": 600,      # 10 hours
        "budget": 660,      # 11 hours
    }
    base_limit = load_limits.get(plan.comfort_level, 600)

    itinerary: list[ItineraryDay] = []
    for day_index, day_places in enumerate(ordered_clusters):
        day_date = (plan.departure_date + timedelta(days=day_index)) if plan.departure_date else None

        items = [
            ItineraryItem(
                place_id=place.id,
                title=place.name,
                category=place.category,
                outdoor="outdoor" in (place.tags or []),
                estimated_cost=float(place.estimated_cost or 0),
                estimated_visit_minutes=place.estimated_visit_minutes,
                maps_url=place.maps_url,
                confidence=place.place_match_status,
            )
            for place in day_places
            if place.category != "hotel" # S1-06: Do not render hotel as a standard visit item
        ]

        route_legs: list[ItineraryLeg] = []
        travel_minutes = 0
        total_km = 0.0
        route_status = "verified"
        
        for a, b in zip(day_places, day_places[1:]):
            route = route_lookup.get((a.id, b.id))
            
            if route and route.duration_minutes is not None:
                dist = float(route.distance_km) if route.distance_km is not None else None
                dur = int(route.duration_minutes)
                provider = route.provider
                data_mode = route.data_mode
                confidence = "verified" if route.data_mode == "live" else "unverified"
            else:
                dist_val = _haversine_km(a, b)
                if dist_val is None:
                    dist = None
                    dur = None
                    confidence = "unverified"
                else:
                    dist = dist_val
                    dur = max(10, int(dist_val / 25 * 60))
                    confidence = "estimated"
                provider = "haversine_fallback" if dist_val is not None else "missing"
                data_mode = "missing"
                
            if confidence == "unverified":
                route_status = "unverified"
            elif confidence == "estimated" and route_status == "verified":
                route_status = "estimated"
                
            dir_url = None
            if a.lat is not None and a.lng is not None and b.lat is not None and b.lng is not None:
                dir_url = f"https://www.google.com/maps/dir/?api=1&origin={a.lat},{a.lng}&destination={b.lat},{b.lng}&travelmode=driving"

            leg = ItineraryLeg(
                from_place_id=a.id,
                from_label=a.name,
                to_place_id=b.id,
                to_label=b.name,
                mode="driving",
                distance_km=round(dist, 1) if dist is not None else None,
                duration_minutes=dur,
                provider=provider,
                data_mode=data_mode,
                confidence=confidence,
                directions_url=dir_url
            )
            route_legs.append(leg)
            if dur is not None:
                travel_minutes += dur
            if dist is not None:
                total_km += dist

        total_visit_minutes = sum(item.estimated_visit_minutes for item in items)
        
        is_family = "family" in (plan.trip_type or "").lower() or "gia đình" in (plan.trip_type or "").lower() or plan.travelers >= 3
        buffer_time = 120 if is_family else 90
        total_load = total_visit_minutes + travel_minutes + buffer_time
        
        flight_loss = _calculate_flight_time_loss(day_index, days, flights)
        daily_limit = max(0, base_limit - flight_loss)
        
        # S2-03: Family load limit (giảm 20% thời lượng hoạt động tối đa)
        if is_family:
            daily_limit = int(daily_limit * 0.8)

        evidence: list[DecisionEvidence] = []
        
        # S2-02: Missing diversity
        non_hotel_items = [i for i in items if i.category != "hotel"]
        if non_hotel_items and all(i.category == "food" for i in non_hotel_items):
            evidence.append(DecisionEvidence(
                type="warning",
                rule="Đa dạng hoạt động (ít nhất 1 non-food activity mỗi ngày)",
                observed_value="Toàn bộ là food/nhà hàng",
                recommendation="Ngày này chỉ có ăn uống. Bạn nên cân nhắc thêm các điểm tham quan hoặc vui chơi.",
            ))
            
        # S2-03: Long route warning for family
        if is_family and travel_minutes > 120:
            evidence.append(DecisionEvidence(
                type="warning",
                rule="Hạn chế di chuyển quá dài cho chuyến đi gia đình",
                observed_value=f"{travel_minutes} phút di chuyển",
                threshold="120 phút",
                recommendation="Cần lưu ý chuẩn bị thêm đồ nghỉ ngơi trên xe cho trẻ em/người lớn tuổi vì thời gian di chuyển khá dài.",
            ))
        if total_load > daily_limit:
            removable = day_places[-1] if day_places else None
            evidence.append(DecisionEvidence(
                type="warning",
                rule=f"Tối đa {daily_limit/60:.1f} giờ hoạt động cho mức {plan.comfort_level}",
                observed_value=f"{total_load/60:.1f} giờ",
                threshold=f"{daily_limit/60:.1f} giờ",
                recommendation=f"Lịch trình quá dày. Gợi ý bỏ '{removable.name}' hoặc dời sang ngày khác." if removable else "Lịch trình quá dày.",
                target_id=removable.id if removable else None,
                suggested_actions=["remove_place"] if removable else []
            ))

        if travel_minutes > 180:
            furthest = day_places[-1] if day_places else None
            evidence.append(DecisionEvidence(
                type="warning",
                rule="Tổng thời gian di chuyển trong ngày không nên vượt quá 180 phút",
                observed_value=f"{travel_minutes} phút",
                threshold="180 phút",
                recommendation="Nên gộp các điểm gần nhau hoặc bỏ điểm xa nhất.",
                target_id=furthest.id if furthest else None,
                suggested_actions=["optimize_route", "remove_place"]
            ))
            
        if total_km > 60:
             evidence.append(DecisionEvidence(
                type="warning",
                rule="Quãng đường di chuyển trong ngày không nên quá xa",
                observed_value=f"~{total_km:.0f} km",
                threshold="60 km",
                recommendation="Kiểm tra lại tuyến đường đi, các điểm đang quá xa nhau.",
                suggested_actions=["optimize_route"]
            ))
             
        backtracking = _check_route_backtracking_day(day_places)
        if backtracking:
            evidence.append(DecisionEvidence(
                type="warning",
                rule="Lộ trình không nên vòng vèo quay lại điểm bắt đầu giữa chừng",
                observed_value="Phát hiện quay vòng",
                recommendation=f"Điểm {', '.join(backtracking)} đang bị vòng ngược. Hãy sắp xếp lại lộ trình.",
                suggested_actions=["optimize_route"]
            ))
            
        # Duplicate names detection
        seen_names = set()
        for p in day_places:
            if p.name in seen_names:
                evidence.append(DecisionEvidence(
                    type="warning",
                    rule="Không nên có các địa điểm trùng tên trong cùng một ngày",
                    observed_value=f"Trùng '{p.name}'",
                    recommendation="Có vẻ hệ thống đã nhầm lẫn lấy 2 địa điểm giống nhau. Vui lòng thay đổi.",
                    target_id=p.id,
                    suggested_actions=["change_place"]
                ))
            seen_names.add(p.name)

        areas = list(dict.fromkeys(p.area for p in day_places if p.area))
        area_summary = " - ".join(areas) if areas else ""

        itinerary.append(
            ItineraryDay(
                day=day_index + 1,
                date=day_date,
                title=f"Ngày {day_index + 1}",
                items=items,
                travel_minutes=travel_minutes,
                evidence=evidence,
                route_legs=route_legs,
                total_visit_minutes=total_visit_minutes,
                area_summary=area_summary,
                route_status=route_status,
            )
        )

    return itinerary
