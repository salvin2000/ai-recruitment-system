"""
Day 25 - Answer Intent & Understanding Engine
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.answer_understanding import (
    AnswerUnderstandingEngine, IntentClassifier, AnswerExtractor,
    INTENT_CATEGORIES, INTENT_SIGNALS
)


SAMPLE_TURNS = [
    {
        "raw_text":          "Yeah I have around 3.5 years of experience with Python.",
        "clean_text":        "I have around 3.5 years of experience with Python.",
        "question_id":       "Q031",
        "question_category": "skills",
        "answer_type":       "numeric",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.91,
    },
    {
        "raw_text":          "Yes definitely, I am comfortable working from Bangalore.",
        "clean_text":        "Yes definitely, I am comfortable working from Bangalore.",
        "question_id":       "Q041",
        "question_category": "location",
        "answer_type":       "yes_no",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.88,
    },
    {
        "raw_text":          "My current CTC is 8 LPA and I expect around 12 to 13 LPA.",
        "clean_text":        "My current CTC is 8 LPA and I expect around 12 to 13 LPA.",
        "question_id":       "Q051",
        "question_category": "salary",
        "answer_type":       "numeric",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.93,
    },
    {
        "raw_text":          "I have a 30 day notice period but I can negotiate.",
        "clean_text":        "I have a 30 day notice period but I can negotiate.",
        "question_id":       "Q061",
        "question_category": "notice_period",
        "answer_type":       "numeric",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.89,
    },
    {
        "raw_text":          "I mainly work with Python, Django, AWS, and Docker.",
        "clean_text":        "I mainly work with Python, Django, AWS, and Docker.",
        "question_id":       "Q030",
        "question_category": "skills",
        "answer_type":       "text",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.94,
    },
    {
        "raw_text":          "It depends.",
        "clean_text":        "It depends.",
        "question_id":       "Q042",
        "question_category": "location",
        "answer_type":       "yes_no",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.85,
    },
    {
        "raw_text":          "I love cricket and the IPL is really exciting this year.",
        "clean_text":        "I love cricket and the IPL is really exciting this year.",
        "question_id":       "Q020",
        "question_category": "experience",
        "answer_type":       "numeric",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.95,
    },
    {
        "raw_text":          "I completed my B.Tech in Computer Science from NIT Calicut in 2022.",
        "clean_text":        "I completed my B.Tech in Computer Science from NIT Calicut in 2022.",
        "question_id":       "Q010",
        "question_category": "education",
        "answer_type":       "choice",
        "session_id":        "ZCP-SESS-20260612-001",
        "confidence":        0.92,
    },
]


def run_understanding():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - ANSWER INTENT & UNDERSTANDING ENGINE v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    engine     = AnswerUnderstandingEngine()
    classifier = IntentClassifier()
    extractor  = AnswerExtractor()

    # ── Step 1: Intent Classification ────────────────────────────────────────
    print("\nStep 1: Intent Classification")
    print("─" * 65)
    test_texts = [
        ("Yeah definitely I am ready to proceed.",           "introduction"),
        ("I have 3.5 years of experience with Python.",      "skills"),
        ("My expected CTC is 12 LPA.",                       "salary"),
        ("I have a 60 day notice period.",                   "notice_period"),
        ("I don't know.",                                    "experience"),
        ("I love cricket and IPL this season.",              "experience"),
        ("Could you repeat the question please?",            "skills"),
    ]
    print(f"\n  {'Text':<50} {'Intent':<18} {'Vague':>6} {'Off-Topic':>10}")
    print(f"  {'─'*50} {'─'*18} {'─'*6} {'─'*10}")
    for text, cat in test_texts:
        result = classifier.classify(text, cat)
        print(f"  {text[:48]:<50} {result['primary_intent']:<18} "
              f"{str(result['is_vague']):>6} {str(result['is_off_topic']):>10}")

    # ── Step 2: Structured Extraction ────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Structured Value Extraction")
    print("─" * 65)
    extraction_tests = [
        ("I have around 3.5 years of experience with Python.",   "numeric"),
        ("My current CTC is 8 LPA and I expect 12 to 13 LPA.",  "numeric"),
        ("I have a 30 day notice period.",                       "numeric"),
        ("My notice period is 2 months.",                        "numeric"),
        ("I would rate myself 4 out of 5 in Python.",            "numeric"),
        ("I mainly work with Python, Django, AWS, and Docker.",  "text"),
        ("I am currently based in Bangalore.",                   "text"),
        ("Yes, I am comfortable with this.",                     "yes_no"),
        ("I can join immediately, no notice period.",            "numeric"),
    ]
    for text, atype in extraction_tests:
        extracted = extractor.extract_all(text, atype)
        print(f"\n  Text     : {text}")
        print(f"  Extracted: {extracted}")

    # ── Step 3: Full Understanding Pipeline ───────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Full Semantic Answer Objects")
    print("─" * 65)
    results = engine.understand_batch(SAMPLE_TURNS)
    print(f"\n  {'Q':<6} {'Category':<14} {'Intent':<18} {'Valid':>6} {'Vague':>6} {'Off-T':>6} {'Extracted'}")
    print(f"  {'─'*6} {'─'*14} {'─'*18} {'─'*6} {'─'*6} {'─'*6} {'─'*30}")
    for r in results:
        ext_str = str(r["extracted"])[:35] if r["extracted"] else "{}"
        print(f"  {r['question_id']:<6} {r['question_category']:<14} "
              f"{r['intent']:<18} {str(r['is_valid']):>6} "
              f"{str(r['is_vague']):>6} {str(r['is_off_topic']):>6}  {ext_str}")

    # ── Step 4: Detailed View ─────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Detailed Answer Objects (first 3)")
    print("─" * 65)
    for r in results[:3]:
        print(f"\n  {r['answer_id']}")
        print(f"    Question    : {r['question_id']} ({r['question_category']})")
        print(f"    Clean Text  : {r['clean_text'][:65]}")
        print(f"    Intent      : {r['intent']}  sub={r['sub_intents']}")
        print(f"    Extracted   : {r['extracted']}")
        print(f"    Valid       : {r['is_valid']}  Vague: {r['is_vague']}  "
              f"Off-topic: {r['is_off_topic']}")
        print(f"    Needs F/U   : {r['needs_followup']}  Words: {r['word_count']}")

    # ── Step 5: Vague and Off-Topic Summary ───────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Quality Summary")
    print("─" * 65)
    valid    = sum(1 for r in results if r["is_valid"])
    vague    = sum(1 for r in results if r["is_vague"])
    off_top  = sum(1 for r in results if r["is_off_topic"])
    followup = sum(1 for r in results if r["needs_followup"])
    print(f"\n  Total Answers   : {len(results)}")
    print(f"  Valid           : {valid}")
    print(f"  Vague           : {vague}")
    print(f"  Off-Topic       : {off_top}")
    print(f"  Needs Follow-Up : {followup}")

    # ── Save ──────────────────────────────────────────────────────────────────
    engine.save_results(results, "data/outputs/answer_understanding_results.json")

    print("\n" + "=" * 65)
    print("Answer Intent & Understanding Engine complete!")
    print("=" * 65 + "\n")
    return results


if __name__ == "__main__":
    run_understanding()
