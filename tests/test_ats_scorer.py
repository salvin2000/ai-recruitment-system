"""
Tests for Day 13 – ATS Scoring Formula Design
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_scorer import (
    ATSScoringEngine, WeightProfile, ComponentScore,
    DEFAULT_WEIGHT_PROFILES, GRADE_THRESHOLDS,
    RECOMMENDATION_THRESHOLDS, MISSING_DATA_PENALTIES
)


# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_JD = {
    "job_id":               "ZCP-JOB-TEST-001",
    "role_name":            "Software Engineer",
    "required_skills":      ["python", "django", "aws", "docker", "postgresql"],
    "preferred_skills":     ["kubernetes", "machine learning"],
    "min_experience_years": 2,
    "max_experience_years": 5,
    "min_education":        "b.tech",
    "field_of_study":       "computer science",
}

GOOD_SKILL_DATA = {
    "skill_summary": {
        "technical": ["python", "django", "aws", "docker", "postgresql", "git"],
        "soft":       ["communication", "leadership"],
        "business":   [],
        "creative":   [],
    }
}

PARTIAL_SKILL_DATA = {
    "skill_summary": {
        "technical": ["python", "sql"],
        "soft":       [],
        "business":   [],
        "creative":   [],
    }
}

GOOD_EXPERIENCE_DATA = {
    "metadata": {"total_years": 4.0},
    "relevance": {
        "relevance_score":      0.85,
        "role_similarity":      1.0,
        "skills_match":         0.80,
        "total_years":          4.0,
        "meets_min_experience": True,
    }
}

FRESHER_EXPERIENCE_DATA = {
    "metadata": {"total_years": 0.0},
    "relevance": {
        "relevance_score":      0.0,
        "role_similarity":      0.5,
        "skills_match":         0.0,
        "total_years":          0.0,
        "meets_min_experience": False,
    }
}

GOOD_EDUCATION_DATA = {
    "metadata": {
        "highest_degree":       "b.tech",
        "total_certifications": 2,
    },
    "relevance": {
        "relevance_score": 1.0,
        "meets_min_degree":True,
        "degree_score":    1.0,
        "field_score":     1.0,
    }
}

GOOD_SEMANTIC_DATA = {
    "overall_match": {"score": 0.28},
    "similarity_scores": {
        "skills":     {"score": 0.40},
        "experience": {"score": 0.21},
        "projects":   {"score": 0.13},
    }
}

LOW_SEMANTIC_DATA = {
    "overall_match": {"score": 0.05},
    "similarity_scores": {
        "skills":     {"score": 0.04},
        "experience": {"score": 0.05},
        "projects":   {"score": 0.00},
    }
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return ATSScoringEngine()

@pytest.fixture
def full_score(engine):
    return engine.score(
        candidate_id     = "ZCP-CAND-TEST",
        job_id           = "ZCP-JOB-TEST",
        skill_data       = GOOD_SKILL_DATA,
        experience_data  = GOOD_EXPERIENCE_DATA,
        education_data   = GOOD_EDUCATION_DATA,
        semantic_data    = GOOD_SEMANTIC_DATA,
        job_requirements = SAMPLE_JD,
        role_type        = "software_engineer",
    )

@pytest.fixture
def missing_score(engine):
    return engine.score(
        candidate_id     = "ZCP-CAND-MISS",
        job_id           = "ZCP-JOB-TEST",
        skill_data       = None,
        experience_data  = None,
        education_data   = None,
        semantic_data    = None,
        job_requirements = SAMPLE_JD,
        role_type        = "default",
    )


# ── Engine Instance Tests ─────────────────────────────────────────────────────

def test_engine_creates_instance(engine):
    assert engine is not None
    assert engine.grade_thresholds is not None

def test_engine_has_grade_thresholds(engine):
    assert "A" in engine.grade_thresholds
    assert "B" in engine.grade_thresholds
    assert "D" in engine.grade_thresholds


# ── Weight Profile Tests ──────────────────────────────────────────────────────

def test_weight_profile_creates(engine):
    profile = engine.get_weight_profile("software_engineer")
    assert profile is not None
    assert profile.profile_name == "software_engineer"

def test_weight_profile_sums_to_one(engine):
    for role in DEFAULT_WEIGHT_PROFILES:
        profile = engine.get_weight_profile(role)
        total   = sum(profile.weights.values())
        assert abs(total - 1.0) < 0.01

def test_weight_profile_all_roles(engine):
    for role in ["software_engineer", "data_analyst", "management_trainee",
                 "data_scientist", "devops_engineer", "hr_manager"]:
        profile = engine.get_weight_profile(role)
        assert profile is not None

def test_weight_profile_unknown_role_uses_default(engine):
    profile = engine.get_weight_profile("unknown_role_xyz")
    default = engine.get_weight_profile("default")
    assert profile.weights == default.weights

def test_custom_weights(engine):
    profile = engine.set_custom_weights(0.50, 0.25, 0.10, 0.15, "skill_heavy")
    assert abs(sum(profile.weights.values()) - 1.0) < 0.01

def test_invalid_negative_weight():
    with pytest.raises(ValueError):
        WeightProfile({
            "skill_match": -0.1, "experience_relevance": 0.4,
            "education_alignment": 0.3, "semantic_similarity": 0.4
        })


# ── Component Score Tests ─────────────────────────────────────────────────────

def test_component_score_creates():
    comp = ComponentScore("skill_match", 0.85, 0.35, "Test explanation")
    assert comp.raw_score    == 0.85
    assert comp.weight       == 0.35
    assert comp.data_present == True

def test_component_score_missing_data():
    comp = ComponentScore("skill_match", 0.0, 0.35, "Missing", data_present=False)
    assert comp.data_present  == False
    assert comp.weighted_score < (0.35 * 100)

def test_component_score_clamps_range():
    comp = ComponentScore("skill_match", 1.5, 0.35, "Over 1.0")
    assert comp.raw_score == 1.0
    comp2 = ComponentScore("skill_match", -0.5, 0.35, "Negative")
    assert comp2.raw_score == 0.0

def test_skill_score_all_matched(engine):
    comp = engine.build_skill_score(GOOD_SKILL_DATA, SAMPLE_JD, 0.35)
    assert comp.raw_score >= 0.7
    assert comp.data_present == True

def test_skill_score_partial_match(engine):
    comp_good    = engine.build_skill_score(GOOD_SKILL_DATA, SAMPLE_JD, 0.35)
    comp_partial = engine.build_skill_score(PARTIAL_SKILL_DATA, SAMPLE_JD, 0.35)
    assert comp_good.raw_score > comp_partial.raw_score

def test_skill_score_no_data(engine):
    comp = engine.build_skill_score(None, SAMPLE_JD, 0.35)
    assert comp.raw_score    == 0.0
    assert comp.data_present == False

def test_experience_score_good(engine):
    comp = engine.build_experience_score(GOOD_EXPERIENCE_DATA, SAMPLE_JD, 0.30)
    assert comp.raw_score > 0.5
    assert comp.data_present == True

def test_experience_score_fresher(engine):
    comp_good    = engine.build_experience_score(GOOD_EXPERIENCE_DATA, SAMPLE_JD, 0.30)
    comp_fresher = engine.build_experience_score(FRESHER_EXPERIENCE_DATA, SAMPLE_JD, 0.30)
    assert comp_good.raw_score > comp_fresher.raw_score

def test_experience_score_no_data(engine):
    comp = engine.build_experience_score(None, SAMPLE_JD, 0.30)
    assert comp.raw_score    == 0.0
    assert comp.data_present == False

def test_education_score_good(engine):
    comp = engine.build_education_score(GOOD_EDUCATION_DATA, SAMPLE_JD, 0.15)
    assert comp.raw_score > 0.5
    assert comp.data_present == True

def test_education_score_no_data(engine):
    comp = engine.build_education_score(None, SAMPLE_JD, 0.15)
    assert comp.raw_score    == 0.0
    assert comp.data_present == False

def test_semantic_score_good(engine):
    comp = engine.build_semantic_score(GOOD_SEMANTIC_DATA, 0.20)
    assert comp.raw_score > 0.0
    assert comp.data_present == True

def test_semantic_score_normalized(engine):
    comp = engine.build_semantic_score(GOOD_SEMANTIC_DATA, 0.20)
    assert 0.0 <= comp.raw_score <= 1.0

def test_semantic_score_no_data(engine):
    comp = engine.build_semantic_score(None, 0.20)
    assert comp.raw_score    == 0.0
    assert comp.data_present == False


# ── Full Score Tests ──────────────────────────────────────────────────────────

def test_full_score_returns_dict(full_score):
    assert isinstance(full_score, dict)

def test_full_score_has_required_fields(full_score):
    assert "metadata"         in full_score
    assert "component_scores" in full_score
    assert "final_score"      in full_score
    assert "score_breakdown"  in full_score

def test_full_score_metadata_fields(full_score):
    meta = full_score["metadata"]
    assert "candidate_id"   in meta
    assert "job_id"         in meta
    assert "role_type"      in meta
    assert "weight_profile" in meta

def test_final_score_fields(full_score):
    final = full_score["final_score"]
    assert "score"          in final
    assert "grade"          in final
    assert "recommendation" in final
    assert "strengths"      in final
    assert "gaps"           in final
    assert "missing_data"   in final
    assert "is_complete"    in final

def test_final_score_range(full_score):
    score = full_score["final_score"]["score"]
    assert 0.0 <= score <= 100.0

def test_final_grade_valid(full_score):
    grade = full_score["final_score"]["grade"]
    assert grade in ["A+", "A", "B+", "B", "C+", "C", "D"]

def test_score_breakdown_sums_to_total(full_score):
    bd    = full_score["score_breakdown"]
    total = round(
        bd["skill_match"] + bd["experience_relevance"] +
        bd["education_alignment"] + bd["semantic_similarity"], 1
    )
    assert abs(total - bd["total"]) < 0.1

def test_complete_data_is_complete(full_score):
    assert full_score["final_score"]["is_complete"] == True

def test_missing_data_not_complete(missing_score):
    missing = missing_score["final_score"]["missing_data"]
    assert len(missing) > 0

def test_good_candidate_scores_higher_than_fresher(engine):
    good_result    = engine.score(
        "GOOD", "JOB", GOOD_SKILL_DATA, GOOD_EXPERIENCE_DATA,
        GOOD_EDUCATION_DATA, GOOD_SEMANTIC_DATA, SAMPLE_JD, "software_engineer"
    )
    fresher_result = engine.score(
        "FRESH","JOB", PARTIAL_SKILL_DATA, FRESHER_EXPERIENCE_DATA,
        GOOD_EDUCATION_DATA, LOW_SEMANTIC_DATA, SAMPLE_JD, "software_engineer"
    )
    assert good_result["final_score"]["score"] > fresher_result["final_score"]["score"]


# ── Grade and Recommendation Tests ───────────────────────────────────────────

def test_assign_grade_high_score(engine):
    assert engine.assign_grade(90) == "A+"

def test_assign_grade_low_score(engine):
    assert engine.assign_grade(10) == "D"

def test_assign_recommendation_high(engine):
    rec = engine.assign_recommendation(90)
    assert "Hire" in rec

def test_assign_recommendation_low(engine):
    rec = engine.assign_recommendation(20)
    assert "Reject" in rec or "Review" in rec


# ── Batch Score Tests ─────────────────────────────────────────────────────────

def test_batch_score_returns_list(engine):
    candidates = [
        {"candidate_id": "C1", "job_id": "J1",
         "skill_data": GOOD_SKILL_DATA,
         "experience_data": GOOD_EXPERIENCE_DATA,
         "education_data": GOOD_EDUCATION_DATA,
         "semantic_data": GOOD_SEMANTIC_DATA},
        {"candidate_id": "C2", "job_id": "J1",
         "skill_data": PARTIAL_SKILL_DATA,
         "experience_data": FRESHER_EXPERIENCE_DATA,
         "education_data": GOOD_EDUCATION_DATA,
         "semantic_data": LOW_SEMANTIC_DATA},
    ]
    results = engine.score_batch(candidates, SAMPLE_JD, "software_engineer")
    assert isinstance(results, list)
    assert len(results) == 2

def test_batch_score_sorted_descending(engine):
    candidates = [
        {"candidate_id": "C1", "job_id": "J1",
         "skill_data": GOOD_SKILL_DATA,
         "experience_data": GOOD_EXPERIENCE_DATA,
         "education_data": GOOD_EDUCATION_DATA,
         "semantic_data": GOOD_SEMANTIC_DATA},
        {"candidate_id": "C2", "job_id": "J1",
         "skill_data": PARTIAL_SKILL_DATA,
         "experience_data": FRESHER_EXPERIENCE_DATA,
         "education_data": GOOD_EDUCATION_DATA,
         "semantic_data": LOW_SEMANTIC_DATA},
    ]
    results = engine.score_batch(candidates, SAMPLE_JD, "software_engineer")
    scores  = [r["final_score"]["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


# ── Scorecard Tests ───────────────────────────────────────────────────────────

def test_generate_scorecard(engine, full_score):
    card = engine.generate_scorecard(full_score)
    assert isinstance(card, str)
    assert "ATS SCORECARD" in card
    assert "GRADE" in card
    assert "RECOMMENDATION" in card


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(engine, full_score, tmp_path):
    output_file = str(tmp_path / "test_ats_score.json")
    engine.save_output(full_score, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "final_score"      in data
    assert "component_scores" in data
    assert "score_breakdown"  in data
