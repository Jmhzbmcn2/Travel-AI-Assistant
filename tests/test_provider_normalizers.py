from travel_ai_agent.providers import fixture_places, fixture_routes, normalize_flights, normalize_hotels, normalize_places


def test_provider_normalizers_and_fixtures_are_typed():
    flights = normalize_flights([{"airline": "Demo", "price": 1_000_000, "total_duration": 90}])
    hotels = normalize_hotels([{"name": "Demo Hotel", "price": 700_000, "rating": 4.2}])
    places = fixture_places("Da Nang")
    routes = fixture_routes(places)
    live_places = normalize_places([{"title": "My Khe", "rating": 4.6, "reviews": 1000}])

    assert flights[0].price == 1_000_000
    assert hotels[0].price_per_night == 700_000
    assert places[0].data_mode == "fixture"
    assert routes[0].data_mode == "fixture"
    assert live_places[0].data_mode == "live"


def test_category_normalization():
    places = normalize_places([
        {"title": "Quán hải sản Bé Mặn", "type": "Nhà hàng hải sản"},
        {"title": "Bảo tàng Đà Nẵng", "category": "Museum"},
        {"title": "Bãi biển Mỹ Khê", "type": "bãi biển"},
        {"title": "Chợ đêm Helio", "type": "chợ đêm"},
        {"title": "Lotte Mart", "type": "supermarket"},
        {"title": "Linh Ứng Tự", "type": "unknown category"},
    ])
    
    assert places[0].category == "food"
    assert places[1].category == "culture"
    assert places[2].category == "beach/nature"
    assert places[3].category == "nightlife"
    assert places[4].category == "shopping"
    assert places[5].category == "attraction"  # default fallback
