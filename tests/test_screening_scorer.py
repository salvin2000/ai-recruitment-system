"""
Tests for Day 26 – Screening Scoring Engine
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.screening_scorer import (
    ScreeningScorer, DimensionScorer,
    SCORING_DIMENSIONS, GRADE_THRESHOLDS,
    QUESTION_SCORING_CONFIG, CATEGORY_WEIGHTS, SCORING_RULES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def scorer():
    return ScreeningScorer()

@pytest.fixture
def dim_scorer():
    return DimensionScorer()

GOOD_ANSWER = {
    "is_vague": False, "is_off_topic": False, "needs_followup": False,
    "word_count": 9, "confidence": 0.91,
    "intent": "experience_info",
    "extracted": {"experience_years": 3.5, "skills_mentioned": ["python"]},
}
VAGUE_ANSWER = {
    "is_vague": True, "is_off_topic": False, "needs_followup": True,
    "word_count": 2, "confidence": 0.85, "intent": "vague", "extracted": {},
}
OFF_TOPIC_ANSWER = {
    "is_vague": False, "is_off_topic": True, "needs_followup": True,
    "word_count": 6, "confidence": 0.95, "intent": "off_topic", "extracted": {},
}
LOW_CONF_ANSWER = {
    "is_vague": False, "is_off_topic": False, "needs_followup": False,
    "word_count": 9, "confidence": 0.55, "intent": "experience_info",
    "extracted": {"experience_years": 3.5},
}
ATS_PROFILE = {
    "experience_years": 3.9,
    "skills": ["python", "django", "aws"],
    "expected_salary_lpa": 12.0,
}


# ── DimensionScorer Instance Tests ────────────────────────────────────────────

def test_dim_scorer_creates_instance(dim_scorer):
    assert dim_scorer is not None

def test_dim_scorer_has_dimensions(dim_scorer):
    assert dim_scorer.dimensions is not None

def test_dim_scorer_has_rules(dim_scorer):
    assert dim_scorer.rules is not None


# ── Clarity Scoring Tests ─────────────────────────────────────────────────────

def test_clarity_good_answer(dim_scorer):
    result = dim_scorer.score_clarity(GOOD_ANSWER)
    assert result["score"] > 0.7

def test_clarity_vague_answer(dim_scorer):
    result = dim_scorer.score_clarity(VAGUE_ANSWER)
    assert result["score"] < dim_scorer.score_clarity(GOOD_ANSWER)["score"]

def test_clarity_low_confidence(dim_scorer):
    result = dim_scorer.score_clarity(LOW_CONF_ANSWER)
    good   = dim_scorer.score_clarity(GOOD_ANSWER)
    assert result["score"] < good["score"]

def test_clarity_returns_reasons(dim_scorer):
    result = dim_scorer.score_clarity(GOOD_ANSWER)
    assert "reasons" in result
    assert len(result["reasons"]) > 0

def test_clarity_score_range(dim_scorer):
    for ans in [GOOD_ANSWER, VAGUE_ANSWER, LOW_CONF_ANSWER]:
        result = dim_scorer.score_clarity(ans)
        assert 0.0 <= result["score"] <= 1.0

def test_clarity_detailed_answer_bonus(dim_scorer):
    detailed = {**GOOD_ANSWER, "word_count": 20}
    normal   = {**GOOD_ANSWER, "word_count": 9}
    assert dim_scorer.score_clarity(detailed)["score"] >= \
           dim_scorer.score_clarity(normal)["score"]


# ── Relevance Scoring Tests ───────────────────────────────────────────────────

def test_relevance_good_answer(dim_scorer):
    result = dim_scorer.score_relevance(GOOD_ANSWER, "experience")
    assert result["score"] > 0.7

def test_relevance_off_topic_zero(dim_scorer):
    result = dim_scorer.score_relevance(OFF_TOPIC_ANSWER, "experience")
    assert result["score"] == 0.0

def test_relevance_returns_reasons(dim_scorer):
    result = dim_scorer.score_relevance(GOOD_ANSWER, "experience")
    assert "reasons" in result
    assert len(result["reasons"]) > 0

def test_relevance_score_range(dim_scorer):
    result = dim_scorer.score_relevance(GOOD_ANSWER, "experience")
    assert 0.0 <= result["score"] <= 1.0

def test_relevance_affirmative_location(dim_scorer):
    ans    = {**GOOD_ANSWER, "intent": "affirmative"}
    result = dim_scorer.score_relevance(ans, "location")
    assert result["score"] > 0.7

def test_relevance_vague_reduced(dim_scorer):
    vague_ans = {**GOOD_ANSWER, "intent": "vague"}
    good_ans  = {**GOOD_ANSWER, "intent": "experience_info"}
    assert dim_scorer.score_relevance(vague_ans, "experience")["score"] < \
           dim_scorer.score_relevance(good_ans, "experience")["score"]


# ── Completeness Scoring Tests ────────────────────────────────────────────────

def test_completeness_good_answer(dim_scorer):
    result = dim_scorer.score_completeness(GOOD_ANSWER, "numeric")
    assert result["score"] > 0.5

def test_completeness_needs_followup_reduced(dim_scorer):
    result = dim_scorer.score_completeness(VAGUE_ANSWER, "numeric")
    good   = dim_scorer.score_completeness(GOOD_ANSWER, "numeric")
    assert result["score"] < good["score"]

def test_completeness_yes_no_with_boolean(dim_scorer):
    ans    = {**GOOD_ANSWER, "extracted": {"boolean_value": True}}
    result = dim_scorer.score_completeness(ans, "yes_no")
    assert result["score"] > 0.5

def test_completeness_returns_reasons(dim_scorer):
    result = dim_scorer.score_completeness(GOOD_ANSWER, "numeric")
    assert "reasons" in result

def test_completeness_score_range(dim_scorer):
    result = dim_scorer.score_completeness(GOOD_ANSWER, "numeric")
    assert 0.0 <= result["score"] <= 1.0


# ── Consistency Scoring Tests ─────────────────────────────────────────────────

def test_consistency_matching_experience(dim_scorer):
    ans = {**GOOD_ANSWER, "extracted": {"experience_years": 3.8}}
    result = dim_scorer.score_consistency(ans, ATS_PROFILE, "Q020")
    assert result["score"] >= 0.9

def test_consistency_mismatched_experience(dim_scorer):
    ans    = {**GOOD_ANSWER, "extracted": {"experience_years": 8.0}}
    result = dim_scorer.score_consistency(ans, ATS_PROFILE, "Q020")
    assert result["score"] < 1.0

def test_consistency_skill_match(dim_scorer):
    ans = {**GOOD_ANSWER, "extracted": {"skills_mentioned": ["python", "django"]}}
    result = dim_scorer.score_consistency(ans, ATS_PROFILE, "Q030")
    assert result["score"] > 0.7

def test_consistency_no_ats_neutral(dim_scorer):
    result = dim_scorer.score_consistency(GOOD_ANSWER, {}, "Q020")
    assert result["score"] == 1.0

def test_consistency_returns_reasons(dim_scorer):
    result = dim_scorer.score_consistency(GOOD_ANSWER, ATS_PROFILE, "Q020")
    assert "reasons" in result


# ── score_answer Tests ────────────────────────────────────────────────────────

def test_score_answer_returns_dict(scorer):
    result = scorer.score_answer(GOOD_ANSWER, "Q020", "experience", "numeric")
    assert isinstance(result, dict)

def test_score_answer_has_required_fields(scorer):
    result = scorer.score_answer(GOOD_ANSWER, "Q020", "experience", "numeric")
    required = ["question_id", "category", "max_score", "raw_score_0_1",
                "scaled_score", "weight", "weighted_score", "dimensions"]
    for field in required:
        assert field in result

def test_score_answer_scaled_within_max(scorer):
    result = scorer.score_answer(GOOD_ANSWER, "Q020", "experience", "numeric")
    assert result["scaled_score"] <= result["max_score"]

def test_score_answer_has_4_dimensions(scorer):
    result = scorer.score_answer(GOOD_ANSWER, "Q020", "experience", "numeric")
    assert set(result["dimensions"].keys()) == {"clarity","relevance","completeness","consistency"}

def test_score_answer_off_topic_zero(scorer):
    result = scorer.score_answer(OFF_TOPIC_ANSWER, "Q031", "skills", "numeric")
    assert result["scaled_score"] == 0.0

def test_score_answer_good_above_bad(scorer):
    good   = scorer.score_answer(GOOD_ANSWER,    "Q020", "experience", "numeric")
    vague  = scorer.score_answer(VAGUE_ANSWER,   "Q021", "experience", "text")
    assert good["raw_score_0_1"] > vague["raw_score_0_1"]


# ── aggregate_scores Tests ────────────────────────────────────────────────────

def _make_q_scores(scorer):
    answers = [
        (GOOD_ANSWER,     "Q020", "experience",    "numeric"),
        (GOOD_ANSWER,     "Q030", "skills",        "text"),
        (VAGUE_ANSWER,    "Q021", "experience",    "text"),
        (OFF_TOPIC_ANSWER,"Q031", "skills",        "numeric"),
    ]
    return [scorer.score_answer(a, qid, cat, atype, ATS_PROFILE)
            for a, qid, cat, atype in answers]

def test_aggregate_returns_dict(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert isinstance(result, dict)

def test_aggregate_has_required_fields(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    required = ["final_score","grade","grade_label","outcome",
                "category_scores","dimension_averages","explanation"]
    for field in required:
        assert field in result

def test_aggregate_score_range(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert 0.0 <= result["final_score"]

def test_aggregate_grade_valid(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert result["grade"] in GRADE_THRESHOLDS

def test_aggregate_outcome_valid(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert result["outcome"] in ["advance", "hold", "reject"]

def test_aggregate_category_scores_present(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert len(result["category_scores"]) > 0

def test_aggregate_dimension_averages_present(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    for dim in SCORING_DIMENSIONS:
        assert dim in result["dimension_averages"]

def test_aggregate_explanation_is_list(scorer):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    assert isinstance(result["explanation"], list)
    assert len(result["explanation"]) > 0

def test_aggregate_empty_list(scorer):
    result = scorer.aggregate_scores([])
    assert result == {}


# ── Grade Tests ───────────────────────────────────────────────────────────────

def test_grade_90_is_aplus(scorer):
    grade, data = scorer._get_grade(90.0)
    assert grade == "A+"

def test_grade_80_is_a(scorer):
    grade, data = scorer._get_grade(80.0)
    assert grade == "A"

def test_grade_50_is_cplus(scorer):
    grade, data = scorer._get_grade(50.0)
    assert grade == "C+"

def test_grade_0_is_d(scorer):
    grade, data = scorer._get_grade(0.0)
    assert grade == "D"

def test_grade_data_has_label(scorer):
    _, data = scorer._get_grade(75.0)
    assert "label" in data

def test_grade_data_has_outcome(scorer):
    _, data = scorer._get_grade(75.0)
    assert data["outcome"] in ["advance", "hold", "reject"]


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_scoring_dimensions_have_4():
    assert len(SCORING_DIMENSIONS) == 4
    for dim in ["clarity","relevance","completeness","consistency"]:
        assert dim in SCORING_DIMENSIONS

def test_dimension_weights_sum_to_one():
    total = sum(d["weight"] for d in SCORING_DIMENSIONS.values())
    assert abs(total - 1.0) < 0.01

def test_grade_thresholds_descending():
    scores = [v["min"] for v in GRADE_THRESHOLDS.values()]
    assert scores == sorted(scores, reverse=True)

def test_category_weights_sum_to_one():
    total = sum(CATEGORY_WEIGHTS.values())
    assert abs(total - 1.0) < 0.01

def test_scoring_rules_defined():
    for rule in ["vague_penalty","off_topic_penalty",
                 "low_confidence_factor","partial_factor"]:
        assert rule in SCORING_RULES

def test_save_results(scorer, tmp_path):
    scores = _make_q_scores(scorer)
    result = scorer.aggregate_scores(scores)
    output = str(tmp_path / "test_score.json")
    scorer.save_results(result, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "final_score" in data
    assert "grade"       in data
