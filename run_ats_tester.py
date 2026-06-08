"""
Day 17 - ATS System Testing
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_tester import ATSTester, TEST_CASES, ACCURACY_THRESHOLDS


def run_ats_tests():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - ATS SYSTEM TESTING v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    tester = ATSTester()

    # ── Step 1: Show Test Cases ───────────────────────────────────────────────
    print("\nStep 1: Test Cases")
    print("─" * 65)
    print(f"  Total test cases : {len(TEST_CASES)}")

    categories = {}
    for tc in TEST_CASES:
        cat = tc["profile_category"]
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in categories.items():
        print(f"  {cat:<25} : {count} case(s)")

    # ── Step 2: Run Tests ─────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: AI vs Manual Review Comparison")
    print("─" * 65)
    print(f"\n  {'Test ID':<10} {'Category':<20} {'Score':>7} {'AI':>12} {'Manual':>12} {'Match'}")
    print(f"  {'─'*10} {'─'*20} {'─'*7} {'─'*12} {'─'*12} {'─'*6}")

    for tc in TEST_CASES:
        match = "YES" if tc["ats_decision"] == tc["manual_decision"] else "NO  *"
        print(f"  {tc['test_id']:<10} {tc['profile_category']:<20} "
              f"{tc['ats_score']:>7.2f} {tc['ats_decision']:>12} "
              f"{tc['manual_decision']:>12} {match}")

    # ── Step 3: Accuracy Metrics ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Accuracy Metrics")
    print("─" * 65)

    report  = tester.run_tests()
    metrics = report["accuracy_metrics"]
    targets = report["meets_targets"]

    print(f"\n  {'Metric':<20} {'Value':>8} {'Target':>8} {'Status'}")
    print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*10}")
    print(f"  {'Precision':<20} {metrics['precision']:>8.4f} "
          f"{ACCURACY_THRESHOLDS['precision_target']:>8.2f} "
          f"{'PASS' if targets['precision'] else 'FAIL'}")
    print(f"  {'Recall':<20} {metrics['recall']:>8.4f} "
          f"{ACCURACY_THRESHOLDS['recall_target']:>8.2f} "
          f"{'PASS' if targets['recall'] else 'FAIL'}")
    print(f"  {'F1 Score':<20} {metrics['f1_score']:>8.4f} "
          f"{ACCURACY_THRESHOLDS['f1_target']:>8.2f} "
          f"{'PASS' if targets['f1_score'] else 'FAIL'}")
    print(f"  {'Accuracy':<20} {metrics['accuracy']:>8.4f} "
          f"{ACCURACY_THRESHOLDS['accuracy_target']:>8.2f} "
          f"{'PASS' if targets['accuracy'] else 'FAIL'}")
    print(f"  {'Mismatch Rate':<20} {metrics['mismatch_rate']:>8.4f} "
          f"{ACCURACY_THRESHOLDS['mismatch_tolerance']:>8.2f} "
          f"{'PASS' if targets['mismatch_rate'] else 'FAIL'}")
    print(f"\n  Overall Pass: {'YES' if report['overall_pass'] else 'NO'}")

    # ── Step 4: Confusion Matrix ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Confusion Matrix")
    print("─" * 65)
    cm = report["confusion_matrix"]
    print(f"\n  True Positives  (AI shortlisted, Human shortlisted) : {cm['true_positive']}")
    print(f"  False Positives (AI shortlisted, Human rejected)     : {cm['false_positive']}")
    print(f"  False Negatives (AI rejected, Human shortlisted)     : {cm['false_negative']}")
    print(f"  True Negatives  (AI rejected, Human rejected)        : {cm['true_negative']}")
    print(f"  Total Mismatches                                      : {metrics['total_mismatches']}")

    if cm["mismatches"]:
        print(f"\n  Mismatch Cases:")
        for m in cm["mismatches"]:
            print(f"    {m['test_id']}: {m['candidate_id']}")
            print(f"      AI: {m['ai_decision']} | Human: {m['manual_decision']} | Score: {m['ats_score']}")
            print(f"      Note: {m['notes']}")

    # ── Step 5: Category Analysis ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Accuracy by Profile Category")
    print("─" * 65)
    print(f"\n  {'Category':<25} {'Correct':>8} {'Total':>7} {'Accuracy':>10} {'Target Met'}")
    print(f"  {'─'*25} {'─'*8} {'─'*7} {'─'*10} {'─'*10}")
    for cat, data in report["category_analysis"].items():
        met = "YES" if data["meets_target"] else "NO"
        print(f"  {cat:<25} {data['correct']:>8} {data['total']:>7} "
              f"{round(data['accuracy']*100,1):>9}% {met:>10}")

    # ── Step 6: Role Analysis ─────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Accuracy by Role Type")
    print("─" * 65)
    print(f"\n  {'Role':<22} {'Correct':>8} {'Total':>7} {'Accuracy':>10} {'Avg Score':>10}")
    print(f"  {'─'*22} {'─'*8} {'─'*7} {'─'*10} {'─'*10}")
    for role, data in report["role_analysis"].items():
        print(f"  {role:<22} {data['correct']:>8} {data['total']:>7} "
              f"{round(data['accuracy']*100,1):>9}% {data['avg_score']:>10}")

    # ── Step 7: Improvement Backlog ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 7: Improvement Backlog")
    print("─" * 65)
    for i, item in enumerate(report["improvement_backlog"], 1):
        print(f"\n  [{item['priority']}] {item['area']}")
        print(f"    Issue       : {item['issue']}")
        print(f"    Improvement : {item['improvement']}")

    # ── Save Output ───────────────────────────────────────────────────────────
    tester.save_report(report, "data/outputs/ats_testing_report.json")

    print("\n" + "=" * 65)
    print("ATS system testing complete!")
    print("=" * 65 + "\n")

    return report


if __name__ == "__main__":
    run_ats_tests()
