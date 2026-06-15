from __future__ import annotations

from travel_ai_agent.schemas import FlightOption, HotelOption, PlaceOption, ReviewSummary, RouteSegment


def normalize_flights(items: list[dict], provider: str = "serpapi_google_flights") -> list[FlightOption]:
    return [
        FlightOption(
            id=f"flight_{index}",
            provider=provider,
            data_mode=item.get("data_mode", "live"),
            assumptions=["Đang dùng dữ liệu fixture do provider live không khả dụng."] if item.get("data_mode") == "fixture" else [],
            airline=item.get("airline") or "Không rõ hãng",
            departure_time=item.get("departure_time", ""),
            arrival_time=item.get("arrival_time", ""),
            duration_minutes=item.get("total_duration", item.get("duration_minutes", 0)) or 0,
            stops=item.get("stops", 0) or 0,
            price=item.get("price", 0) or 0,
            price_scope=item.get("price_scope", "one_way_per_traveler"),
            booking_url=item.get("booking_url"),
        )
        for index, item in enumerate(items, 1)
    ]


def normalize_hotels(items: list[dict], provider: str = "serpapi_google_hotels") -> list[HotelOption]:
    return [
        HotelOption(
            id=f"hotel_{index}",
            provider=provider,
            data_mode=item.get("data_mode", "live"),
            assumptions=["Đang dùng dữ liệu fixture do provider live không khả dụng."] if item.get("data_mode") == "fixture" else [],
            name=item.get("name") or "Khách sạn chưa rõ tên",
            area=item.get("location", item.get("area", "")),
            price_per_night=item.get("price", item.get("price_per_night", 0)) or 0,
            rating=item.get("rating") or None,
            review_count=item.get("reviews", item.get("review_count", 0)) or 0,
            booking_url=item.get("booking_url"),
            amenities=item.get("amenities", []),
        )
        for index, item in enumerate(items, 1)
    ]


def _map_category(raw_category: str) -> str:
    if not raw_category:
        return "attraction"
        
    raw = str(raw_category).lower()
    
    if any(x in raw for x in ["night", "club", "đêm", "chợ đêm", "night market", "lounge", "karaoke"]):
        return "nightlife"
    if any(x in raw for x in ["restaurant", "cafe", "food", "nhà hàng", "quán ăn", "bar", "pub", "ẩm thực", "bakery", "ăn uống", "đặc sản"]):
        return "food"
    if any(x in raw for x in ["museum", "temple", "church", "historic", "culture", "bảo tàng", "đền", "chùa", "nhà thờ", "di tích", "văn hóa", "history", "lịch sử", "monument"]):
        return "culture"
    if any(x in raw for x in ["beach", "park", "nature", "mountain", "bãi biển", "công viên", "núi", "thiên nhiên", "biển", "island", "đảo", "lake", "hồ", "garden", "vườn", "thác"]):
        return "beach/nature"
    if any(x in raw for x in ["mall", "market", "shop", "store", "chợ", "mua sắm", "cửa hàng", "siêu thị", "supermarket"]):
        return "shopping"
    if any(x in raw for x in ["spa", "massage", "relax", "thư giãn", "nghỉ ngơi", "resort", "rest"]):
        return "rest/flexible"
        
    return "attraction"


def normalize_places(items: list[dict], provider: str = "serpapi_google_local") -> list[PlaceOption]:
    places = []
    for index, item in enumerate(items, 1):
        name = item.get("title", item.get("name", "Địa điểm chưa rõ tên"))
        address = item.get("address", "")
        place_id = item.get("place_id")
        
        lat = (item.get("gps_coordinates") or {}).get("latitude", item.get("lat"))
        lng = (item.get("gps_coordinates") or {}).get("longitude", item.get("lng"))
        
        if place_id:
            maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            status = "verified"
            confidence = "high"
        elif lat is not None and lng is not None:
            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
            status = "unverified"
            confidence = "medium"
        else:
            maps_url = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}"
            status = "unverified"
            confidence = "low"
            
        places.append(PlaceOption(
            id=f"place_{index}",
            provider=provider,
            data_mode=item.get("data_mode", "live"),
            assumptions=item.get("assumptions", []),
            name=name,
            category=_map_category(item.get("type", item.get("category", ""))),
            rating=item.get("rating") or None,
            review_count=item.get("reviews", item.get("review_count", 0)) or 0,
            lat=lat,
            lng=lng,
            estimated_visit_minutes=item.get("estimated_visit_minutes", 90),
            estimated_cost=item.get("estimated_cost", 0) or 0,
            tags=item.get("tags", []),
            address=address,
            provider_place_id=place_id,
            maps_url=maps_url,
            place_match_status=status,
            place_match_confidence=confidence,
        ))
    return places


def fixture_places(destination: str | None) -> list[PlaceOption]:
    destination = destination or "Điểm đến"
    names = [
        ("Biển trung tâm", "beach", True, 0),
        ("Khu ẩm thực địa phương", "food", False, 350_000),
        ("Điểm văn hóa nổi bật", "culture", False, 150_000),
        ("Khu ngắm cảnh", "sightseeing", True, 200_000),
    ]
    return [
        PlaceOption(
            id=f"place_{index}",
            provider="mvp_fixture",
            data_mode="fixture",
            assumptions=[f"Địa điểm mẫu dùng để kiểm tra Decision Engine cho {destination}."],
            name=f"{name} - {destination}",
            category=category,
            estimated_cost=cost,
            tags=["outdoor"] if outdoor else ["indoor"],
            address=f"Trung tâm {destination}",
            place_match_status="fixture",
            place_match_confidence="low",
            lat=10.0 + index * 0.01,
            lng=105.0 + index * 0.01,
        )
        for index, (name, category, outdoor, cost) in enumerate(names, 1)
    ]


def fixture_routes(places: list[PlaceOption]) -> list[RouteSegment]:
    return [
        RouteSegment(
            provider="mvp_fixture",
            data_mode="fixture",
            assumptions=["Thời gian tuyến đường là fixture, cần xác minh trước khi đặt chỗ."],
            from_place_id=places[index - 1].id,
            to_place_id=places[index].id,
            distance_km=8 + index * 3,
            duration_minutes=25 + index * 10,
        )
        for index in range(1, len(places))
    ]


def normalize_reviews(hotel_id: str, raw_reviews: list[dict], provider: str = "serpapi_google_maps_reviews") -> ReviewSummary:
    """Extract positive/negative points from SerpAPI review snippets."""
    positive: list[str] = []
    negative: list[str] = []
    risk_flags: list[str] = []

    NEGATIVE_KEYWORDS = {"bẩn", "hỏng", "scam", "lừa", "tệ", "thất vọng", "ồn", "muỗi", "côn trùng", "dirty", "broken", "scam", "noisy", "bad"}
    POSITIVE_KEYWORDS = {"sạch", "đẹp", "thân thiện", "tốt", "tuyệt", "clean", "beautiful", "friendly", "great", "excellent", "gần biển", "view đẹp"}

    for review in raw_reviews:
        snippet = review.get("snippet", review.get("text", ""))
        if not snippet:
            continue
        snippet_lower = snippet.lower()
        rating = review.get("rating")

        if rating is not None and rating >= 4:
            for keyword in POSITIVE_KEYWORDS:
                if keyword in snippet_lower and keyword not in positive:
                    positive.append(keyword)
        elif rating is not None and rating <= 2:
            for keyword in NEGATIVE_KEYWORDS:
                if keyword in snippet_lower:
                    if keyword not in negative:
                        negative.append(keyword)
                    if keyword in {"scam", "lừa", "hỏng", "bẩn", "dirty", "broken"}:
                        flag = f"review_{keyword}"
                        if flag not in risk_flags:
                            risk_flags.append(flag)
        else:
            # Scan neutral/mixed reviews for keywords
            for keyword in NEGATIVE_KEYWORDS:
                if keyword in snippet_lower and keyword not in negative:
                    negative.append(keyword)
            for keyword in POSITIVE_KEYWORDS:
                if keyword in snippet_lower and keyword not in positive:
                    positive.append(keyword)

    review_count = len(raw_reviews)
    confidence = "high" if review_count >= 8 else ("medium" if review_count >= 3 else "low")

    return ReviewSummary(
        provider=provider,
        data_mode="live",
        target_id=hotel_id,
        positive_points=positive[:5],
        negative_points=negative[:5],
        risk_flags=risk_flags,
        confidence=confidence,
    )
