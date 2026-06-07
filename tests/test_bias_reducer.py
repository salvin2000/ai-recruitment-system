"""
Tests for Day 15 – Fairness, Normalization & Bias Reduction
"""

import os
import sys
import json
import math
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.bias_reducer import (
    ResumeNormalizer, ScoreNormalizer, BiasDetector,
    BIAS_MASK_PATTERNS, BUZZWORD_PATTERNS,
    NORMALIZATION_BOUNDS, BIAS_INDICATOR_THRESHOLDS
)


# ── Sample Texts ──────────────────────────────────────────────────────────────

BIASED_RESUME = """Mr. John Smith
john.smith@email.com | +91-9876543210
Male, Age: 28, Hindu, Married
Bangalore, India

Summary
Passionate and enthusiastic rockstar developer.
A true ninja with cutting-edge innovative skills.

Technical Skills
Python, Django, AWS, Docker, PostgreSQL

Work Experience
Software Engineer - TechCorp India
June 2022 - Present
Developed RESTful APIs using Django."""

CLEAN_RESUME = """Software Engineer with 3 years of experience.

Technical Skills
Python, Django, AWS, Docker, PostgreSQL

Work Experience
Software Engineer - TechCorp India
June 2022 - Present
Developed RESTful APIs using Django REST Framework."""

HEADING_RESUME = """
Professional Experience
Software Engineer - TechCorp
June 2022 - Present

Educational Background
B.Tech Computer Science
RV College | 2017 - 2021

Core Competencies
Python, Django, AWS"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def normalizer():
    return ResumeNormalizer()

@pytest.fixture
def score_normalizer():
    return ScoreNormalizer()

@pytest.fixture
def detector():
    return BiasDetector()

@pytest.fixture
def norm_result(normalizer):
    return normalizer.normalize_resume(BIASED_RESUME)

@pytest.fixture
def bias_result(detector):
    return detector.evaluate_resume(BIASED_RESUME)


# ── ResumeNormalizer Tests ────────────────────────────────────────────────────

def test_normalizer_creates_instance(normalizer):
    assert normalizer is not None
    assert normalizer.mask_patterns is not None

def test_mask_personal_attributes_email(normalizer):
    result = normalizer.mask_personal_attributes(
        "Contact: john@email.com", ["email"]
    )
    assert "john@email.com" not in result["masked_text"]
    assert "[EMAIL_MASKED]" in result["masked_text"]

def test_mask_personal_attributes_phone(normalizer):
    result = normalizer.mask_personal_attributes(
        "Phone: +91-9876543210", ["phone"]
    )
    assert "9876543210" not in result["masked_text"]

def test_mask_personal_attributes_gender(normalizer):
    result = normalizer.mask_personal_attributes(
        "Mr. John Smith is applying", ["gender_pronouns"]
    )
    assert result["masking_log"].get("gender_pronouns", 0) > 0

def test_mask_personal_attributes_religion(normalizer):
    result = normalizer.mask_personal_attributes(
        "Religion: Hindu", ["religion"]
    )
    assert "Hindu" not in result["masked_text"]

def test_mask_marital_status(normalizer):
    result = normalizer.mask_personal_attributes(
        "Marital Status: Married", ["marital_status"]
    )
    assert "Married" not in result["masked_text"]

def test_mask_returns_log(normalizer):
    result = normalizer.mask_personal_attributes(
        "john@email.com, Hindu, Married", ["email","religion","marital_status"]
    )
    assert "masking_log" in result
    assert result["total_masked"] > 0

def test_remove_buzzwords(normalizer):
    result = normalizer.remove_buzzwords(
        "I am a passionate rockstar ninja developer"
    )
    assert result["buzzwords_removed"] > 0
    assert "rockstar" not in result["cleaned_text"].lower()
    assert "ninja"    not in result["cleaned_text"].lower()

def test_remove_buzzwords_clean_text(normalizer):
    result = normalizer.remove_buzzwords(
        "Python developer with 3 years of experience"
    )
    assert result["buzzwords_removed"] == 0

def test_normalize_section_headings(normalizer):
    result = normalizer.normalize_section_headings(
        "Professional Experience\nEducational Background\nCore Competencies"
    )
    assert "Work Experience"  in result
    assert "Education"        in result
    assert "Skills"           in result

def test_normalize_dates(normalizer):
    result = normalizer.normalize_dates("January 2022 to Present")
    assert "01-2022" in result

def test_normalize_resume_full_pipeline(norm_result):
    assert "normalized_text"   in norm_result
    assert "original_length"   in norm_result
    assert "normalized_length" in norm_result
    assert "masking_log"       in norm_result
    assert "total_masked"      in norm_result
    assert "buzzwords_removed" in norm_result

def test_normalize_resume_removes_personal_info(normalizer):
    result = normalizer.normalize_resume(BIASED_RESUME)
    assert result["total_masked"] > 0

def test_normalize_resume_removes_buzzwords(normalizer):
    r=normalizer.remove_buzzwords("passionate rockstar ninja cutting-edge")
    assert r["buzzwords_removed"] > 0

def test_normalize_section_headings_in_resume(normalizer):
    r=normalizer.normalize_section_headings(HEADING_RESUME)
    assert "Work Experience" in r
    assert "Education" in r
    assert "Skills" in r


# ── ScoreNormalizer Tests ─────────────────────────────────────────────────────

def test_score_normalizer_creates_instance(score_normalizer):
    assert score_normalizer is not None
    assert score_normalizer.bounds is not None

def test_min_max_normalize_zero(score_normalizer):
    result = score_normalizer.min_max_normalize(0.0, "skill_match")
    assert result == 0.0

def test_min_max_normalize_one(score_normalizer):
    result = score_normalizer.min_max_normalize(1.0, "skill_match")
    assert result == 1.0

def test_min_max_normalize_semantic(score_normalizer):
    # Semantic score 0.20 with max expected 0.40 should normalize to 0.5
    result = score_normalizer.min_max_normalize(0.20, "semantic_similarity")
    assert abs(result - 0.5) < 0.01

def test_min_max_normalize_unknown_component(score_normalizer):
    result = score_normalizer.min_max_normalize(0.75, "unknown_component")
    assert 0.0 <= result <= 1.0

def test_min_max_normalize_clamps_above_max(score_normalizer):
    result = score_normalizer.min_max_normalize(2.0, "skill_match")
    assert result <= 1.0

def test_min_max_normalize_clamps_below_min(score_normalizer):
    result = score_normalizer.min_max_normalize(-1.0, "skill_match")
    assert result >= 0.0

def test_z_score_normalize_mean_zero(score_normalizer):
    scores   = [60.0, 70.0, 80.0]
    z_scores = score_normalizer.z_score_normalize(scores)
    mean_z   = sum(z_scores) / len(z_scores)
    assert abs(mean_z) < 0.01

def test_z_score_normalize_empty(score_normalizer):
    assert score_normalizer.z_score_normalize([]) == []

def test_z_score_normalize_same_scores(score_normalizer):
    z_scores = score_normalizer.z_score_normalize([60.0, 60.0, 60.0])
    assert all(z == 0.0 for z in z_scores)

def test_normalize_batch_returns_list(score_normalizer):
    mock_results = [{
        "component_scores": {
            "skill_match": {"raw_score": 0.7, "weighted_score": 24.5},
        },
        "final_score": {"score": 72.0}
    }]
    normalized = score_normalizer.normalize_batch(mock_results)
    assert isinstance(normalized, list)
    assert len(normalized) == 1

def test_normalize_batch_adds_normalized_score(score_normalizer):
    mock_results = [{
        "component_scores": {
            "skill_match": {"raw_score": 0.7, "weighted_score": 24.5},
        },
        "final_score": {"score": 72.0}
    }]
    normalized = score_normalizer.normalize_batch(mock_results)
    comp = normalized[0]["component_scores"]["skill_match"]
    assert "normalized_score"       in comp
    assert "normalization_applied"  in comp


# ── BiasDetector Tests ────────────────────────────────────────────────────────

def test_detector_creates_instance(detector):
    assert detector is not None
    assert detector.thresholds is not None

def test_detect_personal_info_density_high(detector):
    result = detector.detect_personal_info_density(BIASED_RESUME)
    assert "density"  in result
    assert "flagged"  in result
    assert "fields_found" in result

def test_detect_personal_info_density_low(detector):
    r=detector.detect_personal_info_density(CLEAN_RESUME)
    b=detector.detect_personal_info_density(BIASED_RESUME)
    assert r["personal_info_count"] < b["personal_info_count"]

def test_detect_buzzword_density_high(detector):
    result = detector.detect_buzzword_density(BIASED_RESUME)
    assert result["buzzword_count"] > 0
    assert "found_buzzwords" in result

def test_detect_buzzword_density_low(detector):
    result = detector.detect_buzzword_density(CLEAN_RESUME)
    assert result["buzzword_count"] == 0
    assert result["flagged"] == False

def test_detect_score_variance(detector):
    scores = [80.0, 70.0, 40.0, 30.0]
    result = detector.detect_score_variance(scores)
    assert "mean_score"  in result
    assert "std_dev"     in result
    assert "score_range" in result
    assert "outliers"    in result

def test_detect_score_variance_empty(detector):
    result = detector.detect_score_variance([])
    assert result["flagged"] == False

def test_detect_score_variance_identifies_outlier(detector):
    scores=[70.0,72.0,68.0,71.0,69.0,5.0]
    result=detector.detect_score_variance(scores)
    assert result["flagged"]==True
    assert len(result["outliers"])>0

def test_evaluate_resume_returns_dict(bias_result):
    assert isinstance(bias_result, dict)

def test_evaluate_resume_has_required_fields(bias_result):
    assert "bias_evaluation"   in bias_result
    assert "personal_info"     in bias_result
    assert "buzzword_analysis" in bias_result

def test_evaluate_resume_bias_eval_fields(bias_result):
    beval = bias_result["bias_evaluation"]
    assert "risk_level"  in beval
    assert "flags"       in beval
    assert "total_flags" in beval

def test_evaluate_resume_risk_level_valid(bias_result):
    assert bias_result["bias_evaluation"]["risk_level"] in ["Low","Medium","High"]

def test_biased_resume_higher_risk_than_clean(detector):
    biased = detector.evaluate_resume(BIASED_RESUME)
    clean  = detector.evaluate_resume(CLEAN_RESUME)
    biased_flags = biased["bias_evaluation"]["total_flags"]
    clean_flags  = clean["bias_evaluation"]["total_flags"]
    assert biased_flags >= clean_flags

def test_evaluate_batch_returns_dict(detector):
    result = detector.evaluate_batch(
        [BIASED_RESUME, CLEAN_RESUME],
        [79.87, 44.85],
        ["CAND-1", "CAND-2"]
    )
    assert isinstance(result, dict)

def test_evaluate_batch_has_required_fields(detector):
    result = detector.evaluate_batch([BIASED_RESUME, CLEAN_RESUME])
    assert "batch_summary"      in result
    assert "score_distribution" in result
    assert "individual_results" in result

def test_evaluate_batch_summary_count(detector):
    result  = detector.evaluate_batch(
        [BIASED_RESUME, CLEAN_RESUME, CLEAN_RESUME]
    )
    summary = result["batch_summary"]
    assert summary["total_resumes"] == 3
    assert (summary["high_risk_count"] +
            summary["medium_risk_count"] +
            summary["low_risk_count"]) == 3


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_bias_mask_patterns_defined():
    required = ["email","phone","gender_pronouns","religion",
                 "marital_status","age_indicators"]
    for field in required:
        assert field in BIAS_MASK_PATTERNS

def test_normalization_bounds_defined():
    required = ["skill_match","experience_relevance",
                 "education_alignment","semantic_similarity"]
    for comp in required:
        assert comp in NORMALIZATION_BOUNDS

def test_bias_thresholds_defined():
    assert "personal_info_density" in BIAS_INDICATOR_THRESHOLDS
    assert "buzzword_density"       in BIAS_INDICATOR_THRESHOLDS
    assert "keyword_dependence"     in BIAS_INDICATOR_THRESHOLDS


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(detector, bias_result, tmp_path):
    output_file = str(tmp_path / "test_bias.json")
    detector.save_output(bias_result, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "bias_evaluation" in data