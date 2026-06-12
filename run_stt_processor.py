"""
Day 24 - Speech-to-Text Integration & Cleaning
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.stt_processor import (
    STTCleaner, STTAccuracyTester,
    STT_TEST_CASES, ACCENT_TEST_PROFILES, SPEECH_THRESHOLDS
)


def run_stt():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - SPEECH-TO-TEXT INTEGRATION & CLEANING v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    cleaner = STTCleaner()
    tester  = STTAccuracyTester()

    # ── Step 1: Pipeline Demo ─────────────────────────────────────────────────
    print("\nStep 1: STT Cleaning Pipeline Demo")
    print("─" * 65)
    samples = [
        "Um, so I have like, you know, around five years of experience with Python.",
        "I have been working with— I mean my current role involves Python and Django.",
        "Yeah definitely, my curr CTC is ten LPA and I expect fourteen LPA.",
        "You can reach me at john@email.com or call 9876543210.",
        "i work at infosys i have been there for two years",
    ]
    for raw in samples:
        result = cleaner.clean(raw)
        print(f"\n  Raw  : {raw}")
        print(f"  Clean: {result['clean_text']}")
        comp = result['completeness']
        print(f"  Words: {comp['word_count']}  Completeness: {comp['completeness']}")

    # ── Step 2: Filler Removal Detail ────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Individual Cleaning Steps")
    print("─" * 65)
    test_text = "Um, so basically I have like three yrs exp as a sr dev."
    result = cleaner.clean(test_text)
    print()
    for step in result['steps']:
        print(f"  [{step['step']:<22}]: {step['text']}")

    # ── Step 3: Partial / Silence Classification ──────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Answer Completeness & Silence Detection")
    print("─" * 65)
    answers = [
        "",
        "Yes.",
        "Around three.",
        "I have about three years.",
        "I have been working with Python for about three and a half years, primarily on Django REST APIs and AWS deployments.",
    ]
    print("\n  Completeness Classification:")
    for ans in answers:
        comp = cleaner.classify_answer_completeness(ans)
        print(f"    [{comp['completeness']:<10}] words={comp['word_count']:<4} needs_followup={comp['needs_followup']}  '{ans[:50]}'")

    print("\n  Silence Detection:")
    for secs in [2.0, 6.0, 10.0, 16.0]:
        result_s = cleaner.classify_silence(secs)
        print(f"    {secs}s -> [{result_s['action']:<20}] flagged={result_s['flagged']}  {result_s['message']}")

    # ── Step 4: STT Accuracy Tests ────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: STT Accuracy Test Report")
    print("─" * 65)
    report = tester.run_all_tests()
    meta   = report["report_metadata"]
    print(f"\n  Total Tests : {meta['total_tests']}")
    print(f"  Passed      : {meta['passed']}")
    print(f"  Failed      : {meta['failed']}")
    print(f"  Pass Rate   : {meta['pass_rate']}%")
    print(f"  Avg WER     : {meta['avg_wer']}")

    print(f"\n  {'Test ID':<10} {'Category':<24} {'Accent':<26} {'WER':>6} {'Pass'}")
    print(f"  {'─'*10} {'─'*24} {'─'*26} {'─'*6} {'─'*5}")
    for r in report["test_results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['test_id']:<10} {r['category']:<24} {r['accent']:<26} {r['wer']:>6.4f} {status}")

    print(f"\n  By Category:")
    for cat, data in report["by_category"].items():
        rate = round(data["passed"]/data["total"]*100, 0)
        print(f"    {cat:<24} : {data['passed']}/{data['total']} ({rate:.0f}%)")

    # ── Step 5: Accent Profile Summary ───────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Accent Test Profiles")
    print("─" * 65)
    print(f"\n  {'Profile':<30} {'Region':<24} {'Expected WER'}")
    print(f"  {'─'*30} {'─'*24} {'─'*12}")
    for p in ACCENT_TEST_PROFILES:
        print(f"  {p['profile']:<30} {p['region']:<24} {p['expected_wer']}")

    # ── Save ──────────────────────────────────────────────────────────────────
    tester.save_report(report, "data/outputs/stt_accuracy_report.json")

    clean_results = [
        {
            "test_id": tc["test_id"],
            "raw":     tc["raw"],
            "clean":   cleaner.clean(tc["raw"])["clean_text"],
        }
        for tc in STT_TEST_CASES
    ]
    with open("data/outputs/stt_clean_results.json", "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=2, ensure_ascii=False)
    print("Saved -> data/outputs/stt_clean_results.json")

    print("\n" + "=" * 65)
    print("Speech-to-Text Integration & Cleaning complete!")
    print("=" * 65 + "\n")

    return cleaner, report


if __name__ == "__main__":
    run_stt()
