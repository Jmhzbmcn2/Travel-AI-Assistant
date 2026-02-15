from langchain_core.tools import tool
from serpapi import GoogleSearch
from config.settings import SERPAPI_API_KEY 
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

    try: 
        search = GoogleSearch(params)
        results = search.get_dict()
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
