"""
Tests for Day 21 – Eligibility Decision Engine
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.eligibility_engine import (
    EligibilityDecisionEngine, EligibilityRule,
    ELIGIBILITY_TAGS, DEFAULT_ELIGIBILITY_PARAMS,
    ROLE_ELIGIBILITY_CONFIGS, RULE_FAILURE_REASONS,
)


# ── Sample Candidates ─────────────────────────────────────────────────────────

ELIGIBLE_CANDIDATE = {
    "candidate_id":    "C001",
    "ats_score":        80.0,
    "skills":          ["python", "django", "aws"],
    "experience_years": 3.0,
    "location":        "bangalore",
    "notice_period_days": 30,
}

REVIEW_CANDIDATE = {
    "candidate_id":    "C002",
    "ats_score":        55.0,
    "skills":          ["python", "sql"],
    "experience_years": 2.0,
    "location":        "mumbai",
    "notice_period_days": 45,
}

REJECTED_CANDIDATE = {
    "candidate_id":    "C003",
    "ats_score":        30.0,
    "skills":          ["java", "spring"],
    "experience_years": 1.0,
    "location":        "pune",
    "notice_period_days": 30,
}

MISSING_SKILL_CANDIDATE = {
    "candidate_id":    "C004",
    "ats_score":        75.0,
    "skills":          ["java", "spring", "mysql"],
    "experience_years": 3.0,
    "location":        "bangalore",
    "notice_period_days": 30,
}

LOW_EXP_CANDIDATE = {
    "candidate_id":    "C005",
    "ats_score":        70.0,
    "skills":          ["python", "django"],
    "experience_years": 0.5,
    "location":        "bangalore",
    "notice_period_days": 0,
}

HIGH_EXP_CANDIDATE = {
    "candidate_id":    "C006",
    "ats_score":        72.0,
    "skills":          ["python", "django"],
    "experience_years": 15.0,
    "location":        "bangalore",
    "notice_period_days": 30,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return EligibilityDecisionEngine(role_type="software_engineer")

@pytest.fixture
def engine_with_location():
    params = {
        **ROLE_ELIGIBILITY_CONFIGS["software_engineer"],
        "location_required": True,
        "allowed_locations": ["bangalore", "mumbai"],
    }
    return EligibilityDecisionEngine(params=params)

@pytest.fixture
def engine_with_notice():
    params = {
        **ROLE_ELIGIBILITY_CONFIGS["software_engineer"],
        "availability_required": True,
        "max_notice_period_days": 30,
    }
    return EligibilityDecisionEngine(params=params)

@pytest.fixture
def eligible_result(engine):
    return engine.decide(ELIGIBLE_CANDIDATE)

@pytest.fixture
def rejected_result(engine):
    return engine.decide(REJECTED_CANDIDATE)


# ── Engine Instance Tests ─────────────────────────────────────────────────────

def test_engine_creates_instance(engine):
    assert engine is not None
    assert engine.params is not None

def test_engine_uses_role_config(engine):
    assert engine.params == ROLE_ELIGIBILITY_CONFIGS["software_engineer"]

def test_engine_falls_back_to_default():
    eng = EligibilityDecisionEngine(role_type="unknown_role_xyz")
    assert eng.params == DEFAULT_ELIGIBILITY_PARAMS

def test_engine_accepts_custom_params():
    custom = {**DEFAULT_ELIGIBILITY_PARAMS, "min_ats_score": 75.0}
    eng    = EligibilityDecisionEngine(params=custom)
    assert eng.params["min_ats_score"] == 75.0


# ── Score Check Tests ─────────────────────────────────────────────────────────

def test_score_check_eligible(engine):
    result = engine.check_ats_score(80.0)
    assert result["passed"] == True
    assert result["tag"]    == "eligible"

def test_score_check_review(engine):
    result = engine.check_ats_score(55.0)
    assert result["passed"] == False
    assert result["tag"]    == "review"

def test_score_check_rejected(engine):
    result = engine.check_ats_score(30.0)
    assert result["passed"] == False
    assert result["tag"]    == "rejected"

def test_score_check_at_boundary(engine):
    min_score = engine.params["min_ats_score"]
    result    = engine.check_ats_score(min_score)
    assert result["tag"] == "eligible"

def test_score_check_just_below_min(engine):
    min_score = engine.params["min_ats_score"]
    result    = engine.check_ats_score(min_score - 0.1)
    assert result["tag"] in ["review", "rejected"]


# ── Mandatory Skills Tests ────────────────────────────────────────────────────

def test_skills_check_all_present(engine):
    result = engine.check_mandatory_skills(["python", "django", "aws"])
    assert result["passed"] == True

def test_skills_check_missing(engine):
    result = engine.check_mandatory_skills(["java", "spring"])
    assert result["passed"] == False
    assert result["tag"]    == "rejected"
    assert "python"         in result["missing"]

def test_skills_check_no_mandatory(engine):
    eng = EligibilityDecisionEngine(params={
        **DEFAULT_ELIGIBILITY_PARAMS, "mandatory_skills": []
    })
    result = eng.check_mandatory_skills(["anything"])
    assert result["passed"] == True

def test_skills_check_partial_match():
    params = {
        **DEFAULT_ELIGIBILITY_PARAMS,
        "mandatory_skills":  ["python", "ml", "sql"],
        "min_mandatory_match": 0.66,
    }
    eng    = EligibilityDecisionEngine(params=params)
    result = eng.check_mandatory_skills(["python", "ml"])
    assert result["passed"] == True

def test_skills_check_case_insensitive(engine):
    result = engine.check_mandatory_skills(["Python", "DJANGO"])
    assert result["passed"] == True


# ── Experience Check Tests ────────────────────────────────────────────────────

def test_experience_eligible(engine):
    result = engine.check_experience(3.0)
    assert result["passed"] == True
    assert result["tag"]    == "eligible"

def test_experience_under_minimum(engine):
    result = engine.check_experience(0.5)
    assert result["passed"] == False
    assert result["tag"]    == "rejected"

def test_experience_over_maximum(engine):
    result = engine.check_experience(15.0)
    assert result["passed"] == False
    assert result["tag"]    == "review"

def test_experience_at_minimum_boundary(engine):
    min_exp = engine.params["min_experience_years"]
    result  = engine.check_experience(min_exp)
    assert result["passed"] == True

def test_experience_at_maximum_boundary(engine):
    max_exp = engine.params["max_experience_years"]
    result  = engine.check_experience(max_exp)
    assert result["passed"] == True


# ── Location Check Tests ──────────────────────────────────────────────────────

def test_location_not_required(engine):
    result = engine.check_location("any_city")
    assert result["passed"] == True

def test_location_allowed(engine_with_location):
    result = engine_with_location.check_location("bangalore")
    assert result["passed"] == True

def test_location_not_allowed(engine_with_location):
    result = engine_with_location.check_location("chennai")
    assert result["passed"] == False
    assert result["tag"]    == "review"

def test_location_case_insensitive(engine_with_location):
    result = engine_with_location.check_location("BANGALORE")
    assert result["passed"] == True


# ── Notice Period Tests ───────────────────────────────────────────────────────

def test_notice_not_required(engine):
    result = engine.check_notice_period(120)
    assert result["passed"] == True

def test_notice_within_limit(engine_with_notice):
    result = engine_with_notice.check_notice_period(30)
    assert result["passed"] == True

def test_notice_exceeds_limit(engine_with_notice):
    result = engine_with_notice.check_notice_period(60)
    assert result["passed"] == False
    assert result["tag"]    == "review"


# ── Full Decide Tests ─────────────────────────────────────────────────────────

def test_decide_returns_dict(eligible_result):
    assert isinstance(eligible_result, dict)

def test_decide_has_required_fields(eligible_result):
    assert "candidate_id"    in eligible_result
    assert "ats_score"       in eligible_result
    assert "eligibility_tag" in eligible_result
    assert "tag_label"       in eligible_result
    assert "checks"          in eligible_result
    assert "passed_rules"    in eligible_result
    assert "failed_rules"    in eligible_result
    assert "total_checks"    in eligible_result
    assert "checks_passed"   in eligible_result

def test_decide_eligible_candidate(eligible_result):
    assert eligible_result["eligibility_tag"] == "eligible"

def test_decide_rejected_candidate(rejected_result):
    assert rejected_result["eligibility_tag"] == "rejected"

def test_decide_missing_skill_is_rejected(engine):
    result = engine.decide(MISSING_SKILL_CANDIDATE)
    assert result["eligibility_tag"] == "rejected"
    failed = [r["rule"] for r in result["failed_rules"]]
    assert "mandatory_skills" in failed

def test_decide_low_experience_is_rejected(engine):
    result = engine.decide(LOW_EXP_CANDIDATE)
    assert result["eligibility_tag"] == "rejected"

def test_decide_high_experience_is_review(engine):
    result = engine.decide(HIGH_EXP_CANDIDATE)
    assert result["eligibility_tag"] in ["review", "eligible"]

def test_decide_tag_is_valid(engine):
    for cand in [ELIGIBLE_CANDIDATE, REVIEW_CANDIDATE, REJECTED_CANDIDATE]:
        result = engine.decide(cand)
        assert result["eligibility_tag"] in ["eligible", "review", "rejected"]

def test_decide_counts_correct(eligible_result):
    total  = eligible_result["total_checks"]
    passed = eligible_result["checks_passed"]
    failed = len(eligible_result["failed_rules"])
    assert passed + failed == total


# ── Batch Decision Tests ──────────────────────────────────────────────────────

def test_decide_batch_returns_list(engine):
    results = engine.decide_batch([ELIGIBLE_CANDIDATE, REJECTED_CANDIDATE])
    assert isinstance(results, list)
    assert len(results) == 2

def test_decide_batch_correct_count(engine):
    candidates = [ELIGIBLE_CANDIDATE, REVIEW_CANDIDATE,
                  REJECTED_CANDIDATE, MISSING_SKILL_CANDIDATE]
    results    = engine.decide_batch(candidates)
    assert len(results) == 4


# ── Report Tests ──────────────────────────────────────────────────────────────

def test_report_returns_dict(engine):
    results = engine.decide_batch([ELIGIBLE_CANDIDATE, REJECTED_CANDIDATE])
    report  = engine.generate_eligibility_report(results, "TEST-JOB")
    assert isinstance(report, dict)

def test_report_has_required_sections(engine):
    results = engine.decide_batch([ELIGIBLE_CANDIDATE, REJECTED_CANDIDATE])
    report  = engine.generate_eligibility_report(results)
    assert "report_metadata"       in report
    assert "summary"               in report
    assert "eligible_candidates"   in report
    assert "review_candidates"     in report
    assert "rejected_candidates"   in report

def test_report_summary_counts_correct(engine):
    results = engine.decide_batch([
        ELIGIBLE_CANDIDATE, REVIEW_CANDIDATE, REJECTED_CANDIDATE
    ])
    report  = engine.generate_eligibility_report(results)
    summary = report["summary"]
    assert summary["total"] == (
        summary["eligible_count"] +
        summary["review_count"] +
        summary["rejected_count"]
    )

def test_save_report(engine, tmp_path):
    results = engine.decide_batch([ELIGIBLE_CANDIDATE])
    report  = engine.generate_eligibility_report(results)
    out     = str(tmp_path / "test_eligibility.json")
    engine.save_report(report, out)
    assert os.path.exists(out)
    with open(out) as f:
        data = json.load(f)
    assert "summary" in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_eligibility_tags_defined():
    for tag in ["eligible", "review", "rejected"]:
        assert tag in ELIGIBILITY_TAGS

def test_role_configs_defined():
    for role in ["software_engineer", "data_analyst", "data_scientist",
                 "devops_engineer", "hr_manager", "management_trainee"]:
        assert role in ROLE_ELIGIBILITY_CONFIGS

def test_role_configs_have_required_fields():
    required = ["min_ats_score", "review_ats_score", "min_experience_years",
                "max_experience_years", "mandatory_skills"]
    for role, cfg in ROLE_ELIGIBILITY_CONFIGS.items():
        for field in required:
            assert field in cfg

def test_min_score_above_review_score():
    for role, cfg in ROLE_ELIGIBILITY_CONFIGS.items():
        assert cfg["min_ats_score"] > cfg["review_ats_score"]

def test_rule_failure_reasons_defined():
    required = ["low_ats_score", "missing_mandatory",
                "under_experience", "over_experience"]
    for r in required:
        assert r in RULE_FAILURE_REASONS


# ── EligibilityRule Tests ─────────────────────────────────────────────────────

def test_rule_creates_instance():
    rule = EligibilityRule("R001", "score", "ATS score check")
    assert rule.rule_id   == "R001"
    assert rule.rule_type == "score"

def test_rule_to_dict():
    rule = EligibilityRule("R001", "score", "ATS score check",
                            is_mandatory=True, weight=1.0)
    d = rule.to_dict()
    assert "rule_id"      in d
    assert "rule_type"    in d
    assert "description"  in d
    assert "is_mandatory" in d
    assert "weight"       in d
