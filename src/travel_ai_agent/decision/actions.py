from __future__ import annotations

import math
from typing import Any

from travel_ai_agent.api.schemas.trip import TripActionRequest, TripActionResponse
from travel_ai_agent.schemas.domain import DecisionInput, DecisionOutput, PlaceOption, RouteSegment, ItineraryDay
from travel_ai_agent.decision.engine import build_decision
from travel_ai_agent.decision.itinerary import enrich_itinerary_routes

def _distance_between(p1: PlaceOption, p2: PlaceOption) -> float:
    # A simple euclidean distance or haversine for nearest neighbor
    lat1, lon1 = p1.lat or 0, p1.lng or 0
    lat2, lon2 = p2.lat or 0, p2.lng or 0
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def optimize_day(target_day: int, data: DecisionInput, decision: DecisionOutput) -> TripActionResponse:
    # Find the day in the itinerary
    day_idx = next((i for i, d in enumerate(data.itinerary) if d.day == target_day), -1)
    if day_idx == -1:
        raise ValueError(f"Day {target_day} not found in itinerary")
        
    day_itinerary = data.itinerary[day_idx]
    
    if not day_itinerary.items:
        return TripActionResponse(
            status="no_action",
            message="Không có địa điểm nào trong ngày để tối ưu."
        )
        
    places_in_day = []
    for item in day_itinerary.items:
        place = next((p for p in data.place_options if p.id == item.place_id), None)
        if place:
            places_in_day.append(place)
            
    if len(places_in_day) <= 2:
        return TripActionResponse(
            status="no_action",
            message="Ngày có quá ít điểm (<= 2) nên không cần tối ưu."
        )
        
    # Get hotel for anchor
    hotel = data.hotel_options[0] if data.hotel_options else None
    
    # Nearest neighbor
    unvisited = places_in_day.copy()
    optimized_places = []
    
    # Start from hotel or first place
    if hotel:
        # Create a dummy PlaceOption for hotel to use distance
        current = PlaceOption(id=hotel.id, provider="hotel", category="hotel", name=hotel.name, title=hotel.name, lat=hotel.lat, lng=hotel.lng, price_level=1)
    else:
        current = unvisited.pop(0)
        optimized_places.append(current)
        
    while unvisited:
        # find nearest
        nearest = min(unvisited, key=lambda p: _distance_between(current, p))
        unvisited.remove(nearest)
        optimized_places.append(nearest)
        current = nearest
        
    # Build new ordered lists
    all_ordered_places = []
    for d in data.itinerary:
        if d.day == target_day:
            all_ordered_places.append(optimized_places)
        else:
            ps = []
            for item in d.items:
                p = next((p_opt for p_opt in data.place_options if p_opt.id == item.place_id), None)
                if p: ps.append(p)
            all_ordered_places.append(ps)
            
    old_travel_time = day_itinerary.travel_minutes
    new_itinerary = enrich_itinerary_routes(
        data.trip_plan, 
        all_ordered_places, 
        data.route_segments, 
        flights=data.flight_options
    )
    
    new_day = next(d for d in new_itinerary if d.day == target_day)
    new_travel_time = new_day.travel_minutes
    
    if new_travel_time >= old_travel_time:
        return TripActionResponse(
            status="no_action",
            message="Tuyến đường hiện tại đã tối ưu."
        )
        
    # Build new decision
    data.itinerary = new_itinerary
    new_decision = build_decision(data)
    
    return TripActionResponse(
        status="success",
        message=f"Đã giảm thời gian di chuyển từ {old_travel_time} xuống {new_travel_time} phút.",
        before_summary={"travel_minutes": old_travel_time},
        after_summary={"travel_minutes": new_travel_time},
        decision=new_decision
    )

async def replace_place(target_place_id: str, data: DecisionInput, decision: DecisionOutput, session_id: str) -> TripActionResponse:
    target_day_idx = -1
    target_item_idx = -1
    for i, day in enumerate(data.itinerary):
        for j, item in enumerate(day.items):
            if item.place_id == target_place_id:
                target_day_idx = i
                target_item_idx = j
                break
        if target_day_idx != -1:
            break
            
    if target_day_idx == -1:
        raise ValueError(f"Địa điểm {target_place_id} không có trong lịch trình.")
        
    day_itinerary = data.itinerary[target_day_idx]
    
    current_place = next((p for p in data.place_options if p.id == target_place_id), None)
    if not current_place:
        raise ValueError(f"Không tìm thấy thông tin cho {target_place_id}")
        
    category = current_place.category
    
    used_place_ids = {item.place_id for day in data.itinerary for item in day.items}
    candidates = [
        p for p in data.place_options 
        if p.category == category 
        and p.id not in used_place_ids
        and getattr(p, "place_match_status", "") != "unverified"
        and getattr(p, "confidence", "") != "missing"
    ]
    
    if not candidates:
        return TripActionResponse(
            status="no_action",
            message="Không tìm thấy địa điểm thay thế phù hợp cùng loại."
        )
        
    best_candidate = candidates[0]
    
    all_ordered_places = []
    for d in data.itinerary:
        ps = []
        for item in d.items:
            if item.place_id == target_place_id:
                ps.append(best_candidate)
            else:
                p = next((p_opt for p_opt in data.place_options if p_opt.id == item.place_id), None)
                if p: ps.append(p)
        all_ordered_places.append(ps)
        
    day_places = all_ordered_places[target_day_idx]
    hotel = data.hotel_options[0] if data.hotel_options else None
    
    if hotel:
        hotel_place = PlaceOption(id=hotel.id, provider="hotel", category="hotel", name=hotel.name, title=hotel.name, lat=hotel.lat, lng=hotel.lng, price_level=1)
        route_sequence = [hotel_place] + day_places + [hotel_place]
    else:
        route_sequence = day_places
        
    from travel_ai_agent.providers.gateway import fetch_routes
    import asyncio
    new_routes = await asyncio.to_thread(fetch_routes, route_sequence, session_id)
    
    existing_pairs = {(r.from_place_id, r.to_place_id) for r in data.route_segments}
    for r in new_routes:
        if (r.from_place_id, r.to_place_id) not in existing_pairs:
            data.route_segments.append(r)
            existing_pairs.add((r.from_place_id, r.to_place_id))
            
    new_itinerary = enrich_itinerary_routes(
        data.trip_plan, 
        all_ordered_places, 
        data.route_segments, 
        flights=data.flight_options
    )
    
    data.itinerary = new_itinerary
    new_decision = build_decision(data)
    
    return TripActionResponse(
        status="success",
        message=f"Đã thay {current_place.name} bằng {best_candidate.name}.",
        before_summary={"replaced": current_place.name},
        after_summary={"replacement": best_candidate.name},
        decision=new_decision
    )

async def execute_trip_action(req: TripActionRequest, data: DecisionInput, decision: DecisionOutput, session_id: str) -> TripActionResponse:
    if req.action == "optimize_day":
        if not req.target_day:
            raise ValueError("target_day is required for optimize_day")
        return optimize_day(req.target_day, data, decision)
    elif req.action == "replace_place":
        if not req.target_place_id:
            raise ValueError("target_place_id is required for replace_place")
        return await replace_place(req.target_place_id, data, decision, session_id)
    else:
        raise ValueError("Invalid action")
