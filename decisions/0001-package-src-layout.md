# Decision 0001: Package Src Layout

## Decision

Use `src/travel_ai_agent` as the single Python package for backend API, LangGraph agents, tools, config, and state.

## Consequences

- Backend command is `uvicorn --app-dir src travel_ai_agent.api.main:app`.
- Old `backend`, `config`, and top-level `src` package imports are removed.
- Frontend remains in `frontend/`.
