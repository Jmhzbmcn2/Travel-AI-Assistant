# Project Skill Router

This is a local project hook/registry for Codex work in this repo. It does not modify global Codex configuration.

## Routing

- Use `.agents/skills/backend` for backend graph, agents, tools, schemas, routers, services, state, HITL, and SSE backend changes.
- Use `.agents/skills/frontend` for React UI, chat streaming client, session sidebar, cards, itinerary timeline, budget panel, and user actions.
- Use `.agents/skills/guardrails-cost` for out-of-scope handling, tool budgets, rate limits, cache, missing API key behavior, and cost/audit logging.
- Use `.agents/skills/validation-demo` for tests, smoke checks, README/demo polish, Docker validation, and interview readiness.
- Use `.agents/skills/product-strategy` for product scope, roadmap, user pain point, and decision-engine planning.

## File Pattern Hints

- `src/travel_ai_agent/api/**`, `src/travel_ai_agent/graphs/**`, `src/travel_ai_agent/agents/**`, `src/travel_ai_agent/nodes/**`, `src/travel_ai_agent/state/**`, `src/travel_ai_agent/tools/**` -> backend skill.
- `frontend/src/**` -> frontend skill.
- `*guard*`, `*rate*`, `*cache*`, `*cost*`, `src/travel_ai_agent/config/prompts.py`, intent routing -> guardrails skill.
- `README.md`, `Dockerfile*`, `docker-compose.yml`, `requirements.txt`, `frontend/package.json`, `tests/**` -> validation skill.
