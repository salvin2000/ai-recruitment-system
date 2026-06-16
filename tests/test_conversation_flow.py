"""
Tests for Day 29 – AI Conversation Flow Design
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.conversation_flow import (
    ConversationStateMachine, TurnDecisionEngine, ConversationFlowController,
    CONVERSATION_STATES, STATE_TRANSITIONS, TURN_OUTCOMES,
    FALLBACK_QUESTIONS, FOLLOW_UP_TRIGGERS, FOLLOW_UP_MESSAGES,
    SILENCE_HANDLING, RETRY_CONFIG, POLITE_MESSAGES,
)


# ── Sample Answers ────────────────────────────────────────────────────────────

VALID_ANSWER = {
    "clean_text": "I have 3.5 years of Python experience.", "intent": "experience_info",
    "extracted": {"experience_years": 3.5}, "is_valid": True,
    "is_vague": False, "is_off_topic": False, "needs_followup": False,
    "word_count": 8, "confidence": 0.91,
}
PARTIAL_ANSWER = {
    "clean_text": "Around three.", "intent": "experience_info",
    "extracted": {}, "is_valid": True,
    "is_vague": False, "is_off_topic": False, "needs_followup": True,
    "word_count": 2, "confidence": 0.89,
}
VAGUE_ANSWER = {
    "clean_text": "It depends.", "intent": "vague",
    "extracted": {}, "is_valid": False,
    "is_vague": True, "is_off_topic": False, "needs_followup": True,
    "word_count": 2, "confidence": 0.85,
}
OFF_TOPIC_ANSWER = {
    "clean_text": "I love cricket.", "intent": "off_topic",
    "extracted": {}, "is_valid": False,
    "is_vague": False, "is_off_topic": True, "needs_followup": True,
    "word_count": 3, "confidence": 0.95,
}
SILENCE_ANSWER = {
    "clean_text": "", "intent": "unknown",
    "extracted": {}, "is_valid": False,
    "is_vague": False, "is_off_topic": False, "needs_followup": False,
    "word_count": 0, "confidence": 0.0,
}
CLARIFICATION_ANSWER = {
    "clean_text": "Could you repeat the question please?", "intent": "clarification",
    "extracted": {}, "is_valid": False,
    "is_vague": False, "is_off_topic": False, "needs_followup": False,
    "word_count": 6, "confidence": 0.90,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def machine():
    return ConversationStateMachine("SESS-001", "Arjun Krishnan")

@pytest.fixture
def engine():
    return TurnDecisionEngine()

@pytest.fixture
def controller():
    return ConversationFlowController("SESS-001", "Arjun Krishnan")


# ── ConversationStateMachine Tests ────────────────────────────────────────────

def test_machine_creates_instance(machine):
    assert machine is not None
    assert machine.state == "idle"

def test_machine_initial_state(machine):
    assert machine.state        == "idle"
    assert machine.turn_count   == 0
    assert machine.skip_count   == 0
    assert machine.total_failures == 0

def test_valid_transition(machine):
    result = machine.transition("greeting")
    assert result["success"] == True
    assert machine.state     == "greeting"

def test_invalid_transition(machine):
    result = machine.transition("completed")
    assert result["success"] == False
    assert machine.state     == "idle"

def test_transition_updates_previous_state(machine):
    machine.transition("greeting")
    assert machine.previous_state == "idle"

def test_transition_adds_to_history(machine):
    machine.transition("greeting")
    assert len(machine.state_history) == 1
    assert machine.state_history[0]["to"] == "greeting"

def test_can_transition_valid(machine):
    assert machine.can_transition("greeting") == True

def test_can_transition_invalid(machine):
    assert machine.can_transition("completed") == False

def test_increment_retry(machine):
    count = machine.increment_retry("Q020")
    assert count == 1
    assert machine.total_failures == 1

def test_increment_retry_multiple(machine):
    machine.increment_retry("Q020")
    count = machine.increment_retry("Q020")
    assert count == 2

def test_should_abort_false(machine):
    assert machine.should_abort() == False

def test_should_abort_true(machine):
    for _ in range(RETRY_CONFIG["abort_threshold"]):
        machine.increment_retry("Q020")
    assert machine.should_abort() == True

def test_should_skip_false(machine):
    assert machine.should_skip("Q020") == False

def test_should_skip_true(machine):
    for _ in range(RETRY_CONFIG["max_retries_per_question"]):
        machine.increment_retry("Q020")
    assert machine.should_skip("Q020") == True

def test_mark_asked(machine):
    machine.mark_asked("Q020")
    assert "Q020" in machine.asked_questions
    assert machine.turn_count == 1

def test_mark_skipped(machine):
    machine.mark_skipped("Q021")
    assert "Q021" in machine.skipped_questions
    assert machine.skip_count == 1

def test_get_status_returns_dict(machine):
    status = machine.get_status()
    assert isinstance(status, dict)
    assert "state"          in status
    assert "turn_count"     in status
    assert "should_abort"   in status

def test_to_dict_returns_dict(machine):
    d = machine.to_dict()
    assert "state_history" in d
    assert "created_at"    in d


# ── TurnDecisionEngine Tests ──────────────────────────────────────────────────

def test_engine_creates_instance(engine):
    assert engine is not None

def test_valid_complete_answer(engine):
    result = engine.classify_turn(VALID_ANSWER, "Q020", "numeric", 0)
    assert result["action"]  == "next_question"
    assert result["outcome"] == "valid_complete"

def test_partial_answer_follow_up(engine):
    result = engine.classify_turn(PARTIAL_ANSWER, "Q031", "numeric", 0)
    assert result["action"]  == "follow_up"
    assert result["outcome"] == "valid_partial"

def test_vague_answer_retry(engine):
    result = engine.classify_turn(VAGUE_ANSWER, "Q021", "text", 0)
    assert result["action"]  == "retry"
    assert result["outcome"] == "vague"

def test_off_topic_answer_retry(engine):
    result = engine.classify_turn(OFF_TOPIC_ANSWER, "Q030", "text", 0)
    assert result["action"]  == "retry"
    assert result["outcome"] == "off_topic"

def test_silence_handled(engine):
    result = engine.classify_turn(SILENCE_ANSWER, "Q020", "numeric", 0)
    assert result["outcome"] == "silence"

def test_clarification_request(engine):
    result = engine.classify_turn(CLARIFICATION_ANSWER, "Q020", "numeric", 0)
    assert result["action"]  == "clarify"
    assert result["outcome"] == "confusion"

def test_vague_at_max_retries_skips(engine):
    result = engine.classify_turn(VAGUE_ANSWER, "Q021", "text",
                                   RETRY_CONFIG["max_retries_per_question"])
    assert result["action"]  == "skip"
    assert result["outcome"] == "max_retries_reached"

def test_decision_returns_required_fields(engine):
    result = engine.classify_turn(VALID_ANSWER, "Q020", "numeric", 0)
    assert "action"     in result
    assert "outcome"    in result
    assert "next_state" in result
    assert "message"    in result
    assert "reason"     in result

def test_next_state_is_valid(engine):
    for ans, qid, atype, retry in [
        (VALID_ANSWER, "Q020", "numeric", 0),
        (VAGUE_ANSWER, "Q021", "text",    0),
        (OFF_TOPIC_ANSWER, "Q030", "text",0),
    ]:
        result = engine.classify_turn(ans, qid, atype, retry)
        assert result["next_state"] in CONVERSATION_STATES

def test_handle_contradiction_returns_dict(engine):
    result = engine.handle_contradiction(VALID_ANSWER, VALID_ANSWER)
    assert isinstance(result, dict)
    assert result["outcome"] == "contradiction"


# ── ConversationFlowController Tests ─────────────────────────────────────────

def test_controller_creates_instance(controller):
    assert controller is not None

def test_start_call_returns_dict(controller):
    result = controller.start_call()
    assert isinstance(result, dict)
    assert "message" in result
    assert "state"   in result

def test_start_call_state(controller):
    result = controller.start_call()
    assert result["state"] in CONVERSATION_STATES

def test_ask_question_returns_dict(controller):
    controller.start_call()
    result = controller.ask_question("Q020", "How many years of experience?")
    assert isinstance(result, dict)
    assert "question_id" in result
    assert "message"     in result

def test_process_answer_returns_dict(controller):
    controller.start_call()
    controller.ask_question("Q020", "How many years?")
    result = controller.process_answer(VALID_ANSWER, "Q020", "numeric")
    assert isinstance(result, dict)
    assert "action"   in result
    assert "outcome"  in result
    assert "message"  in result
    assert "state"    in result

def test_process_valid_answer_next_question(controller):
    controller.start_call()
    controller.ask_question("Q020", "How many years?")
    result = controller.process_answer(VALID_ANSWER, "Q020", "numeric")
    assert result["action"] == "next_question"

def test_process_vague_increments_retry(controller):
    controller.start_call()
    controller.ask_question("Q021", "Current title?")
    controller.process_answer(VAGUE_ANSWER, "Q021", "text")
    assert controller.machine.retry_count.get("Q021", 0) >= 1

def test_end_call_returns_dict(controller):
    controller.start_call()
    result = controller.end_call()
    assert isinstance(result, dict)
    assert "state"   in result
    assert "message" in result
    assert "status"  in result

def test_end_call_completed_state(controller):
    controller.start_call()
    controller.ask_question("Q001", "Are you ready?")
    controller.process_answer({"clean_text": "Yes.", "intent": "affirmative", "extracted": {"boolean_value": True}, "is_valid": True, "is_vague": False, "is_off_topic": False, "needs_followup": False, "word_count": 1, "confidence": 0.92}, "Q001", "yes_no")
    result = controller.end_call()
    assert result["state"] == "completed"

def test_call_log_populated(controller):
    controller.start_call()
    controller.ask_question("Q020", "test question")
    assert len(controller.call_log) >= 2

def test_save_flow(controller, tmp_path):
    controller.start_call()
    controller.end_call()
    output = str(tmp_path / "test_flow.json")
    controller.save_flow(output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "final_status" in data
    assert "call_log"     in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_conversation_states_defined():
    for state in ["idle","greeting","asking","listening","processing",
                  "follow_up","retry","completed","aborted"]:
        assert state in CONVERSATION_STATES

def test_state_transitions_complete(machine):
    for state in CONVERSATION_STATES:
        assert state in STATE_TRANSITIONS

def test_all_transitions_valid():
    for state, targets in STATE_TRANSITIONS.items():
        for target in targets:
            assert target in CONVERSATION_STATES

def test_turn_outcomes_defined():
    for outcome in ["valid_complete","valid_partial","vague",
                    "off_topic","silence","confusion"]:
        assert outcome in TURN_OUTCOMES

def test_fallback_questions_have_categories():
    for cat in ["experience","skills","salary","notice_period","general"]:
        assert cat in FALLBACK_QUESTIONS
        assert len(FALLBACK_QUESTIONS[cat]) >= 2

def test_silence_handling_has_stages():
    for stage in ["prompt_1","prompt_2","retry","skip"]:
        assert stage in SILENCE_HANDLING

def test_retry_config_has_limits():
    assert "max_retries_per_question" in RETRY_CONFIG
    assert "max_skips_per_session"    in RETRY_CONFIG
    assert "abort_threshold"          in RETRY_CONFIG

def test_polite_messages_defined():
    for key in ["off_topic_redirect","repeat_question",
                "max_retries_skip","call_closing","call_abort"]:
        assert key in POLITE_MESSAGES
