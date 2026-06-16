"""
Day 27 – Confidence & Sentiment Signal Analysis
Zecpath AI Recruitment Platform

Assesses communication quality and behavioral indicators from
candidate screening responses. Detects hesitation, measures pace,
identifies sentiment, detects uncertainty and contradictions,
and creates communication strength indicators.
"""

import re
import json
from datetime import datetime
from typing import Optional


# ── Hesitation Patterns ───────────────────────────────────────────────────────

HESITATION_PATTERNS = [
    r"\bum+\b", r"\buh+\b", r"\bhmm+\b", r"\bah+\b", r"\ber+\b",
    r"\byou know\b", r"\bi mean\b", r"\bkind of\b", r"\bsort of\b",
    r"\blike\b", r"\bbasically\b", r"\bactually\b",
    r"\blet me think\b", r"\blet me see\b", r"\bhow do i say\b",
    r"\bwhat do you call\b", r"\bi guess\b", r"\bi suppose\b",
    r"\bprobably\b", r"\bmaybe\b", r"\bperhaps\b",
    r"\bnot sure\b", r"\bi think\b", r"\bi believe\b",
    r"\bsomething like\b", r"\baround that\b", r"\bmore or less\b",
]

# ── Confidence Signal Patterns ────────────────────────────────────────────────

CONFIDENCE_SIGNALS = {
    "high_confidence": [
        r"\bi have\b", r"\bi worked\b", r"\bi built\b", r"\bi led\b",
        r"\bi managed\b", r"\bi delivered\b", r"\bi achieved\b",
        r"\bi designed\b", r"\bi implemented\b", r"\bi developed\b",
        r"\bspecifically\b", r"\bexactly\b", r"\bprecisely\b",
        r"\bin my experience\b", r"\bin my current role\b",
        r"\bmy team\b", r"\bmy project\b", r"\bi am confident\b",
        r"\bwithout a doubt\b", r"\bdefintely\b", r"\bcertainly\b",
    ],
    "low_confidence": [
        r"\bi don't know\b", r"\bnot sure\b", r"\bi think so\b",
        r"\bmaybe\b", r"\bperhaps\b", r"\bi guess\b", r"\bprobably\b",
        r"\bsomewhere around\b", r"\bapproximately\b", r"\broughly\b",
        r"\bi might\b", r"\bi could be wrong\b", r"\bnot really\b",
        r"\bi'm not certain\b", r"\bhard to say\b", r"\bit depends\b",
        r"\bkind of\b", r"\bsort of\b", r"\bmore or less\b",
    ],
}

# ── Sentiment Lexicon ─────────────────────────────────────────────────────────

SENTIMENT_LEXICON = {
    "positive": [
        "excited", "passionate", "love", "enjoy", "great", "excellent",
        "fantastic", "wonderful", "happy", "eager", "enthusiastic",
        "proud", "confident", "strong", "good", "excellent", "perfect",
        "amazing", "outstanding", "successful", "achieved", "delivered",
        "built", "led", "managed", "improved", "optimized", "grew",
        "opportunity", "challenge", "growth", "learn", "contribute",
        "motivated", "dedicated", "committed", "reliable", "collaborative",
    ],
    "negative": [
        "difficult", "struggle", "problem", "issue", "challenge",
        "failed", "unable", "cannot", "worried", "concerned", "stressed",
        "boring", "tedious", "hate", "dislike", "unfortunate", "poor",
        "bad", "worse", "terrible", "awful", "disappointed", "frustrated",
        "confused", "lost", "unsure", "unstable", "unclear", "vague",
    ],
    "neutral": [
        "work", "job", "role", "company", "team", "project", "years",
        "experience", "currently", "previously", "skills", "technology",
    ],
}

# ── Uncertainty Indicators ────────────────────────────────────────────────────

UNCERTAINTY_INDICATORS = [
    r"\bi (don't|dont) know\b",
    r"\bnot (really|sure|certain|clear)\b",
    r"\b(maybe|perhaps|possibly|probably)\b",
    r"\b(around|approximately|roughly|about)\s+\d+",
    r"\b(i think|i believe|i suppose|i guess)\b",
    r"\bit depends\b",
    r"\bhard to say\b",
    r"\bcould be\b",
    r"\bmight be\b",
    r"\bsomewhere (around|between)\b",
]

# ── Contradiction Patterns ────────────────────────────────────────────────────

CONTRADICTION_PAIRS = [
    ("yes", "no"),
    ("can", "cannot"),
    ("will", "won't"),
    ("available", "not available"),
    ("comfortable", "not comfortable"),
    ("agree", "disagree"),
    ("interested", "not interested"),
    ("open to", "not open"),
]

# ── Pace Thresholds ───────────────────────────────────────────────────────────

PACE_THRESHOLDS = {
    "very_fast":  {"wpm_min": 180, "label": "Very Fast", "signal": "May indicate nervousness or rehearsed answer"},
    "fast":       {"wpm_min": 150, "label": "Fast",      "signal": "Confident pace — slightly above normal"},
    "normal":     {"wpm_min": 120, "label": "Normal",    "signal": "Ideal conversational pace"},
    "slow":       {"wpm_min":  90, "label": "Slow",      "signal": "Thoughtful or hesitant — may need follow-up"},
    "very_slow":  {"wpm_min":   0, "label": "Very Slow", "signal": "Significant hesitation or uncertainty detected"},
}

# ── Communication Strength Levels ─────────────────────────────────────────────

COMMUNICATION_STRENGTH = {
    "strong":    {"min_score": 75, "label": "Strong Communicator",   "color": "green"},
    "moderate":  {"min_score": 50, "label": "Moderate Communicator", "color": "amber"},
    "weak":      {"min_score": 25, "label": "Weak Communicator",     "color": "orange"},
    "poor":      {"min_score":  0, "label": "Poor Communicator",     "color": "red"},
}

# ── Behavioral Indicator Tags ─────────────────────────────────────────────────

BEHAVIORAL_TAGS = {
    "highly_confident":    "Candidate used strong ownership language and specific examples",
    "hesitant":            "Candidate showed multiple hesitation markers in their response",
    "positive_framing":    "Candidate framed experiences and challenges in a positive light",
    "negative_framing":    "Candidate expressed concerns or negativity about past experiences",
    "contradictory":       "Candidate made statements that appear to contradict each other",
    "uncertain_on_facts":  "Candidate was uncertain about specific facts like years or salary",
    "fast_responder":      "Candidate responded quickly — may indicate preparation or confidence",
    "slow_responder":      "Candidate took time to respond — may indicate thoughtfulness or hesitation",
    "concise":             "Candidate answered clearly and concisely without over-explaining",
    "verbose":             "Candidate provided very detailed responses beyond what was asked",
    "on_topic":            "Candidate stayed on topic throughout the response",
    "off_topic":           "Candidate drifted off topic during the response",
}


class HesitationDetector:
    """Detects hesitation patterns in candidate speech."""

    def __init__(self):
        self.patterns = HESITATION_PATTERNS

    def count_hesitations(self, text: str) -> dict:
        """Count total hesitation markers and return details."""
        text_lower = text.lower()
        found      = []
        for pat in self.patterns:
            matches = re.findall(pat, text_lower)
            if matches:
                found.extend(matches)

        word_count   = max(len(text.split()), 1)
        count        = len(found)
        density      = round(count / word_count, 4)

        return {
            "count":         count,
            "density":       density,
            "found":         list(set(found)),
            "is_hesitant":   count >= 3 or density >= 0.15,
            "severity":      "high" if count >= 5 or density >= 0.20
                             else "medium" if count >= 3 or density >= 0.15
                             else "low",
        }


class ConfidenceAnalyzer:
    """Analyzes confidence level from candidate text signals."""

    def __init__(self):
        self.signals    = CONFIDENCE_SIGNALS
        self.hesitation = HesitationDetector()

    def analyze(self, text: str, duration_ms: int = 0) -> dict:
        """
        Compute a confidence score from 0.0 to 1.0.
        Combines signal patterns, hesitation density, and response pace.
        """
        text_lower = text.lower()

        # Signal scoring
        high_matches = sum(
            1 for pat in self.signals["high_confidence"]
            if re.search(pat, text_lower)
        )
        low_matches = sum(
            1 for pat in self.signals["low_confidence"]
            if re.search(pat, text_lower)
        )

        signal_score = min(1.0, max(0.0,
            0.5 + (high_matches * 0.08) - (low_matches * 0.10)
        ))

        # Hesitation penalty
        hes     = self.hesitation.count_hesitations(text)
        hes_pen = min(0.40, hes["count"] * 0.04)

        # Pace analysis
        word_count = len(text.split())
        wpm        = 0
        pace_label = "unknown"
        if duration_ms > 0:
            minutes = duration_ms / 60000
            wpm     = int(word_count / max(minutes, 0.01))
            pace_label = self._classify_pace(wpm)

        confidence_score = round(max(0.0, signal_score - hes_pen), 4)

        # Tags
        tags = []
        if high_matches >= 3:
            tags.append("highly_confident")
        if hes["is_hesitant"]:
            tags.append("hesitant")
        if wpm >= 150 and duration_ms > 0:
            tags.append("fast_responder")
        elif wpm < 100 and duration_ms > 0:
            tags.append("slow_responder")
        if word_count >= 30:
            tags.append("verbose")
        elif word_count <= 8:
            tags.append("concise")

        return {
            "confidence_score":  confidence_score,
            "high_conf_signals": high_matches,
            "low_conf_signals":  low_matches,
            "hesitation":        hes,
            "wpm":               wpm,
            "pace_label":        pace_label,
            "tags":              tags,
            "word_count":        word_count,
        }

    def _classify_pace(self, wpm: int) -> str:
        for level, data in PACE_THRESHOLDS.items():
            if wpm >= data["wpm_min"]:
                return level
        return "very_slow"


class SentimentScorer:
    """Scores positive and negative sentiment in candidate responses."""

    def __init__(self):
        self.lexicon      = SENTIMENT_LEXICON
        self.uncertainty  = UNCERTAINTY_INDICATORS
        self.contradictions = CONTRADICTION_PAIRS

    def score_sentiment(self, text: str) -> dict:
        """
        Compute sentiment score from -1.0 (negative) to +1.0 (positive).
        Also detects uncertainty and contradiction signals.
        """
        text_lower = text.lower()
        words      = text_lower.split()

        pos_count = sum(1 for w in words if w.strip(".,!?") in self.lexicon["positive"])
        neg_count = sum(1 for w in words if w.strip(".,!?") in self.lexicon["negative"])
        total     = pos_count + neg_count

        if total == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = round((pos_count - neg_count) / total, 4)

        # Sentiment label
        if sentiment_score >= 0.4:
            label = "positive"
        elif sentiment_score <= -0.4:
            label = "negative"
        else:
            label = "neutral"

        # Tags
        tags = []
        if sentiment_score >= 0.4:
            tags.append("positive_framing")
        elif sentiment_score <= -0.3:
            tags.append("negative_framing")

        return {
            "sentiment_score":  sentiment_score,
            "sentiment_label":  label,
            "positive_words":   pos_count,
            "negative_words":   neg_count,
            "tags":             tags,
        }

    def detect_uncertainty(self, text: str) -> dict:
        """Detect uncertainty expressions in the answer."""
        text_lower = text.lower()
        found = []
        for pat in self.uncertainty:
            matches = re.findall(pat, text_lower)
            if matches:
                found.extend(matches)

        count     = len(found)
        is_uncert = count >= 2

        return {
            "uncertainty_count":   count,
            "is_uncertain":        is_uncert,
            "indicators_found":    list(set(str(f) for f in found)),
            "uncertainty_level":   "high" if count >= 4 else "medium" if count >= 2 else "low",
        }

    def detect_contradiction(self, text: str) -> dict:
        """Detect contradictory statements within a single answer."""
        text_lower = text.lower()
        found_pairs = []

        for pos, neg in self.contradiction_pairs_check():
            if re.search(r"\b" + pos + r"\b", text_lower) and \
               re.search(r"\b" + neg + r"\b", text_lower):
                found_pairs.append((pos, neg))

        return {
            "has_contradiction": len(found_pairs) > 0,
            "contradiction_pairs": found_pairs,
            "count": len(found_pairs),
        }

    def contradiction_pairs_check(self):
        return CONTRADICTION_PAIRS


class CommunicationStrengthEngine:
    """
    Combines confidence and sentiment signals to produce
    a final communication strength score and behavioral report.
    """

    def __init__(self):
        self.confidence = ConfidenceAnalyzer()
        self.sentiment  = SentimentScorer()
        self.strength_levels = COMMUNICATION_STRENGTH
        self.behavior_tags   = BEHAVIORAL_TAGS

    def analyze(self,
                text:          str,
                duration_ms:   int = 0,
                question_id:   str = "",
                session_id:    str = "",
                is_off_topic:  bool = False) -> dict:
        """
        Run full communication strength analysis on a candidate answer.
        Returns confidence, sentiment, uncertainty, contradiction,
        communication strength score, and behavioral tags.
        """
        conf_result  = self.confidence.analyze(text, duration_ms)
        sent_result  = self.sentiment.score_sentiment(text)
        uncert       = self.sentiment.detect_uncertainty(text)
        contra       = self.sentiment.detect_contradiction(text)

        # Communication strength score (0-100)
        conf_component  = conf_result["confidence_score"] * 40   # 40 points
        sent_component  = max(0, sent_result["sentiment_score"]) * 30  # 30 points
        hes_component   = max(0, 1 - conf_result["hesitation"]["density"] * 5) * 20  # 20 points
        uncert_component= max(0, 1 - uncert["uncertainty_count"] * 0.2) * 10  # 10 points

        strength_score  = round(min(100, conf_component + sent_component +
                                    hes_component + uncert_component), 2)

        # Strength level
        strength_label = "poor"
        for level, data in self.strength_levels.items():
            if strength_score >= data["min_score"]:
                strength_label = level
                break

        # Compile all behavioral tags
        all_tags = list(set(
            conf_result.get("tags", []) +
            sent_result.get("tags", []) +
            (["uncertain_on_facts"] if uncert["is_uncertain"] else []) +
            (["contradictory"] if contra["has_contradiction"] else []) +
            (["off_topic"] if is_off_topic else ["on_topic"])
        ))

        return {
            "analysis_id":         f"CS-{session_id}-{question_id}" if session_id else f"CS-{question_id}",
            "question_id":         question_id,
            "session_id":          session_id,
            "text_analyzed":       text,
            "word_count":          conf_result["word_count"],
            "duration_ms":         duration_ms,
            "confidence": {
                "score":           conf_result["confidence_score"],
                "high_signals":    conf_result["high_conf_signals"],
                "low_signals":     conf_result["low_conf_signals"],
                "hesitation":      conf_result["hesitation"],
                "wpm":             conf_result["wpm"],
                "pace_label":      conf_result["pace_label"],
            },
            "sentiment": {
                "score":           sent_result["sentiment_score"],
                "label":           sent_result["sentiment_label"],
                "positive_words":  sent_result["positive_words"],
                "negative_words":  sent_result["negative_words"],
            },
            "uncertainty":         uncert,
            "contradiction":       contra,
            "communication_strength": {
                "score":           strength_score,
                "level":           strength_label,
                "label":           self.strength_levels[strength_label]["label"],
            },
            "behavioral_tags":     all_tags,
            "analyzed_at":         datetime.now().isoformat(),
        }

    def analyze_batch(self, turns: list) -> list:
        """Analyze a batch of candidate turns."""
        return [self.analyze(**turn) for turn in turns]

    def generate_report(self, results: list,
                         candidate_id: str = "",
                         session_id:   str = "") -> dict:
        """Generate a behavioral indicators report from batch results."""
        if not results:
            return {}

        avg_conf     = round(sum(r["confidence"]["score"] for r in results) / len(results), 4)
        avg_sent     = round(sum(r["sentiment"]["score"]  for r in results) / len(results), 4)
        avg_strength = round(sum(r["communication_strength"]["score"] for r in results) / len(results), 2)
        total_hes    = sum(r["confidence"]["hesitation"]["count"] for r in results)
        total_uncert = sum(r["uncertainty"]["uncertainty_count"] for r in results)

        # Collect all tags
        all_tags = [tag for r in results for tag in r["behavioral_tags"]]
        tag_freq = {}
        for tag in all_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1

        # Overall strength
        overall_level = "poor"
        for level, data in self.strength_levels.items():
            if avg_strength >= data["min_score"]:
                overall_level = level
                break

        return {
            "report_metadata": {
                "generated_at":     datetime.now().isoformat(),
                "candidate_id":     candidate_id,
                "session_id":       session_id,
                "total_answers":    len(results),
            },
            "summary": {
                "avg_confidence_score":   avg_conf,
                "avg_sentiment_score":    avg_sent,
                "avg_strength_score":     avg_strength,
                "overall_strength_level": overall_level,
                "overall_strength_label": self.strength_levels[overall_level]["label"],
                "total_hesitations":      total_hes,
                "total_uncertainties":    total_uncert,
            },
            "behavioral_tag_frequency": tag_freq,
            "per_answer_results":       results,
        }

    def save_report(self, report: dict, output_path: str):
        """Save behavioral report to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
