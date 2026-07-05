"""
Tests for Day 35 - Communication Skill Evaluation
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.communication_evaluator import (
    FluencyAnalyzer, GrammarAnalyzer, VocabularyAnalyzer,
    ClarityAnalyzer, StructureAnalyzer, CommunicationScorer,
    FILLER_WORDS, SCORE_WEIGHTS, COMMUNICATION_BANDS,
    STRUCTURE_MARKERS, ADVANCED_VOCABULARY,
)

# ── Sample Responses ──────────────────────────────────────────────────────────

WEAK     = "Um yeah I like basically do stuff and things you know."
MODERATE = ("I work well with others. I try to communicate clearly and I think "
            "I am a good team player. I have done many projects.")
STRONG   = ("For example, when I led a team of 6 engineers, I implemented a "
            "structured communication framework that improved our delivery "
            "efficiency by 35% and reduced misalignment substantially.")
EMPTY    = ""
FILLER_HEAVY = "Um um uh like basically literally you know right so yeah."
STRUCTURED   = ("To begin, I prioritize clarity. For example, I implemented "
                "async documentation. Additionally, I ran weekly syncs. "
                "In summary, communication is central to my work.")


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def fluency():    return FluencyAnalyzer()
@pytest.fixture
def grammar():    return GrammarAnalyzer()
@pytest.fixture
def vocabulary(): return VocabularyAnalyzer()
@pytest.fixture
def clarity():    return ClarityAnalyzer()
@pytest.fixture
def structure():  return StructureAnalyzer()
@pytest.fixture
def scorer():     return CommunicationScorer()


# ── FluencyAnalyzer Tests ─────────────────────────────────────────────────────

def test_fluency_creates_instance(fluency):
    assert fluency is not None

def test_fluency_returns_dict(fluency):
    assert isinstance(fluency.analyze(MODERATE), dict)

def test_fluency_has_required_fields(fluency):
    result = fluency.analyze(MODERATE)
    for f in ["score", "avg_sentence_len", "sentence_count", "filler_count",
              "filler_density", "filler_words_found"]:
        assert f in result

def test_fluency_score_in_range(fluency):
    for text in [WEAK, MODERATE, STRONG]:
        assert 0 <= fluency.analyze(text)["score"] <= 100

def test_empty_response_scores_zero(fluency):
    assert fluency.analyze(EMPTY)["score"] == 0

def test_filler_words_detected(fluency):
    result = fluency.analyze(FILLER_HEAVY)
    assert result["filler_count"] > 3

def test_filler_density_calculated(fluency):
    result = fluency.analyze(FILLER_HEAVY)
    assert result["filler_density"] > 0

def test_strong_response_higher_fluency_than_weak(fluency):
    assert fluency.analyze(STRONG)["score"] >= fluency.analyze(WEAK)["score"]

def test_filler_words_found_is_list(fluency):
    result = fluency.analyze(WEAK)
    assert isinstance(result["filler_words_found"], list)


# ── GrammarAnalyzer Tests ─────────────────────────────────────────────────────

def test_grammar_creates_instance(grammar):
    assert grammar is not None

def test_grammar_returns_dict(grammar):
    assert isinstance(grammar.analyze(MODERATE), dict)

def test_grammar_has_required_fields(grammar):
    result = grammar.analyze(MODERATE)
    for f in ["score", "errors", "error_count", "error_rate"]:
        assert f in result

def test_grammar_score_in_range(grammar):
    for text in [WEAK, MODERATE, STRONG]:
        assert 0 <= grammar.analyze(text)["score"] <= 100

def test_grammar_error_detected(grammar):
    result = grammar.analyze("he don't understand the concept")
    assert result["error_count"] >= 1

def test_clean_response_gets_high_grammar_score(grammar):
    result = grammar.analyze(STRONG)
    assert result["score"] >= 70

def test_empty_grammar_scores_zero(grammar):
    assert grammar.analyze(EMPTY)["score"] == 0


# ── VocabularyAnalyzer Tests ──────────────────────────────────────────────────

def test_vocabulary_creates_instance(vocabulary):
    assert vocabulary is not None

def test_vocabulary_returns_dict(vocabulary):
    assert isinstance(vocabulary.analyze(MODERATE), dict)

def test_vocabulary_has_required_fields(vocabulary):
    result = vocabulary.analyze(MODERATE)
    for f in ["score", "advanced_words", "simple_words",
              "unique_word_count", "total_word_count", "diversity_ratio"]:
        assert f in result

def test_vocabulary_score_in_range(vocabulary):
    for text in [WEAK, MODERATE, STRONG]:
        assert 0 <= vocabulary.analyze(text)["score"] <= 100

def test_advanced_words_detected_in_strong(vocabulary):
    result = vocabulary.analyze(STRONG)
    assert len(result["advanced_words"]) > 0

def test_diversity_ratio_between_0_and_1(vocabulary):
    result = vocabulary.analyze(MODERATE)
    assert 0 <= result["diversity_ratio"] <= 1

def test_strong_response_higher_vocab_than_weak(vocabulary):
    assert vocabulary.analyze(STRONG)["score"] >= vocabulary.analyze(WEAK)["score"]


# ── ClarityAnalyzer Tests ─────────────────────────────────────────────────────

def test_clarity_creates_instance(clarity):
    assert clarity is not None

def test_clarity_returns_dict(clarity):
    assert isinstance(clarity.analyze(MODERATE), dict)

def test_clarity_has_required_fields(clarity):
    result = clarity.analyze(MODERATE)
    for f in ["score", "has_example", "has_context", "has_specifics", "on_topic"]:
        assert f in result

def test_clarity_score_in_range(clarity):
    for text in [WEAK, MODERATE, STRONG]:
        assert 0 <= clarity.analyze(text)["score"] <= 100

def test_example_detected_in_strong(clarity):
    result = clarity.analyze(STRONG)
    assert result["has_example"] == True

def test_no_example_in_weak(clarity):
    result = clarity.analyze(WEAK)
    assert result["has_example"] == False

def test_on_topic_when_keyword_matches(clarity):
    result = clarity.analyze("I led a team and implemented a framework", ["team", "framework"])
    assert result["on_topic"] == True

def test_off_topic_when_no_keyword_matches(clarity):
    result = clarity.analyze("I like to cook pasta on weekends", ["engineering", "software"])
    assert result["on_topic"] == False


# ── StructureAnalyzer Tests ───────────────────────────────────────────────────

def test_structure_creates_instance(structure):
    assert structure is not None

def test_structure_returns_dict(structure):
    assert isinstance(structure.analyze(MODERATE), dict)

def test_structure_has_required_fields(structure):
    result = structure.analyze(MODERATE)
    for f in ["score", "layers_found", "markers_found"]:
        assert f in result

def test_structure_score_in_range(structure):
    for text in [WEAK, MODERATE, STRUCTURED]:
        assert 0 <= structure.analyze(text)["score"] <= 100

def test_structured_response_has_high_structure_score(structure):
    result = structure.analyze(STRUCTURED)
    assert result["layers_found"] >= 3

def test_weak_response_has_low_structure_score(structure):
    result = structure.analyze(WEAK)
    assert result["score"] <= 25

def test_markers_found_is_dict(structure):
    result = structure.analyze(STRUCTURED)
    assert isinstance(result["markers_found"], dict)


# ── CommunicationScorer Tests ────────────────────────────────────────────────

def test_scorer_creates_instance(scorer):
    assert scorer is not None

def test_score_returns_dict(scorer):
    assert isinstance(scorer.score(MODERATE), dict)

def test_score_has_required_fields(scorer):
    result = scorer.score(MODERATE)
    for f in ["communication_score", "band", "raw_score", "dimensions",
              "weights", "bias_reduction", "generated_at"]:
        assert f in result

def test_final_score_in_range(scorer):
    for text in [WEAK, MODERATE, STRONG]:
        assert 0 <= scorer.score(text)["communication_score"] <= 100

def test_strong_scores_higher_than_weak(scorer):
    assert scorer.score(STRONG)["communication_score"] > scorer.score(WEAK)["communication_score"]

def test_band_is_valid_string(scorer):
    result = scorer.score(MODERATE)
    valid_bands = [info["label"] for info in COMMUNICATION_BANDS.values()]
    assert result["band"] in valid_bands

def test_excellent_band_for_strong_response(scorer):
    result = scorer.score(STRONG)
    assert result["band"] == "Excellent Communicator"

def test_dimensions_has_all_5(scorer):
    result = scorer.score(MODERATE)
    for dim in ["fluency", "grammar", "vocabulary", "clarity", "structure"]:
        assert dim in result["dimensions"]

def test_bias_reduction_is_list(scorer):
    result = scorer.score(WEAK)
    assert isinstance(result["bias_reduction"], list)
    assert len(result["bias_reduction"]) > 0

def test_keywords_passed_to_clarity(scorer):
    result = scorer.score("I managed a team of engineers effectively", ["team", "engineers"])
    assert result["dimensions"]["clarity"]["on_topic"] == True


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_filler_words_not_empty():
    assert len(FILLER_WORDS) > 0

def test_score_weights_sum_to_1():
    total = sum(SCORE_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001

def test_communication_bands_cover_0_to_100():
    all_values = []
    for info in COMMUNICATION_BANDS.values():
        lo, hi = info["range"]
        all_values.extend([lo, hi])
    assert 0 in all_values
    assert 100 in all_values

def test_structure_markers_has_4_categories():
    assert len(STRUCTURE_MARKERS) == 4

def test_advanced_vocabulary_not_empty():
    assert len(ADVANCED_VOCABULARY) > 0
