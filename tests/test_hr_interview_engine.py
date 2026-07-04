"""
Tests for Day 33 - HR Interview Engine Design
"""

import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.hr_interview_engine import (
    RoleBasedQuestionGenerator, InterviewStateManager, InterviewFlowDesigner,
    HR_INTERVIEW_CATEGORIES, ROLE_PROFILES, CONVERSATION_PHASES,
    QUESTION_BANK, QUESTION_STATE_FIELDS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def generator():
    return RoleBasedQuestionGenerator()

@pytest.fixture
def manager():
    return InterviewStateManager("SESS-TEST", "Test Candidate", "experienced_technical")

@pytest.fixture
def designer():
    return InterviewFlowDesigner()


# ── RoleBasedQuestionGenerator Tests ─────────────────────────────────────────

def test_generator_creates_instance(generator):
    assert generator is not None

def test_get_question_returns_dict(generator):
    result = generator.get_question("self_introduction", "fresher_technical")
    assert isinstance(result, dict)

def test_get_question_has_required_fields(generator):
    result = generator.get_question("career_journey", "experienced_technical")
    for field in ["category", "role_profile", "question_text", "follow_up"]:
        assert field in result

def test_get_question_text_not_empty(generator):
    for profile in ROLE_PROFILES:
        for category in HR_INTERVIEW_CATEGORIES:
            result = generator.get_question(category, profile)
            assert len(result["question_text"]) > 0

def test_follow_up_present_for_all_categories(generator):
    for category in HR_INTERVIEW_CATEGORIES:
        result = generator.get_question(category, "fresher_technical")
        assert len(result["follow_up"]) > 0

def test_invalid_category_returns_error(generator):
    result = generator.get_question("nonexistent_category", "fresher_technical")
    assert "error" in result

def test_invalid_profile_returns_error(generator):
    result = generator.get_question("career_journey", "nonexistent_profile")
    assert "error" in result

def test_get_full_interview_set_returns_6_questions(generator):
    result = generator.get_full_interview_set("fresher_technical")
    assert len(result) == 6

def test_full_interview_set_covers_all_categories(generator):
    result = generator.get_full_interview_set("experienced_nontechnical")
    categories = {q["category"] for q in result}
    assert categories == set(HR_INTERVIEW_CATEGORIES.keys())

def test_fresher_and_experienced_questions_differ(generator):
    fresher = generator.get_question("career_journey", "fresher_technical")
    experienced = generator.get_question("career_journey", "experienced_technical")
    assert fresher["question_text"] != experienced["question_text"]

def test_technical_and_nontechnical_questions_differ(generator):
    technical = generator.get_question("strengths_weaknesses", "fresher_technical")
    nontechnical = generator.get_question("strengths_weaknesses", "fresher_nontechnical")
    assert technical["question_text"] != nontechnical["question_text"]

def test_get_all_role_profiles_returns_4(generator):
    profiles = generator.get_all_role_profiles()
    assert len(profiles) == 4

def test_get_all_categories_returns_6(generator):
    categories = generator.get_all_categories()
    assert len(categories) == 6


# ── InterviewStateManager Tests ───────────────────────────────────────────────

def test_manager_creates_instance(manager):
    assert manager is not None
    assert manager.session_id == "SESS-TEST"

def test_create_question_state_returns_dict(manager):
    state = manager.create_question_state("self_introduction", "Tell me about yourself.")
    assert isinstance(state, dict)

def test_create_question_state_has_all_fields(manager):
    state = manager.create_question_state("career_journey", "Walk me through your career.")
    for field in QUESTION_STATE_FIELDS:
        assert field in state

def test_question_id_format(manager):
    state = manager.create_question_state("self_introduction", "Tell me about yourself.")
    assert state["question_id"].startswith("Q-")

def test_multiple_states_get_unique_ids(manager):
    s1 = manager.create_question_state("self_introduction", "Q1")
    s2 = manager.create_question_state("career_journey", "Q2")
    assert s1["question_id"] != s2["question_id"]

def test_record_response_updates_state(manager):
    state = manager.create_question_state("strengths_weaknesses", "What are your strengths?")
    updated = manager.record_response(state["question_id"], "I am very detail-oriented and a fast learner.")
    assert updated["response_captured"] == "I am very detail-oriented and a fast learner."

def test_record_response_calculates_word_count(manager):
    state = manager.create_question_state("career_goals", "What are your goals?")
    updated = manager.record_response(state["question_id"], "I want to become a senior engineer.")
    assert updated["response_word_count"] == 7

def test_short_response_triggers_follow_up(manager):
    state = manager.create_question_state("teamwork_culture_fit", "Tell me about teamwork.")
    updated = manager.record_response(state["question_id"], "I work well with others.")
    assert updated["follow_up_eligible"] == True

def test_long_response_does_not_trigger_follow_up(manager):
    state = manager.create_question_state("career_journey", "Walk me through your career.")
    long_response = " ".join(["word"] * 30)
    updated = manager.record_response(state["question_id"], long_response)
    assert updated["follow_up_eligible"] == False

def test_vague_response_triggers_follow_up(manager):
    state = manager.create_question_state("strengths_weaknesses", "What is your weakness?")
    vague = " ".join(["word"] * 25) + " maybe I think so"
    updated = manager.record_response(state["question_id"], vague)
    assert updated["follow_up_eligible"] == True

def test_invalid_question_id_returns_error(manager):
    result = manager.record_response("INVALID-ID", "Some response")
    assert "error" in result

def test_get_session_summary_has_required_fields(manager):
    manager.create_question_state("self_introduction", "Tell me about yourself.")
    summary = manager.get_session_summary()
    for field in ["session_id", "candidate_name", "role_profile", "questions_asked",
                  "follow_ups_eligible", "question_states", "generated_at"]:
        assert field in summary

def test_session_summary_counts_questions_correctly(manager):
    manager.create_question_state("self_introduction", "Q1")
    manager.create_question_state("career_journey", "Q2")
    summary = manager.get_session_summary()
    assert summary["questions_asked"] == 2


# ── InterviewFlowDesigner Tests ───────────────────────────────────────────────

def test_designer_creates_instance(designer):
    assert designer is not None

def test_get_phase_flow_returns_4_phases(designer):
    phases = designer.get_phase_flow()
    assert len(phases) == 4

def test_phases_are_ordered(designer):
    phases = designer.get_phase_flow()
    orders = [p["order"] for p in phases]
    assert orders == sorted(orders)

def test_introduction_is_first_phase(designer):
    phases = designer.get_phase_flow()
    assert phases[0]["phase"] == "introduction"

def test_closing_is_last_phase(designer):
    phases = designer.get_phase_flow()
    assert phases[-1]["phase"] == "closing"

def test_generate_flow_document_returns_dict(designer):
    doc = designer.generate_flow_document("fresher_technical")
    assert isinstance(doc, dict)

def test_flow_document_has_required_fields(designer):
    doc = designer.generate_flow_document("experienced_technical")
    for field in ["document_title", "role_profile", "role_label", "total_questions",
                  "phase_flow", "question_set", "state_fields", "categories", "generated_at"]:
        assert field in doc

def test_flow_document_has_6_questions(designer):
    doc = designer.generate_flow_document("fresher_nontechnical")
    assert doc["total_questions"] == 6

def test_get_architecture_summary_has_required_fields(designer):
    arch = designer.get_architecture_summary()
    for field in ["total_categories", "total_phases", "total_role_profiles",
                  "questions_per_profile", "total_questions_in_bank", "follow_up_questions"]:
        assert field in arch

def test_architecture_has_6_categories(designer):
    arch = designer.get_architecture_summary()
    assert arch["total_categories"] == 6

def test_architecture_has_4_phases(designer):
    arch = designer.get_architecture_summary()
    assert arch["total_phases"] == 4

def test_architecture_has_4_role_profiles(designer):
    arch = designer.get_architecture_summary()
    assert arch["total_role_profiles"] == 4

def test_architecture_has_24_questions_in_bank(designer):
    arch = designer.get_architecture_summary()
    assert arch["total_questions_in_bank"] == 24


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_hr_interview_categories_has_6():
    assert len(HR_INTERVIEW_CATEGORIES) == 6

def test_each_category_has_required_fields():
    for key, cat in HR_INTERVIEW_CATEGORIES.items():
        for field in ["label", "description", "order", "phase"]:
            assert field in cat

def test_category_orders_are_unique():
    orders = [cat["order"] for cat in HR_INTERVIEW_CATEGORIES.values()]
    assert len(orders) == len(set(orders))

def test_role_profiles_has_4():
    assert len(ROLE_PROFILES) == 4

def test_role_profiles_cover_fresher_and_experienced():
    keys = list(ROLE_PROFILES.keys())
    assert any("fresher" in k for k in keys)
    assert any("experienced" in k for k in keys)

def test_role_profiles_cover_technical_and_nontechnical():
    keys = list(ROLE_PROFILES.keys())
    assert any("technical" in k and "non" not in k for k in keys)
    assert any("nontechnical" in k for k in keys)

def test_conversation_phases_has_4():
    assert len(CONVERSATION_PHASES) == 4

def test_question_state_fields_not_empty():
    assert len(QUESTION_STATE_FIELDS) > 0

def test_question_bank_covers_all_categories():
    for category in HR_INTERVIEW_CATEGORIES:
        assert category in QUESTION_BANK

def test_question_bank_has_follow_up_per_category():
    for category in QUESTION_BANK:
        assert "follow_up" in QUESTION_BANK[category]
