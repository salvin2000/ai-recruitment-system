"""
Tests for Day 32 - Screening System Finalization
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.screening_finalization import (
    ProductionChecklistRunner, EndToEndDemoRunner, FinalEvaluationReport,
    PIPELINE_DAYS, PRODUCTION_CHECKLIST, DEMO_CANDIDATE, DEMO_QUESTIONS,
    API_ENDPOINTS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def checklist_runner():
    return ProductionChecklistRunner()

@pytest.fixture
def demo_runner():
    return EndToEndDemoRunner()

@pytest.fixture
def report_gen():
    return FinalEvaluationReport()


# ── ProductionChecklistRunner Tests ──────────────────────────────────────────

def test_checklist_runner_creates_instance(checklist_runner):
    assert checklist_runner is not None

def test_run_returns_dict(checklist_runner):
    result = checklist_runner.run()
    assert isinstance(result, dict)

def test_run_has_required_fields(checklist_runner):
    result = checklist_runner.run()
    for field in ["categories", "total_checks", "passed_checks", "pass_rate", "verdict"]:
        assert field in result

def test_all_categories_present(checklist_runner):
    result = checklist_runner.run()
    for key in PRODUCTION_CHECKLIST:
        assert key in result["categories"]

def test_verdict_is_production_ready(checklist_runner):
    result = checklist_runner.run()
    assert result["verdict"] == "PRODUCTION READY"

def test_pass_rate_is_100_percent(checklist_runner):
    result = checklist_runner.run()
    assert result["pass_rate"] == 1.0

def test_total_checks_matches_passed_checks(checklist_runner):
    result = checklist_runner.run()
    assert result["total_checks"] == result["passed_checks"]

def test_get_total_test_count_matches_sum(checklist_runner):
    expected = sum(info["tests"] for info in PIPELINE_DAYS.values())
    assert checklist_runner.get_total_test_count() == expected

def test_get_total_test_count_is_561(checklist_runner):
    assert checklist_runner.get_total_test_count() == 561

def test_pipeline_completeness_has_11_days(checklist_runner):
    result = checklist_runner.run()
    assert result["categories"]["pipeline_completeness"]["total"] == 11


# ── EndToEndDemoRunner Tests ─────────────────────────────────────────────────

def test_demo_runner_creates_instance(demo_runner):
    assert demo_runner is not None

def test_run_returns_dict(demo_runner):
    result = demo_runner.run()
    assert isinstance(result, dict)

def test_run_has_required_fields(demo_runner):
    result = demo_runner.run()
    for field in ["candidate", "turns", "overall_score", "recommendation", "transcript", "generated_at"]:
        assert field in result

def test_run_has_one_turn_per_question(demo_runner):
    result = demo_runner.run()
    assert len(result["turns"]) == len(DEMO_QUESTIONS)

def test_each_turn_has_required_fields(demo_runner):
    result = demo_runner.run()
    for turn in result["turns"]:
        for field in ["question_id", "category", "question", "answer", "score"]:
            assert field in turn

def test_overall_score_in_valid_range(demo_runner):
    result = demo_runner.run()
    assert 0 <= result["overall_score"] <= 100

def test_recommendation_is_valid_category(demo_runner):
    result = demo_runner.run()
    assert result["recommendation"] in (
        "Strongly Recommend", "Recommend", "Review Required", "Not Recommended"
    )

def test_high_score_yields_strongly_recommend(demo_runner):
    assert demo_runner._recommend(90) == "Strongly Recommend"

def test_low_score_yields_not_recommended(demo_runner):
    assert demo_runner._recommend(20) == "Not Recommended"

def test_transcript_has_two_lines_per_turn(demo_runner):
    result = demo_runner.run()
    assert len(result["transcript"]) == len(result["turns"]) * 2

def test_custom_candidate_is_used():
    custom = {"name": "Priya Nair", "role_applied": "Data Analyst", "session_id": "SESS-CUSTOM"}
    runner = EndToEndDemoRunner(candidate=custom)
    result = runner.run()
    assert result["candidate"]["name"] == "Priya Nair"


# ── FinalEvaluationReport Tests ──────────────────────────────────────────────

def test_report_gen_creates_instance(report_gen):
    assert report_gen is not None

def test_generate_returns_dict(report_gen):
    result = report_gen.generate()
    assert isinstance(result, dict)

def test_generate_has_required_sections(report_gen):
    result = report_gen.generate()
    for field in ["report_metadata", "production_checklist", "end_to_end_demo", "api_endpoints", "final_verdict"]:
        assert field in result

def test_report_metadata_has_required_fields(report_gen):
    result = report_gen.generate()
    for field in ["title", "pipeline_days", "total_tests", "generated_at"]:
        assert field in result["report_metadata"]

def test_final_verdict_is_production_ready(report_gen):
    result = report_gen.generate()
    assert result["final_verdict"] == "PRODUCTION READY"

def test_get_management_summary_returns_string(report_gen):
    summary = report_gen.get_management_summary()
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_management_summary_contains_verdict(report_gen):
    summary = report_gen.get_management_summary()
    assert "PRODUCTION READY" in summary

def test_save_report(report_gen, tmp_path):
    output = str(tmp_path / "test_report.json")
    report_gen.save_report(output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "final_verdict" in data


# ── Constants Tests ──────────────────────────────────────────────────────────

def test_pipeline_days_covers_21_to_31():
    for day in range(21, 32):
        assert day in PIPELINE_DAYS

def test_pipeline_days_have_name_and_tests():
    for day, info in PIPELINE_DAYS.items():
        assert "name" in info
        assert "tests" in info
        assert info["tests"] > 0

def test_production_checklist_has_6_categories():
    assert len(PRODUCTION_CHECKLIST) == 6

def test_demo_candidate_has_required_fields():
    for field in ["name", "role_applied", "session_id"]:
        assert field in DEMO_CANDIDATE

def test_demo_questions_cover_6_categories():
    categories = {q["category"] for q in DEMO_QUESTIONS}
    assert len(categories) == 6

def test_api_endpoints_not_empty():
    assert len(API_ENDPOINTS) >= 5

def test_api_endpoints_have_descriptions():
    for endpoint, description in API_ENDPOINTS.items():
        assert isinstance(description, str)
        assert len(description) > 0
