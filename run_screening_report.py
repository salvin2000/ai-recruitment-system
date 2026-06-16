"""
Day 28 - AI Screening Report Generator
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.screening_report import ScreeningReportGenerator


# ── Sample Data (from Days 25-27 outputs) ────────────────────────────────────

CANDIDATE_PROFILE = {
    "candidate_id":  "ZCP-CAND-ARJU",
    "session_id":    "ZCP-SESS-20260612-001",
    "name":          "Arjun Krishnan",
    "ats_score":     82.24,
    "experience_years": 3.9,
    "skills":        ["python", "django", "aws", "docker", "postgresql"],
}

JOB_PROFILE = {
    "job_id":         "ZCP-JOB-20260529-SW01",
    "role_name":      "Software Engineer",
    "company":        "Zescer Business LLP",
    "required_skills":["python", "django", "aws", "docker", "rest api"],
    "preferred_skills":["kubernetes", "machine learning", "react"],
    "min_salary_lpa":  8,
    "max_salary_lpa":  14,
    "max_notice_days": 60,
}

ANSWER_OBJECTS = [
    {
        "question_id": "Q020", "question_category": "experience", "answer_type": "numeric",
        "clean_text": "I have around 3.5 years of experience with Python.",
        "intent": "experience_info", "extracted": {"experience_years": 3.5, "skills_mentioned": ["python"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 9, "confidence": 0.91,
    },
    {
        "question_id": "Q030", "question_category": "skills", "answer_type": "text",
        "clean_text": "I mainly work with Python, Django, AWS, and Docker.",
        "intent": "skill_info", "extracted": {"skills_mentioned": ["python", "django", "aws", "docker"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 9, "confidence": 0.94,
    },
    {
        "question_id": "Q041", "question_category": "location", "answer_type": "yes_no",
        "clean_text": "Yes definitely, I am comfortable working from Bangalore.",
        "intent": "affirmative", "extracted": {"boolean_value": True, "location": "Bangalore"},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 8, "confidence": 0.88,
    },
    {
        "question_id": "Q051", "question_category": "salary", "answer_type": "numeric",
        "clean_text": "My current CTC is 8 LPA and I expect around 12 to 13 LPA.",
        "intent": "salary_info", "extracted": {"salary_lpa": 8.0, "experience_years": 12.0},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 14, "confidence": 0.93,
    },
    {
        "question_id": "Q052", "question_category": "salary", "answer_type": "yes_no",
        "clean_text": "Yes, that budget aligns with my expectations.",
        "intent": "affirmative", "extracted": {"boolean_value": True},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 7, "confidence": 0.92,
    },
    {
        "question_id": "Q061", "question_category": "notice_period", "answer_type": "numeric",
        "clean_text": "I have a 30 day notice period but can negotiate.",
        "intent": "availability", "extracted": {"notice_period": {"value": 30, "unit": "days"}},
        "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False,
        "word_count": 9, "confidence": 0.89,
    },
    {
        "question_id": "Q021", "question_category": "experience", "answer_type": "text",
        "clean_text": "It depends.",
        "intent": "vague", "extracted": {},
        "is_valid": False, "is_vague": True, "is_off_topic": False, "needs_followup": True,
        "word_count": 2, "confidence": 0.85,
    },
    {
        "question_id": "Q031", "question_category": "skills", "answer_type": "numeric",
        "clean_text": "I love cricket and IPL this season.",
        "intent": "off_topic", "extracted": {},
        "is_valid": False, "is_vague": False, "is_off_topic": True, "needs_followup": True,
        "word_count": 6, "confidence": 0.95,
    },
]

SCREENING_SCORE = {
    "final_score": 86.5,
    "grade": "A",
    "grade_label": "Excellent — Recommend for Interview",
    "outcome": "advance",
    "category_scores": {
        "experience":    {"total_score": 25.9, "max_score": 30, "percentage": 86.3},
        "skills":        {"total_score": 20.0, "max_score": 35, "percentage": 57.1},
        "location":      {"total_score": 10.0, "max_score": 10, "percentage": 100.0},
        "salary":        {"total_score": 10.0, "max_score": 10, "percentage": 100.0},
        "notice_period": {"total_score": 10.0, "max_score": 10, "percentage": 100.0},
    },
    "dimension_averages": {
        "clarity": 0.9450, "relevance": 0.8125,
        "completeness": 0.8550, "consistency": 1.0000,
    },
    "explanation": [
        "Final screening score: 86.5/100 — Grade A — Excellent — Recommend for Interview",
        "Strongest area: location (100.0%)",
        "Weakest area: skills (57.1%)",
    ],
    "mandatory_failed": ["Q031"],
}

BEHAVIORAL_REPORT = {
    "summary": {
        "avg_confidence_score":   0.5800,
        "avg_sentiment_score":    0.3333,
        "avg_strength_score":     68.5,
        "overall_strength_level": "moderate",
        "overall_strength_label": "Moderate Communicator",
        "total_hesitations":      3,
        "total_uncertainties":    1,
    },
    "behavioral_tag_frequency": {
        "on_topic": 6, "positive_framing": 4, "fast_responder": 5,
        "off_topic": 1, "hesitant": 0, "contradictory": 0,
    },
    "per_answer_results": [
        {"behavioral_tags": ["on_topic", "positive_framing", "fast_responder"]},
        {"behavioral_tags": ["on_topic", "positive_framing"]},
        {"behavioral_tags": ["on_topic", "fast_responder"]},
        {"behavioral_tags": ["on_topic", "positive_framing"]},
        {"behavioral_tags": ["on_topic"]},
        {"behavioral_tags": ["on_topic", "fast_responder"]},
        {"behavioral_tags": ["on_topic"]},
        {"behavioral_tags": ["off_topic"]},
    ],
}


def run_report():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - SCREENING REPORT GENERATOR v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    generator = ScreeningReportGenerator()

    # ── Step 1: Generate Report ───────────────────────────────────────────────
    print("\nStep 1: Generating Screening Report")
    print("─" * 65)
    report = generator.generate(
        CANDIDATE_PROFILE, JOB_PROFILE, ANSWER_OBJECTS,
        SCREENING_SCORE, BEHAVIORAL_REPORT
    )

    # Candidate Summary
    c = report["candidate_summary"]
    print(f"\n  Candidate     : {c['name']}")
    print(f"  Role          : {c['role_applied']} at {c['company']}")
    print(f"  ATS Score     : {c['ats_score']}")
    print(f"  Screen Score  : {c['screening_score']} / 100  |  Grade: {c['grade']}")
    print(f"  Outcome       : {c['outcome'].upper()}")

    # ── Step 2: Skill Confirmations ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Skill Confirmations")
    print("─" * 65)
    skills = report["skill_confirmations"]
    print(f"\n  All Confirmed  : {', '.join(skills['confirmed'])}")
    print(f"  Required Match : {', '.join(skills['required_match'])}")
    print(f"  Preferred Match: {', '.join(skills['preferred_match']) or 'None'}")

    # ── Step 3: Availability & Salary ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Availability & Salary")
    print("─" * 65)
    avail = report["availability"]
    sal   = report["salary_expectation"]
    print(f"\n  Notice Period   : {avail.get('notice_period', {}).get('value', 'N/A')} days")
    print(f"  Location OK     : {avail.get('location_comfortable')}")
    print(f"  Availability OK : {avail.get('availability_ok')}")
    print(f"  Stated CTC      : {sal.get('stated_lpa', 'N/A')} LPA")
    print(f"  Budget Range    : {sal.get('budget_min_lpa')} - {sal.get('budget_max_lpa')} LPA")
    print(f"  Budget Aligned  : {sal.get('budget_aligned')}")

    # ── Step 4: Strengths & Risks ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Strengths & Risks")
    print("─" * 65)
    print(f"\n  Strengths ({len(report['strengths'])}):")
    for s in report["strengths"]:
        print(f"    [+] {s['label']}")
        print(f"        {s['evidence']}")

    print(f"\n  Risks ({len(report['risks'])}):")
    for r in report["risks"]:
        print(f"    [!] [{r['severity'].upper()}] {r['label']}")
        print(f"        {r['evidence']}")

    # ── Step 5: Missing Data ──────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Missing Data")
    print("─" * 65)
    missing = report["missing_data"]
    print(f"\n  Total Answers  : {missing['total_answers']}")
    print(f"  Valid Answers  : {missing['total_valid_answers']}")
    print(f"  Unanswered     : {missing['unanswered_questions']}")
    print(f"  Vague          : {missing['vague_questions']}")
    print(f"  Off-Topic      : {missing['offtopic_questions']}")

    # ── Step 6: Recommendation ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Final Recommendation")
    print("─" * 65)
    rec = report["recommendation"]
    print(f"\n  Level       : {rec['level'].upper()}")
    print(f"  Label       : {rec['label']}")
    print(f"  Description : {rec['description']}")

    # ── Step 7: Export Formats ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 7: Exported Formats")
    print("─" * 65)
    summary_text  = generator.export_summary(report)
    markdown_text = generator.export_markdown(report)
    print("\n" + summary_text)

    # ── Save ──────────────────────────────────────────────────────────────────
    generator.save_report(report, "data/outputs/screening_report.json")

    with open("data/outputs/screening_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_text)
    print("Saved -> data/outputs/screening_report.md")

    with open("data/outputs/screening_report_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary_text)
    print("Saved -> data/outputs/screening_report_summary.txt")

    print("\n" + "=" * 65)
    print("AI Screening Report Generator complete!")
    print("=" * 65 + "\n")
    return report


if __name__ == "__main__":
    run_report()
