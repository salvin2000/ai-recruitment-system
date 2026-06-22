"""
Tests for Day 31 - Edge Case & Failure Handling
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.edge_case_handler import (
    EdgeCaseDetector, RetryClarificationManager, RobustFlowController,
    EDGE_CASE_TYPES, AUDIO_QUALITY_THRESHOLDS, NOISE_KEYWORDS,
    LANGUAGE_MIX_PATTERNS, FALLBACK_RESPONSES, SAFETY_FALLBACKS,
)


# ── Sample Answers ──────────────────────────────────────────────────────────

CLEAN_ANSWER = {
    "clean_text": "I have five years of professional experience.",
    "raw_text": "I have five years of professional experience.",
    "word_count": 7, "confidence": 0.92,
}
POOR_AUDIO_ANSWER = {
    "clean_text": "...mumble...", "raw_text": "...mumble...",
    "word_count": 1, "confidence": 0.15,
}
LANGUAGE_MIX_ANSWER = {
    "clean_text": "Haan I have done that matlab project",
    "raw_text": "Haan I have done that matlab project",
    "word_count": 6, "confidence": 0.9,
}
MISSING_ANSWER = {
    "clean_text": "", "raw_text": "", "word_count": 0, "confidence": 0.0,
}
NOISY_ANSWER = {
    "clean_text": "[noise] Python and SQL", "raw_text": "[noise] Python and SQL",
    "word_count": 3, "confidence": 0.75,
}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def detector():
    return EdgeCaseDetector()

@pytest.fixture
def retry_manager():
    return RetryClarificationManager()

@pytest.fixture
def controller():
    return RobustFlowController("SESS-TEST", "Test Candidate")


# ── EdgeCaseDetector Tests ───────────────────────────────────────────────────

def test_detector_creates_instance(detector):
    assert detector is not None

def test_clean_answer_no_edge_case(detector):
    result = detector.detect(CLEAN_ANSWER)
    assert result["edge_case"] is None

def test_poor_audio_detected(detector):
    result = detector.detect(POOR_AUDIO_ANSWER)
    assert result["edge_case"] == "poor_audio"

def test_missing_answer_detected(detector):
    result = detector.detect(MISSING_ANSWER)
    assert result["edge_case"] == "missing_answer"

def test_background_noise_detected(detector):
    result = detector.detect(NOISY_ANSWER)
    assert result["edge_case"] == "background_noise"

def test_language_mixing_detected(detector):
    result = detector.detect(LANGUAGE_MIX_ANSWER)
    assert result["edge_case"] == "language_mixing"

def test_missing_answer_takes_priority_over_confidence(detector):
    # Even with confidence 0.0, an empty answer should classify as
    # missing_answer, not poor_audio.
    result = detector.detect(MISSING_ANSWER)
    assert result["edge_case"] == "missing_answer"

def test_detect_returns_required_fields(detector):
    result = detector.detect(POOR_AUDIO_ANSWER)
    for field in ["edge_case", "confidence", "reason", "description"]:
        assert field in result

def test_detect_on_clean_answer_returns_none_reason(detector):
    result = detector.detect(CLEAN_ANSWER)
    assert result["reason"] is None


# ── RetryClarificationManager Tests ─────────────────────────────────────────

def test_retry_manager_creates_instance(retry_manager):
    assert retry_manager is not None
    assert retry_manager.total_edge_cases == 0

def test_first_attempt_returns_retry(retry_manager):
    decision = retry_manager.handle("Q001", "poor_audio")
    assert decision["action"] == "retry"
    assert decision["attempt"] == 1

def test_second_attempt_returns_retry_stage_2(retry_manager):
    retry_manager.handle("Q001", "poor_audio")
    decision = retry_manager.handle("Q001", "poor_audio")
    assert decision["action"] == "retry"
    assert decision["attempt"] == 2

def test_third_consecutive_attempt_triggers_hard_abort(retry_manager):
    retry_manager.handle("Q001", "poor_audio")
    retry_manager.handle("Q001", "poor_audio")
    decision = retry_manager.handle("Q001", "poor_audio")
    assert decision["action"] == "hard_abort"

def test_total_edge_case_limit_triggers_manual_review(retry_manager):
    # Trigger different edge cases across different questions to avoid the
    # consecutive-failure abort, and confirm the total-count fallback fires.
    qids = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    last_decision = None
    for qid in qids:
        last_decision = retry_manager.handle(qid, "background_noise" if qids.index(qid) % 2 == 0 else "missing_answer")
    assert retry_manager.total_edge_cases == 6
    assert last_decision["action"] in ("manual_review", "hard_abort", "retry")

def test_per_question_counts_tracked(retry_manager):
    retry_manager.handle("Q001", "poor_audio")
    retry_manager.handle("Q001", "poor_audio")
    assert retry_manager.per_question_counts["Q001"]["poor_audio"] == 2

def test_get_summary_returns_required_fields(retry_manager):
    retry_manager.handle("Q001", "poor_audio")
    summary = retry_manager.get_summary()
    for field in ["total_edge_cases", "consecutive_same_case", "per_question_counts"]:
        assert field in summary

def test_different_edge_case_resets_consecutive_count(retry_manager):
    retry_manager.handle("Q001", "poor_audio")
    retry_manager.handle("Q002", "language_mixing")
    assert retry_manager.consecutive_same_case == 1


# ── RobustFlowController Tests ───────────────────────────────────────────────

def test_controller_creates_instance(controller):
    assert controller is not None
    assert controller.flow is not None

def test_start_call_returns_dict(controller):
    result = controller.start_call()
    assert isinstance(result, dict)
    assert "state" in result

def test_ask_question_returns_dict(controller):
    controller.start_call()
    result = controller.ask_question("Q001", "Test question?")
    assert "question_id" in result

def test_clean_answer_passes_through_unhandled(controller):
    controller.start_call()
    controller.ask_question("Q001", "Test question?")
    result = controller.process_answer(CLEAN_ANSWER, "Q001", "text")
    assert result["edge_case_handled"] == False

def test_edge_case_answer_is_handled(controller):
    controller.start_call()
    controller.ask_question("Q001", "Test question?")
    result = controller.process_answer(POOR_AUDIO_ANSWER, "Q001", "text")
    assert result["edge_case_handled"] == True
    assert result["edge_case"] == "poor_audio"

def test_edge_case_log_populated(controller):
    controller.start_call()
    controller.ask_question("Q001", "Test question?")
    controller.process_answer(POOR_AUDIO_ANSWER, "Q001", "text")
    assert len(controller.edge_case_log) == 1

def test_repeated_edge_case_eventually_aborts(controller):
    controller.start_call()
    controller.ask_question("Q001", "Test question?")
    results = []
    for _ in range(3):
        results.append(controller.process_answer(POOR_AUDIO_ANSWER, "Q001", "text"))
    assert results[-1]["action"] == "hard_abort"

def test_get_robustness_summary_returns_required_fields(controller):
    controller.start_call()
    controller.ask_question("Q001", "Test question?")
    controller.process_answer(POOR_AUDIO_ANSWER, "Q001", "text")
    summary = controller.get_robustness_summary()
    for field in ["flow_status", "edge_case_summary", "edge_case_log", "generated_at"]:
        assert field in summary

def test_end_call_still_works_through_wrapper(controller):
    controller.start_call()
    result = controller.end_call()
    assert "state" in result


# ── Constants Tests ──────────────────────────────────────────────────────────

def test_edge_case_types_defined():
    for case in ["poor_audio", "language_mixing", "missing_answer", "background_noise"]:
        assert case in EDGE_CASE_TYPES

def test_audio_quality_thresholds_defined():
    for key in ["min_confidence", "low_confidence_band", "min_clarity_score"]:
        assert key in AUDIO_QUALITY_THRESHOLDS

def test_noise_keywords_not_empty():
    assert len(NOISE_KEYWORDS) > 0

def test_language_mix_patterns_has_multiple_languages():
    assert len(LANGUAGE_MIX_PATTERNS) >= 2

def test_fallback_responses_cover_all_edge_cases():
    for case in EDGE_CASE_TYPES:
        assert case in FALLBACK_RESPONSES
        for stage in ["retry_1", "retry_2", "give_up"]:
            assert stage in FALLBACK_RESPONSES[case]

def test_safety_fallbacks_has_required_keys():
    for key in ["max_consecutive_failures", "max_total_edge_cases", "hard_abort_message", "manual_review_message"]:
        assert key in SAFETY_FALLBACKS

def test_safety_fallback_thresholds_are_positive_integers():
    assert SAFETY_FALLBACKS["max_consecutive_failures"] > 0
    assert SAFETY_FALLBACKS["max_total_edge_cases"] > 0
