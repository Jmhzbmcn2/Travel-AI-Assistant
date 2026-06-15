from langchain_core.tools import tool
from serpapi import GoogleSearch
from travel_ai_agent.config.settings import SERPAPI_API_KEY 
from travel_ai_agent.providers.provider_utils import with_retry
import json 

@tool
def search_hotels(destination: str, check_in_date: str, check_out_date: str) -> str:
    """Search hotels using Google Hotels via SerpAPI."""
    params = {
        "engine": "google_hotels",
        "q": f"Khách sạn {destination}",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "currency": "VND",
        "hl": "vi",
        "api_key": SERPAPI_API_KEY,
    }

    def _fetch():
        search = GoogleSearch(params)
        search.params_dict["timeout"] = 15
        return search.get_dict()

    try: 
        results = with_retry(_fetch)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
    
    hotels = []
    for hotel in results.get("properties", []):
        hotels.append({
            "name": hotel.get("name", ""),
            "price": hotel.get("rate_per_night", {}).get("extracted_lowest", 0),
            "rating": hotel.get("rating", 0),   
            "reviews": hotel.get("reviews", 0),
            "amenities": hotel.get("amenities", []),
            "location": hotel.get("neighborhood", hotel.get("address", "")),
        })
    
    return json.dumps({
        "status": "success",
        "total": len(hotels),
        "hotels": hotels,
    }, ensure_ascii=False)
