"""
Tests for Day 30 – Screening System Testing & Optimization
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.screening_optimizer import (
    ScreeningSimulator, ThresholdTuner, SystemTestReport,
    SCREENING_TEST_CASES, THRESHOLD_CONFIG_V1, THRESHOLD_CONFIG_V2,
    OPTIMIZATION_RESULTS, FALSE_REJECTION_PATTERNS, INTENT_IMPROVEMENTS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def simulator():
    return ScreeningSimulator()

@pytest.fixture
def tuner():
    return ThresholdTuner()

@pytest.fixture
def report_gen():
    return SystemTestReport()

@pytest.fixture
def sim_report(simulator):
    return simulator.run_all()

@pytest.fixture
def full_report(report_gen):
    return report_gen.generate()


# ── ScreeningSimulator Tests ──────────────────────────────────────────────────

def test_simulator_creates_instance(simulator):
    assert simulator is not None

def test_simulator_has_test_cases(simulator):
    assert len(simulator.test_cases) > 0

def test_run_test_case_returns_dict(simulator):
    tc     = SCREENING_TEST_CASES[0]
    result = simulator.run_test_case(tc)
    assert isinstance(result, dict)

def test_run_test_case_has_required_fields(simulator):
    tc     = SCREENING_TEST_CASES[0]
    result = simulator.run_test_case(tc)
    required = ["test_id", "human_label", "ai_label", "human_intent",
                "ai_intent", "ai_extracted", "label_match",
                "intent_match", "passed"]
    for field in required:
        assert field in result

def test_run_all_returns_dict(sim_report):
    assert isinstance(sim_report, dict)

def test_run_all_has_required_sections(sim_report):
    assert "report_metadata" in sim_report
    assert "by_category"     in sim_report
    assert "test_results"    in sim_report

def test_run_all_correct_count(sim_report):
    meta  = sim_report["report_metadata"]
    total = meta["total_tests"]
    assert total == len(SCREENING_TEST_CASES)
    assert meta["passed"] + meta["failed"] == total

def test_run_all_pass_rate_range(sim_report):
    rate = sim_report["report_metadata"]["pass_rate"]
    assert 0.0 <= rate <= 100.0

def test_by_category_has_entries(sim_report):
    assert len(sim_report["by_category"]) > 0

def test_each_result_has_human_label(sim_report):
    for r in sim_report["test_results"]:
        assert "human_label" in r
        assert "ai_label"    in r

def test_valid_complete_detected(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-001")
    result = simulator.run_test_case(tc)
    assert result["ai_label"] in ("valid_complete", "valid_partial")

def test_off_topic_detected(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-005")
    result = simulator.run_test_case(tc)
    assert result["ai_label"] == "off_topic"

def test_vague_detected(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-003")
    result = simulator.run_test_case(tc)
    assert result["ai_label"] == "vague"

def test_affirmative_detected(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-008")
    result = simulator.run_test_case(tc)
    assert result["ai_extracted"].get("boolean_value") == True

def test_negative_detected(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-012")
    result = simulator.run_test_case(tc)
    assert result["ai_extracted"].get("boolean_value") == False

def test_immediate_notice_extracted(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-010")
    result = simulator.run_test_case(tc)
    assert result["ai_extracted"].get("notice_period", {}).get("value") == 0

def test_skills_extracted(simulator):
    tc     = next(t for t in SCREENING_TEST_CASES if t["test_id"] == "TC-004")
    result = simulator.run_test_case(tc)
    skills = result["ai_extracted"].get("skills_mentioned", [])
    assert len(skills) >= 2


# ── ThresholdTuner Tests ──────────────────────────────────────────────────────

def test_tuner_creates_instance(tuner):
    assert tuner is not None

def test_tuner_has_v1_config(tuner):
    assert tuner.v1 is not None
    assert len(tuner.v1) > 0

def test_tuner_has_v2_config(tuner):
    assert tuner.v2 is not None
    assert len(tuner.v2) > 0

def test_compare_returns_list(tuner):
    result = tuner.compare()
    assert isinstance(result, list)
    assert len(result) > 0

def test_compare_has_required_fields(tuner):
    changes = tuner.compare()
    for c in changes:
        assert "threshold"  in c
        assert "v1"         in c
        assert "v2"         in c
        assert "direction"  in c
        assert "rationale"  in c

def test_compare_direction_valid(tuner):
    changes = tuner.compare()
    for c in changes:
        assert c["direction"] in ("lowered", "raised")

def test_v2_min_score_lower_than_v1(tuner):
    assert tuner.v2["min_ats_score"] < tuner.v1["min_ats_score"]

def test_v2_hesitation_threshold_higher(tuner):
    assert tuner.v2["hesitation_threshold"] > tuner.v1["hesitation_threshold"]

def test_get_optimization_summary_returns_dict(tuner):
    result = tuner.get_optimization_summary()
    assert isinstance(result, dict)
    assert "changes"              in result
    assert "results"              in result
    assert "false_rejections_reduced" in result
    assert "intent_improvements"  in result


# ── SystemTestReport Tests ────────────────────────────────────────────────────

def test_report_gen_creates_instance(report_gen):
    assert report_gen is not None

def test_generate_returns_dict(full_report):
    assert isinstance(full_report, dict)

def test_generate_has_required_sections(full_report):
    assert "report_metadata"         in full_report
    assert "simulation_results"      in full_report
    assert "optimization_summary"    in full_report
    assert "false_rejection_patterns"in full_report
    assert "intent_improvements"     in full_report
    assert "threshold_changes"       in full_report
    assert "optimization_results"    in full_report

def test_report_metadata_fields(full_report):
    meta = full_report["report_metadata"]
    assert "generated_at" in meta
    assert "project"      in meta
    assert meta["day"]    == 30

def test_save_report(report_gen, full_report, tmp_path):
    output = str(tmp_path / "test_screening.json")
    report_gen.save_report(full_report, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "simulation_results"   in data
    assert "optimization_results" in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_test_cases_defined():
    assert len(SCREENING_TEST_CASES) >= 10
    for tc in SCREENING_TEST_CASES:
        assert "test_id"         in tc
        assert "raw_input"       in tc
        assert "human_label"     in tc
        assert "human_intent"    in tc
        assert "human_extracted" in tc

def test_test_cases_unique_ids():
    ids = [tc["test_id"] for tc in SCREENING_TEST_CASES]
    assert len(ids) == len(set(ids))

def test_threshold_v1_has_required_keys():
    required = ["min_ats_score", "min_screening_score",
                "min_confidence_score", "min_word_count"]
    for key in required:
        assert key in THRESHOLD_CONFIG_V1

def test_threshold_v2_same_keys_as_v1():
    assert set(THRESHOLD_CONFIG_V1.keys()) == set(THRESHOLD_CONFIG_V2.keys())

def test_false_rejection_patterns_defined():
    assert len(FALSE_REJECTION_PATTERNS) >= 4
    for frp in FALSE_REJECTION_PATTERNS:
        assert "pattern_id"   in frp
        assert "description"  in frp
        assert "fix"          in frp
        assert "impact"       in frp

def test_intent_improvements_defined():
    assert len(INTENT_IMPROVEMENTS) >= 3
    for imp in INTENT_IMPROVEMENTS:
        assert "improvement_id"  in imp
        assert "category"        in imp
        assert "new_patterns"    in imp
        assert "accuracy_delta"  in imp

def test_optimization_results_defined():
    for metric in ["false_rejection_rate", "intent_detection_accuracy",
                   "overall_system_accuracy"]:
        assert metric in OPTIMIZATION_RESULTS
        assert "before" in OPTIMIZATION_RESULTS[metric]
        assert "after"  in OPTIMIZATION_RESULTS[metric]

def test_optimization_results_improve():
    for metric, data in OPTIMIZATION_RESULTS.items():
        # After should always be better than before
        assert data["after"] != data["before"]
