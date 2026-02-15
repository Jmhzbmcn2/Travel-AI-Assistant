import sys
sys.path.insert(0, ".")

from src.tools.flight_search import search_flights
from src.tools.hotel_search import search_hotels
import json

# Test flight
print("=== TEST FLIGHT ===")
flights = search_flights.invoke({
    "departure_id": "SGN",
    "arrival_id": "DAD",
    "outbound_date": "2026-03-20"
})
print(json.dumps(json.loads(flights), indent=2, ensure_ascii=False))

# Test hotel
print("\n=== TEST HOTEL ===")
hotels = search_hotels.invoke({
    "destination": "Đà Nẵng",
    "check_in_date": "2026-03-20",
    "check_out_date": "2026-03-22"
})
print(json.dumps(json.loads(hotels), indent=2, ensure_ascii=False)) 