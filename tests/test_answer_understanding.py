"""
Tests for Day 25 – Answer Intent & Understanding Engine
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.answer_understanding import (
    AnswerUnderstandingEngine, IntentClassifier, AnswerExtractor,
    INTENT_CATEGORIES, INTENT_SIGNALS, VAGUE_PATTERNS,
    OFF_TOPIC_SIGNALS, ANSWER_SCHEMA, EXTRACTION_RULES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return AnswerUnderstandingEngine()

@pytest.fixture
def classifier():
    return IntentClassifier()

@pytest.fixture
def extractor():
    return AnswerExtractor()

EXPERIENCE_TEXT   = "I have around 3.5 years of experience with Python."
SALARY_TEXT       = "My current CTC is 8 LPA and I expect 12 to 13 LPA."
NOTICE_TEXT       = "I have a 30 day notice period."
SKILLS_TEXT       = "I mainly work with Python, Django, AWS, and Docker."
LOCATION_TEXT     = "I am currently based in Bangalore."
YES_TEXT          = "Yes, I am comfortable with this."
NO_TEXT           = "No, I cannot relocate at this time."
VAGUE_TEXT        = "I don't know."
OFF_TOPIC_TEXT    = "I love cricket and the IPL."
IMMEDIATE_TEXT    = "I can join immediately, no notice period."
RATING_TEXT       = "I would rate myself 4 out of 5 in Python."
MONTH_NOTICE_TEXT = "My notice period is 2 months."


# ── IntentClassifier Instance Tests ──────────────────────────────────────────

def test_classifier_creates_instance(classifier):
    assert classifier is not None

def test_classifier_has_signals(classifier):
    assert len(classifier.signals) > 0

def test_classifier_has_categories(classifier):
    assert len(classifier.categories) > 0


# ── Intent Classification Tests ───────────────────────────────────────────────

def test_classify_returns_dict(classifier):
    result = classifier.classify(EXPERIENCE_TEXT)
    assert isinstance(result, dict)

def test_classify_has_required_fields(classifier):
    result = classifier.classify(EXPERIENCE_TEXT)
    assert "primary_intent"  in result
    assert "sub_intents"     in result
    assert "intent_scores"   in result
    assert "is_vague"        in result
    assert "is_off_topic"    in result

def test_classify_experience_intent(classifier):
    result = classifier.classify(EXPERIENCE_TEXT)
    assert result["primary_intent"] == "experience_info"

def test_classify_salary_intent(classifier):
    result = classifier.classify(SALARY_TEXT)
    assert result["primary_intent"] == "salary_info"

def test_classify_affirmative(classifier):
    result = classifier.classify("Yes definitely, I am ready.")
    assert result["primary_intent"] == "affirmative"

def test_classify_negative(classifier):
    result = classifier.classify("No, I cannot do that.")
    assert result["primary_intent"] == "negative"

def test_classify_skill_info(classifier):
    result = classifier.classify(SKILLS_TEXT)
    assert result["primary_intent"] == "skill_info"

def test_classify_location_info(classifier):
    result = classifier.classify(LOCATION_TEXT)
    assert result["primary_intent"] == "location_info"

def test_classify_vague(classifier):
    result = classifier.classify(VAGUE_TEXT)
    assert result["is_vague"] == True
    assert result["primary_intent"] == "vague"

def test_classify_off_topic(classifier):
    result = classifier.classify(OFF_TOPIC_TEXT)
    assert result["is_off_topic"] == True
    assert result["primary_intent"] == "off_topic"

def test_classify_unknown(classifier):
    result = classifier.classify("blah blah blah xyz")
    assert result["primary_intent"] in ("unknown", "vague")

def test_classify_sub_intents_list(classifier):
    result = classifier.classify(EXPERIENCE_TEXT)
    assert isinstance(result["sub_intents"], list)

def test_is_vague_short_text(classifier):
    assert classifier.is_vague("Maybe.") == True

def test_is_vague_clear_text(classifier):
    assert classifier.is_vague(EXPERIENCE_TEXT) == False

def test_is_off_topic_cricket(classifier):
    assert classifier.is_off_topic(OFF_TOPIC_TEXT) == True

def test_is_off_topic_clear(classifier):
    assert classifier.is_off_topic(EXPERIENCE_TEXT) == False


# ── Experience Extraction Tests ───────────────────────────────────────────────

def test_extract_experience_years(extractor):
    result = extractor.extract_experience(EXPERIENCE_TEXT)
    assert result == 3.5

def test_extract_experience_around(extractor):
    result = extractor.extract_experience("I have around 5 years of experience.")
    assert result == 5.0

def test_extract_experience_none(extractor):
    result = extractor.extract_experience("I work with Python.")
    assert result is None

def test_extract_experience_integer(extractor):
    result = extractor.extract_experience("I have 4 years experience.")
    assert result == 4.0


# ── Salary Extraction Tests ───────────────────────────────────────────────────

def test_extract_salary_lpa(extractor):
    result = extractor.extract_salary("My CTC is 8 LPA.")
    assert result == 8.0

def test_extract_salary_lakhs(extractor):
    result = extractor.extract_salary("I earn 10 lakhs per annum.")
    assert result == 10.0

def test_extract_salary_none(extractor):
    result = extractor.extract_salary("I work with Python.")
    assert result is None

def test_extract_salary_decimal(extractor):
    result = extractor.extract_salary("My expected CTC is 12.5 LPA.")
    assert result == 12.5


# ── Notice Period Extraction Tests ───────────────────────────────────────────

def test_extract_notice_days(extractor):
    result = extractor.extract_notice_period(NOTICE_TEXT)
    assert result["value"] == 30
    assert result["unit"] == "days"

def test_extract_notice_months(extractor):
    result = extractor.extract_notice_period(MONTH_NOTICE_TEXT)
    assert result["unit"] == "days"
    assert result["value"] == 60

def test_extract_notice_immediate(extractor):
    result = extractor.extract_notice_period(IMMEDIATE_TEXT)
    assert result["value"] == 0

def test_extract_notice_empty(extractor):
    result = extractor.extract_notice_period("I work with Python.")
    assert result == {}


# ── Skills Extraction Tests ───────────────────────────────────────────────────

def test_extract_skills_multiple(extractor):
    result = extractor.extract_skills(SKILLS_TEXT)
    assert "python" in result
    assert "django" in result
    assert "aws"    in result
    assert "docker" in result

def test_extract_skills_empty(extractor):
    result = extractor.extract_skills("I enjoy reading books.")
    assert result == []

def test_extract_skills_returns_list(extractor):
    result = extractor.extract_skills(SKILLS_TEXT)
    assert isinstance(result, list)

def test_extract_skills_no_duplicates(extractor):
    result = extractor.extract_skills("Python python PYTHON")
    assert len(result) == len(set(result))


# ── Rating Extraction Tests ───────────────────────────────────────────────────

def test_extract_rating_out_of_5(extractor):
    result = extractor.extract_rating(RATING_TEXT)
    assert result == 4

def test_extract_rating_none(extractor):
    result = extractor.extract_rating("I work with Python.")
    assert result is None

def test_extract_rating_range(extractor):
    result = extractor.extract_rating("I rate myself 3 out of 5.")
    assert 1 <= result <= 5


# ── Location Extraction Tests ─────────────────────────────────────────────────

def test_extract_location_bangalore(extractor):
    result = extractor.extract_location(LOCATION_TEXT)
    assert result is not None
    assert "bangalore" in result.lower()

def test_extract_location_none(extractor):
    result = extractor.extract_location("I work with Python.")
    assert result is None


# ── Yes/No Extraction Tests ───────────────────────────────────────────────────

def test_extract_yes(extractor):
    assert extractor.extract_yes_no(YES_TEXT) == True

def test_extract_no(extractor):
    assert extractor.extract_yes_no(NO_TEXT) == False

def test_extract_yes_no_none(extractor):
    assert extractor.extract_yes_no("I work with Python.") is None


# ── extract_all Tests ─────────────────────────────────────────────────────────

def test_extract_all_returns_dict(extractor):
    result = extractor.extract_all(EXPERIENCE_TEXT, "numeric")
    assert isinstance(result, dict)

def test_extract_all_experience(extractor):
    result = extractor.extract_all(EXPERIENCE_TEXT, "numeric")
    assert "experience_years" in result

def test_extract_all_salary(extractor):
    result = extractor.extract_all(SALARY_TEXT, "numeric")
    assert "salary_lpa" in result

def test_extract_all_yes_no(extractor):
    result = extractor.extract_all(YES_TEXT, "yes_no")
    assert "boolean_value" in result
    assert result["boolean_value"] == True

def test_extract_all_skills(extractor):
    result = extractor.extract_all(SKILLS_TEXT, "text")
    assert "skills_mentioned" in result

def test_extract_all_empty_text(extractor):
    result = extractor.extract_all("", "text")
    assert isinstance(result, dict)


# ── Full Engine understand() Tests ───────────────────────────────────────────

def test_understand_returns_dict(engine):
    result = engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.91
    )
    assert isinstance(result, dict)

def test_understand_has_required_fields(engine):
    result = engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.91
    )
    required = ["answer_id","session_id","question_id","intent",
                "extracted","is_valid","is_vague","is_off_topic",
                "needs_followup","word_count","confidence"]
    for field in required:
        assert field in result

def test_understand_valid_answer(engine):
    result = engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.91
    )
    assert result["is_valid"] == True

def test_understand_vague_invalid(engine):
    result = engine.understand(
        VAGUE_TEXT, VAGUE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.91
    )
    assert result["is_vague"] == True
    assert result["is_valid"] == False

def test_understand_off_topic(engine):
    result = engine.understand(
        OFF_TOPIC_TEXT, OFF_TOPIC_TEXT,
        "Q020", "experience", "numeric", "SESS-001", 0.95
    )
    assert result["is_off_topic"] == True

def test_understand_low_confidence_invalid(engine):
    result = engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.40
    )
    assert result["is_valid"] == False

def test_understand_answer_id_format(engine):
    result = engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "SESS-001", 0.91
    )
    assert "Q031" in result["answer_id"]

def test_understand_batch_returns_list(engine):
    turns = [
        {"raw_text": EXPERIENCE_TEXT, "clean_text": EXPERIENCE_TEXT,
         "question_id": "Q031", "question_category": "skills",
         "answer_type": "numeric", "session_id": "S1", "confidence": 0.9},
        {"raw_text": YES_TEXT, "clean_text": YES_TEXT,
         "question_id": "Q041", "question_category": "location",
         "answer_type": "yes_no", "session_id": "S1", "confidence": 0.9},
    ]
    results = engine.understand_batch(turns)
    assert isinstance(results, list)
    assert len(results) == 2


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_intent_categories_defined():
    expected = ["affirmative","negative","experience_info","skill_info",
                "availability","salary_info","education_info",
                "location_info","off_topic","vague","unknown"]
    for cat in expected:
        assert cat in INTENT_CATEGORIES

def test_intent_signals_cover_categories():
    for cat in ["affirmative","negative","experience_info","skill_info",
                "availability","salary_info"]:
        assert cat in INTENT_SIGNALS
        assert len(INTENT_SIGNALS[cat]) > 0

def test_extraction_rules_defined():
    for rule in ["experience_years","salary_lpa","notice_days","skill_rating"]:
        assert rule in EXTRACTION_RULES

def test_extraction_rules_have_patterns():
    for key, rule in EXTRACTION_RULES.items():
        assert "patterns" in rule
        assert len(rule["patterns"]) > 0

def test_answer_schema_fields():
    for field in ["answer_id","session_id","question_id","intent",
                  "extracted","is_valid","is_vague","is_off_topic"]:
        assert field in ANSWER_SCHEMA

def test_save_results(engine, tmp_path):
    results = [engine.understand(
        EXPERIENCE_TEXT, EXPERIENCE_TEXT,
        "Q031", "skills", "numeric", "S1", 0.91
    )]
    output = str(tmp_path / "test_answers.json")
    engine.save_results(results, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert len(data) == 1
    assert "intent" in data[0]
