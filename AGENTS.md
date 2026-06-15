# Travel AI Agent Workspace Guide

## Product Direction

This repo is being developed as a real travel-planning product, not just a multi-agent demo. The product should help users turn loose travel ideas into actionable trip decisions: feasible itinerary, cost estimate, route sanity check, risks, and next booking or lead action.

Before substantial work, read:

1. `docs/00-product-brief.md`
2. `docs/01-mvp-scope.md`
3. The relevant skill under `.agents/skills/`

## Engineering Rules

- Keep the Python backend inside `src/travel_ai_agent`.
- Run backend entrypoints with `uvicorn --app-dir src travel_ai_agent.api.main:app`.
- Preserve FastAPI SSE event types unless frontend API client changes in the same task.
- Preserve `thread_id=session_id`; LangGraph HITL resume depends on it.
- Treat `AgentState.messages` as append-only LangGraph message state.
- Prefer deterministic code, validators, and API services before adding new LLM calls.
- Do not add agents just to make the architecture look more agentic.
- Use LLMs for natural-language parsing, plan drafting, review summarization, and response explanation.
- Use code/services for routing, budget math, cost estimation, feasibility checks, and API normalization.

## Skill Routing

- Backend graph/API/state/tools: `.agents/skills/backend`
- Frontend workspace/chat/itinerary UI: `.agents/skills/frontend`
- Guardrails, cost, API keys, refusal policy: `.agents/skills/guardrails-cost`
- Product scope and roadmap: `.agents/skills/product-strategy`
- Validation, demo, README, Docker: `.agents/skills/validation-demo`

## Validation Defaults

Use the smallest checks that match the change:

```powershell
python -m compileall src main.py
Set-Location frontend
npm run lint
npm run build
```

For backend smoke checks:

```powershell
uvicorn --app-dir src travel_ai_agent.api.main:app --reload --port 8000
```
