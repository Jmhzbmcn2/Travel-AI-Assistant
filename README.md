# Travel AI Agent

Travel AI Agent is a FastAPI + LangGraph + React project for turning natural-language travel requests into structured trip plans, tool-backed travel results, and final recommendations.

The current product direction is not "another generic travel chatbot". The goal is to evolve into a travel decision workspace: itinerary feasibility, cost clarity, route sanity checks, risk warnings, and a clear next action.

## Stack

- Python 3.11+
- FastAPI
- LangGraph
- Google Gemini via OpenRouter or the native Gemini API
- React + Vite
- SerpApi, OpenWeatherMap, Tavily

## Repository Layout

```text
Travel AI Agent/
  AGENTS.md
  docs/
  checklists/
  decisions/
  prompts/
  .agents/skills/
  src/travel_ai_agent/
    api/
      main.py
      dependencies.py
      routers/
      schemas/
      services/
      utils/
    agents/
    config/
    edges/
    graphs/
    nodes/
    services/
    state/
    tools/
  frontend/
  Dockerfile.backend
  docker-compose.yml
  requirements.txt
  main.py
```

## Backend Flow

```text
User message
-> classify_intent
-> planner
-> HITL plan confirmation
-> supervisor
-> flight/hotel/weather/info agents
-> reflection
-> response
```

Important runtime behavior:

- FastAPI endpoints live under `src/travel_ai_agent/api`.
- The compiled graph lives in `src/travel_ai_agent/graphs/main_graph.py`.
- HITL resume depends on `thread_id=session_id`.
- SSE event types are `session`, `chunk`, `interrupt`, `done`, and `error`.

## Setup

```powershell
pip install -r requirements.txt
Set-Location frontend
npm install
```

Create `.env` in the repo root:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=google/gemini-2.5-flash-lite
SERPAPI_API_KEY=your_serpapi_key
OPENWEATHERMAP_API_KEY=your_openweathermap_key
TAVILY_API_KEY=your_tavily_key
```

## Run Locally

Backend:

```powershell
uvicorn --app-dir src travel_ai_agent.api.main:app --reload --port 8000
```

Frontend:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:5173`.

## API

The public API shape is unchanged after the package-layout migration:

- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`
- `POST /api/v1/chat/resume`
- `POST /api/v1/chat/stream/resume`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `DELETE /api/v1/sessions/{id}`
- `GET /api/v1/health`

## Validation

Backend:

```powershell
python -m compileall src main.py
```

Frontend:

```powershell
Set-Location frontend
npm run lint
npm run build
```

Full local pre-commit check:

```powershell
.\project-hooks\pre-commit.ps1
```

## Product Harness

Before substantial work, read `AGENTS.md` and the relevant docs:

- `docs/00-product-brief.md`
- `docs/01-mvp-scope.md`
- `.agents/skills/backend/SKILL.md`
- `.agents/skills/frontend/SKILL.md`
- `.agents/skills/product-strategy/SKILL.md`

The harness prioritizes product value over architecture theater: use LLMs where they help understand, plan, summarize, and explain; use deterministic code for math, routing, validation, API normalization, and cost controls.

## Decision Workspace MVP

The current workspace persists sessions and typed trip plans in SQLite, supports same-session plan editing, normalizes provider results, and calculates cost, feasibility, option ranking, and risks through deterministic code.

- `GET /api/v1/trips/{session_id}` returns the current plan and decision workspace payload.
- `PATCH /api/v1/trips/{session_id}/plan` edits the interrupted plan without creating a new session.
- `GET /api/v1/trips/{session_id}/export.md` exports the current recommendation.
- Live flight/hotel/weather/search providers are used when available; visible fixture fallbacks keep tests and demos deterministic.
- Out-of-scope requests are refused before expensive travel tools, and SQLite usage events support request/tool budgets.

LangGraph checkpoints and trip/session/decision state are persisted in SQLite. If the optional checkpoint package is unavailable, the graph falls back to the in-process checkpointer while the product data remains persistent.
