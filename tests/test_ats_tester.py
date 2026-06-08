"""
Tests for Day 17 – ATS System Testing
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_tester import (
    ATSTester, TEST_CASES, ACCURACY_THRESHOLDS,
    PROFILE_CATEGORIES, MANUAL_REVIEW_DECISIONS,
)


# ── Sample Test Cases ─────────────────────────────────────────────────────────

PERFECT_MATCH_CASES = [
    {"test_id": "T1", "profile_category": "tech_senior",
     "candidate_id": "C1", "ats_score": 80.0,
     "ats_decision": "shortlisted", "manual_decision": "shortlisted",
     "role_type": "software_engineer", "notes": ""},
    {"test_id": "T2", "profile_category": "tech_mid",
     "candidate_id": "C2", "ats_score": 55.0,
     "ats_decision": "review", "manual_decision": "review",
     "role_type": "software_engineer", "notes": ""},
    {"test_id": "T3", "profile_category": "tech_fresher",
     "candidate_id": "C3", "ats_score": 30.0,
     "ats_decision": "rejected", "manual_decision": "rejected",
     "role_type": "software_engineer", "notes": ""},
    {"test_id": "T4", "profile_category": "non_tech_senior",
     "candidate_id": "C4", "ats_score": 75.0,
     "ats_decision": "shortlisted", "manual_decision": "shortlisted",
     "role_type": "hr_manager", "notes": ""},
]

MISMATCH_CASES = [
    {"test_id": "M1", "profile_category": "tech_fresher",
     "candidate_id": "C5", "ats_score": 45.0,
     "ats_decision": "review", "manual_decision": "shortlisted",
     "role_type": "software_engineer", "notes": "Mismatch — AI too conservative"},
    {"test_id": "M2", "profile_category": "non_tech_mid",
     "candidate_id": "C6", "ats_score": 40.0,
     "ats_decision": "rejected", "manual_decision": "review",
     "role_type": "data_analyst", "notes": "Mismatch — AI too strict"},
]

MIXED_CASES = PERFECT_MATCH_CASES + MISMATCH_CASES

ALL_SHORTLIST = [
    {"test_id": f"S{i}", "profile_category": "tech_senior",
     "candidate_id": f"CS{i}", "ats_score": 80.0,
     "ats_decision": "shortlisted", "manual_decision": "shortlisted",
     "role_type": "software_engineer", "notes": ""}
    for i in range(4)
]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tester():
    return ATSTester()

@pytest.fixture
def perfect_report(tester):
    return tester.run_tests(PERFECT_MATCH_CASES)

@pytest.fixture
def mixed_report(tester):
    return tester.run_tests(MIXED_CASES)

@pytest.fixture
def full_report(tester):
    return tester.run_tests()


# ── ATSTester Instance Tests ──────────────────────────────────────────────────

def test_tester_creates_instance(tester):
    assert tester is not None
    assert tester.thresholds is not None

def test_tester_has_test_cases(tester):
    assert len(tester.test_cases) > 0

def test_tester_uses_default_thresholds(tester):
    assert tester.thresholds == ACCURACY_THRESHOLDS

def test_tester_accepts_custom_thresholds():
    custom = {"precision_target": 0.90, "recall_target": 0.85,
              "f1_target": 0.87, "accuracy_target": 0.90,
              "mismatch_tolerance": 0.10}
    t = ATSTester(thresholds=custom)
    assert t.thresholds == custom


# ── Confusion Matrix Tests ────────────────────────────────────────────────────

def test_confusion_matrix_returns_dict(tester):
    cm = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    assert isinstance(cm, dict)

def test_confusion_matrix_has_required_fields(tester):
    cm = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    assert "true_positive"  in cm
    assert "false_positive" in cm
    assert "false_negative" in cm
    assert "true_negative"  in cm
    assert "mismatches"     in cm
    assert "total"          in cm

def test_confusion_matrix_perfect_match(tester):
    cm = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    assert cm["total"]          == len(PERFECT_MATCH_CASES)
    assert len(cm["mismatches"])== 0

def test_confusion_matrix_counts_mismatches(tester):
    cm = tester.build_confusion_matrix(MISMATCH_CASES)
    assert len(cm["mismatches"]) == len(MISMATCH_CASES)

def test_confusion_matrix_tp_fn_sum(tester):
    cm = tester.build_confusion_matrix(MIXED_CASES)
    assert cm["total"] == (cm["true_positive"] + cm["false_positive"] +
                           cm["false_negative"] + cm["true_negative"])

def test_mismatch_has_required_fields(tester):
    cm = tester.build_confusion_matrix(MISMATCH_CASES)
    for m in cm["mismatches"]:
        assert "test_id"         in m
        assert "ai_decision"     in m
        assert "manual_decision" in m
        assert "ats_score"       in m


# ── Accuracy Metrics Tests ────────────────────────────────────────────────────

def test_compute_metrics_returns_dict(tester):
    cm  = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    met = tester.compute_metrics(cm)
    assert isinstance(met, dict)

def test_compute_metrics_has_required_fields(tester):
    cm  = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    met = tester.compute_metrics(cm)
    assert "precision"       in met
    assert "recall"          in met
    assert "f1_score"        in met
    assert "accuracy"        in met
    assert "mismatch_rate"   in met
    assert "total_mismatches"in met

def test_precision_range(tester):
    cm  = tester.build_confusion_matrix(MIXED_CASES)
    met = tester.compute_metrics(cm)
    assert 0.0 <= met["precision"] <= 1.0

def test_recall_range(tester):
    cm  = tester.build_confusion_matrix(MIXED_CASES)
    met = tester.compute_metrics(cm)
    assert 0.0 <= met["recall"] <= 1.0

def test_f1_range(tester):
    cm  = tester.build_confusion_matrix(MIXED_CASES)
    met = tester.compute_metrics(cm)
    assert 0.0 <= met["f1_score"] <= 1.0

def test_accuracy_range(tester):
    cm  = tester.build_confusion_matrix(MIXED_CASES)
    met = tester.compute_metrics(cm)
    assert 0.0 <= met["accuracy"] <= 1.0

def test_perfect_match_zero_mismatches(tester):
    cm  = tester.build_confusion_matrix(PERFECT_MATCH_CASES)
    met = tester.compute_metrics(cm)
    assert met["total_mismatches"] == 0
    assert met["mismatch_rate"]    == 0.0

def test_all_mismatch_nonzero_rate(tester):
    cm  = tester.build_confusion_matrix(MISMATCH_CASES)
    met = tester.compute_metrics(cm)
    assert met["mismatch_rate"] > 0.0


# ── Category Analysis Tests ───────────────────────────────────────────────────

def test_analyze_by_category_returns_dict(tester):
    result = tester.analyze_by_category(MIXED_CASES)
    assert isinstance(result, dict)

def test_category_analysis_has_fields(tester):
    result = tester.analyze_by_category(MIXED_CASES)
    for cat, data in result.items():
        assert "total"        in data
        assert "correct"      in data
        assert "accuracy"     in data
        assert "meets_target" in data

def test_category_accuracy_range(tester):
    result = tester.analyze_by_category(MIXED_CASES)
    for cat, data in result.items():
        assert 0.0 <= data["accuracy"] <= 1.0

def test_full_test_cases_have_all_categories(full_report):
    cats = set(full_report["category_analysis"].keys())
    expected = {"tech_senior", "tech_mid", "tech_fresher",
                "non_tech_senior", "non_tech_mid", "non_tech_fresher"}
    assert cats == expected


# ── Role Analysis Tests ───────────────────────────────────────────────────────

def test_analyze_by_role_returns_dict(tester):
    result = tester.analyze_by_role(MIXED_CASES)
    assert isinstance(result, dict)

def test_role_analysis_has_fields(tester):
    result = tester.analyze_by_role(MIXED_CASES)
    for role, data in result.items():
        assert "total"     in data
        assert "correct"   in data
        assert "accuracy"  in data
        assert "avg_score" in data

def test_role_avg_score_reasonable(tester):
    result = tester.analyze_by_role(MIXED_CASES)
    for role, data in result.items():
        assert 0 <= data["avg_score"] <= 100


# ── Improvement Backlog Tests ─────────────────────────────────────────────────

def test_backlog_returns_list(tester):
    cm      = tester.build_confusion_matrix(MIXED_CASES)
    metrics = tester.compute_metrics(cm)
    cats    = tester.analyze_by_category(MIXED_CASES)
    backlog = tester.generate_improvement_backlog(metrics, cm["mismatches"], cats)
    assert isinstance(backlog, list)

def test_backlog_has_required_fields(tester):
    cm      = tester.build_confusion_matrix(MIXED_CASES)
    metrics = tester.compute_metrics(cm)
    cats    = tester.analyze_by_category(MIXED_CASES)
    backlog = tester.generate_improvement_backlog(metrics, cm["mismatches"], cats)
    for item in backlog:
        assert "priority"    in item
        assert "area"        in item
        assert "issue"       in item
        assert "improvement" in item

def test_backlog_priorities_valid(tester):
    cm      = tester.build_confusion_matrix(MIXED_CASES)
    metrics = tester.compute_metrics(cm)
    cats    = tester.analyze_by_category(MIXED_CASES)
    backlog = tester.generate_improvement_backlog(metrics, cm["mismatches"], cats)
    for item in backlog:
        assert item["priority"] in ["High", "Medium", "Low"]

def test_backlog_sorted_by_priority(tester):
    cm      = tester.build_confusion_matrix(MIXED_CASES)
    metrics = tester.compute_metrics(cm)
    cats    = tester.analyze_by_category(MIXED_CASES)
    backlog = tester.generate_improvement_backlog(metrics, cm["mismatches"], cats)
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    priorities = [priority_order[item["priority"]] for item in backlog]
    assert priorities == sorted(priorities)


# ── Full Test Run Tests ───────────────────────────────────────────────────────

def test_run_tests_returns_dict(perfect_report):
    assert isinstance(perfect_report, dict)

def test_run_tests_has_required_sections(perfect_report):
    assert "report_metadata"    in perfect_report
    assert "confusion_matrix"   in perfect_report
    assert "accuracy_metrics"   in perfect_report
    assert "meets_targets"      in perfect_report
    assert "overall_pass"       in perfect_report
    assert "category_analysis"  in perfect_report
    assert "role_analysis"      in perfect_report
    assert "improvement_backlog"in perfect_report

def test_report_metadata_fields(perfect_report):
    meta = perfect_report["report_metadata"]
    assert "generated_at"     in meta
    assert "tester_version"   in meta
    assert "total_test_cases" in meta

def test_meets_targets_has_all_metrics(perfect_report):
    targets = perfect_report["meets_targets"]
    assert "precision"     in targets
    assert "recall"        in targets
    assert "f1_score"      in targets
    assert "accuracy"      in targets
    assert "mismatch_rate" in targets

def test_overall_pass_is_bool(perfect_report):
    assert isinstance(perfect_report["overall_pass"], bool)

def test_full_test_cases_run(full_report):
    assert full_report["report_metadata"]["total_test_cases"] == len(TEST_CASES)


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_profile_categories_defined():
    required = ["tech_senior", "tech_mid", "tech_fresher",
                "non_tech_senior", "non_tech_mid", "non_tech_fresher"]
    for cat in required:
        assert cat in PROFILE_CATEGORIES

def test_accuracy_thresholds_defined():
    required = ["precision_target", "recall_target", "f1_target",
                "accuracy_target", "mismatch_tolerance"]
    for t in required:
        assert t in ACCURACY_THRESHOLDS

def test_thresholds_in_valid_range():
    for key, val in ACCURACY_THRESHOLDS.items():
        assert 0.0 <= val <= 1.0

def test_test_cases_have_required_fields():
    required = ["test_id", "profile_category", "candidate_id",
                "ats_score", "ats_decision", "manual_decision",
                "role_type"]
    for tc in TEST_CASES:
        for field in required:
            assert field in tc

def test_test_cases_decisions_valid():
    valid = {"shortlisted", "review", "rejected"}
    for tc in TEST_CASES:
        assert tc["ats_decision"]    in valid
        assert tc["manual_decision"] in valid


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_report(tester, perfect_report, tmp_path):
    output_file = str(tmp_path / "test_report.json")
    tester.save_report(perfect_report, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "accuracy_metrics"    in data
    assert "improvement_backlog" in data
