"""Response node là template deterministic — không LLM, không leak raw data."""
from travel_ai_agent.nodes.respond_node import response_agent_node
from travel_ai_agent.schemas import (
    CostBreakdown, DecisionOutput, ItineraryDay, ItineraryItem, RankedOption, Risk, TripPlan,
)


def _decision(**over) -> dict:
    base = dict(
        recommended_option="balanced",
        budget_status="under_budget",
        total_cost=9_800_000,
        total_cost_per_person=4_900_000,
        budget_delta=-200_000,
        feasibility_score=0.9,
        comfort_score=0.6,
        value_score=0.7,
        cost_breakdown=CostBreakdown(flights=5_000_000, hotels=2_400_000, food=2_100_000, buffer=300_000),
        options=[RankedOption(id="balanced", total_cost=9_800_000)],
        itinerary=[ItineraryDay(day=1, title="Ngày 1", items=[ItineraryItem(title="Biển Mỹ Khê")])],
        risks=[Risk(type="budget_tight", severity="medium", message="Ngân sách sát mức.")],
        assumptions=["Ăn uống 350k/người/ngày."],
        why_recommended=["Dưới ngân sách 200.000₫."],
        decision_status="recommended",
        coverage_status="verified",
        confidence="high",
    )
    base.update(over)
    return DecisionOutput(**base).model_dump(mode="json")


def _plan() -> dict:
    return TripPlan(destination="Đà Nẵng", days=3, travelers=2, budget_total=10_000_000).model_dump(mode="json")


def test_recommended_verdict_has_cost_and_option():
    out = response_agent_node({"plan": _plan(), "decision_output": _decision()})["messages"][0].content
    assert "Đi được với" in out
    assert "9.800.000₫" in out
    assert "Cân bằng" in out
    assert "Dưới ngân sách 200.000₫." in out  # why_recommended surfaced
    # chat message stays short — full itinerary lives in the workspace
    assert "Biển Mỹ Khê" not in out
    assert len(out.splitlines()) <= 6


def test_insufficient_data_lists_blocking_reasons():
    d = _decision(decision_status="insufficient_data", recommended_option=None,
                  blocking_reasons=["Chưa có vé máy bay live."])
    out = response_agent_node({"plan": _plan(), "decision_output": d})["messages"][0].content
    assert "Chưa đủ dữ liệu" in out
    assert "Chưa có vé máy bay live." in out


def test_no_decision_falls_back_to_plan_summary():
    out = response_agent_node({"plan": _plan(), "decision_output": None})["messages"][0].content
    assert "Đà Nẵng" in out
