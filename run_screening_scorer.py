"""
Day 26 - Screening Scoring Engine
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.screening_scorer import (
    ScreeningScorer, DimensionScorer,
    SCORING_DIMENSIONS, GRADE_THRESHOLDS, QUESTION_SCORING_CONFIG
)


# ── Sample Answers from Day 25 ────────────────────────────────────────────────

SAMPLE_ANSWERS = [
    {
        "question_id": "Q020", "question_category": "experience",
        "answer_type": "numeric",
        "raw_text":    "I have around 3.5 years of experience with Python.",
        "clean_text":  "I have around 3.5 years of experience with Python.",
        "intent": "experience_info", "sub_intents": ["skill_info"],
        "extracted": {"experience_years": 3.5, "skills_mentioned": ["python"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 9, "confidence": 0.91,
    },
    {
        "question_id": "Q030", "question_category": "skills",
        "answer_type": "text",
        "raw_text":    "I mainly work with Python, Django, AWS, and Docker.",
        "clean_text":  "I mainly work with Python, Django, AWS, and Docker.",
        "intent": "skill_info", "sub_intents": [],
        "extracted": {"skills_mentioned": ["python", "django", "aws", "docker"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 9, "confidence": 0.94,
    },
    {
        "question_id": "Q041", "question_category": "location",
        "answer_type": "yes_no",
        "raw_text":    "Yes definitely, I am comfortable working from Bangalore.",
        "clean_text":  "Yes definitely, I am comfortable working from Bangalore.",
        "intent": "affirmative", "sub_intents": ["location_info"],
        "extracted": {"boolean_value": True, "location": "Bangalore"},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 8, "confidence": 0.88,
    },
    {
        "question_id": "Q052", "question_category": "salary",
        "answer_type": "yes_no",
        "raw_text":    "Yes, that budget aligns with my expectations.",
        "clean_text":  "Yes, that budget aligns with my expectations.",
        "intent": "affirmative", "sub_intents": ["salary_info"],
        "extracted": {"boolean_value": True},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 7, "confidence": 0.92,
    },
    {
        "question_id": "Q061", "question_category": "notice_period",
        "answer_type": "numeric",
        "raw_text":    "I have a 30 day notice period but can negotiate.",
        "clean_text":  "I have a 30 day notice period but can negotiate.",
        "intent": "availability", "sub_intents": [],
        "extracted": {"notice_period": {"value": 30, "unit": "days"}},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 9, "confidence": 0.89,
    },
    {
        "question_id": "Q010", "question_category": "education",
        "answer_type": "choice",
        "raw_text":    "I completed my B.Tech in Computer Science from NIT Calicut in 2022.",
        "clean_text":  "I completed my B.Tech in Computer Science from NIT Calicut in 2022.",
        "intent": "education_info", "sub_intents": [],
        "extracted": {},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 12, "confidence": 0.93,
    },
    {
        "question_id": "Q021", "question_category": "experience",
        "answer_type": "text",
        "raw_text":    "It depends.",
        "clean_text":  "It depends.",
        "intent": "vague", "sub_intents": [],
        "extracted": {},
        "is_valid": False, "is_vague": True, "is_off_topic": False,
        "needs_followup": True, "word_count": 2, "confidence": 0.85,
    },
    {
        "question_id": "Q031", "question_category": "skills",
        "answer_type": "numeric",
        "raw_text":    "I love cricket and IPL this season.",
        "clean_text":  "I love cricket and IPL this season.",
        "intent": "off_topic", "sub_intents": [],
        "extracted": {},
        "is_valid": False, "is_vague": False, "is_off_topic": True,
        "needs_followup": True, "word_count": 6, "confidence": 0.95,
    },
]

ATS_PROFILE = {
    "experience_years":     3.9,
    "skills":               ["python", "django", "aws", "docker", "postgresql"],
    "expected_salary_lpa":  12.0,
}


def run_scorer():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - SCREENING SCORING ENGINE v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    scorer     = ScreeningScorer()
    dim_scorer = DimensionScorer()

    # ── Step 1: Dimension Scoring Examples ───────────────────────────────────
    print("\nStep 1: Dimension Scoring Examples")
    print("─" * 65)
    test_cases = [
        ({"is_vague": False, "confidence": 0.91, "word_count": 9},   "Normal answer"),
        ({"is_vague": True,  "confidence": 0.85, "word_count": 3},   "Vague answer"),
        ({"is_vague": False, "confidence": 0.55, "word_count": 9},   "Low confidence"),
        ({"is_vague": False, "confidence": 0.91, "word_count": 2},   "Too short"),
        ({"is_vague": False, "confidence": 0.91, "word_count": 20},  "Detailed answer"),
    ]
    print(f"\n  {'Case':<20} {'Clarity':>8} {'Relevance':>10} {'Complete':>10}")
    print(f"  {'─'*20} {'─'*8} {'─'*10} {'─'*10}")
    for ans, label in test_cases:
        cl = dim_scorer.score_clarity(ans)
        rl = dim_scorer.score_relevance({**ans, "intent": "experience_info"}, "experience")
        co = dim_scorer.score_completeness({**ans, "extracted": {"experience_years": 3.5}}, "numeric")
        print(f"  {label:<20} {cl['score']:>8.4f} {rl['score']:>10.4f} {co['score']:>10.4f}")

    # ── Step 2: Per-Question Scoring ──────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Per-Question Score Breakdown")
    print("─" * 65)
    question_scores = []
    for ans in SAMPLE_ANSWERS:
        qs = scorer.score_answer(
            ans, ans["question_id"],
            ans["question_category"], ans["answer_type"],
            ATS_PROFILE
        )
        question_scores.append(qs)

    print(f"\n  {'Q':<6} {'Category':<14} {'Max':>5} {'Score':>7} {'0-1':>7} {'Valid'}")
    print(f"  {'─'*6} {'─'*14} {'─'*5} {'─'*7} {'─'*7} {'─'*5}")
    for qs in question_scores:
        print(f"  {qs['question_id']:<6} {qs['category']:<14} "
              f"{qs['max_score']:>5} {qs['scaled_score']:>7.2f} "
              f"{qs['raw_score_0_1']:>7.4f} {str(qs['is_valid'])}")

    # ── Step 3: Dimension Breakdown ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Dimension Scores per Question")
    print("─" * 65)
    print(f"\n  {'Q':<6} {'Clarity':>9} {'Relevance':>10} {'Complete':>10} {'Consist':>9}")
    print(f"  {'─'*6} {'─'*9} {'─'*10} {'─'*10} {'─'*9}")
    for qs in question_scores:
        d = qs["dimensions"]
        print(f"  {qs['question_id']:<6} "
              f"{d['clarity']['score']:>9.4f} "
              f"{d['relevance']['score']:>10.4f} "
              f"{d['completeness']['score']:>10.4f} "
              f"{d['consistency']['score']:>9.4f}")

    # ── Step 4: Final Aggregated Score ────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Final Screening Score")
    print("─" * 65)
    result = scorer.aggregate_scores(
        question_scores,
        session_id="ZCP-SESS-20260612-001",
        candidate_id="ZCP-CAND-ARJU"
    )
    print(f"\n  Final Score : {result['final_score']} / 100")
    print(f"  Grade       : {result['grade']} — {result['grade_label']}")
    print(f"  Outcome     : {result['outcome'].upper()}")

    print(f"\n  Category Breakdown:")
    for cat, data in result["category_scores"].items():
        bar = int(data["percentage"] / 5) * "█"
        print(f"    {cat:<14} : {data['total_score']:>5.1f}/{data['max_score']:>3} "
              f"({data['percentage']:>5.1f}%) {bar}")

    print(f"\n  Dimension Averages:")
    for dim, avg in result["dimension_averages"].items():
        print(f"    {dim:<15}: {avg:.4f}")

    print(f"\n  Explanation:")
    for line in result["explanation"]:
        print(f"    {line}")

    # ── Save ──────────────────────────────────────────────────────────────────
    scorer.save_results(result, "data/outputs/screening_score_result.json")

    print("\n" + "=" * 65)
    print("Screening Scoring Engine complete!")
    print("=" * 65 + "\n")
    return result


if __name__ == "__main__":
    run_scorer()
