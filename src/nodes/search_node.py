from src.state.agent_state import AgentState
from src.tools.flight_search import search_flights
from src.tools.hotel_search import search_hotels
from datetime import datetime, timedelta
import json

def search_node(agent_state: AgentState) -> dict:
    try: 
        user_request = agent_state["user_request"]
        flight_results = None
        hotel_results = None

        print(f"[SEARCH] Searching: {user_request.get('origin')} → {user_request.get('destination')} on {user_request.get('departure_date')}")


        check_out = user_request.get("return_date")
        if not check_out and user_request.get("departure_date"):
            dep = datetime.strptime(user_request["departure_date"], "%Y-%m-%d")
            check_out = (dep + timedelta(days=2)).strftime("%Y-%m-%d")

        if user_request.get("origin") and user_request.get("destination") and user_request.get("departure_date"):
            flight_raw = search_flights.invoke({
                "departure_id": user_request["origin"],
                "arrival_id": user_request["destination"],
                "outbound_date": user_request["departure_date"]
            })
            flight_data = json.loads(flight_raw)
            flight_results = flight_data.get("flights", [])
        
        if user_request.get("hotel_needed"):
            hotel_raw = search_hotels.invoke({
                "destination": user_request["destination"],
                "check_in_date": user_request["departure_date"],
                "check_out_date": check_out
            })
            hotel_data = json.loads(hotel_raw)
            hotel_results = hotel_data.get("hotels", [])
        
        return {
            "flight_results": sorted(flight_results, key=lambda x: x["price"])[:10] if flight_results else [],
            "hotel_results": sorted(hotel_results, key=lambda x: x["price"])[:10] if hotel_results else [],
            "current_step": "search"
        }
    except Exception as e:
        return {"error": str(e), "current_step": "search"}
        