"""
Tests for Day 36 - Confidence & Stress Indicators
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.confidence_analyzer import (
    HesitationDetector, SentimentAnalyzer, StressIndicatorAnalyzer,
    ContradictionDetector, ConfidenceScorer,
    UNCERTAINTY_PHRASES, CONFIDENCE_PHRASES, STRESS_MARKERS,
    CONFIDENCE_BANDS, CONFIDENCE_SCORE_WEIGHTS, CONTRADICTION_PAIRS,
    POSITIVE_SENTIMENT_WORDS, NEGATIVE_SENTIMENT_WORDS,
)

# ── Sample Responses ──────────────────────────────────────────────────────────

HESITANT   = "I'm not sure... maybe I think possibly I could be wrong."
CONFIDENT  = "I am confident. I successfully led a team and delivered results absolutely on time."
STRESSED   = "I'm sorry, I'm not the best at this. Let me think. I just might not be ideal."
POSITIVE   = "I am excited and passionate. I love this work and I thrive in teams."
NEGATIVE   = "I have struggled and found it difficult. I feel overwhelmed and uncertain."
NEUTRAL    = "I have worked here for 3 years doing various tasks."
INTERNAL_CONTRA = "I never lead teams but I led a project last year."
EMPTY      = ""

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def hesitation():   return HesitationDetector()
@pytest.fixture
def sentiment():    return SentimentAnalyzer()
@pytest.fixture
def stress():       return StressIndicatorAnalyzer()
@pytest.fixture
def contradiction(): return ContradictionDetector()
@pytest.fixture
def scorer():       return ConfidenceScorer()


# ── HesitationDetector Tests ──────────────────────────────────────────────────

def test_hesitation_creates_instance(hesitation):
    assert hesitation is not None

def test_hesitation_returns_dict(hesitation):
    assert isinstance(hesitation.analyze(NEUTRAL), dict)

def test_hesitation_has_required_fields(hesitation):
    result = hesitation.analyze(NEUTRAL)
    for f in ["score", "pause_count", "repeated_words",
              "uncertainty_phrases", "hesitation_signals"]:
        assert f in result

def test_hesitation_score_in_range(hesitation):
    for text in [HESITANT, NEUTRAL, CONFIDENT, EMPTY]:
        assert 0 <= hesitation.analyze(text)["score"] <= 100

def test_uncertainty_phrases_detected(hesitation):
    result = hesitation.analyze(HESITANT)
    assert len(result["uncertainty_phrases"]) > 0

def test_confident_response_low_hesitation(hesitation):
    result = hesitation.analyze(CONFIDENT)
    assert result["uncertainty_phrases"] == []

def test_confident_scores_higher_than_hesitant(hesitation):
    assert hesitation.analyze(CONFIDENT)["score"] > hesitation.analyze(HESITANT)["score"]

def test_empty_scores_zero(hesitation):
    assert hesitation.analyze(EMPTY)["score"] == 0

def test_repeated_words_detected(hesitation):
    result = hesitation.analyze("I I think we we should move forward.")
    assert len(result["repeated_words"]) > 0

def test_hesitation_signals_count_is_sum(hesitation):
    result = hesitation.analyze(HESITANT)
    expected = result["pause_count"] + len(result["repeated_words"]) + len(result["uncertainty_phrases"])
    assert result["hesitation_signals"] == expected


# ── SentimentAnalyzer Tests ───────────────────────────────────────────────────

def test_sentiment_creates_instance(sentiment):
    assert sentiment is not None

def test_sentiment_returns_dict(sentiment):
    assert isinstance(sentiment.analyze(NEUTRAL), dict)

def test_sentiment_has_required_fields(sentiment):
    result = sentiment.analyze(NEUTRAL)
    for f in ["score", "label", "positive_words", "negative_words", "net_sentiment"]:
        assert f in result

def test_sentiment_score_in_range(sentiment):
    for text in [POSITIVE, NEUTRAL, NEGATIVE, EMPTY]:
        assert 0 <= sentiment.analyze(text)["score"] <= 100

def test_positive_sentiment_detected(sentiment):
    result = sentiment.analyze(POSITIVE)
    assert result["label"] == "Positive"
    assert len(result["positive_words"]) > 0

def test_negative_sentiment_detected(sentiment):
    result = sentiment.analyze(NEGATIVE)
    assert result["label"] == "Negative"
    assert len(result["negative_words"]) > 0

def test_positive_scores_higher_than_negative(sentiment):
    assert sentiment.analyze(POSITIVE)["score"] > sentiment.analyze(NEGATIVE)["score"]

def test_net_sentiment_is_difference(sentiment):
    result = sentiment.analyze(POSITIVE)
    expected = len(result["positive_words"]) - len(result["negative_words"])
    assert result["net_sentiment"] == expected

def test_empty_scores_zero_sentiment(sentiment):
    assert sentiment.analyze(EMPTY)["score"] == 0


# ── StressIndicatorAnalyzer Tests ─────────────────────────────────────────────

def test_stress_creates_instance(stress):
    assert stress is not None

def test_stress_returns_dict(stress):
    assert isinstance(stress.analyze(NEUTRAL), dict)

def test_stress_has_required_fields(stress):
    result = stress.analyze(NEUTRAL)
    for f in ["score", "stress_markers", "stress_hit_count",
              "confidence_phrases", "stress_categories"]:
        assert f in result

def test_stress_score_in_range(stress):
    for text in [STRESSED, NEUTRAL, CONFIDENT, EMPTY]:
        assert 0 <= stress.analyze(text)["score"] <= 100

def test_stress_markers_detected(stress):
    result = stress.analyze(STRESSED)
    assert result["stress_hit_count"] > 0

def test_confidence_phrases_detected(stress):
    result = stress.analyze(CONFIDENT)
    assert len(result["confidence_phrases"]) > 0

def test_confident_scores_higher_stress_than_stressed(stress):
    assert stress.analyze(CONFIDENT)["score"] > stress.analyze(STRESSED)["score"]

def test_empty_stress_scores_zero(stress):
    assert stress.analyze(EMPTY)["score"] == 0


# ── ContradictionDetector Tests ───────────────────────────────────────────────

def test_contradiction_creates_instance(contradiction):
    assert contradiction is not None

def test_contradiction_returns_dict(contradiction):
    assert isinstance(contradiction.analyze(NEUTRAL), dict)

def test_contradiction_has_required_fields(contradiction):
    result = contradiction.analyze(NEUTRAL)
    for f in ["score", "contradictions", "contradiction_count", "has_contradiction"]:
        assert f in result

def test_score_in_range(contradiction):
    for text in [INTERNAL_CONTRA, NEUTRAL, CONFIDENT, EMPTY]:
        assert 0 <= contradiction.analyze(text)["score"] <= 100

def test_internal_contradiction_detected(contradiction):
    result = contradiction.analyze(INTERNAL_CONTRA)
    assert result["has_contradiction"] == True
    assert result["contradiction_count"] >= 1

def test_clean_response_no_contradiction(contradiction):
    result = contradiction.analyze(CONFIDENT)
    assert result["has_contradiction"] == False

def test_cross_session_contradiction_detected(contradiction):
    prior = ["I work alone and I am not a team player."]
    result = contradiction.analyze("I am a strong team player.", prior)
    assert result["contradiction_count"] >= 1

def test_empty_returns_perfect_score(contradiction):
    result = contradiction.analyze(EMPTY)
    assert result["score"] == 100


# ── ConfidenceScorer Tests ────────────────────────────────────────────────────

def test_scorer_creates_instance(scorer):
    assert scorer is not None

def test_score_returns_dict(scorer):
    assert isinstance(scorer.score(NEUTRAL), dict)

def test_score_has_required_fields(scorer):
    result = scorer.score(NEUTRAL)
    for f in ["confidence_score", "band", "dimensions",
              "weights", "signal_notes", "generated_at"]:
        assert f in result

def test_final_score_in_range(scorer):
    for text in [HESITANT, NEUTRAL, CONFIDENT, EMPTY]:
        assert 0 <= scorer.score(text)["confidence_score"] <= 100

def test_confident_scores_higher_than_hesitant(scorer):
    assert scorer.score(CONFIDENT)["confidence_score"] > scorer.score(HESITANT)["confidence_score"]

def test_band_is_valid_string(scorer):
    valid = [info["label"] for info in CONFIDENCE_BANDS.values()]
    assert scorer.score(NEUTRAL)["band"] in valid

def test_excellent_band_for_confident_response(scorer):
    result = scorer.score(CONFIDENT)
    assert result["band"] == "Highly Confident"

def test_dimensions_has_all_4(scorer):
    result = scorer.score(NEUTRAL)
    for dim in ["hesitation", "sentiment", "stress", "contradiction"]:
        assert dim in result["dimensions"]

def test_signal_notes_is_list(scorer):
    result = scorer.score(HESITANT)
    assert isinstance(result["signal_notes"], list)
    assert len(result["signal_notes"]) > 0

def test_prior_responses_passed_to_contradiction(scorer):
    prior = ["I work alone and I am not a team player."]
    result = scorer.score("I am a strong team player.", prior_responses=prior)
    assert result["dimensions"]["contradiction"]["contradiction_count"] >= 1


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_uncertainty_phrases_not_empty():
    assert len(UNCERTAINTY_PHRASES) > 0

def test_confidence_phrases_not_empty():
    assert len(CONFIDENCE_PHRASES) > 0

def test_stress_markers_has_4_categories():
    assert len(STRESS_MARKERS) == 4

def test_contradiction_pairs_not_empty():
    assert len(CONTRADICTION_PAIRS) > 0

def test_score_weights_sum_to_1():
    total = sum(CONFIDENCE_SCORE_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001

def test_confidence_bands_cover_0_to_100():
    all_values = []
    for info in CONFIDENCE_BANDS.values():
        lo, hi = info["range"]
        all_values.extend([lo, hi])
    assert 0 in all_values
    assert 100 in all_values

def test_positive_sentiment_words_not_empty():
    assert len(POSITIVE_SENTIMENT_WORDS) > 0

def test_negative_sentiment_words_not_empty():
    assert len(NEGATIVE_SENTIMENT_WORDS) > 0
