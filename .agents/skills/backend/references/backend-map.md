# Backend Map

Use this reference when changing backend behavior.

## Layout

- `src/travel_ai_agent/` is the Python package (import root: `travel_ai_agent.*`).
- `main.py` (root) is a dev REPL only — not the ASGI app.
- ASGI app: `travel_ai_agent.api.main:app`, run with `uvicorn --app-dir src`.

## Request Flow

- `api/main.py`: FastAPI app factory, CORS, router registration.
- `api/routers/chat.py`: sync + SSE chat endpoints (`/chat`, `/chat/stream`); `/chat/resume`, `/chat/stream/resume` are dormant (return 409, no interrupt in the lean graph).
- `api/services/chat_service.py`: graph invocation + final message extraction.
- `api/services/session_store.py`: SQLite persistence (sessions, messages, trips, decisions, usage events, cache, users, refresh tokens).
- `core/`: cross-cutting services — `guardrails.py` (request/tool budgets, rate limit), `llm_service.py` (`LLMs`, `get_llm`).

## Graph Flow (`graphs/main_graph.py`)

```
classify_intent ─┬─ chitchat        → END   (intent chitchat | out_of_scope)
                 └─ planner                  (intent travel | follow_up)
planner ─┬─ END        (missing required fields → asks user)
         └─ decision
decision → respond → END
```

Nodes in `nodes/`: `classify_intent_node`, `chitchat_node`, `planner_node`, `decision_node`, `respond_node`.

- `planner_node` builds a typed `TripPlan` (LLM structured output), merges with prior turns.
- `decision_node` is `async`: fetches flights + hotels concurrently (`asyncio.to_thread` + `gather`), then places/routes/weather/reviews, runs `decision.build_decision`, and writes normalized options into state for `/trips/{id}/actions`.
- `respond_node` renders a short deterministic markdown verdict (no LLM). Full detail lives in the frontend workspace.

## Decision layer (`decision/`, untouched by graph changes)

`engine.build_decision` · `coverage.evaluate_coverage` (verified-coverage gate: domestic VND, 2–5 days, 1–4 travelers, ≥1 live flight + hotel) · `itinerary` (nearest-neighbor + Haversine) · `cost_rules` · `actions` (`optimize_day`, `replace_place`).

## Providers (`providers/gateway.py`)

SerpAPI (Flights/Hotels/Local/Directions/Reviews), OpenWeatherMap, Tavily. Per-session SQLite cache. Fixtures only when `DEMO_MODE=true`; every record carries `data_mode` (`live` | `fixture` | `missing`).

## Invariants

- Graph config must use `{"configurable": {"thread_id": sid}}` (thread_id == session_id).
- `state["plan"]` is `TripPlan.model_dump(mode="json")` (no `{steps, constraints}` wrapper — resolve city → IATA via `api.services.trip_service.to_iata` at the provider call).
- `messages` uses LangGraph `add_messages`; append message objects.
- Nodes return partial state dicts.
- SSE emits `session`, `status`, `chunk`, `done`, `error`. `NODE_STATUS_MAP` in `chat.py` must list every graph node.
