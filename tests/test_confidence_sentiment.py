"""
Tests for Day 27 – Confidence & Sentiment Signal Analysis
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.confidence_sentiment import (
    CommunicationStrengthEngine, HesitationDetector,
    ConfidenceAnalyzer, SentimentScorer,
    HESITATION_PATTERNS, CONFIDENCE_SIGNALS, SENTIMENT_LEXICON,
    UNCERTAINTY_INDICATORS, CONTRADICTION_PAIRS,
    PACE_THRESHOLDS, COMMUNICATION_STRENGTH, BEHAVIORAL_TAGS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return CommunicationStrengthEngine()

@pytest.fixture
def hes_det():
    return HesitationDetector()

@pytest.fixture
def conf_anal():
    return ConfidenceAnalyzer()

@pytest.fixture
def sent_sc():
    return SentimentScorer()

CONFIDENT_TEXT = "I built and delivered three production APIs at Infosys managing a team of five engineers."
HESITANT_TEXT  = "Um, I think I have like, you know, around three years maybe I am not really sure sort of."
POSITIVE_TEXT  = "I am excited about this opportunity and would love to contribute and grow."
NEGATIVE_TEXT  = "My previous role was boring and I struggled with poor management and tedious work."
UNCERTAIN_TEXT = "I think maybe around 12 LPA, I am not sure approximately."
CONTRA_TEXT    = "Yes I can join within 30 days. Actually I cannot join within 30 days."
NEUTRAL_TEXT   = "I have three years of experience working with Python and Django."


# ── HesitationDetector Tests ──────────────────────────────────────────────────

def test_hes_det_creates_instance(hes_det):
    assert hes_det is not None

def test_count_hesitations_returns_dict(hes_det):
    result = hes_det.count_hesitations(HESITANT_TEXT)
    assert isinstance(result, dict)

def test_count_hesitations_has_fields(hes_det):
    result = hes_det.count_hesitations(HESITANT_TEXT)
    assert "count"      in result
    assert "density"    in result
    assert "is_hesitant"in result
    assert "severity"   in result
    assert "found"      in result

def test_hesitant_text_flagged(hes_det):
    result = hes_det.count_hesitations(HESITANT_TEXT)
    assert result["is_hesitant"] == True
    assert result["count"] >= 3

def test_confident_text_not_hesitant(hes_det):
    result = hes_det.count_hesitations(CONFIDENT_TEXT)
    assert result["is_hesitant"] == False

def test_hesitation_density_range(hes_det):
    result = hes_det.count_hesitations(HESITANT_TEXT)
    assert 0.0 <= result["density"] <= 2.0

def test_hesitation_severity_values(hes_det):
    result = hes_det.count_hesitations(HESITANT_TEXT)
    assert result["severity"] in ("low", "medium", "high")

def test_empty_text_no_hesitations(hes_det):
    result = hes_det.count_hesitations("")
    assert result["count"] == 0


# ── ConfidenceAnalyzer Tests ──────────────────────────────────────────────────

def test_conf_analyzer_creates_instance(conf_anal):
    assert conf_anal is not None

def test_analyze_returns_dict(conf_anal):
    result = conf_anal.analyze(CONFIDENT_TEXT)
    assert isinstance(result, dict)

def test_analyze_has_required_fields(conf_anal):
    result = conf_anal.analyze(CONFIDENT_TEXT)
    assert "confidence_score"  in result
    assert "high_conf_signals" in result
    assert "low_conf_signals"  in result
    assert "hesitation"        in result
    assert "word_count"        in result

def test_confident_text_higher_score(conf_anal):
    conf  = conf_anal.analyze(CONFIDENT_TEXT)
    hes   = conf_anal.analyze(HESITANT_TEXT)
    assert conf["confidence_score"] > hes["confidence_score"]

def test_confidence_score_range(conf_anal):
    for text in [CONFIDENT_TEXT, HESITANT_TEXT, NEUTRAL_TEXT]:
        result = conf_anal.analyze(text)
        assert 0.0 <= result["confidence_score"] <= 1.0

def test_high_signals_detected(conf_anal):
    result = conf_anal.analyze(CONFIDENT_TEXT)
    assert result["high_conf_signals"] >= 1

def test_low_signals_in_hesitant(conf_anal):
    result = conf_anal.analyze(HESITANT_TEXT)
    assert result["low_conf_signals"] >= 1

def test_wpm_with_duration(conf_anal):
    result = conf_anal.analyze(CONFIDENT_TEXT, duration_ms=5000)
    assert result["wpm"] > 0

def test_wpm_without_duration(conf_anal):
    result = conf_anal.analyze(CONFIDENT_TEXT, duration_ms=0)
    assert result["wpm"] == 0

def test_hesitant_tag_added(conf_anal):
    result = conf_anal.analyze(HESITANT_TEXT)
    assert "hesitant" in result["tags"]

def test_verbose_tag_for_long_text(conf_anal):
    long_text = " ".join(["word"] * 35)
    result    = conf_anal.analyze(long_text)
    assert "verbose" in result["tags"]


# ── SentimentScorer Tests ─────────────────────────────────────────────────────

def test_sent_scorer_creates_instance(sent_sc):
    assert sent_sc is not None

def test_score_sentiment_returns_dict(sent_sc):
    result = sent_sc.score_sentiment(POSITIVE_TEXT)
    assert isinstance(result, dict)

def test_sentiment_has_required_fields(sent_sc):
    result = sent_sc.score_sentiment(POSITIVE_TEXT)
    assert "sentiment_score" in result
    assert "sentiment_label" in result
    assert "positive_words"  in result
    assert "negative_words"  in result

def test_positive_text_positive_label(sent_sc):
    result = sent_sc.score_sentiment(POSITIVE_TEXT)
    assert result["sentiment_label"] == "positive"
    assert result["sentiment_score"] >= 0.0

def test_negative_text_negative_label(sent_sc):
    result = sent_sc.score_sentiment(NEGATIVE_TEXT)
    assert result["sentiment_label"] == "negative"
    assert result["sentiment_score"] <= 0.0

def test_neutral_text_label(sent_sc):
    result = sent_sc.score_sentiment(NEUTRAL_TEXT)
    assert result["sentiment_label"] in ("neutral", "positive", "negative")

def test_sentiment_score_range(sent_sc):
    for text in [POSITIVE_TEXT, NEGATIVE_TEXT, NEUTRAL_TEXT]:
        result = sent_sc.score_sentiment(text)
        assert -1.0 <= result["sentiment_score"] <= 1.0

def test_positive_text_more_pos_words(sent_sc):
    result = sent_sc.score_sentiment(POSITIVE_TEXT)
    assert result["positive_words"] > 0

def test_negative_text_more_neg_words(sent_sc):
    result = sent_sc.score_sentiment(NEGATIVE_TEXT)
    assert result["negative_words"] > 0


# ── Uncertainty Detection Tests ───────────────────────────────────────────────

def test_detect_uncertainty_returns_dict(sent_sc):
    result = sent_sc.detect_uncertainty(UNCERTAIN_TEXT)
    assert isinstance(result, dict)

def test_detect_uncertainty_has_fields(sent_sc):
    result = sent_sc.detect_uncertainty(UNCERTAIN_TEXT)
    assert "uncertainty_count"  in result
    assert "is_uncertain"       in result
    assert "uncertainty_level"  in result

def test_uncertain_text_flagged(sent_sc):
    result = sent_sc.detect_uncertainty(UNCERTAIN_TEXT)
    assert result["is_uncertain"] == True
    assert result["uncertainty_count"] >= 2

def test_confident_text_not_uncertain(sent_sc):
    result = sent_sc.detect_uncertainty(CONFIDENT_TEXT)
    assert result["is_uncertain"] == False

def test_uncertainty_level_values(sent_sc):
    result = sent_sc.detect_uncertainty(UNCERTAIN_TEXT)
    assert result["uncertainty_level"] in ("low", "medium", "high")


# ── Contradiction Detection Tests ─────────────────────────────────────────────

def test_detect_contradiction_returns_dict(sent_sc):
    result = sent_sc.detect_contradiction(CONTRA_TEXT)
    assert isinstance(result, dict)

def test_detect_contradiction_has_fields(sent_sc):
    result = sent_sc.detect_contradiction(CONTRA_TEXT)
    assert "has_contradiction"   in result
    assert "contradiction_pairs" in result
    assert "count"               in result

def test_contradiction_detected(sent_sc):
    result = sent_sc.detect_contradiction(CONTRA_TEXT)
    assert result["has_contradiction"] == True
    assert result["count"] >= 1

def test_no_contradiction_clean_text(sent_sc):
    result = sent_sc.detect_contradiction(CONFIDENT_TEXT)
    assert result["has_contradiction"] == False


# ── CommunicationStrengthEngine Tests ─────────────────────────────────────────

def test_engine_creates_instance(engine):
    assert engine is not None

def test_analyze_returns_dict(engine):
    result = engine.analyze(CONFIDENT_TEXT, 5000, "Q022", "SESS-001")
    assert isinstance(result, dict)

def test_analyze_has_required_fields(engine):
    result = engine.analyze(CONFIDENT_TEXT, 5000, "Q022", "SESS-001")
    required = ["analysis_id", "confidence", "sentiment", "uncertainty",
                "contradiction", "communication_strength", "behavioral_tags"]
    for field in required:
        assert field in result

def test_strength_score_range(engine):
    result = engine.analyze(CONFIDENT_TEXT)
    assert 0.0 <= result["communication_strength"]["score"] <= 100.0

def test_strength_level_valid(engine):
    result = engine.analyze(CONFIDENT_TEXT)
    assert result["communication_strength"]["level"] in COMMUNICATION_STRENGTH

def test_confident_text_stronger(engine):
    conf = engine.analyze(CONFIDENT_TEXT)
    hes  = engine.analyze(HESITANT_TEXT)
    assert conf["communication_strength"]["score"] > \
           hes["communication_strength"]["score"]

def test_off_topic_tag_set(engine):
    result = engine.analyze(CONFIDENT_TEXT, is_off_topic=True)
    assert "off_topic" in result["behavioral_tags"]

def test_on_topic_tag_set(engine):
    result = engine.analyze(CONFIDENT_TEXT, is_off_topic=False)
    assert "on_topic" in result["behavioral_tags"]

def test_contradiction_tag_when_detected(engine):
    result = engine.analyze(CONTRA_TEXT)
    assert "contradictory" in result["behavioral_tags"]

def test_analyze_batch_returns_list(engine):
    turns = [
        {"text": CONFIDENT_TEXT, "question_id": "Q022"},
        {"text": HESITANT_TEXT,  "question_id": "Q020"},
    ]
    results = engine.analyze_batch(turns)
    assert isinstance(results, list)
    assert len(results) == 2


# ── Report Generation Tests ───────────────────────────────────────────────────

def test_generate_report_returns_dict(engine):
    turns   = [{"text": CONFIDENT_TEXT}, {"text": HESITANT_TEXT}]
    results = engine.analyze_batch(turns)
    report  = engine.generate_report(results, "CAND-001", "SESS-001")
    assert isinstance(report, dict)

def test_report_has_required_sections(engine):
    results = engine.analyze_batch([{"text": CONFIDENT_TEXT}])
    report  = engine.generate_report(results)
    assert "report_metadata"         in report
    assert "summary"                 in report
    assert "behavioral_tag_frequency"in report
    assert "per_answer_results"      in report

def test_report_summary_fields(engine):
    results = engine.analyze_batch([{"text": CONFIDENT_TEXT}])
    report  = engine.generate_report(results)
    summary = report["summary"]
    assert "avg_confidence_score"   in summary
    assert "avg_sentiment_score"    in summary
    assert "avg_strength_score"     in summary
    assert "overall_strength_level" in summary

def test_report_empty_list(engine):
    report = engine.generate_report([])
    assert report == {}

def test_save_report(engine, tmp_path):
    results = engine.analyze_batch([{"text": CONFIDENT_TEXT}])
    report  = engine.generate_report(results)
    output  = str(tmp_path / "test_report.json")
    engine.save_report(report, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "summary" in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_hesitation_patterns_defined():
    assert len(HESITATION_PATTERNS) > 0
    assert any("um" in p for p in HESITATION_PATTERNS)

def test_confidence_signals_have_two_levels():
    assert "high_confidence" in CONFIDENCE_SIGNALS
    assert "low_confidence"  in CONFIDENCE_SIGNALS
    assert len(CONFIDENCE_SIGNALS["high_confidence"]) > 0

def test_sentiment_lexicon_has_categories():
    assert "positive" in SENTIMENT_LEXICON
    assert "negative" in SENTIMENT_LEXICON
    assert len(SENTIMENT_LEXICON["positive"]) > 0
    assert len(SENTIMENT_LEXICON["negative"]) > 0

def test_communication_strength_levels():
    for level in ["strong", "moderate", "weak", "poor"]:
        assert level in COMMUNICATION_STRENGTH

def test_behavioral_tags_defined():
    expected = ["highly_confident", "hesitant", "positive_framing",
                "negative_framing", "contradictory", "on_topic", "off_topic"]
    for tag in expected:
        assert tag in BEHAVIORAL_TAGS

def test_contradiction_pairs_are_tuples():
    for pair in CONTRADICTION_PAIRS:
        assert isinstance(pair, tuple)
        assert len(pair) == 2
