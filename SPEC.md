# Product + Implementation Spec: AI Travel Decision Assistant

## 1. Product Summary

**Working product name:** AI Travel Decision Assistant

AI Travel Decision Assistant helps Vietnamese travelers turn vague trip ideas into feasible, budget-aware, actionable travel plans. The product is not meant to replace TikTok, Google, Booking, Agoda, or Traveloka as sources of inspiration. It sits after inspiration and helps users decide what trip option is realistic, worth the money, and safe enough to book.

The core value is not "chat with travel AI". The core value is:

> Convert scattered travel intent into a feasible itinerary, cost estimate, route sanity check, risk warning, and next booking or lead action.

## 2. Problem Statement

Users can already find travel ideas from TikTok, Google Maps, blogs, Booking, Traveloka, Facebook groups, and ChatGPT. The harder problem is deciding whether a trip plan is actually good.

Current planning pain points:

- Information is scattered across many platforms.
- There are too many flights, hotels, places, reviews, and opinions.
- Users do not know whether an itinerary is too dense or too tiring.
- Users do not know the real total cost after flights, hotels, food, transport, tickets, and buffer.
- Users struggle to compare options beyond "cheapest".
- Group trips are hard to align around budget, taste, comfort level, and schedule.
- Users lack confidence before booking.

Core pain point:

> Users lack confidence when making travel decisions because they cannot easily compare options, verify feasibility, estimate total cost, and choose the best-value plan for their budget, preferences, dates, and comfort level.

## 3. Target Users

### MVP Primary Users

Vietnamese independent travelers planning short domestic or outbound trips.

Priority segments:

- Young professionals and students with limited budgets.
- Couples who want a comfortable, low-friction itinerary.
- Friend groups that need a balanced plan and shareable cost breakdown.

### Later Users

- Travel agencies that want faster itinerary and quote generation.
- Families needing safer, lower-density trip plans.
- Corporate travel teams needing policy and budget checks.

## 4. Positioning

Current generic positioning:

> AI Travel Planning Assistant: understands travel requests, calls travel APIs, and summarizes results.

Target positioning:

> AI Travel Decision Assistant: checks whether a trip plan is feasible, estimates total cost, compares alternatives, identifies risks, and recommends the best-value option.

One-liner:

> Nhập ngân sách, số ngày và kiểu du lịch mong muốn; AI tạo một chuyến đi khả thi, đáng tiền và có thể chuyển sang booking hoặc tư vấn ngay.

## 5. MVP Scope

### In Scope For MVP

- Natural-language trip request parsing.
- Structured `TripPlan` with editable fields.
- HITL plan confirmation and same-session plan editing.
- Flight, hotel, place, route, review, weather, and cost-data provider adapters.
- Budget estimation v1.
- Route and itinerary feasibility check v1.
- Option ranking: cheapest, balanced, comfortable, best-value.
- Risk detection: budget tight, day too dense, bad weather, distance too high, weak reviews, missing data.
- Final structured recommendation.
- Lead/affiliate/booking handoff placeholder, not full booking.

### Out Of Scope For MVP

- In-app payment.
- Booking management, cancellation, refund.
- Complex multi-city itinerary optimization.
- Group voting.
- TikTok/YouTube direct video understanding.
- Price tracking and notifications.
- Long-term personalization.
- Marketplace for local tours.
- Mobile app.

## 6. Current Workspace Fit

The repo currently has the correct foundation, but not the full decision-product implementation.

Already present:

- Python package layout under `src/travel_ai_agent`.
- FastAPI backend under `src/travel_ai_agent/api`.
- LangGraph flow under `src/travel_ai_agent/graphs/main_graph.py`.
- Planner, supervisor, flight, hotel, weather, info, reflection, and response agents.
- HITL interrupt before `human_confirm`.
- SSE chat and resume endpoints under `/api/v1/chat`.
- React/Vite frontend under `frontend/`.
- Product harness: `AGENTS.md`, `docs/`, `.agents/skills/`, `checklists/`, `decisions/`, `prompts/`.

Missing or not yet product-ready:

- Typed `TripPlan` schema matching this spec.
- Same-session plan edit after HITL.
- Provider adapter layer.
- Decision Engine modules.
- Cost estimator.
- Route feasibility checker.
- Option ranker.
- Risk detector.
- Structured final recommendation payload.
- Frontend trip workspace panels for plan, itinerary, cost, risks, and options.

## 7. Provider Inventory

The project can assume API access exists for the providers below, but code integration must still be explicit and normalized.

| Domain | Provider source | Access status | Current code status | MVP role |
|---|---|---:|---:|---|
| Flights | Google Flights provider / SerpApi | Available | Partially integrated | Flight options and price/time trade-offs |
| Hotels | Google Hotels provider / SerpApi | Available | Partially integrated | Hotel options, price, rating, area |
| Places | Google Maps / Local / Places | Available | Not integrated | Attractions, food, activities |
| Directions | Google Maps Directions / Routes | Available | Not integrated | Travel time and route feasibility |
| Reviews | Google Maps Reviews / Tripadvisor | Available | Not integrated | Value and risk assessment |
| Weather | OpenWeather / WeatherAPI / Open-Meteo | Available | Partially integrated | Daily forecast and activity impact |
| Cost data | Internal Cost Database | Available or planned | Not integrated | Food, local transport, ticket, buffer estimates |

Provider rule:

> External API responses must not flow directly into LLM reasoning. They must be normalized into internal schemas first.

## 8. Internal Data Contracts

### TripPlan

The planner should produce a structured trip plan before any expensive provider call.

```json
{
  "origin": "Hà Nội",
  "destination": "Đà Nẵng",
  "departure_date": "2026-07-10",
  "return_date": "2026-07-12",
  "days": 3,
  "nights": 2,
  "travelers": 2,
  "budget_total": 10000000,
  "budget_per_person": 5000000,
  "currency": "VND",
  "preferences": ["biển", "ăn ngon", "không quá mệt"],
  "comfort_level": "medium",
  "trip_type": "couple",
  "must_have": [],
  "avoid": [],
  "special_requirements": [],
  "steps": ["find_flights", "find_hotels", "search_places", "check_routes", "check_weather", "estimate_costs"]
}
```

Required MVP fields:

- `destination`
- `days` or date range
- `travelers`
- `budget_total` or `budget_per_person`
- `preferences`
- `comfort_level`

If required fields are missing, the assistant asks a short follow-up question before provider calls.

### FlightOption

```json
{
  "id": "flight_1",
  "provider": "serpapi_google_flights",
  "airline": "Vietnam Airlines",
  "departure_time": "08:00",
  "arrival_time": "09:25",
  "duration_minutes": 85,
  "stops": 0,
  "price": 1800000,
  "currency": "VND",
  "booking_url": "https://...",
  "tradeoffs": ["morning_arrival", "higher_price"]
}
```

### HotelOption

```json
{
  "id": "hotel_1",
  "provider": "serpapi_google_hotels",
  "name": "Hotel near My Khe",
  "area": "Mỹ Khê",
  "price_per_night": 900000,
  "rating": 4.4,
  "review_count": 820,
  "distance_to_center_km": 3.2,
  "booking_url": "https://...",
  "risk_flags": []
}
```

### PlaceOption

```json
{
  "id": "place_1",
  "provider": "google_places",
  "name": "Biển Mỹ Khê",
  "category": "beach",
  "rating": 4.6,
  "review_count": 12000,
  "location": {"lat": 16.061, "lng": 108.247},
  "estimated_visit_minutes": 120,
  "estimated_cost": 0,
  "tags": ["biển", "chill", "free"],
  "priority": "must_go"
}
```

### RouteSegment

```json
{
  "from_place_id": "hotel_1",
  "to_place_id": "place_1",
  "mode": "driving",
  "distance_km": 4.1,
  "duration_minutes": 16,
  "provider": "google_routes"
}
```

### WeatherForecast

```json
{
  "date": "2026-07-10",
  "location": "Đà Nẵng",
  "temperature_min": 27,
  "temperature_max": 34,
  "rain_probability": 0.45,
  "summary": "Có khả năng mưa chiều",
  "activity_impact": ["prefer_indoor_after_15h"]
}
```

### ReviewSummary

```json
{
  "target_id": "hotel_1",
  "source": "google_reviews",
  "positive_points": ["gần biển", "nhân viên tốt"],
  "negative_points": ["phòng nhỏ"],
  "risk_flags": ["room_size_complaint"],
  "confidence": "medium"
}
```

## 9. Decision Engine Contract

The Decision Engine is the product differentiator. It must be deterministic code first, with LLM used only for explanation.

### Modules

Implement under future package:

```text
src/travel_ai_agent/providers/
  flights_provider.py
  hotels_provider.py
  places_provider.py
  directions_provider.py
  reviews_provider.py
  weather_provider.py
  cost_provider.py

src/travel_ai_agent/decision/
  cost_estimator.py
  feasibility_checker.py
  option_ranker.py
  risk_detector.py
  recommendation_builder.py
```

### DecisionInput

```json
{
  "trip_plan": {},
  "flight_options": [],
  "hotel_options": [],
  "place_options": [],
  "route_segments": [],
  "weather_forecasts": [],
  "review_summaries": [],
  "cost_rules": {}
}
```

### DecisionOutput

```json
{
  "recommended_option": "balanced",
  "budget_status": "slightly_over",
  "total_cost": 11000000,
  "total_cost_per_person": 5500000,
  "feasibility_score": 0.78,
  "comfort_score": 0.82,
  "value_score": 0.76,
  "cost_breakdown": {
    "flights": 3600000,
    "hotels": 1800000,
    "food": 1800000,
    "local_transport": 800000,
    "tickets": 1400000,
    "buffer": 1600000
  },
  "risks": [
    {
      "type": "budget_tight",
      "severity": "medium",
      "message": "Ngân sách 5 triệu/người hơi sát so với tổng ước lượng."
    },
    {
      "type": "day_too_dense",
      "severity": "medium",
      "message": "Ngày 2 có tổng di chuyển khoảng 2 giờ 40 phút."
    }
  ],
  "why_recommended": [
    "Khách sạn gần khu biển hơn.",
    "Tổng thời gian di chuyển thấp hơn phương án rẻ nhất.",
    "Chi phí chỉ vượt ngân sách khoảng 10%."
  ]
}
```

### Scoring Principles

- Cheapest is not always best.
- Penalize excessive travel time.
- Penalize low review confidence and repeated negative review themes.
- Penalize plans that exceed budget too much.
- Reward options near preferred activities.
- Reward lower route complexity.
- Always expose assumptions when data is missing.

## 10. MVP Feature Specs

### Feature 1: Natural-Language Trip Request

User can enter a natural-language travel request.

Example:

> Tôi muốn đi Đà Nẵng 3 ngày 2 đêm, 2 người, ngân sách 5 triệu/người, thích biển, ăn ngon, không muốn lịch quá mệt.

The system extracts:

- origin
- destination
- date range or duration
- travelers
- budget
- preferences
- comfort level
- trip type
- special requirements

### Feature 2: Structured Plan + HITL

Before provider calls, the assistant displays the parsed trip plan.

User can:

- confirm
- edit budget
- edit dates
- edit travelers
- edit preferences
- remove or add requirements

Implementation requirement:

> Plan editing must happen in the same session. The current behavior where "modify" abandons the interrupted session is not acceptable for the MVP.

### Feature 3: Provider Calls

After confirmation, the system calls only the providers required by `TripPlan.steps`.

Provider call rules:

- Do not call provider APIs for chitchat or out-of-scope messages.
- Do not call expensive providers until required fields are present.
- Return structured normalized options, not raw provider payloads.
- Attach provider name and timestamp where possible.

### Feature 4: Budget Estimation

Estimate total trip cost using:

- flights
- hotels
- food
- local transport
- tickets and activities
- buffer

Budget output must include:

- total cost
- cost per person
- budget delta
- budget status: `under_budget`, `near_limit`, `slightly_over`, `over_budget`
- assumptions

### Feature 5: Route And Feasibility Check

Check whether the itinerary is realistic:

- total travel time per day
- number of places per day
- route backtracking
- outdoor/indoor mix with weather
- hotel area fit
- rest time

Output must identify which day is too dense and what to remove or move.

### Feature 6: Option Ranking

Generate at least three option styles when enough data exists:

- cheapest
- balanced
- comfortable

Also identify the best-value option.

Ranking must include:

- cost score
- feasibility score
- comfort score
- value score
- reason for recommendation

### Feature 7: Final Structured Recommendation

Final response should include:

1. Trip summary.
2. Recommended option.
3. Itinerary by day.
4. Flight recommendation.
5. Hotel recommendation.
6. Main places.
7. Cost breakdown.
8. Feasibility assessment.
9. Risks and warnings.
10. Next action: booking link, affiliate link, lead form, export/share, or "ask for quote".

## 11. User Flow

```text
User enters travel request
-> classify intent
-> Planner extracts TripPlan
-> System asks for missing required fields if needed
-> HITL plan confirmation
-> User confirms or edits plan in same session
-> Provider router calls required APIs
-> Provider adapters normalize data
-> Decision Engine estimates cost, checks feasibility, ranks options, detects risks
-> Response Agent explains recommendation
-> Frontend shows itinerary, cost, risks, and next actions
```

## 12. Repo Implementation Mapping

Current package:

```text
src/travel_ai_agent/
  api/          FastAPI routes, schemas, chat services
  graphs/       LangGraph topology and HITL checkpoint
  agents/       Planner, supervisor, tool agents, reflection, response
  tools/        Existing external API wrappers
  state/        LangGraph AgentState
  config/       Settings, prompts, constants
```

Add for MVP:

```text
src/travel_ai_agent/providers/
  Normalize external API responses into internal option schemas.

src/travel_ai_agent/decision/
  Cost, feasibility, ranking, risk, and recommendation logic.

src/travel_ai_agent/schemas/
  Shared domain models for TripPlan, options, provider outputs, and DecisionOutput.
```

Frontend additions:

```text
frontend/src/components/
  PlanEditor
  ItineraryTimeline
  CostBreakdown
  RiskPanel
  OptionComparison
  NextActionPanel
```

## 13. Public API Direction

Existing chat endpoints remain:

- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`
- `POST /api/v1/chat/resume`
- `POST /api/v1/chat/stream/resume`

MVP should add action-oriented plan endpoints only if chat/resume becomes too awkward:

- `PATCH /api/v1/trips/{session_id}/plan`
- `POST /api/v1/trips/{session_id}/confirm`
- `GET /api/v1/trips/{session_id}/decision`

Do not add these until the frontend plan editor needs explicit non-chat actions.

## 14. Acceptance Criteria

### Product Acceptance

- User can create a structured trip plan from natural language.
- User can correct plan fields without starting a new session.
- User receives at least one recommended option with a clear reason.
- User sees cost estimate and assumptions.
- User sees feasibility warnings when itinerary is too dense.
- User sees next action after final recommendation.

### Technical Acceptance

- Provider outputs are normalized before decision logic.
- Decision Engine does not rely on LLM for math or scoring.
- LLM response does not invent prices, route time, or review facts.
- Missing provider data is shown as an assumption or warning.
- SSE chat behavior remains compatible with the current frontend.
- `python -m compileall src main.py` passes.
- `npm run lint` and `npm run build` pass from `frontend/`.

## 15. Metrics

MVP metrics:

- Plan completion rate.
- Plan edit rate.
- Time from first message to confirmed plan.
- Cost per generated plan.
- Provider calls per successful trip.
- Recommendation acceptance rate.
- Lead/booking/next-action click rate.
- User-reported confidence after seeing recommendation.

## 16. Future Features

Future, not MVP:

- Group trip planner.
- TikTok/YouTube link import.
- Trip board.
- Price tracking.
- In-trip assistant.
- Calendar sync.
- Full booking/payment.
- Long-term personalization.
- Agency dashboard.

## 17. Key Product Rule

The product wins only if it helps users make better travel decisions than they could make from inspiration content alone.

Do not optimize for "more agents". Optimize for:

- clearer trip decisions
- verified cost
- feasible route
- fewer planning mistakes
- higher booking or lead confidence
