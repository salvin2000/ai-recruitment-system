"""
Day 35 - Communication Skill Evaluation
Zecpath AI Recruitment Platform

Evaluates candidate communication skills objectively across 4 dimensions:
fluency, grammar quality, vocabulary range, and clarity of explanation.
Also detects filler words, measures answer structure, assigns a final
communication score (0-100), and normalizes scoring to reduce bias.
"""

from datetime import datetime
import re


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "honestly", "right", "so yeah", "kind of",
    "sort of", "i mean", "well", "anyway", "whatever",
]

STRUCTURE_MARKERS = {
    "opening":     ["firstly", "to begin", "let me start", "i would say", "so basically"],
    "transition":  ["then", "after that", "following that", "additionally", "furthermore",
                    "on the other hand", "however", "moving on", "also", "besides"],
    "example":     ["for example", "for instance", "such as", "to illustrate",
                    "in my experience", "specifically", "one time", "i once"],
    "closing":     ["in conclusion", "to summarize", "overall", "in short",
                    "to wrap up", "finally", "in the end"],
}

ADVANCED_VOCABULARY = [
    "collaborate", "implement", "facilitate", "optimize", "leverage",
    "strategize", "prioritize", "mitigate", "synthesize", "orchestrate",
    "articulate", "demonstrate", "comprehend", "initiative", "proactive",
    "analytical", "systematic", "innovative", "substantial", "efficiency",
    "perspective", "stakeholder", "deliverable", "methodology", "framework",
]

SIMPLE_VOCABULARY = [
    "good", "bad", "nice", "stuff", "things", "do", "make", "get",
    "put", "big", "small", "a lot", "very", "really", "just",
]

GRAMMAR_ERROR_PATTERNS = [
    (r"\bi goes\b",           "subject-verb agreement: 'I goes'"),
    (r"\bwe was\b",           "subject-verb agreement: 'we was'"),
    (r"\bthey was\b",         "subject-verb agreement: 'they was'"),
    (r"\bdone did\b",         "double past tense: 'done did'"),
    (r"\bmore better\b",      "double comparative: 'more better'"),
    (r"\bmost biggest\b",     "double superlative: 'most biggest'"),
    (r"\bi seen\b",           "incorrect past tense: 'I seen'"),
    (r"\bhe don't\b",         "subject-verb agreement: 'he don't'"),
    (r"\bshe don't\b",        "subject-verb agreement: 'she don't'"),
    (r"\b(\w+)\s+\1\b",       "word repetition"),
]

SCORE_WEIGHTS = {
    "fluency":     0.25,
    "grammar":     0.25,
    "vocabulary":  0.20,
    "clarity":     0.20,
    "structure":   0.10,
}

COMMUNICATION_BANDS = {
    "excellent":    {"range": (85, 100), "label": "Excellent Communicator"},
    "good":         {"range": (70,  84), "label": "Good Communicator"},
    "adequate":     {"range": (55,  69), "label": "Adequate Communicator"},
    "developing":   {"range": (40,  54), "label": "Developing Communicator"},
    "needs_work":   {"range": (0,   39), "label": "Needs Improvement"},
}


# ---------------------------------------------------------------------------
# FluencyAnalyzer
# ---------------------------------------------------------------------------

class FluencyAnalyzer:
    """Measures sentence continuity — how naturally and smoothly the
    candidate constructs and connects their sentences."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 5]
        if not sentences:
            return self._zero()

        words = text.split()
        avg_sentence_len = len(words) / max(len(sentences), 1)

        filler_count = sum(
            text.lower().count(f) for f in FILLER_WORDS
        )
        filler_density = filler_count / max(len(words), 1)

        # Penalize very short sentences (choppy) and very long (rambling)
        len_score = 100
        if avg_sentence_len < 5:  len_score = 40
        elif avg_sentence_len < 10: len_score = 65
        elif avg_sentence_len > 40: len_score = 70
        else:                       len_score = 100

        filler_penalty = min(filler_count * 8, 40)
        score = max(0, len_score - filler_penalty)

        return {
            "score":            score,
            "avg_sentence_len": round(avg_sentence_len, 1),
            "sentence_count":   len(sentences),
            "filler_count":     filler_count,
            "filler_density":   round(filler_density, 3),
            "filler_words_found": [f for f in FILLER_WORDS if f in text.lower()],
        }

    def _zero(self):
        return {"score": 0, "avg_sentence_len": 0, "sentence_count": 0,
                "filler_count": 0, "filler_density": 0, "filler_words_found": []}


# ---------------------------------------------------------------------------
# GrammarAnalyzer
# ---------------------------------------------------------------------------

class GrammarAnalyzer:
    """Checks for common grammar error patterns and scores the response
    based on how many are found relative to response length."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        words = text.split()
        errors = []
        for pattern, label in GRAMMAR_ERROR_PATTERNS:
            if re.search(pattern, text.lower()):
                errors.append(label)

        error_rate = len(errors) / max(len(words), 1)
        penalty = min(len(errors) * 15, 60)
        score = max(0, 100 - penalty)

        return {
            "score":      score,
            "errors":     errors,
            "error_count": len(errors),
            "error_rate": round(error_rate, 4),
        }

    def _zero(self):
        return {"score": 0, "errors": [], "error_count": 0, "error_rate": 0}


# ---------------------------------------------------------------------------
# VocabularyAnalyzer
# ---------------------------------------------------------------------------

class VocabularyAnalyzer:
    """Measures vocabulary range by checking for advanced vocabulary usage
    and penalizing over-reliance on simple/filler vocabulary."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower()
        words = lower.split()
        unique_words = set(words)

        advanced_hits = [w for w in ADVANCED_VOCABULARY if w in lower]
        simple_hits = [w for w in SIMPLE_VOCABULARY if w in lower]

        diversity_ratio = len(unique_words) / max(len(words), 1)

        base = 50
        base += len(advanced_hits) * 8
        base -= len(simple_hits) * 3
        base += int(diversity_ratio * 30)
        score = max(0, min(100, base))

        return {
            "score":           score,
            "advanced_words":  advanced_hits,
            "simple_words":    simple_hits,
            "unique_word_count": len(unique_words),
            "total_word_count": len(words),
            "diversity_ratio": round(diversity_ratio, 3),
        }

    def _zero(self):
        return {"score": 0, "advanced_words": [], "simple_words": [],
                "unique_word_count": 0, "total_word_count": 0, "diversity_ratio": 0}


# ---------------------------------------------------------------------------
# ClarityAnalyzer
# ---------------------------------------------------------------------------

class ClarityAnalyzer:
    """Measures how clearly the candidate explains their point — whether
    they give enough context, use examples, and stay on topic."""

    def analyze(self, text: str, question_keywords: list = None) -> dict:
        if not text.strip():
            return self._zero()

        words = text.split()
        lower = text.lower()

        has_example = any(m in lower for m in STRUCTURE_MARKERS["example"])
        has_context = len(words) >= 20
        has_specifics = any(char.isdigit() for char in text)

        on_topic = True
        if question_keywords:
            on_topic = any(kw.lower() in lower for kw in question_keywords)

        score = 40
        if has_context:  score += 20
        if has_example:  score += 25
        if has_specifics: score += 15
        if on_topic:     score += 10
        score = min(100, score)

        return {
            "score":        score,
            "has_example":  has_example,
            "has_context":  has_context,
            "has_specifics": has_specifics,
            "on_topic":     on_topic,
        }

    def _zero(self):
        return {"score": 0, "has_example": False, "has_context": False,
                "has_specifics": False, "on_topic": False}


# ---------------------------------------------------------------------------
# StructureAnalyzer
# ---------------------------------------------------------------------------

class StructureAnalyzer:
    """Measures how well the answer is structured — whether it has a
    recognizable opening, transitions between points, and a closing."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower()
        found = {
            key: [m for m in markers if m in lower]
            for key, markers in STRUCTURE_MARKERS.items()
        }
        layers_present = sum(1 for hits in found.values() if hits)
        score = min(100, layers_present * 25)

        return {
            "score":          score,
            "layers_found":   layers_present,
            "markers_found":  {k: v for k, v in found.items() if v},
        }

    def _zero(self):
        return {"score": 0, "layers_found": 0, "markers_found": {}}


# ---------------------------------------------------------------------------
# CommunicationScorer — orchestrates all analyzers
# ---------------------------------------------------------------------------

class CommunicationScorer:
    """Runs all 5 analyzers, applies weighted scoring, normalizes the
    result to reduce bias, and produces the final communication
    score with a label, dimension breakdown, and bias-reduction notes."""

    def __init__(self):
        self.fluency    = FluencyAnalyzer()
        self.grammar    = GrammarAnalyzer()
        self.vocabulary = VocabularyAnalyzer()
        self.clarity    = ClarityAnalyzer()
        self.structure  = StructureAnalyzer()
        self.weights    = SCORE_WEIGHTS

    def score(self, text: str, question_keywords: list = None) -> dict:
        fluency_result    = self.fluency.analyze(text)
        grammar_result    = self.grammar.analyze(text)
        vocabulary_result = self.vocabulary.analyze(text)
        clarity_result    = self.clarity.analyze(text, question_keywords)
        structure_result  = self.structure.analyze(text)

        raw_score = (
            fluency_result["score"]    * self.weights["fluency"]    +
            grammar_result["score"]    * self.weights["grammar"]    +
            vocabulary_result["score"] * self.weights["vocabulary"] +
            clarity_result["score"]    * self.weights["clarity"]    +
            structure_result["score"]  * self.weights["structure"]
        )

        normalized_score = self._normalize(raw_score, text)
        band = self._band(normalized_score)

        return {
            "communication_score": round(normalized_score, 1),
            "band":                band,
            "raw_score":           round(raw_score, 1),
            "dimensions": {
                "fluency":    fluency_result,
                "grammar":    grammar_result,
                "vocabulary": vocabulary_result,
                "clarity":    clarity_result,
                "structure":  structure_result,
            },
            "weights":            self.weights,
            "bias_reduction":     self._bias_notes(text, fluency_result),
            "generated_at":       datetime.now().isoformat(),
        }

    def _normalize(self, raw: float, text: str) -> float:
        """Apply mild normalization to reduce bias from response length.
        Very short responses are not automatically penalized to the floor,
        and very long responses are not automatically rewarded."""
        words = text.split()
        length_factor = 1.0
        if len(words) < 10:
            length_factor = 0.85   # slight penalty, but not catastrophic
        elif len(words) > 200:
            length_factor = 0.95   # very long doesn't automatically mean better
        return min(100, raw * length_factor)

    def _band(self, score: float) -> str:
        for band, info in COMMUNICATION_BANDS.items():
            lo, hi = info["range"]
            if lo <= score <= hi:
                return info["label"]
        return "Needs Improvement"

    def _bias_notes(self, text: str, fluency: dict) -> list:
        notes = []
        if fluency["filler_count"] > 3:
            notes.append("High filler word count may reflect nervousness rather than poor communication — considered but not heavily penalized")
        if len(text.split()) < 20:
            notes.append("Short response — score reflects what was said, not length alone")
        if fluency["avg_sentence_len"] > 30:
            notes.append("Long sentences may indicate a non-native speaker constructing careful answers — not penalized beyond fluency score")
        if not notes:
            notes.append("No significant bias factors detected")
        return notes
