"""Compatibility gate before the deterministic Decision Engine."""


def reflection_node(state: dict) -> dict:
    """Mark tool collection complete.

    Cost, feasibility, ranking, and risk checks are handled by decision_node.
    """
    return {
        "needs_revision": False,
        "reflection_issues": [],
        "suggested_fixes": [],
        "plan_modifications": {},
        "agents_to_retry": [],
        "current_step": "reflect",
        "completed_agents": state.get("completed_agents", []) + ["reflect"],
    }


def route_after_reflection(state: dict) -> str:
    return "supervisor" if state.get("needs_revision") else "respond"
