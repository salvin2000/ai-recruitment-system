"""
Day 31 - Edge Case & Failure Handling
Runner script

Simulates a screening call that runs into every edge case the module is
designed to handle: poor audio, language mixing, a missing answer,
background noise, and finally a repeated failure that triggers the
hard-abort safety fallback.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.edge_case_handler import (
    RobustFlowController, EdgeCaseDetector, RetryClarificationManager,
    EDGE_CASE_TYPES, AUDIO_QUALITY_THRESHOLDS, FALLBACK_RESPONSES,
    SAFETY_FALLBACKS,
)


def run_edge_case_demo():
    print("=" * 65)
    print("   ZECPATH AI - EDGE CASE & FAILURE HANDLING v1.0")
    print("=" * 65)

    controller = RobustFlowController("SESS-EDGE-001", "Arjun Krishnan")

    # ── Step 1: Start the call ──────────────────────────────────────────
    print("\nStep 1: Start Call")
    print("-" * 65)
    start = controller.start_call()
    print(f"  [{start['state'].upper()}] {start['message']}")

    # ── Step 2: Poor audio ──────────────────────────────────────────────
    print("\nStep 2: Poor Audio Quality")
    print("-" * 65)
    controller.ask_question("Q020", "How many years of experience do you have?")
    poor_audio_answer = {
        "clean_text": "...experience around...", "raw_text": "...experience around...",
        "word_count": 2, "confidence": 0.25,
    }
    result = controller.process_answer(poor_audio_answer, "Q020", "numeric")
    print(f"  Edge Case : {result['edge_case']}")
    print(f"  Action    : {result['action']}")
    print(f"  Message   : {result['message']}")

    # ── Step 3: Language mixing ──────────────────────────────────────────
    print("\nStep 3: Language Mixing")
    print("-" * 65)
    controller.ask_question("Q021", "What is your current role?")
    mixed_answer = {
        "clean_text": "Haan I am working as a software engineer matlab developer",
        "raw_text": "Haan I am working as a software engineer matlab developer",
        "word_count": 9, "confidence": 0.88,
    }
    result = controller.process_answer(mixed_answer, "Q021", "text")
    print(f"  Edge Case : {result['edge_case']}")
    print(f"  Action    : {result['action']}")
    print(f"  Message   : {result['message']}")

    # ── Step 4: Missing answer ───────────────────────────────────────────
    print("\nStep 4: Missing Answer")
    print("-" * 65)
    controller.ask_question("Q022", "What is your notice period?")
    missing_answer = {"clean_text": "", "raw_text": "", "word_count": 0, "confidence": 0.0}
    result = controller.process_answer(missing_answer, "Q022", "text")
    print(f"  Edge Case : {result['edge_case']}")
    print(f"  Action    : {result['action']}")
    print(f"  Message   : {result['message']}")

    # ── Step 5: Background noise ─────────────────────────────────────────
    print("\nStep 5: Background Noise")
    print("-" * 65)
    controller.ask_question("Q023", "What are your top technical skills?")
    noisy_answer = {
        "clean_text": "[noise] Python and [crosstalk] SQL",
        "raw_text": "[noise] Python and [crosstalk] SQL",
        "word_count": 4, "confidence": 0.7,
    }
    result = controller.process_answer(noisy_answer, "Q023", "text")
    print(f"  Edge Case : {result['edge_case']}")
    print(f"  Action    : {result['action']}")
    print(f"  Message   : {result['message']}")

    # ── Step 6: Repeated failure escalation ──────────────────────────────
    print("\nStep 6: Repeated Failure Escalation (Safety Fallback)")
    print("-" * 65)
    controller.ask_question("Q024", "What is your expected salary?")
    for attempt in range(1, 4):
        bad_audio = {"clean_text": "xx", "raw_text": "xx", "word_count": 1, "confidence": 0.1}
        result = controller.process_answer(bad_audio, "Q024", "text")
        print(f"  Attempt {attempt}: [{result['action']:<14}] {result['message'][:55]}")

    # ── Step 7: Robustness Summary ───────────────────────────────────────
    print("\nStep 7: Robustness Summary")
    print("-" * 65)
    summary = controller.get_robustness_summary()
    ec_summary = summary["edge_case_summary"]
    print(f"  Total Edge Cases Handled : {ec_summary['total_edge_cases']}")
    print(f"  Consecutive Same Case    : {ec_summary['consecutive_same_case']}")
    print(f"  Per-Question Breakdown   :")
    for qid, counts in ec_summary["per_question_counts"].items():
        print(f"    {qid}: {counts}")

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = "data/outputs/edge_case_log.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved -> {output_path}")

    print("\n" + "=" * 65)
    print("Edge Case & Failure Handling complete!")
    print("=" * 65 + "\n")
    return controller


if __name__ == "__main__":
    run_edge_case_demo()
