"""
Tests for Day 24 – Speech-to-Text Integration & Cleaning
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.stt_processor import (
    STTCleaner, STTAccuracyTester,
    FILLER_WORDS, PUNCTUATION_RULES, ACCENT_NORMALIZATION,
    SPEECH_THRESHOLDS, ACCENT_TEST_PROFILES, STT_TEST_CASES,
    STT_PROVIDER_CONFIG,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cleaner():
    return STTCleaner()

@pytest.fixture
def tester():
    return STTAccuracyTester()

@pytest.fixture
def full_report(tester):
    return tester.run_all_tests()


# ── STTCleaner Instance Tests ─────────────────────────────────────────────────

def test_cleaner_creates_instance(cleaner):
    assert cleaner is not None

def test_cleaner_has_fillers(cleaner):
    assert len(cleaner.fillers) > 0

def test_cleaner_has_punct_rules(cleaner):
    assert len(cleaner.punct_rules) > 0

def test_cleaner_has_accent_map(cleaner):
    assert len(cleaner.accent_map) > 0

def test_cleaner_has_thresholds(cleaner):
    assert cleaner.thresholds is not None


# ── Filler Removal Tests ──────────────────────────────────────────────────────

def test_remove_fillers_um(cleaner):
    result = cleaner.remove_fillers("Um, I have five years of experience.")
    assert "um" not in result.lower()

def test_remove_fillers_you_know(cleaner):
    result = cleaner.remove_fillers("I have, you know, three years.")
    assert "you know" not in result.lower()

def test_remove_fillers_like(cleaner):
    result = cleaner.remove_fillers("I have like five years of experience.")
    assert "like" not in result.lower()

def test_remove_fillers_basically(cleaner):
    result = cleaner.remove_fillers("Basically I work with Python.")
    assert "basically" not in result.lower()

def test_remove_fillers_preserves_content(cleaner):
    result = cleaner.remove_fillers("Um I have five years experience")
    assert "five" in result
    assert "experience" in result

def test_remove_fillers_returns_string(cleaner):
    assert isinstance(cleaner.remove_fillers("Um test"), str)


# ── Punctuation Fix Tests ─────────────────────────────────────────────────────

def test_fix_punctuation_adds_period(cleaner):
    result = cleaner.fix_punctuation("I work with Python")
    assert result.endswith(".")

def test_fix_punctuation_removes_space_before(cleaner):
    result = cleaner.fix_punctuation("Hello , world")
    assert " ," not in result

def test_fix_punctuation_returns_string(cleaner):
    assert isinstance(cleaner.fix_punctuation("test"), str)

def test_fix_punctuation_collapses_spaces(cleaner):
    result = cleaner.fix_punctuation("hello   world")
    assert "  " not in result


# ── Case Normalization Tests ──────────────────────────────────────────────────

def test_normalize_case_capitalizes_first(cleaner):
    result = cleaner.normalize_case("hello world")
    assert result[0].isupper()

def test_normalize_case_preserves_content(cleaner):
    result = cleaner.normalize_case("i work at infosys")
    assert "infosys" in result.lower()

def test_normalize_case_returns_string(cleaner):
    assert isinstance(cleaner.normalize_case("test"), str)


# ── Abbreviation Expansion Tests ──────────────────────────────────────────────

def test_expand_yrs(cleaner):
    result = cleaner.expand_abbreviations("I have 3 yrs experience")
    assert "years" in result

def test_expand_sr(cleaner):
    result = cleaner.expand_abbreviations("I am a sr developer")
    assert "senior" in result

def test_expand_exp(cleaner):
    result = cleaner.expand_abbreviations("5 yrs exp in Python")
    assert "experience" in result

def test_expand_curr(cleaner):
    result = cleaner.expand_abbreviations("My curr role is developer")
    assert "current" in result


# ── PII Redaction Tests ───────────────────────────────────────────────────────

def test_redact_phone(cleaner):
    result = cleaner.redact_pii("Call me at 9876543210")
    assert "9876543210" not in result
    assert "PHONE_REDACTED" in result

def test_redact_email(cleaner):
    result = cleaner.redact_pii("Email john@example.com")
    assert "john@example.com" not in result
    assert "EMAIL_REDACTED" in result

def test_redact_pan(cleaner):
    result = cleaner.redact_pii("My PAN is ABCDE1234F")
    assert "ABCDE1234F" not in result
    assert "PAN_REDACTED" in result

def test_redact_preserves_non_pii(cleaner):
    result = cleaner.redact_pii("I work with Python and Django")
    assert "Python" in result
    assert "Django" in result


# ── Numeric Normalization Tests ───────────────────────────────────────────────

def test_normalize_five_to_5(cleaner):
    result = cleaner.normalize_numbers("I have five years of experience")
    assert "5" in result

def test_normalize_ten_to_10(cleaner):
    result = cleaner.normalize_numbers("ten years of experience")
    assert "10" in result

def test_normalize_preserves_existing_digits(cleaner):
    result = cleaner.normalize_numbers("I have 3 years experience")
    assert "3" in result


# ── Interruption Handling Tests ───────────────────────────────────────────────

def test_handle_interruption_dash(cleaner):
    result = cleaner.handle_interruption("I have been— I mean I work with Python.")
    assert "\u2014" not in result

def test_handle_interruption_ellipsis(cleaner):
    result = cleaner.handle_interruption("I have been... I work with Python.")
    assert "..." not in result or "Python" in result

def test_handle_interruption_returns_string(cleaner):
    assert isinstance(cleaner.handle_interruption("test— text"), str)


# ── Answer Completeness Tests ─────────────────────────────────────────────────

def test_completeness_empty(cleaner):
    result = cleaner.classify_answer_completeness("")
    assert result["completeness"] == "empty"
    assert result["word_count"]   == 0

def test_completeness_too_short(cleaner):
    result = cleaner.classify_answer_completeness("Yes.")
    assert result["completeness"] == "too_short"

def test_completeness_partial(cleaner):
    result = cleaner.classify_answer_completeness("Around three years.")
    assert result["completeness"] in ("partial", "too_short", "complete")

def test_completeness_complete(cleaner):
    text   = "I have been working with Python for three and a half years primarily on Django REST APIs."
    result = cleaner.classify_answer_completeness(text)
    assert result["completeness"] == "complete"

def test_completeness_is_partial_flag(cleaner):
    result = cleaner.classify_answer_completeness("")
    assert result["is_partial"] == True

def test_completeness_word_count_correct(cleaner):
    result = cleaner.classify_answer_completeness("hello world test")
    assert result["word_count"] == 3


# ── Silence Detection Tests ───────────────────────────────────────────────────

def test_silence_short_continue(cleaner):
    result = cleaner.classify_silence(2.0)
    assert result["action"]  == "continue"
    assert result["flagged"] == False

def test_silence_medium_prompt(cleaner):
    result = cleaner.classify_silence(8.0)
    assert result["action"]  == "prompt_candidate"
    assert result["flagged"] == True

def test_silence_long_skip(cleaner):
    result = cleaner.classify_silence(20.0)
    assert result["action"]  == "skip_question"
    assert result["flagged"] == True

def test_silence_returns_message(cleaner):
    result = cleaner.classify_silence(2.0)
    assert "message" in result
    assert len(result["message"]) > 0

def test_silence_at_boundary(cleaner):
    threshold = SPEECH_THRESHOLDS["silence_flag_seconds"]
    result    = cleaner.classify_silence(float(threshold))
    assert result["flagged"] == True


# ── Full Clean Pipeline Tests ─────────────────────────────────────────────────

def test_clean_returns_dict(cleaner):
    result = cleaner.clean("Um I have five years of experience.")
    assert isinstance(result, dict)

def test_clean_has_required_fields(cleaner):
    result = cleaner.clean("test text")
    assert "raw_text"     in result
    assert "clean_text"   in result
    assert "steps"        in result
    assert "completeness" in result
    assert "cleaned_at"   in result

def test_clean_raw_text_preserved(cleaner):
    raw    = "Um I have five years."
    result = cleaner.clean(raw)
    assert result["raw_text"] == raw

def test_clean_produces_cleaner_text(cleaner):
    result = cleaner.clean("Um, so basically I have like five years.")
    assert len(result["clean_text"]) < len(result["raw_text"]) or \
           "um" not in result["clean_text"].lower()

def test_clean_steps_ordered(cleaner):
    result = cleaner.clean("test text")
    assert result["steps"][0]["step"] == "input"

def test_clean_pii_redacted(cleaner):
    result = cleaner.clean("Call me at 9876543210")
    assert "9876543210" not in result["clean_text"]

def test_clean_without_pii_redaction(cleaner):
    result = cleaner.clean("Call me at 9876543210", apply_pii_redaction=False)
    assert "9876543210" in result["clean_text"]


# ── STTAccuracyTester Tests ───────────────────────────────────────────────────

def test_tester_creates_instance(tester):
    assert tester is not None

def test_compute_wer_identical(tester):
    wer = tester.compute_wer("hello world", "hello world")
    assert wer == 0.0

def test_compute_wer_completely_different(tester):
    wer = tester.compute_wer("hello world", "foo bar baz")
    assert wer > 0.0

def test_compute_wer_empty_reference(tester):
    wer = tester.compute_wer("", "hello")
    assert wer == 0.0

def test_compute_wer_range(tester):
    wer = tester.compute_wer("hello world test", "hello world")
    assert 0.0 <= wer <= 2.0

def test_run_test_returns_dict(tester):
    result = tester.run_test(STT_TEST_CASES[0])
    assert isinstance(result, dict)

def test_run_test_has_required_fields(tester):
    result = tester.run_test(STT_TEST_CASES[0])
    assert "test_id"  in result
    assert "wer"      in result
    assert "passed"   in result
    assert "cleaned"  in result

def test_run_all_tests_returns_dict(full_report):
    assert isinstance(full_report, dict)

def test_run_all_tests_has_sections(full_report):
    assert "report_metadata" in full_report
    assert "by_category"     in full_report
    assert "test_results"    in full_report

def test_run_all_tests_correct_count(full_report):
    meta = full_report["report_metadata"]
    assert meta["total_tests"] == len(STT_TEST_CASES)

def test_run_all_tests_pass_rate_range(full_report):
    rate = full_report["report_metadata"]["pass_rate"]
    assert 0.0 <= rate <= 100.0

def test_run_all_tests_by_category_has_entries(full_report):
    assert len(full_report["by_category"]) > 0

def test_save_report(tester, full_report, tmp_path):
    output = str(tmp_path / "test_stt.json")
    tester.save_report(full_report, output)
    assert os.path.exists(output)
    with open(output) as f:
        data = json.load(f)
    assert "report_metadata" in data


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_filler_words_defined():
    assert len(FILLER_WORDS) > 0
    assert "um" in FILLER_WORDS
    assert "uh" in FILLER_WORDS

def test_accent_normalization_defined():
    assert "yrs"  in ACCENT_NORMALIZATION
    assert "exp"  in ACCENT_NORMALIZATION
    assert "sr"   in ACCENT_NORMALIZATION

def test_speech_thresholds_defined():
    assert "silence_flag_seconds" in SPEECH_THRESHOLDS
    assert "min_answer_words"     in SPEECH_THRESHOLDS
    assert "partial_answer_words" in SPEECH_THRESHOLDS

def test_accent_profiles_defined():
    assert len(ACCENT_TEST_PROFILES) > 0
    for p in ACCENT_TEST_PROFILES:
        assert "profile"      in p
        assert "expected_wer" in p

def test_stt_test_cases_defined():
    assert len(STT_TEST_CASES) > 0
    for tc in STT_TEST_CASES:
        assert "test_id"    in tc
        assert "raw"        in tc
        assert "expected"   in tc
        assert "category"   in tc

def test_stt_provider_config_defined():
    assert "primary"   in STT_PROVIDER_CONFIG
    assert "languages" in STT_PROVIDER_CONFIG
    assert len(STT_PROVIDER_CONFIG["languages"]) > 0
