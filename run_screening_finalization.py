"""
Day 32 - Screening System Finalization
Runner script

Runs the full production-readiness checklist, an end-to-end live demo of
the screening call, and generates the final Screening AI evaluation
report for management review.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.screening_finalization import (
    ProductionChecklistRunner, EndToEndDemoRunner, FinalEvaluationReport,
    PIPELINE_DAYS, API_ENDPOINTS,
)


def run_finalization():
    print("=" * 65)
    print("   ZECPATH AI - SCREENING SYSTEM FINALIZATION v1.0")
    print("=" * 65)

    # ── Step 1: Production Readiness Checklist ──────────────────────────
    print("\nStep 1: Production Readiness Checklist")
    print("-" * 65)
    checklist_runner = ProductionChecklistRunner()
    checklist = checklist_runner.run()
    for key, cat in checklist["categories"].items():
        print(f"\n  {cat['label']} ({cat['passed']}/{cat['total']})")
        for check in cat["checks"]:
            mark = "PASS" if check["passed"] else "FAIL"
            print(f"    [{mark}] {check['item']}")

    print(f"\n  TOTAL: {checklist['passed_checks']} / {checklist['total_checks']} checks passed "
          f"({checklist['pass_rate']*100:.1f}%)")
    print(f"  VERDICT: {checklist['verdict']}")

    # ── Step 2: Pipeline Test Summary ────────────────────────────────────
    print("\nStep 2: Pipeline Test Summary (Days 21-31)")
    print("-" * 65)
    for day, info in PIPELINE_DAYS.items():
        print(f"  Day {day:<3}: {info['name']:<42} {info['tests']:>4} tests")
    print(f"  {'TOTAL':<48} {checklist_runner.get_total_test_count():>4} tests")

    # ── Step 3: API Endpoint Design ───────────────────────────────────────
    print("\nStep 3: API Endpoint Design")
    print("-" * 65)
    for endpoint, description in API_ENDPOINTS.items():
        print(f"  {endpoint:<32} {description}")

    # ── Step 4: End-to-End Live Demo ─────────────────────────────────────
    print("\nStep 4: End-to-End Live Demo")
    print("-" * 65)
    demo_runner = EndToEndDemoRunner()
    demo = demo_runner.run()
    print(f"  Candidate : {demo['candidate']['name']} ({demo['candidate']['role_applied']})")
    print()
    for turn in demo["turns"]:
        print(f"  [{turn['category']:<13}] Q: {turn['question']}")
        print(f"  {'':<15} A: {turn['answer']}  (score: {turn['score']})")
    print(f"\n  Overall Score   : {demo['overall_score']}")
    print(f"  Recommendation  : {demo['recommendation']}")

    # ── Step 5: Final Evaluation Report ──────────────────────────────────
    print("\nStep 5: Final Evaluation Report")
    print("-" * 65)
    report_gen = FinalEvaluationReport()
    print(report_gen.get_management_summary())

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = "data/outputs/screening_final_evaluation.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    report_gen.save_report(output_path)

    print("\n" + "=" * 65)
    print("Screening System Finalization complete!")
    print("=" * 65 + "\n")
    return report_gen


if __name__ == "__main__":
    run_finalization()
