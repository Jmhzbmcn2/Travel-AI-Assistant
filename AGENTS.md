# Travel AI Agent Workspace Guide

## Product Direction

This repo is being developed as a real travel-planning product, not just a multi-agent demo. The product should help users turn loose travel ideas into actionable trip decisions: feasible itinerary, cost estimate, route sanity check, risks, and next booking or lead action.

Before substantial work, read:

1. `docs/00-product-brief.md`
2. `docs/01-mvp-scope.md`
3. The relevant skill under `.agents/skills/`

## Startup Workflow

Before writing code for any substantial task:

1. Read `feature_list.json` to identify the `active_feature`, status, dependencies, done criteria, and next step.
2. Read `progress.md` for recent Verification Evidence, blockers, and work already completed.
3. Read `session-handoff.md` for the current objective, files in flight, and the recommended next action.
4. Route the task through the relevant project skill under `.agents/skills/`.
5. Stay in scope for the active feature unless the user explicitly changes the objective.

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

## Scope Rules

- One feature at a time: work on only one `active_feature` unless the user explicitly assigns parallel work.
- Treat `feature_list.json` as the source of truth for feature status, dependencies, done criteria, evidence, and next step.
- Stay in scope for the selected feature; do not add product features, agents, tools, or UI redesigns unless they are part of the active feature.
- If a task requires changing scope, update `feature_list.json`, record the reason in `progress.md`, and refresh `session-handoff.md`.

## Skill Routing

- Backend graph/API/state/tools: `.agents/skills/backend`
- Frontend workspace/chat/itinerary UI: `.agents/skills/frontend`
- Guardrails, cost, API keys, refusal policy: `.agents/skills/guardrails-cost`
- Product scope and roadmap: `.agents/skills/product-strategy`
- Validation, demo, README, Docker: `.agents/skills/validation-demo`

## Global Skill Policy

- Prefer repo-local skills under `.agents/skills/` for Travel AI Agent work.
- Use personal/global skills only when the task explicitly matches their purpose or the user asks for them.
- Use `design-taste-frontend` for UI audit/redesign quality; do not use it for backend, data model, or API-only tasks.
- Use `prompt-master` only for writing or improving prompts.
- Use `understand*` skills for codebase mapping, architecture explanation, onboarding, or diff analysis.
- Use `vibecode-kit` only for large, ambiguous, multi-step development planning; do not force it onto small edits.
- Use `harness-creator` only when creating, auditing, or improving agent harness files.
- When multiple skills apply, announce the selected skill order and read the relevant `SKILL.md` before acting.

## Verification Commands

Use the smallest checks that match the change. Prefer the root entrypoints so verification is discoverable:

```powershell
.\init.ps1
.\init.ps1 -SkipFrontend
```

```bash
./init.sh
./init.sh --skip-frontend
```

For backend smoke checks:

```powershell
uvicorn --app-dir src travel_ai_agent.api.main:app --reload --port 8000
```

## Definition of Done

A task is done only when:

- The implementation matches the active feature scope and does not close unrelated work.
- Relevant tests, build, lint, or compile checks have passed through `init.ps1`, `init.sh`, or an explicitly documented narrower command.
- Verification Evidence records the command and output summary in `progress.md`.
- `feature_list.json` reflects the current feature status, evidence, and next step.
- `session-handoff.md` is updated so the next session is restartable from a clean, current handoff.

## End of Session

Before ending a work session:

1. Append a short entry to `progress.md` with Current State, What changed, Verification Evidence, Blockers, and Next.
2. Update `session-handoff.md` with Last Updated, Current Objective, Files, Blockers, and Recommended Next Step.
3. Keep `feature_list.json` aligned with actual status and evidence.
4. Leave the repo restartable: a future agent should be able to read this file, `feature_list.json`, `progress.md`, and `session-handoff.md` to continue without relying on chat history.
