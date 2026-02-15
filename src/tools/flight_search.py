from langchain_core.tools import tool
from serpapi import GoogleSearch
from config.settings import SERPAPI_API_KEY
import json

@tool
def search_flights(departure_id: str, arrival_id: str, outbound_date: str) -> str:
    """Search flights using Google Flights via SerpAPI."""
    
    # 1. Tạo params cho SerpAPI
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,    # VD: "SGN"
        "arrival_id": arrival_id,        # VD: "DAD"
        "outbound_date": outbound_date,  # VD: "2026-03-20"
        "currency": "VND",
        "hl": "vi",
        "type": "2",  # one-way
        "api_key": SERPAPI_API_KEY,
    }
    # 2. Gọi SerpAPI
    try: 
        search = GoogleSearch(params)
        results = search.get_dict()
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

    