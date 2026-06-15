# Decision 0002: Product Harness

## Decision

Use `AGENTS.md`, `docs/`, `checklists/`, `decisions/`, `prompts/`, and `.agents/skills/` as the repo-local product and engineering harness.

## Consequences

- Agents should read product docs before large feature work.
- Project-specific skills live under `.agents/skills`.
- Old `project-skills/` is removed to avoid duplicate guidance.
