"""
Day 30 - Screening System Testing & Optimization
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.screening_optimizer import (
    SystemTestReport, ScreeningSimulator, ThresholdTuner,
    SCREENING_TEST_CASES, THRESHOLD_CONFIG_V1, THRESHOLD_CONFIG_V2,
    OPTIMIZATION_RESULTS, FALSE_REJECTION_PATTERNS, INTENT_IMPROVEMENTS
)


def run_optimization():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - SCREENING SYSTEM TESTING & OPTIMIZATION v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    report_gen = SystemTestReport()
    simulator  = ScreeningSimulator()
    tuner      = ThresholdTuner()

    # ── Step 1: Simulated Screening Call Results ───────────────────────────────
    print("\nStep 1: Simulated Screening Calls")
    print("─" * 65)
    sim = simulator.run_all()
    meta = sim["report_metadata"]
    print(f"\n  Total Tests      : {meta['total_tests']}")
    print(f"  Passed           : {meta['passed']}")
    print(f"  Failed           : {meta['failed']}")
    print(f"  Pass Rate        : {meta['pass_rate']}%")
    print(f"  Label Accuracy   : {meta['label_accuracy']}")
    print(f"  Intent Accuracy  : {meta['intent_accuracy']}")

    print(f"\n  {'Test ID':<10} {'Category':<14} {'Human Label':<18} {'AI Label':<18} {'Pass'}")
    print(f"  {'─'*10} {'─'*14} {'─'*18} {'─'*18} {'─'*5}")
    for r in sim["test_results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['test_id']:<10} {r['category']:<14} "
              f"{r['human_label']:<18} {r['ai_label']:<18} {status}")

    # ── Step 2: By Category Accuracy ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Accuracy by Category")
    print("─" * 65)
    print(f"\n  {'Category':<16} {'Passed':>7} {'Total':>6} {'Rate':>6}")
    print(f"  {'─'*16} {'─'*7} {'─'*6} {'─'*6}")
    for cat, data in sim["by_category"].items():
        rate = round(data["passed"]/data["total"]*100, 0)
        print(f"  {cat:<16} {data['passed']:>7} {data['total']:>6} {rate:>5.0f}%")

    # ── Step 3: Threshold Comparison ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Threshold Optimization — V1 vs V2")
    print("─" * 65)
    changes = tuner.compare()
    print(f"\n  {'Threshold':<30} {'V1':>8} {'V2':>8} {'Change':<10} {'Rationale'}")
    print(f"  {'─'*30} {'─'*8} {'─'*8} {'─'*10} {'─'*30}")
    for c in changes:
        print(f"  {c['threshold']:<30} {str(c['v1']):>8} {str(c['v2']):>8} "
              f"{c['direction']:<10} {c['rationale'][:40]}")

    # ── Step 4: False Rejection Patterns ─────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: False Rejection Patterns Fixed")
    print("─" * 65)
    for frp in FALSE_REJECTION_PATTERNS:
        print(f"\n  [{frp['pattern_id']}] {frp['description']}")
        print(f"    Example    : {str(frp['example'])[:60]}")
        print(f"    Old Behavior: {frp['old_behavior']}")
        print(f"    Fix        : {frp['fix']}")
        print(f"    Impact     : {frp['impact']}")

    # ── Step 5: Intent Detection Improvements ────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Intent Detection Improvements")
    print("─" * 65)
    for imp in INTENT_IMPROVEMENTS:
        print(f"\n  [{imp['improvement_id']}] {imp['category']} — {imp['issue']}")
        print(f"    New patterns added: {len(imp['new_patterns']) - len(imp['old_patterns'])}")
        print(f"    Accuracy delta    : {imp['accuracy_delta']}")

    # ── Step 6: Optimization Results ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Optimization Results Summary")
    print("─" * 65)
    print(f"\n  {'Metric':<35} {'Before':>8} {'After':>8} {'Improvement'}")
    print(f"  {'─'*35} {'─'*8} {'─'*8} {'─'*20}")
    for metric, data in OPTIMIZATION_RESULTS.items():
        print(f"  {metric:<35} {data['before']:>8} {data['after']:>8}  {data['improvement']}")

    # ── Save ──────────────────────────────────────────────────────────────────
    full_report = report_gen.generate()
    report_gen.save_report(full_report, "data/outputs/screening_test_report.json")

    print("\n" + "=" * 65)
    print("Screening System Testing & Optimization complete!")
    print("=" * 65 + "\n")
    return full_report


if __name__ == "__main__":
    run_optimization()
