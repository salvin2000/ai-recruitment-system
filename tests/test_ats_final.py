"""
Tests for Day 20 – ATS Final Review & Production Readiness
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_final import (
    ATSFinalEvaluator,
    PRODUCTION_CHECKLIST, FINAL_METRICS,
    DEMO_CANDIDATES, DEMO_JOB,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def evaluator():
    return ATSFinalEvaluator()

@pytest.fixture
def checklist_result(evaluator):
    return evaluator.run_checklist()

@pytest.fixture
def demo_result(evaluator):
    return evaluator.run_demo()

@pytest.fixture
def final_report(evaluator):
    return evaluator.generate_final_report()


# ── Evaluator Instance Tests ──────────────────────────────────────────────────

def test_evaluator_creates_instance(evaluator):
    assert evaluator is not None
    assert evaluator.checklist  is not None
    assert evaluator.metrics    is not None
    assert evaluator.candidates is not None

def test_evaluator_has_candidates(evaluator):
    assert len(evaluator.candidates) > 0

def test_evaluator_has_job(evaluator):
    assert evaluator.job is not None
    assert "role_name" in evaluator.job


# ── Production Checklist Tests ────────────────────────────────────────────────

def test_checklist_returns_dict(checklist_result):
    assert isinstance(checklist_result, dict)

def test_checklist_has_required_fields(checklist_result):
    assert "total_checks"     in checklist_result
    assert "passed_checks"    in checklist_result
    assert "failed_checks"    in checklist_result
    assert "pass_rate"        in checklist_result
    assert "production_ready" in checklist_result
    assert "categories"       in checklist_result

def test_checklist_has_all_categories(checklist_result):
    expected = ["pipeline_completeness", "code_quality", "testing",
                "fairness", "api_readiness", "documentation"]
    for cat in expected:
        assert cat in checklist_result["categories"]

def test_checklist_counts_correct(checklist_result):
    total    = checklist_result["total_checks"]
    passed   = checklist_result["passed_checks"]
    failed   = checklist_result["failed_checks"]
    assert passed + failed == total

def test_checklist_pass_rate_range(checklist_result):
    assert 0.0 <= checklist_result["pass_rate"] <= 1.0

def test_checklist_all_pass(checklist_result):
    assert checklist_result["production_ready"] == True
    assert checklist_result["failed_checks"]    == 0

def test_each_category_has_fields(checklist_result):
    for cat_name, cat_data in checklist_result["categories"].items():
        assert "label"    in cat_data
        assert "passed"   in cat_data
        assert "total"    in cat_data
        assert "all_pass" in cat_data
        assert "checks"   in cat_data

def test_pipeline_completeness_has_18_days(checklist_result):
    cat = checklist_result["categories"]["pipeline_completeness"]
    assert cat["total"] == 17  # 17 days checked (Day 20 is today)
    assert cat["passed"] == 17

def test_all_checks_pass(checklist_result):
    for cat_name, cat_data in checklist_result["categories"].items():
        assert cat_data["all_pass"] == True


# ── Demo Run Tests ────────────────────────────────────────────────────────────

def test_demo_returns_dict(demo_result):
    assert isinstance(demo_result, dict)

def test_demo_has_required_fields(demo_result):
    assert "demo_metadata"    in demo_result
    assert "job_requirements" in demo_result
    assert "ranked_results"   in demo_result
    assert "summary"          in demo_result
    assert "shortlisted"      in demo_result
    assert "review"           in demo_result
    assert "rejected"         in demo_result

def test_demo_metadata_fields(demo_result):
    meta = demo_result["demo_metadata"]
    assert "run_at"            in meta
    assert "job_id"            in meta
    assert "total_candidates"  in meta

def test_demo_ranked_results_sorted(demo_result):
    scores = [c["ats_score"] for c in demo_result["ranked_results"]]
    assert scores == sorted(scores, reverse=True)

def test_demo_zones_cover_all_candidates(demo_result):
    total = demo_result["demo_metadata"]["total_candidates"]
    zoned = (len(demo_result["shortlisted"]) +
             len(demo_result["review"]) +
             len(demo_result["rejected"]))
    assert total == zoned

def test_demo_summary_has_fields(demo_result):
    summary = demo_result["summary"]
    assert "shortlisted_count" in summary
    assert "review_count"      in summary
    assert "rejected_count"    in summary
    assert "avg_score"         in summary
    assert "top_score"         in summary
    assert "shortlist_rate"    in summary

def test_demo_top_score_is_highest(demo_result):
    scores    = [c["ats_score"] for c in demo_result["ranked_results"]]
    top_score = demo_result["summary"]["top_score"]
    assert top_score == max(scores)

def test_demo_shortlisted_have_correct_zone(demo_result):
    for c in demo_result["shortlisted"]:
        assert c["zone"] == "shortlisted"

def test_demo_rejected_have_correct_zone(demo_result):
    for c in demo_result["rejected"]:
        assert c["zone"] == "rejected"


# ── Final Report Tests ────────────────────────────────────────────────────────

def test_final_report_returns_dict(final_report):
    assert isinstance(final_report, dict)

def test_final_report_has_required_sections(final_report):
    assert "report_metadata"     in final_report
    assert "production_readiness"in final_report
    assert "final_metrics"       in final_report
    assert "demo_results"        in final_report
    assert "pipeline_summary"    in final_report
    assert "verdict"             in final_report

def test_report_metadata_fields(final_report):
    meta = final_report["report_metadata"]
    assert "generated_at"   in meta
    assert "project"        in meta
    assert "developer"      in meta
    assert "report_version" in meta

def test_pipeline_summary_fields(final_report):
    summary = final_report["pipeline_summary"]
    assert "total_days"    in summary
    assert "total_modules" in summary
    assert "total_tests"   in summary
    assert "all_tests_pass"in summary
    assert "accuracy"      in summary

def test_all_tests_pass_flag(final_report):
    assert final_report["pipeline_summary"]["all_tests_pass"] == True

def test_verdict_production_ready(final_report):
    assert final_report["verdict"]["production_ready"] == True
    assert "APPROVED" in final_report["verdict"]["recommendation"]

def test_report_accuracy_correct(final_report):
    acc = final_report["pipeline_summary"]["accuracy"]
    assert acc == FINAL_METRICS["accuracy_metrics"]["accuracy"]


# ── Management Summary Tests ──────────────────────────────────────────────────

def test_management_summary_returns_string(evaluator, final_report):
    summary = evaluator.generate_management_summary(final_report)
    assert isinstance(summary, str)

def test_management_summary_has_key_sections(evaluator, final_report):
    summary = evaluator.generate_management_summary(final_report)
    assert "PRODUCTION READINESS" in summary
    assert "PIPELINE SUMMARY"     in summary
    assert "ACCURACY METRICS"     in summary
    assert "LIVE DEMO RESULTS"    in summary
    assert "VERDICT"              in summary

def test_management_summary_shows_production_ready(evaluator, final_report):
    summary = evaluator.generate_management_summary(final_report)
    assert "PRODUCTION READY" in summary

def test_management_summary_shows_approved(evaluator, final_report):
    summary = evaluator.generate_management_summary(final_report)
    assert "APPROVED" in summary


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_production_checklist_has_categories():
    assert len(PRODUCTION_CHECKLIST) == 6

def test_final_metrics_has_required_fields():
    required = ["total_days", "total_modules", "total_tests",
                "accuracy_metrics", "performance_metrics"]
    for field in required:
        assert field in FINAL_METRICS

def test_final_metrics_total_tests():
    assert FINAL_METRICS["total_tests"] >= 500

def test_final_metrics_accuracy_pass():
    acc = FINAL_METRICS["accuracy_metrics"]
    assert acc["precision"]  >= 0.80
    assert acc["recall"]     >= 0.75
    assert acc["f1_score"]   >= 0.77
    assert acc["accuracy"]   >= 0.80

def test_demo_candidates_have_required_fields():
    required = ["candidate_id", "name", "ats_score", "grade", "zone", "decision"]
    for c in DEMO_CANDIDATES:
        for field in required:
            assert field in c

def test_demo_candidates_valid_zones():
    valid = {"shortlisted", "review", "rejected"}
    for c in DEMO_CANDIDATES:
        assert c["zone"] in valid

def test_demo_job_has_required_fields():
    required = ["job_id", "role_name", "required_skills",
                "min_experience_years", "role_type"]
    for field in required:
        assert field in DEMO_JOB


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_report(evaluator, final_report, tmp_path):
    output_file = str(tmp_path / "test_final.json")
    evaluator.save_report(final_report, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "production_readiness" in data
    assert "verdict"              in data
    assert "final_metrics"        in data
