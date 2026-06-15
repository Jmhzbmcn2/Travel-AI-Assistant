from travel_ai_agent.providers import gateway
from travel_ai_agent.schemas import PlaceOption


def test_fetch_routes_uses_serpapi_google_maps_directions(monkeypatch):
    places = [
        PlaceOption(id="a", provider="test", name="A", category="sight", lat=10.7769, lng=106.7009),
        PlaceOption(id="b", provider="test", name="B", category="sight", lat=10.7798, lng=106.6990),
    ]
    captured = {}

    class FakeSearch:
        def __init__(self, params):
            captured.update(params)

        def get_dict(self):
            return {"directions": [{"distance": 903, "duration": 285}]}

    monkeypatch.setattr(gateway, "SERPAPI_API_KEY", "test-key")
    monkeypatch.setattr(gateway, "GoogleSearch", FakeSearch)

    routes = gateway.fetch_routes(places)

    assert captured["engine"] == "google_maps_directions"
    assert captured["start_addr"] == "10.7769,106.7009"
    assert captured["end_addr"] == "10.7798,106.699"
    assert routes[0].provider == "serpapi_google_maps_directions"
    assert routes[0].distance_km == 0.903
    assert routes[0].duration_minutes == 5
