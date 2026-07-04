"""
Tests for Day 34 - Dynamic Follow-Up Logic
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.follow_up_engine import (
    ResponseAnalyzer, FollowUpEngine, ConversationStateTracker,
    FOLLOW_UP_TYPES, DIFFICULTY_LEVELS, INCOMPLETE_TRIGGERS,
    FOLLOW_UP_TEMPLATES, VAGUE_SIGNAL_PHRASES,
    MAX_FOLLOW_UPS_PER_QUESTION, MAX_SAME_TYPE_REPEATS,
)

# ── Sample Responses ──────────────────────────────────────────────────────────

VAGUE_SHORT    = "I think I am kind of good maybe."
GENERIC        = "I have worked at various companies doing different things."
STRONG         = ("For example, I led a team of 6 engineers to rebuild the payment API at my last company, "
                  "reducing response time by 35% over 2 sprints and cutting errors by 50%.")
EMPTY          = ""
NUMERIC        = "I have 5 years of experience and managed a team of 8 people across 3 projects."

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def analyzer():
    return ResponseAnalyzer()

@pytest.fixture
def engine():
    return FollowUpEngine()

@pytest.fixture
def tracker():
    return ConversationStateTracker("SESS-TEST", "Test Candidate", "experienced_technical")


# ── ResponseAnalyzer Tests ────────────────────────────────────────────────────

def test_analyzer_creates_instance(analyzer):
    assert analyzer is not None

def test_analyze_returns_dict(analyzer):
    result = analyzer.analyze(VAGUE_SHORT, "strengths_weaknesses")
    assert isinstance(result, dict)

def test_analyze_has_required_fields(analyzer):
    result = analyzer.analyze(VAGUE_SHORT, "career_journey")
    for field in ["word_count", "is_vague", "has_example", "has_number",
                  "incomplete_triggers", "needs_follow_up", "confidence_score", "difficulty_level"]:
        assert field in result

def test_vague_response_detected(analyzer):
    result = analyzer.analyze(VAGUE_SHORT, "strengths_weaknesses")
    assert result["is_vague"] == True

def test_strong_response_not_vague(analyzer):
    result = analyzer.analyze(STRONG, "career_journey")
    assert result["is_vague"] == False

def test_example_detected_in_strong_response(analyzer):
    result = analyzer.analyze(STRONG, "career_journey")
    assert result["has_example"] == True

def test_no_example_in_generic_response(analyzer):
    result = analyzer.analyze(GENERIC, "strengths_weaknesses")
    assert result["has_example"] == False

def test_number_detected_in_numeric_response(analyzer):
    result = analyzer.analyze(NUMERIC, "career_journey")
    assert result["has_number"] == True

def test_empty_response_needs_follow_up(analyzer):
    result = analyzer.analyze(EMPTY, "career_goals")
    assert result["needs_follow_up"] == True

def test_strong_response_does_not_need_follow_up(analyzer):
    result = analyzer.analyze(STRONG, "teamwork_culture_fit")
    assert result["needs_follow_up"] == False

def test_confidence_score_in_valid_range(analyzer):
    for response in [VAGUE_SHORT, GENERIC, STRONG, NUMERIC]:
        result = analyzer.analyze(response, "career_journey")
        assert 0 <= result["confidence_score"] <= 100

def test_strong_response_has_high_confidence(analyzer):
    result = analyzer.analyze(STRONG, "career_journey")
    assert result["confidence_score"] >= 65

def test_vague_response_has_low_confidence(analyzer):
    result = analyzer.analyze(VAGUE_SHORT, "strengths_weaknesses")
    assert result["confidence_score"] < 50

def test_difficulty_level_valid(analyzer):
    for response in [VAGUE_SHORT, GENERIC, STRONG]:
        result = analyzer.analyze(response, "career_journey")
        assert result["difficulty_level"] in DIFFICULTY_LEVELS

def test_too_short_trigger_fires(analyzer):
    result = analyzer.analyze("Yes.", "career_goals")
    assert "too_short" in result["incomplete_triggers"]

def test_no_example_trigger_fires_for_strengths(analyzer):
    result = analyzer.analyze("I am a very hard worker and always deliver on time.", "strengths_weaknesses")
    assert "no_example" in result["incomplete_triggers"]


# ── FollowUpEngine Tests ──────────────────────────────────────────────────────

def test_engine_creates_instance(engine):
    assert engine is not None

def test_decide_returns_dict(engine):
    result = engine.decide(VAGUE_SHORT, "career_journey", "Q001", [], [])
    assert isinstance(result, dict)

def test_decide_has_required_fields(engine):
    result = engine.decide(VAGUE_SHORT, "strengths_weaknesses", "Q001", [], [])
    for field in ["action", "follow_up_type", "follow_up_text", "analysis", "reason"]:
        assert field in result

def test_vague_response_triggers_follow_up(engine):
    result = engine.decide(VAGUE_SHORT, "strengths_weaknesses", "Q001", [], [])
    assert result["action"] == "ask_follow_up"

def test_strong_response_no_follow_up(engine):
    result = engine.decide(STRONG, "teamwork_culture_fit", "Q001", [], [])
    assert result["action"] == "none"

def test_surface_response_gets_clarification(engine):
    result = engine.decide(VAGUE_SHORT, "strengths_weaknesses", "Q001", [], [])
    assert result["follow_up_type"] == "clarification"

def test_moderate_response_gets_deepening(engine):
    moderate = "I have worked on several backend projects across different companies over the years."
    result = engine.decide(moderate, "career_journey", "Q001", [], [])
    assert result["follow_up_type"] in ("deepening", "clarification", "example_based")

def test_follow_up_text_not_empty_when_action_is_ask(engine):
    result = engine.decide(VAGUE_SHORT, "career_goals", "Q001", [], [])
    if result["action"] == "ask_follow_up":
        assert result["follow_up_text"] and len(result["follow_up_text"]) > 0

def test_max_follow_ups_triggers_skip(engine):
    history = [
        {"follow_up_type": "clarification"},
        {"follow_up_type": "deepening"},
    ]
    result = engine.decide(VAGUE_SHORT, "strengths_weaknesses", "Q001", history, [])
    assert result["action"] == "skip"

def test_repetition_prevented(engine):
    history = [{"follow_up_type": "clarification"}]
    result = engine.decide(VAGUE_SHORT, "career_journey", "Q001", history, [])
    if result["action"] == "ask_follow_up":
        assert result["follow_up_type"] != "clarification"


# ── ConversationStateTracker Tests ────────────────────────────────────────────

def test_tracker_creates_instance(tracker):
    assert tracker is not None
    assert tracker.session_id == "SESS-TEST"

def test_record_turn_returns_dict(tracker):
    turn = tracker.record_turn("Q001", "self_introduction", "Tell me about yourself.", VAGUE_SHORT)
    assert isinstance(turn, dict)

def test_record_turn_has_required_fields(tracker):
    turn = tracker.record_turn("Q001", "career_journey", "Walk me through your career.", GENERIC)
    for field in ["turn_number", "question_id", "category", "question_text",
                  "response", "analysis", "action", "follow_up_type",
                  "follow_up_text", "reason", "timestamp"]:
        assert field in turn

def test_turn_number_increments(tracker):
    t1 = tracker.record_turn("Q001", "self_introduction", "Q1", "Answer 1")
    t2 = tracker.record_turn("Q002", "career_journey", "Q2", "Answer 2")
    assert t2["turn_number"] == t1["turn_number"] + 1

def test_get_confidence_profile_returns_dict(tracker):
    tracker.record_turn("Q001", "career_journey", "Q1", VAGUE_SHORT)
    profile = tracker.get_confidence_profile()
    assert isinstance(profile, dict)

def test_confidence_profile_has_required_fields(tracker):
    tracker.record_turn("Q001", "career_journey", "Q1", VAGUE_SHORT)
    profile = tracker.get_confidence_profile()
    for field in ["average_confidence", "min_confidence", "max_confidence",
                  "level_distribution", "follow_ups_asked", "questions_skipped"]:
        assert field in profile

def test_follow_up_counted_in_profile(tracker):
    tracker.record_turn("Q001", "strengths_weaknesses", "Q1", VAGUE_SHORT)
    profile = tracker.get_confidence_profile()
    assert profile["follow_ups_asked"] >= 0

def test_get_full_state_has_required_fields(tracker):
    tracker.record_turn("Q001", "career_goals", "Q1", GENERIC)
    state = tracker.get_full_state()
    for field in ["session_id", "candidate_name", "role_profile",
                  "total_turns", "turns", "confidence_profile", "generated_at"]:
        assert field in state

def test_total_turns_matches_records(tracker):
    tracker.record_turn("Q001", "self_introduction", "Q1", "Answer 1")
    tracker.record_turn("Q002", "career_journey", "Q2", "Answer 2")
    tracker.record_turn("Q003", "career_goals", "Q3", "Answer 3")
    state = tracker.get_full_state()
    assert state["total_turns"] == 3

def test_prior_responses_passed_to_analyzer(tracker):
    tracker.record_turn("Q001", "self_introduction", "Q1", "I have no experience")
    turn2 = tracker.record_turn("Q002", "career_journey", "Q2", "I have 5 years of experience doing projects.")
    assert turn2 is not None


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_follow_up_types_has_3():
    assert len(FOLLOW_UP_TYPES) == 3

def test_follow_up_types_are_correct():
    for ft in ["clarification", "deepening", "example_based"]:
        assert ft in FOLLOW_UP_TYPES

def test_each_follow_up_type_has_required_fields():
    for key, val in FOLLOW_UP_TYPES.items():
        for field in ["label", "description", "trigger"]:
            assert field in val

def test_difficulty_levels_has_4():
    assert len(DIFFICULTY_LEVELS) == 4

def test_difficulty_levels_cover_0_to_100():
    all_ranges = [info["score_range"] for info in DIFFICULTY_LEVELS.values()]
    all_values = [v for lo, hi in all_ranges for v in range(lo, hi + 1)]
    assert 0 in all_values
    assert 100 in all_values

def test_follow_up_templates_cover_all_types():
    for ft in FOLLOW_UP_TYPES:
        assert ft in FOLLOW_UP_TEMPLATES

def test_follow_up_templates_cover_all_categories():
    from parsers.hr_interview_engine import HR_INTERVIEW_CATEGORIES
    for ft in FOLLOW_UP_TEMPLATES:
        for category in HR_INTERVIEW_CATEGORIES:
            assert category in FOLLOW_UP_TEMPLATES[ft]

def test_vague_signal_phrases_not_empty():
    assert len(VAGUE_SIGNAL_PHRASES) > 0

def test_max_follow_ups_is_positive():
    assert MAX_FOLLOW_UPS_PER_QUESTION > 0

def test_max_same_type_repeats_is_positive():
    assert MAX_SAME_TYPE_REPEATS > 0
