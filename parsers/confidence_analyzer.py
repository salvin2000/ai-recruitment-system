"""
Day 36 - Confidence & Stress Indicators
Zecpath AI Recruitment Platform

Assesses candidate confidence and emotional signals from responses.
Detects hesitation patterns (long pauses, repeated words, uncertainty
phrases), implements sentiment analysis, identifies contradiction patterns,
measures stress indicators, and generates a behavioral confidence score.
"""

from datetime import datetime
import re


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNCERTAINTY_PHRASES = [
    "i'm not sure", "i don't know", "maybe", "perhaps", "possibly",
    "i think", "i guess", "i hope", "might be", "could be",
    "not certain", "hard to say", "it depends", "i suppose",
    "probably", "i believe so", "more or less", "kind of", "sort of",
    "to be honest", "i'm not confident", "i may be wrong",
]

CONFIDENCE_PHRASES = [
    "i am confident", "i know", "definitely", "absolutely", "certainly",
    "i have proven", "i successfully", "i led", "i achieved", "i delivered",
    "i built", "i implemented", "i managed", "without a doubt", "i am sure",
    "i can guarantee", "i will", "i always", "i consistently",
]

POSITIVE_SENTIMENT_WORDS = [
    "excited", "passionate", "love", "enjoy", "thrive", "confident",
    "proud", "achieved", "successful", "excellent", "great", "strong",
    "motivated", "eager", "enthusiastic", "dedicated", "committed",
    "accomplished", "driven", "inspired",
]

NEGATIVE_SENTIMENT_WORDS = [
    "struggle", "difficult", "hate", "dislike", "frustrated", "stressed",
    "anxious", "nervous", "worried", "failed", "weak", "terrible",
    "overwhelmed", "confused", "uncertain", "uncomfortable", "unsure",
    "challenging", "problematic", "exhausted",
]

STRESS_MARKERS = {
    "over_apologizing":    ["i'm sorry", "apologies", "sorry if", "forgive me", "excuse me for"],
    "excessive_hedging":   ["just", "only", "merely", "a little bit", "somewhat", "rather"],
    "self_deprecation":    ["i'm not the best", "i'm not great at", "i'm probably not",
                            "i might not be", "i lack", "i struggle with"],
    "avoidance_language":  ["that's a tough question", "i never really thought about",
                            "let me think", "that's hard to answer", "i would need more time"],
}

PAUSE_INDICATORS = ["...", "—", "- -", "[ pause ]", "[pause]", "um...", "uh..."]

CONTRADICTION_PAIRS = [
    ("no experience",        "years of experience"),
    ("i work alone",         "team player"),
    ("not looking to move",  "open to relocation"),
    ("i never",              "i always"),
    ("i hate",               "i love"),
    ("no leadership",        "i led"),
    ("never lead",           "i led"),
    ("introvert",            "i enjoy networking"),
]

CONFIDENCE_SCORE_WEIGHTS = {
    "hesitation":    0.25,
    "sentiment":     0.25,
    "stress":        0.25,
    "contradiction": 0.25,
}

CONFIDENCE_BANDS = {
    "highly_confident":  {"range": (80, 100), "label": "Highly Confident"},
    "confident":         {"range": (65,  79), "label": "Confident"},
    "neutral":           {"range": (50,  64), "label": "Neutral / Composed"},
    "slightly_stressed": {"range": (35,  49), "label": "Slightly Stressed"},
    "stressed":          {"range": (0,   34), "label": "Shows Stress Signals"},
}


# ---------------------------------------------------------------------------
# HesitationDetector
# ---------------------------------------------------------------------------

class HesitationDetector:
    """Detects hesitation patterns: long pauses, repeated words,
    and uncertainty phrases."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower()
        words = lower.split()

        pause_count = sum(1 for p in PAUSE_INDICATORS if p in lower)

        repeated = []
        for i in range(len(words) - 1):
            w = words[i].strip(".,!?")
            if w == words[i + 1].strip(".,!?") and len(w) > 1:
                if w not in repeated:
                    repeated.append(w)

        uncertainty_hits = [p for p in UNCERTAINTY_PHRASES if p in lower]

        penalty = (pause_count * 10) + (len(repeated) * 8) + (len(uncertainty_hits) * 6)
        score = max(0, 100 - penalty)

        return {
            "score":              score,
            "pause_count":        pause_count,
            "repeated_words":     repeated,
            "uncertainty_phrases": uncertainty_hits,
            "hesitation_signals": pause_count + len(repeated) + len(uncertainty_hits),
        }

    def _zero(self):
        return {"score": 0, "pause_count": 0, "repeated_words": [],
                "uncertainty_phrases": [], "hesitation_signals": 0}


# ---------------------------------------------------------------------------
# SentimentAnalyzer
# ---------------------------------------------------------------------------

class SentimentAnalyzer:
    """Measures emotional tone by detecting positive and negative
    sentiment words and computing a net sentiment score."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower()
        positive_hits = [w for w in POSITIVE_SENTIMENT_WORDS if w in lower]
        negative_hits = [w for w in NEGATIVE_SENTIMENT_WORDS if w in lower]

        net = len(positive_hits) - len(negative_hits)
        raw_score = 50 + (net * 10)
        score = max(0, min(100, raw_score))

        if score >= 65:
            label = "Positive"
        elif score >= 45:
            label = "Neutral"
        else:
            label = "Negative"

        return {
            "score":          score,
            "label":          label,
            "positive_words": positive_hits,
            "negative_words": negative_hits,
            "net_sentiment":  net,
        }

    def _zero(self):
        return {"score": 0, "label": "Negative", "positive_words": [],
                "negative_words": [], "net_sentiment": 0}


# ---------------------------------------------------------------------------
# StressIndicatorAnalyzer
# ---------------------------------------------------------------------------

class StressIndicatorAnalyzer:
    """Detects stress markers across 4 categories: over-apologizing,
    excessive hedging, self-deprecation, and avoidance language.
    Also checks for the presence of confidence phrases as a positive signal."""

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower().replace("\u2019", "'").replace("\u2018", "'")
        found_markers = {}
        total_stress_hits = 0

        for category, phrases in STRESS_MARKERS.items():
            hits = [p for p in phrases if p in lower]
            if hits:
                found_markers[category] = hits
                total_stress_hits += len(hits)

        confidence_hits = [p for p in CONFIDENCE_PHRASES if p in lower]

        stress_penalty = min(total_stress_hits * 10, 60)
        confidence_bonus = min(len(confidence_hits) * 8, 30)
        score = max(0, min(100, 70 - stress_penalty + confidence_bonus))

        return {
            "score":             score,
            "stress_markers":    found_markers,
            "stress_hit_count":  total_stress_hits,
            "confidence_phrases": confidence_hits,
            "stress_categories": list(found_markers.keys()),
        }

    def _zero(self):
        return {"score": 0, "stress_markers": {}, "stress_hit_count": 0,
                "confidence_phrases": [], "stress_categories": []}


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------

class ContradictionDetector:
    """Scans for internal contradictions within a response and across
    prior responses in the same session."""

    def analyze(self, text: str, prior_responses: list = None) -> dict:
        if not text.strip():
            return self._zero()

        lower = text.lower()
        contradictions = []

        # Within this response
        for claim_a, claim_b in CONTRADICTION_PAIRS:
            if claim_a in lower and claim_b in lower:
                contradictions.append({
                    "type":    "internal",
                    "claim_a": claim_a,
                    "claim_b": claim_b,
                })

        # Against prior responses
        for prior in (prior_responses or []):
            prior_lower = prior.lower()
            for claim_a, claim_b in CONTRADICTION_PAIRS:
                if claim_a in prior_lower and claim_b in lower:
                    contradictions.append({
                        "type":    "cross_session",
                        "claim_a": claim_a,
                        "claim_b": claim_b,
                    })
                elif claim_b in prior_lower and claim_a in lower:
                    contradictions.append({
                        "type":    "cross_session",
                        "claim_a": claim_b,
                        "claim_b": claim_a,
                    })

        penalty = min(len(contradictions) * 20, 60)
        score = max(0, 100 - penalty)

        return {
            "score":            score,
            "contradictions":   contradictions,
            "contradiction_count": len(contradictions),
            "has_contradiction": len(contradictions) > 0,
        }

    def _zero(self):
        return {"score": 100, "contradictions": [], "contradiction_count": 0,
                "has_contradiction": False}


# ---------------------------------------------------------------------------
# ConfidenceScorer — orchestrates all detectors
# ---------------------------------------------------------------------------

class ConfidenceScorer:
    """Runs all 4 behavioral signal analyzers, applies equal-weighted
    scoring, and produces the final behavioral confidence score with
    a label, dimension breakdown, and signal interpretation notes."""

    def __init__(self):
        self.hesitation    = HesitationDetector()
        self.sentiment     = SentimentAnalyzer()
        self.stress        = StressIndicatorAnalyzer()
        self.contradiction = ContradictionDetector()
        self.weights       = CONFIDENCE_SCORE_WEIGHTS

    def score(self, text: str, prior_responses: list = None) -> dict:
        hesitation_result    = self.hesitation.analyze(text)
        sentiment_result     = self.sentiment.analyze(text)
        stress_result        = self.stress.analyze(text)
        contradiction_result = self.contradiction.analyze(text, prior_responses)

        raw_score = (
            hesitation_result["score"]    * self.weights["hesitation"]    +
            sentiment_result["score"]     * self.weights["sentiment"]     +
            stress_result["score"]        * self.weights["stress"]        +
            contradiction_result["score"] * self.weights["contradiction"]
        )

        final_score = round(raw_score, 1)
        band = self._band(final_score)

        return {
            "confidence_score": final_score,
            "band":             band,
            "dimensions": {
                "hesitation":    hesitation_result,
                "sentiment":     sentiment_result,
                "stress":        stress_result,
                "contradiction": contradiction_result,
            },
            "weights":          self.weights,
            "signal_notes":     self._signal_notes(
                hesitation_result, sentiment_result,
                stress_result, contradiction_result
            ),
            "generated_at":     datetime.now().isoformat(),
        }

    def _band(self, score: float) -> str:
        for band, info in CONFIDENCE_BANDS.items():
            lo, hi = info["range"]
            if lo <= score <= hi:
                return info["label"]
        return "Shows Stress Signals"

    def _signal_notes(self, hesitation, sentiment, stress, contradiction) -> list:
        notes = []
        if hesitation["hesitation_signals"] > 4:
            notes.append(f"High hesitation signal count ({hesitation['hesitation_signals']}) — may indicate interview anxiety")
        if sentiment["label"] == "Negative":
            notes.append("Predominantly negative sentiment detected — monitor for genuine disengagement vs. topic difficulty")
        if stress["stress_hit_count"] > 2:
            notes.append(f"Multiple stress markers detected across {len(stress['stress_categories'])} categories")
        if contradiction["has_contradiction"]:
            notes.append(f"{contradiction['contradiction_count']} contradiction(s) detected — worth clarifying in follow-up")
        if hesitation["uncertainty_phrases"] and len(hesitation["uncertainty_phrases"]) >= 3:
            notes.append("Frequent uncertainty language — candidate may need reassurance before answering")
        if not notes:
            notes.append("No significant stress or confidence concerns detected")
        return notes
