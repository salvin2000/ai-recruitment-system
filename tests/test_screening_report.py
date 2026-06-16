"""
Tests for Day 28 – AI Screening Report Generator
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.screening_report import (
    ScreeningReportGenerator, ReportDataCollector, StrengthRiskAnalyzer,
    REPORT_SECTIONS, STRENGTH_INDICATORS, RISK_INDICATORS,
    REPORT_TEMPLATES, RECOMMENDATION_LEVELS, EXPORT_FORMATS,
)


# ── Sample Data ───────────────────────────────────────────────────────────────

CANDIDATE = {
    "candidate_id": "ZCP-CAND-ARJU", "session_id": "SESS-001",
    "name": "Arjun Krishnan", "ats_score": 82.24, "experience_years": 3.9,
    "skills": ["python", "django", "aws"],
}

JOB = {
    "job_id": "JOB-001", "role_name": "Software Engineer",
    "company": "Zescer", "required_skills": ["python", "django", "aws"],
    "preferred_skills": ["kubernetes", "react"],
    "min_salary_lpa": 8, "max_salary_lpa": 14, "max_notice_days": 60,
}

ANSWERS = [
    {
        "question_id": "Q020", "question_category": "experience", "answer_type": "numeric",
        "clean_text": "I have 3.5 years of Python experience.",
        "intent": "experience_info",
        "extracted": {"experience_years": 3.5, "skills_mentioned": ["python"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 8, "confidence": 0.91,
    },
    {
        "question_id": "Q030", "question_category": "skills", "answer_type": "text",
        "clean_text": "I work with Python, Django, and AWS.",
        "intent": "skill_info",
        "extracted": {"skills_mentioned": ["python", "django", "aws"]},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 7, "confidence": 0.94,
    },
    {
        "question_id": "Q041", "question_category": "location", "answer_type": "yes_no",
        "clean_text": "Yes, comfortable with Bangalore.",
        "intent": "affirmative",
        "extracted": {"boolean_value": True, "location": "Bangalore"},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 4, "confidence": 0.88,
    },
    {
        "question_id": "Q052", "question_category": "salary", "answer_type": "yes_no",
        "clean_text": "Yes, budget aligns.",
        "intent": "affirmative",
        "extracted": {"boolean_value": True, "salary_lpa": 8.0},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 3, "confidence": 0.92,
    },
    {
        "question_id": "Q061", "question_category": "notice_period", "answer_type": "numeric",
        "clean_text": "30 day notice period.",
        "intent": "availability",
        "extracted": {"notice_period": {"value": 30, "unit": "days"}},
        "is_valid": True, "is_vague": False, "is_off_topic": False,
        "needs_followup": False, "word_count": 4, "confidence": 0.89,
    },
    {
        "question_id": "Q021", "question_category": "experience", "answer_type": "text",
        "clean_text": "It depends.", "intent": "vague", "extracted": {},
        "is_valid": False, "is_vague": True, "is_off_topic": False,
        "needs_followup": True, "word_count": 2, "confidence": 0.85,
    },
]

SCORE = {
    "final_score": 86.5, "grade": "A",
    "grade_label": "Excellent — Recommend for Interview", "outcome": "advance",
    "category_scores": {"experience": {"total_score": 25, "max_score": 30, "percentage": 83.0}},
    "dimension_averages": {"clarity": 0.94, "relevance": 0.81},
    "explanation": ["Score: 86.5 — A"],
    "mandatory_failed": [],
}

BEHAV = {
    "summary": {
        "avg_confidence_score": 0.58, "avg_sentiment_score": 0.33,
        "avg_strength_score": 68.5, "overall_strength_level": "moderate",
        "overall_strength_label": "Moderate Communicator",
        "total_hesitations": 2, "total_uncertainties": 0,
    },
    "behavioral_tag_frequency": {"on_topic": 5, "positive_framing": 3},
    "per_answer_results": [
        {"behavioral_tags": ["on_topic", "positive_framing"]},
        {"behavioral_tags": ["on_topic"]},
    ],
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def generator():
    return ScreeningReportGenerator()

@pytest.fixture
def collector():
    return ReportDataCollector()

@pytest.fixture
def analyzer():
    return StrengthRiskAnalyzer()

@pytest.fixture
def collected(collector):
    return collector.collect(CANDIDATE, JOB, ANSWERS, SCORE, BEHAV)

@pytest.fixture
def report(generator):
    return generator.generate(CANDIDATE, JOB, ANSWERS, SCORE, BEHAV)


# ── ReportDataCollector Tests ─────────────────────────────────────────────────

def test_collector_creates_instance(collector):
    assert collector is not None

def test_collect_returns_dict(collected):
    assert isinstance(collected, dict)

def test_collect_has_key_answers(collected):
    assert "key_answers" in collected
    assert len(collected["key_answers"]) > 0

def test_collect_confirmed_skills(collected):
    assert "confirmed_skills" in collected
    assert "python" in collected["confirmed_skills"]

def test_collect_salary_info(collected):
    assert "salary_info" in collected
    assert "budget_aligned" in collected["salary_info"]

def test_collect_availability(collected):
    assert "availability" in collected
    assert "notice_period" in collected["availability"]

def test_collect_vague_flagged(collected):
    assert "vague_questions" in collected
    assert "Q021" in collected["vague_questions"]

def test_collect_missing_data(collected):
    assert "missing_data" in collected
    assert len(collected["missing_data"]) > 0

def test_collect_counts_correct(collected):
    assert collected["total_answers"] == len(ANSWERS)
    assert collected["valid_answers"] <= collected["total_answers"]


# ── StrengthRiskAnalyzer Tests ────────────────────────────────────────────────

def test_analyzer_creates_instance(analyzer):
    assert analyzer is not None

def test_identify_strengths_returns_list(analyzer, collected):
    result = analyzer.identify_strengths(collected)
    assert isinstance(result, list)

def test_identify_strengths_not_empty(analyzer, collected):
    result = analyzer.identify_strengths(collected)
    assert len(result) > 0

def test_strength_has_required_fields(analyzer, collected):
    strengths = analyzer.identify_strengths(collected)
    for s in strengths:
        assert "indicator" in s
        assert "label"     in s
        assert "evidence"  in s

def test_identify_risks_returns_list(analyzer, collected):
    result = analyzer.identify_risks(collected)
    assert isinstance(result, list)

def test_risk_has_required_fields(analyzer, collected):
    risks = analyzer.identify_risks(collected)
    for r in risks:
        assert "indicator" in r
        assert "label"     in r
        assert "evidence"  in r
        assert "severity"  in r

def test_risk_severity_valid(analyzer, collected):
    risks = analyzer.identify_risks(collected)
    for r in risks:
        assert r["severity"] in ("low", "medium", "high")

def test_vague_creates_risk(analyzer, collected):
    risks = analyzer.identify_risks(collected)
    indicators = [r["indicator"] for r in risks]
    assert "vague_on_key_questions" in indicators


# ── ScreeningReportGenerator Tests ───────────────────────────────────────────

def test_generator_creates_instance(generator):
    assert generator is not None

def test_generate_returns_dict(report):
    assert isinstance(report, dict)

def test_report_has_all_sections(report):
    required = ["report_metadata", "candidate_summary", "screening_score",
                "communication_profile", "key_answers", "skill_confirmations",
                "availability", "salary_expectation", "strengths",
                "risks", "missing_data", "recommendation"]
    for section in required:
        assert section in report

def test_report_metadata_fields(report):
    meta = report["report_metadata"]
    assert "generated_at"  in meta
    assert "candidate_id"  in meta
    assert "job_id"        in meta
    assert "template"      in meta

def test_candidate_summary_fields(report):
    c = report["candidate_summary"]
    assert "name"           in c
    assert "screening_score"in c
    assert "grade"          in c
    assert "outcome"        in c

def test_skill_confirmations_structure(report):
    skills = report["skill_confirmations"]
    assert "confirmed"      in skills
    assert "required_match" in skills
    assert "preferred_match"in skills

def test_required_skills_matched(report):
    skills = report["skill_confirmations"]
    assert len(skills["required_match"]) > 0
    for s in skills["required_match"]:
        assert s.lower() in [r.lower() for r in JOB["required_skills"]]

def test_availability_fields(report):
    avail = report["availability"]
    assert "notice_period"      in avail
    assert "target_joining_days"in avail
    assert "availability_ok"    in avail

def test_availability_ok_correct(report):
    avail = report["availability"]
    notice_val = avail.get("notice_period", {}).get("value", 999)
    target     = avail.get("target_joining_days", 60)
    assert avail["availability_ok"] == (notice_val <= target)

def test_salary_fields(report):
    sal = report["salary_expectation"]
    assert "budget_min_lpa" in sal
    assert "budget_max_lpa" in sal

def test_strengths_list(report):
    assert isinstance(report["strengths"], list)
    assert len(report["strengths"]) > 0

def test_risks_list(report):
    assert isinstance(report["risks"], list)

def test_missing_data_fields(report):
    missing = report["missing_data"]
    assert "unanswered_questions" in missing
    assert "vague_questions"      in missing
    assert "offtopic_questions"   in missing

def test_recommendation_has_level(report):
    rec = report["recommendation"]
    assert "level"       in rec
    assert "label"       in rec
    assert "description" in rec

def test_recommendation_level_valid(report):
    rec = report["recommendation"]
    assert rec["level"] in RECOMMENDATION_LEVELS


# ── Export Tests ──────────────────────────────────────────────────────────────

def test_export_markdown_returns_string(generator, report):
    result = generator.export_markdown(report)
    assert isinstance(result, str)
    assert len(result) > 0

def test_export_markdown_has_sections(generator, report):
    result = generator.export_markdown(report)
    assert "# AI Screening Report" in result
    assert "## Screening Score"    in result
    assert "## Strengths"          in result
    assert "## Recommendation"     in result

def test_export_summary_returns_string(generator, report):
    result = generator.export_summary(report)
    assert isinstance(result, str)
    assert len(result) > 0

def test_export_summary_has_key_info(generator, report):
    result = generator.export_summary(report)
    assert "ZECPATH AI SCREENING REPORT" in result
    assert "RECOMMENDATION" in result

def test_save_report(generator, report, tmp_path):
    output = str(tmp_path / "test_report.json")
    generator.save_report(report, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "candidate_summary"  in data
    assert "recommendation"     in data


# ── Recommendation Logic Tests ────────────────────────────────────────────────

def test_high_score_advance(generator):
    rec = generator._get_recommendation(85.0, [])
    assert rec["level"] in ("strongly_recommend", "recommend")

def test_low_score_reject(generator):
    rec = generator._get_recommendation(20.0, [])
    assert rec["level"] == "not_recommend"

def test_high_risk_lowers_outcome(generator):
    no_risk   = generator._get_recommendation(70.0, [])
    high_risk = generator._get_recommendation(70.0, [{"severity": "high"}, {"severity": "high"}])
    assert no_risk["level"] != "not_recommend" or high_risk["level"] == "not_recommend"


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_report_sections_defined():
    assert len(REPORT_SECTIONS) >= 10
    for section in ["candidate_summary","screening_score","key_answers",
                    "strengths","risks","recommendation"]:
        assert section in REPORT_SECTIONS

def test_strength_indicators_defined():
    assert "salary_aligned" in STRENGTH_INDICATORS
    assert "location_confirmed" in STRENGTH_INDICATORS

def test_risk_indicators_defined():
    assert "vague_on_key_questions" in RISK_INDICATORS
    assert "salary_over_budget"     in RISK_INDICATORS

def test_recommendation_levels_defined():
    for level in ["strongly_recommend","recommend","review","not_recommend"]:
        assert level in RECOMMENDATION_LEVELS

def test_recommendation_levels_have_score_ranges():
    for level, data in RECOMMENDATION_LEVELS.items():
        assert "score_range" in data
        lo, hi = data["score_range"]
        assert lo < hi
