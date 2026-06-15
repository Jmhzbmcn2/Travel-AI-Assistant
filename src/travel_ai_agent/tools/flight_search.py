from langchain_core.tools import tool
from serpapi import GoogleSearch
from travel_ai_agent.config.settings import SERPAPI_API_KEY
from travel_ai_agent.providers.provider_utils import with_retry
import json

@tool
def search_flights(departure_id: str, arrival_id: str, outbound_date: str, return_date: str = "") -> str:
    """Search flights using Google Flights via SerpAPI."""
    
    trip_type = "1" if return_date else "2"  # 1=round-trip, 2=one-way
    price_scope = "round_trip_per_traveler" if return_date else "one_way_per_traveler"
    
    # 1. Tạo params cho SerpAPI
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,    # VD: "SGN"
        "arrival_id": arrival_id,        # VD: "DAD"
        "outbound_date": outbound_date,  # VD: "2026-03-20"
        "currency": "VND",
        "hl": "vi",
        "type": trip_type,
        "api_key": SERPAPI_API_KEY,
    }
    if return_date:
        params["return_date"] = return_date

    # 2. Gọi SerpAPI
    def _fetch():
        search = GoogleSearch(params)
        search.params_dict["timeout"] = 15
        return search.get_dict()

    try: 
        results = with_retry(_fetch)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    # 3. Xử lý kết quả
    flights = []
    for flight in results.get("best_flights", []) + results.get("other_flights", []):
        segments = flight.get("flights", [])
        first = segments[0] if segments else {}
        last = segments[-1] if segments else {}
        flights.append({
            "price": flight.get("price", 0),
            "price_scope": price_scope,
            "total_duration": flight.get("total_duration", 0),
            "airline": first.get("airline", ""),
            "flight_number": first.get("flight_number", ""),
            "departure_time": first.get("departure_airport", {}).get("time", ""),
            "arrival_time": last.get("arrival_airport", {}).get("time", ""),
            "departure_airport": first.get("departure_airport", {}).get("name", ""),
            "arrival_airport": last.get("arrival_airport", {}).get("name", ""),
            "stops": len(segments) - 1,
        })
        
    return json.dumps({
        "status": "success",
        "total": len(flights),
        "flights": flights,
    }, ensure_ascii=False)