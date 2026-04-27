import json
from datetime import datetime

def load_test_cases(filepath):
    with open(filepath) as f:
        return json.load(f)["test_cases"]

def mock_agent(input_data):
    # Mock agent responses for demonstration
    if "simulate_timeout" in input_data:
        return {"status": "retry", "attempts": 3}
    if "simulate_db_failure" in input_data:
        return {"status": "error", "reason": "db_unavailable"}
    if "simulate_sheets_failure" in input_data:
        return {"status": "logged_locally", "reason": "sheets_unavailable"}
    if "simulate_api_failure" in input_data:
        return {"status": "error", "reason": "api_unavailable"}
    if "notes" in input_data:
        notes = input_data["notes"].lower()
        if any(phrase in notes for phrase in ["ignore", "bypass", "admin mode", "reveal"]):
            return {"blocked": True, "reason": "injection_detected"}
    if "action" in input_data and input_data["action"] == "register":
        if "waiver_sent" in input_data:
            return {"status": "cached", "reason": "already_sent"}
        return {"status": "success", "action": "waiver_sent"}
    if "type" in input_data:
        if input_data["type"] in ["24h", "1h"]:
            return {"status": "sent", "type": input_data["type"]}
        return {"status": "error", "reason": "invalid_type"}
    if "reminders_sent" in input_data:
        if input_data["reminders_sent"] >= 2:
            return {"escalated": True, "logged": True}
        return {"status": "error", "reason": "insufficient_reminders"}
    if not input_data.get("member_id"):
        return {"status": "error", "reason": "missing_member_id"}
    return {"status": "success"}

def compare_outputs(actual, expected):
    for key, value in expected.items():
        if key not in actual:
            return False
        if value != "*" and actual[key] != value:
            return False
    return True

def run_eval():
    test_cases = load_test_cases("eval/test_cases.json")
    results = []
    passed = 0
    failed = 0

    for tc in test_cases:
        actual = mock_agent(tc["input"])
        success = compare_outputs(actual, tc["expected_output"])
        
        if success:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "category": tc["category"],
            "status": status,
            "expected": tc["expected_output"],
            "actual": actual
        })

    print("=" * 60)
    print(f"EVAL REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Total: {len(test_cases)} | Passed: {passed} | Failed: {failed}")
    print(f"Overall Accuracy: {(passed/len(test_cases)*100):.1f}%")
    print()

    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r["status"] == "PASS":
            categories[cat]["passed"] += 1

    print("--- Results by Category ---")
    for cat, stats in categories.items():
        pct = (stats["passed"]/stats["total"]*100)
        print(f"  {cat}: {pct:.0f}% ({stats['passed']}/{stats['total']})")

    print()
    print("--- Failed Tests ---")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  [{r['id']}] {r['name']}")
            print(f"    Expected: {r['expected']}")
            print(f"    Actual:   {r['actual']}")

    with open("eval/results/eval_results.json", "w") as f:
        json.dump({
            "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "accuracy": f"{(passed/len(test_cases)*100):.1f}%",
            "results": results
        }, f, indent=2)

    print()
    print("Results saved to eval/results/eval_results.json")

if __name__ == "__main__":
    run_eval()
