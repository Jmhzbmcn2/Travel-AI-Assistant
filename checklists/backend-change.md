# Backend Change Checklist

- Read `.agents/skills/backend/SKILL.md`.
- Confirm affected state fields are defined in `src/travel_ai_agent/state/agent_state.py`.
- Preserve `thread_id=session_id`.
- Preserve SSE event types or update frontend client in the same change.
- Prefer deterministic services before new LLM calls.
- Run `python -m compileall src main.py`.
