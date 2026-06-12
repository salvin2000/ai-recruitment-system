"""
Day 23 - Transcript Data Architecture
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.transcript_architecture import (
    TranscriptArchitecture,
    METADATA_STANDARDS, DATABASE_SCHEMA,
    NORMALIZATION_RULES, TRANSCRIPT_STATUS, SCREENING_OUTCOMES
)


def run_architecture():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - TRANSCRIPT DATA ARCHITECTURE v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    arch = TranscriptArchitecture()

    # ── Step 1: Metadata Standards ────────────────────────────────────────────
    print("\nStep 1: Metadata Standards")
    print("─" * 65)
    print(f"\n  {'Field':<22} {'Format':<30} {'Required'}")
    print(f"  {'─'*22} {'─'*30} {'─'*8}")
    for field, meta in METADATA_STANDARDS.items():
        req = "Yes" if meta["required"] else "No"
        print(f"  {field:<22} {meta['format']:<30} {req}")

    # ── Step 2: Confidence Thresholds ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Confidence Level Classification")
    print("─" * 65)
    test_scores = [0.95, 0.87, 0.75, 0.62, 0.41]
    for score in test_scores:
        level = arch.classify_confidence(score)
        print(f"  Score {score:.2f} -> {level}")

    # ── Step 3: Text Normalization ────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Text Normalization Examples")
    print("─" * 65)
    samples = [
        "Um, yeah I have like five yrs of experience with Python",
        "My CTC is around 10 LPA and I expect about 14-15 LPA",
        "Contact me at john@email.com or call 9876543210",
        "I have worked with ML and JS for about 3 yrs",
        "Nope, I am not open to relocation at this time",
    ]
    for sample in samples:
        normalized = arch.normalize_text(sample)
        print(f"\n  Raw  : {sample}")
        print(f"  Clean: {normalized}")

    # ── Step 4: Answer Extraction ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Answer Extraction")
    print("─" * 65)
    print("\n  Yes/No Extraction:")
    yn_tests = [
        "Yeah definitely, I am ready",
        "Nope, that doesn't work for me",
        "Of course, absolutely",
        "I cannot commit to that timeline",
    ]
    for t in yn_tests:
        result = arch.extract_yes_no(arch.normalize_text(t))
        print(f"    '{t[:45]}' -> {result}")

    print("\n  Numeric Extraction:")
    num_tests = [
        "I have about 3.5 years of experience",
        "My expected CTC is 12 LPA",
        "Notice period is 60 days",
    ]
    for t in num_tests:
        result = arch.extract_numeric(arch.normalize_text(t))
        print(f"    '{t}' -> {result}")

    # ── Step 5: Build a Sample Transcript ─────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Sample Transcript Build")
    print("─" * 65)
    session_id = arch.generate_session_id("20260610", 1)
    turns = [
        arch.build_turn(session_id, 0, "ai",
            "Good morning, Arjun Krishnan. I am an AI screening assistant from Zecpath.",
            question_id="Q001", confidence=1.0, duration_ms=4200),
        arch.build_turn(session_id, 1, "candidate",
            "Yeah, good morning! Um, I am ready to proceed.",
            question_id="Q001", confidence=0.91, duration_ms=3100),
        arch.build_turn(session_id, 2, "ai",
            "How many years of experience do you have with Python?",
            question_id="Q031", confidence=1.0, duration_ms=2800),
        arch.build_turn(session_id, 3, "candidate",
            "I have around 3.5 yrs of Python experience, mostly with Django and REST APIs.",
            question_id="Q031", confidence=0.88, duration_ms=5200),
        arch.build_turn(session_id, 4, "ai",
            "Our budget for this role is between 8 and 14 LPA. Does this align with your expectations?",
            question_id="Q052", confidence=1.0, duration_ms=3500),
        arch.build_turn(session_id, 5, "candidate",
            "Yes, that aligns with my expectations.",
            question_id="Q052", confidence=0.72, duration_ms=2400),
    ]

    transcript = arch.build_transcript(
        "ZCP-CAND-ARJU", "ZCP-JOB-20260529-SW01", turns
    )

    print(f"\n  Transcript ID  : {transcript['transcript_id']}")
    print(f"  Session ID     : {transcript['session_id']}")
    print(f"  Candidate      : {transcript['candidate_id']}")
    print(f"  Job            : {transcript['job_id']}")
    print(f"  Status         : {transcript['status']}")
    print(f"  Total Turns    : {transcript['total_turns']}")
    print(f"  AI Turns       : {transcript['ai_turns']}")
    print(f"  Candidate Turns: {transcript['candidate_turns']}")
    print(f"  Avg Confidence : {transcript['avg_confidence']}")
    print(f"  Flagged Turns  : {transcript['flagged_turns']}")

    print(f"\n  {'Turn':<5} {'Speaker':<12} {'Q':<6} {'Confidence':<12} {'Flagged':<8} {'Text (first 50 chars)'}")
    print(f"  {'─'*5} {'─'*12} {'─'*6} {'─'*12} {'─'*8} {'─'*50}")
    for t in turns:
        flag = "YES" if t["is_flagged"] else "-"
        qid  = t["question_id"] or "-"
        print(f"  {t['turn_index']:<5} {t['speaker']:<12} {qid:<6} "
              f"{t['confidence_score']:<12} {flag:<8} {t['raw_text'][:50]}")

    # ── Step 6: Schema Summary ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Database Schema Summary")
    print("─" * 65)
    summary = arch.get_schema_summary()
    print(f"\n  Total Tables : {summary['total_tables']}")
    print(f"  Total Fields : {summary['total_fields']}")
    print(f"\n  {'Table':<28} {'Fields':>7} {'Primary Key'}")
    print(f"  {'─'*28} {'─'*7} {'─'*30}")
    for table in summary["tables"]:
        pk   = summary["primary_keys"][table]
        flds = summary["field_counts"][table]
        print(f"  {table:<28} {flds:>7} {', '.join(pk)}")

    # ── Step 7: Turn Validation ───────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 7: Turn Validation")
    print("─" * 65)
    for t in turns:
        result = arch.validate_turn(t)
        status = "VALID" if result["valid"] else "INVALID"
        print(f"  Turn {t['turn_index']} ({t['speaker']:<10}) : {status}")

    # ── Save ──────────────────────────────────────────────────────────────────
    arch.save_architecture("data/outputs/transcript_architecture.json")

    with open("data/outputs/sample_transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, default=str, ensure_ascii=False)
    print("Saved -> data/outputs/sample_transcript.json")

    print("\n" + "=" * 65)
    print("Transcript data architecture complete!")
    print("=" * 65 + "\n")

    return arch, transcript


if __name__ == "__main__":
    run_architecture()
