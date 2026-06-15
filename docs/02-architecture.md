# Architecture

## Runtime Layout

```text
src/travel_ai_agent/
  api/        FastAPI routers, schemas, services, app factory
  graphs/     LangGraph topology and checkpointer
  agents/     Planner, supervisor, reflection, response, tool agents
  tools/      External API wrappers
  state/      LangGraph shared state
  config/     Prompts, settings, constants
frontend/     React/Vite chat workspace
```

## Current Flow

```text
User
-> classify_intent
-> planner
-> HITL human_confirm interrupt
-> supervisor
-> flight/hotel/weather/info agents
-> reflection
-> response
```

## Product Architecture Direction

Future work should evolve from "tool agents return text" toward:

```text
Planner
-> Tool Router / API Services
-> Decision Engine
-> Response Agent
```

Decision Engine should be mostly deterministic code: cost math, feasibility checks, route checks, scoring, and warnings.
