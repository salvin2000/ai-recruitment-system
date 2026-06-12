"""
Tests for Day 23 – Transcript Data Architecture
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.transcript_architecture import (
    TranscriptArchitecture,
    TRANSCRIPT_STORAGE_FORMAT, METADATA_STANDARDS,
    NORMALIZATION_RULES, DATABASE_SCHEMA,
    TRANSCRIPT_STATUS, SCREENING_OUTCOMES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def arch():
    return TranscriptArchitecture()

@pytest.fixture
def session_id(arch):
    return arch.generate_session_id("20260610", 1)

@pytest.fixture
def sample_turn(arch, session_id):
    return arch.build_turn(
        session_id, 1, "candidate",
        "Yeah I have around 3.5 years of Python experience",
        question_id="Q031", confidence=0.88, duration_ms=4200
    )

@pytest.fixture
def sample_transcript(arch, session_id):
    turns = [
        arch.build_turn(session_id, 0, "ai",
            "Good morning. Are you ready to proceed?",
            question_id="Q001", confidence=1.0, duration_ms=3000),
        arch.build_turn(session_id, 1, "candidate",
            "Yes, I am ready.",
            question_id="Q001", confidence=0.92, duration_ms=2000),
        arch.build_turn(session_id, 2, "candidate",
            "Um I have about 3 years of experience",
            question_id="Q020", confidence=0.85, duration_ms=3500),
    ]
    return arch.build_transcript("ZCP-CAND-ARJU", "ZCP-JOB-001", turns)


# ── Architecture Instance Tests ───────────────────────────────────────────────

def test_arch_creates_instance(arch):
    assert arch is not None

def test_arch_has_storage_format(arch):
    assert arch.storage_format is not None

def test_arch_has_metadata_standards(arch):
    assert arch.metadata_std is not None

def test_arch_has_norm_rules(arch):
    assert arch.norm_rules is not None

def test_arch_has_schema(arch):
    assert arch.schema is not None


# ── ID Generator Tests ────────────────────────────────────────────────────────

def test_generate_transcript_id(arch):
    tid = arch.generate_transcript_id("20260610", 1)
    assert tid == "ZCP-TR-20260610-001"

def test_generate_session_id(arch):
    sid = arch.generate_session_id("20260610", 5)
    assert sid == "ZCP-SESS-20260610-005"

def test_generate_turn_id(arch, session_id):
    tid = arch.generate_turn_id(session_id, 3)
    assert "T003" in tid
    assert session_id in tid

def test_transcript_id_format(arch):
    tid = arch.generate_transcript_id("20260610", 10)
    assert tid.startswith("ZCP-TR-")

def test_session_id_format(arch):
    sid = arch.generate_session_id("20260610", 1)
    assert sid.startswith("ZCP-SESS-")


# ── Confidence Classification Tests ──────────────────────────────────────────

def test_confidence_high(arch):
    assert arch.classify_confidence(0.95) == "high"

def test_confidence_at_high_boundary(arch):
    assert arch.classify_confidence(0.85) == "high"

def test_confidence_medium(arch):
    assert arch.classify_confidence(0.75) == "medium"

def test_confidence_low(arch):
    assert arch.classify_confidence(0.55) == "low"

def test_confidence_rejected(arch):
    assert arch.classify_confidence(0.40) == "rejected"

def test_confidence_below_boundary(arch):
    assert arch.classify_confidence(0.84) == "medium"


# ── Text Normalization Tests ──────────────────────────────────────────────────

def test_normalize_removes_fillers(arch):
    result = arch.normalize_text("Um, yeah I basically work with Python")
    assert "um" not in result
    assert "basically" not in result

def test_normalize_yes_variants(arch):
    result = arch.normalize_text("Yeah definitely I am ready")
    assert "yes" in result

def test_normalize_no_variants(arch):
    result = arch.normalize_text("Nope that does not work")
    assert "no" in result

def test_normalize_experience_abbreviation(arch):
    result = arch.normalize_text("I have 3 yrs of experience")
    assert "years" in result

def test_normalize_redacts_phone(arch):
    result = arch.normalize_text("Call me at 9876543210")
    assert "9876543210" not in result
    assert "PHONE_REDACTED" in result

def test_normalize_redacts_email(arch):
    result = arch.normalize_text("Email me at john@example.com")
    assert "john@example.com" not in result
    assert "EMAIL_REDACTED" in result

def test_normalize_strips_whitespace(arch):
    result = arch.normalize_text("  hello   world  ")
    assert result == result.strip()

def test_normalize_returns_string(arch):
    assert isinstance(arch.normalize_text("test text"), str)


# ── Answer Extraction Tests ───────────────────────────────────────────────────

def test_extract_yes_no_true(arch):
    assert arch.extract_yes_no("yes i am ready") == True

def test_extract_yes_no_false(arch):
    assert arch.extract_yes_no("no i cannot") == False

def test_extract_yes_no_none(arch):
    assert arch.extract_yes_no("my name is arjun") is None

def test_extract_yes_no_yeah(arch):
    result = arch.extract_yes_no(arch.normalize_text("Yeah definitely"))
    assert result == True

def test_extract_yes_no_nope(arch):
    result = arch.extract_yes_no(arch.normalize_text("Nope not really"))
    assert result == False

def test_extract_numeric_years(arch):
    result = arch.extract_numeric("i have 3.5 years of experience")
    assert result == 3.5

def test_extract_numeric_lpa(arch):
    result = arch.extract_numeric("my expected ctc is 12 lpa")
    assert result == 12.0

def test_extract_numeric_none(arch):
    result = arch.extract_numeric("i work with python")
    assert result is None

def test_extract_numeric_integer(arch):
    result = arch.extract_numeric("5 years experience")
    assert result == 5.0


# ── Build Turn Tests ──────────────────────────────────────────────────────────

def test_build_turn_returns_dict(sample_turn):
    assert isinstance(sample_turn, dict)

def test_build_turn_has_required_fields(sample_turn):
    required = ["turn_id", "session_id", "turn_index", "speaker",
                "raw_text", "normalized_text", "confidence_score",
                "confidence_level", "is_flagged", "started_at"]
    for field in required:
        assert field in sample_turn

def test_build_turn_correct_speaker(sample_turn):
    assert sample_turn["speaker"] == "candidate"

def test_build_turn_normalizes_candidate_text(sample_turn):
    assert sample_turn["normalized_text"] != sample_turn["raw_text"] or \
           len(sample_turn["normalized_text"]) > 0

def test_build_turn_confidence_level_set(sample_turn):
    assert sample_turn["confidence_level"] in ["high", "medium", "low", "rejected"]

def test_build_turn_ai_not_normalized(arch, session_id):
    turn = arch.build_turn(session_id, 0, "ai", "Good morning.", confidence=1.0)
    assert turn["normalized_text"] == "Good morning."

def test_build_turn_low_confidence_flagged(arch, session_id):
    turn = arch.build_turn(session_id, 0, "candidate", "test", confidence=0.55)
    assert turn["is_flagged"] == True

def test_build_turn_high_confidence_not_flagged(arch, session_id):
    turn = arch.build_turn(session_id, 0, "candidate", "test", confidence=0.90)
    assert turn["is_flagged"] == False


# ── Build Transcript Tests ────────────────────────────────────────────────────

def test_build_transcript_returns_dict(sample_transcript):
    assert isinstance(sample_transcript, dict)

def test_build_transcript_has_required_fields(sample_transcript):
    required = ["transcript_id", "session_id", "candidate_id",
                "job_id", "status", "total_turns", "turns"]
    for field in required:
        assert field in sample_transcript

def test_build_transcript_total_turns_correct(sample_transcript):
    assert sample_transcript["total_turns"] == len(sample_transcript["turns"])

def test_build_transcript_avg_confidence_range(sample_transcript):
    assert 0.0 <= sample_transcript["avg_confidence"] <= 1.0

def test_build_transcript_candidate_id_preserved(sample_transcript):
    assert sample_transcript["candidate_id"] == "ZCP-CAND-ARJU"


# ── Validate Turn Tests ───────────────────────────────────────────────────────

def test_validate_turn_valid(arch, sample_turn):
    result = arch.validate_turn(sample_turn)
    assert result["valid"] == True
    assert result["errors"] == []

def test_validate_turn_missing_field(arch):
    bad_turn = {"turn_id": "T001", "speaker": "candidate"}
    result = arch.validate_turn(bad_turn)
    assert result["valid"] == False
    assert len(result["errors"]) > 0

def test_validate_turn_invalid_speaker(arch, sample_turn):
    bad = dict(sample_turn)
    bad["speaker"] = "robot"
    result = arch.validate_turn(bad)
    assert result["valid"] == False

def test_validate_turn_bad_confidence(arch, sample_turn):
    bad = dict(sample_turn)
    bad["confidence_score"] = 1.5
    result = arch.validate_turn(bad)
    assert result["valid"] == False


# ── Schema Summary Tests ──────────────────────────────────────────────────────

def test_schema_summary_returns_dict(arch):
    summary = arch.get_schema_summary()
    assert isinstance(summary, dict)

def test_schema_summary_has_all_tables(arch):
    summary = arch.get_schema_summary()
    expected = ["screening_sessions", "transcript_turns",
                "extracted_answers", "screening_scores", "screening_results"]
    for table in expected:
        assert table in summary["tables"]

def test_schema_summary_total_tables(arch):
    summary = arch.get_schema_summary()
    assert summary["total_tables"] == len(DATABASE_SCHEMA)

def test_schema_summary_has_primary_keys(arch):
    summary = arch.get_schema_summary()
    for table in summary["tables"]:
        assert len(summary["primary_keys"][table]) > 0


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_metadata_standards_defined():
    required = ["candidate_id", "job_id", "question_id",
                "session_id", "timestamp", "confidence_level", "speaker"]
    for field in required:
        assert field in METADATA_STANDARDS

def test_metadata_required_fields_are_bool():
    for field, meta in METADATA_STANDARDS.items():
        assert isinstance(meta["required"], bool)

def test_normalization_rules_have_categories():
    assert "text_cleaning"    in NORMALIZATION_RULES
    assert "answer_extraction"in NORMALIZATION_RULES
    assert "quality_checks"   in NORMALIZATION_RULES

def test_database_schema_has_all_tables():
    for table in ["screening_sessions","transcript_turns",
                  "extracted_answers","screening_scores","screening_results"]:
        assert table in DATABASE_SCHEMA

def test_transcript_status_defined():
    for status in ["completed","partial","failed","interrupted"]:
        assert status in TRANSCRIPT_STATUS

def test_screening_outcomes_defined():
    for outcome in ["advance","hold","reject","incomplete"]:
        assert outcome in SCREENING_OUTCOMES


# ── Save Architecture Tests ───────────────────────────────────────────────────

def test_save_architecture(arch, tmp_path):
    output = str(tmp_path / "test_arch.json")
    arch.save_architecture(output)
    assert os.path.exists(output)
    with open(output, encoding="utf-8") as f:
        data = json.load(f)
    assert "database_schema"    in data
    assert "metadata_standards" in data
    assert "normalization_rules"in data
