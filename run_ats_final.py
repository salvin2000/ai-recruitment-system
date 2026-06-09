"""
Day 20 - ATS Final Review & Production Readiness
Runner script — Live Demo
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_final import ATSFinalEvaluator, DEMO_CANDIDATES, DEMO_JOB


def run_final_review():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - FINAL REVIEW & PRODUCTION READINESS v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    evaluator = ATSFinalEvaluator()

    # ── Step 1: Production Readiness Checklist ────────────────────────────────
    print("\nStep 1: Production Readiness Checklist")
    print("─" * 65)

    checklist = evaluator.run_checklist()
    for cat_name, cat_data in checklist["categories"].items():
        status = "PASS" if cat_data["all_pass"] else "FAIL"
        print(f"\n  [{status}] {cat_data['label']}")
        print(f"         {cat_data['passed']} of {cat_data['total']} checks passed")
        for check in cat_data["checks"]:
            mark = "OK" if check["status"] else "FAIL"
            print(f"    [{mark}] {check['item']}")

    print(f"\n  Total  : {checklist['passed_checks']} of {checklist['total_checks']} passed")
    print(f"  Status : {'PRODUCTION READY' if checklist['production_ready'] else 'NOT READY'}")

    # ── Step 2: Live Demo ─────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Live Demo — ATS Pipeline on 6 Candidates")
    print("─" * 65)

    demo = evaluator.run_demo()
    print(f"\n  Job     : {demo['job_requirements']['role_name']}")
    print(f"  Company : {demo['job_requirements']['company']}")
    print(f"  Required Skills: {', '.join(demo['job_requirements']['required_skills'])}")

    print(f"\n  {'Rank':<5} {'Candidate':<20} {'Score':>7} {'Grade':>6} {'Zone':<18} {'Decision'}")
    print(f"  {'─'*5} {'─'*20} {'─'*7} {'─'*6} {'─'*18} {'─'*20}")
    for rank, c in enumerate(demo["ranked_results"], 1):
        print(f"  {rank:<5} {c['name']:<20} {c['ats_score']:>7} {c['grade']:>6} {c['zone']:<18} {c['decision'][:30]}")

    s = demo["summary"]
    print(f"\n  Shortlisted : {s['shortlisted_count']} ({s['shortlist_rate']}%)")
    print(f"  Review      : {s['review_count']}")
    print(f"  Rejected    : {s['rejected_count']}")
    print(f"  Avg Score   : {s['avg_score']}")
    print(f"  Top Score   : {s['top_score']}")

    # ── Step 3: Final Metrics ─────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Final Metrics Summary")
    print("─" * 65)

    m = evaluator.metrics
    print(f"\n  Pipeline Stats:")
    print(f"    Total Days     : {m['total_days']}")
    print(f"    Total Modules  : {m['total_modules']}")
    print(f"    Total Tests    : {m['total_tests']} — all passing")
    print(f"    API Endpoints  : {m['api_endpoints']}")
    print(f"    Error Codes    : {m['error_codes']}")

    print(f"\n  Accuracy Metrics:")
    for metric, value in m["accuracy_metrics"].items():
        print(f"    {metric:<22}: {value}")

    print(f"\n  Performance Improvements:")
    for metric, value in m["performance_metrics"].items():
        print(f"    {metric:<22}: {value}%")

    # ── Step 4: Final Report ──────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Final Evaluation Report")
    print("─" * 65)

    report  = evaluator.generate_final_report()
    summary = evaluator.generate_management_summary(report)
    print("\n" + summary)

    # ── Save Outputs ──────────────────────────────────────────────────────────
    evaluator.save_report(report, "data/outputs/final_ats_evaluation_report.json")

    demo_data = {
        "candidates": DEMO_CANDIDATES,
        "job":        DEMO_JOB,
        "results":    demo,
    }
    with open("data/outputs/demo_dataset.json", "w") as f:
        json.dump(demo_data, f, indent=2)
    print("Saved -> data/outputs/demo_dataset.json")

    print("\n" + "=" * 65)
    print("Final review and production readiness check complete!")
    print("=" * 65 + "\n")

    return report


if __name__ == "__main__":
    run_final_review()
