import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ["DEMO_MODE"] = "1"

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from travel_ai_agent.decision.engine import build_decision
from travel_ai_agent.providers.gateway import _fixture_flights, _fixture_hotels
from travel_ai_agent.providers.normalizers import normalize_flights, normalize_hotels
from travel_ai_agent.schemas.domain import DecisionInput, TripPlan

def load_dataset(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_benchmark():
    dataset_path = Path(__file__).parent.parent / "tests" / "benchmark_data.json"
    dataset = load_dataset(str(dataset_path))
    
    results = []
    unsafe_count = 0
    blocking_correct = 0
    warning_correct = 0
    
    total_insufficient = 0
    total_cases = len(dataset)
    
    for case in dataset:
        # Create TripPlan
        plan = TripPlan(
            destination=case["destination"],
            origin=case["origin"],
            days=case["days"],
            travelers=case["travelers"],
            budget_total=case["budget_total"],
            departure_date=case["departure_date"],
            return_date=case["return_date"],
        )
        
        # Fetch mocks directly
        flights_data = [] if case["destination"] == "NoFlightCity" or case["origin"] == "NoFlightCity" else _fixture_flights()
        hotels_data = [] if case["destination"] == "NoHotelCity" else _fixture_hotels()
        
        for f in flights_data:
            f["data_mode"] = "live"
        for h in hotels_data:
            h["data_mode"] = "live"
            
        flights = normalize_flights(flights_data)
        hotels = normalize_hotels(hotels_data)
        
        # Build input
        decision_input = DecisionInput(
            trip_plan=plan,
            flight_options=flights,
            hotel_options=hotels,
            weather_forecast=[],
            place_options=[],
            routes=[]
        )
        
        # Run engine
        decision = build_decision(decision_input)
        
        # Evaluate
        expected_status = case["expected_status"]
        expected_warnings = case["expected_warnings"]
        actual_status = decision.decision_status
        actual_warnings = decision.blocking_reasons + [r.type for r in decision.risks] if decision.risks else decision.blocking_reasons
        
        is_unsafe = False
        if case["type"] in ["insufficient", "unsupported"] and actual_status == "recommended":
            is_unsafe = True
            unsafe_count += 1
            
        if case["type"] in ["insufficient", "unsupported"]:
            total_insufficient += 1
            if actual_status in ["insufficient_data", "needs_revision"]:
                blocking_correct += 1
                
        warning_match = True
        for w in expected_warnings:
            if not any(w in aw for aw in actual_warnings):
                warning_match = False
                break
        if warning_match:
            warning_correct += 1
            
        results.append({
            "id": case["id"],
            "type": case["type"],
            "expected_status": expected_status,
            "actual_status": actual_status,
            "expected_warnings": expected_warnings,
            "actual_warnings": actual_warnings,
            "is_unsafe": is_unsafe,
            "warning_match": warning_match
        })
        
    # Calculate metrics
    unsafe_rate = (unsafe_count / total_cases) * 100
    blocking_accuracy = (blocking_correct / total_insufficient) * 100 if total_insufficient > 0 else 100
    warning_precision = (warning_correct / total_cases) * 100
    
    report = [
        "# Benchmark Report",
        "",
        f"**Total Cases:** {total_cases}",
        f"**Unsafe Recommendation Rate:** {unsafe_rate:.2f}% (Target: 0%)",
        f"**Insufficient/Unsupported Blocking Accuracy:** {blocking_accuracy:.2f}% (Target: 100%)",
        f"**Warning Precision:** {warning_precision:.2f}% (Target: >=80%)",
        "",
        "## Detailed Results",
        ""
    ]
    
    for r in results:
        status_icon = "❌" if r["is_unsafe"] or not r["warning_match"] else "✅"
        report.append(f"### {status_icon} Case {r['id']} ({r['type']})")
        report.append(f"- Expected Status: `{r['expected_status']}` | Actual: `{r['actual_status']}`")
        report.append(f"- Expected Warnings: `{r['expected_warnings']}` | Actual: `{r['actual_warnings']}`")
        if r["is_unsafe"]:
            report.append("- **ERROR**: Unsafe recommendation!")
        if not r["warning_match"]:
            report.append("- **ERROR**: Warning mismatch!")
        report.append("")
        
    with open("benchmark_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Benchmark completed. Report saved to benchmark_report.md")
    print(f"Unsafe: {unsafe_rate:.2f}% | Blocking Acc: {blocking_accuracy:.2f}% | Warn Precision: {warning_precision:.2f}%")
    
    if unsafe_rate > 0 or blocking_accuracy < 100 or warning_precision < 80:
        sys.exit(1)

if __name__ == "__main__":
    run_benchmark()
