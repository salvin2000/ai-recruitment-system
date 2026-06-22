"""
Day 31 - Edge Case & Failure Handling
Zecpath AI Recruitment Platform

Extends the Day 29 ConversationFlowController to keep AI screening calls
stable under real-world conditions: poor audio, language mixing, missing
answers, and background noise. Adds retry/clarification logic specific to
these failure modes and a set of safety fallbacks so a call never crashes
or hangs no matter what the candidate's environment throws at it.
"""

import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from parsers.conversation_flow import (
    ConversationFlowController, ConversationStateMachine, TurnDecisionEngine,
    CONVERSATION_STATES, STATE_TRANSITIONS, TURN_OUTCOMES,
    SILENCE_HANDLING, RETRY_CONFIG, POLITE_MESSAGES,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EDGE_CASE_TYPES = {
    "poor_audio":        "Speech-to-text confidence too low to trust the transcript",
    "language_mixing":   "Candidate mixes multiple languages in one answer",
    "missing_answer":    "No usable answer was captured for the question",
    "background_noise":  "Non-speech noise interfering with transcription",
}

AUDIO_QUALITY_THRESHOLDS = {
    "min_confidence":       0.40,   # below this, treat transcript as unreliable
    "low_confidence_band":  0.60,   # below this but above min, ask for repeat
    "min_clarity_score":    0.50,   # derived signal-to-noise proxy
}

NOISE_KEYWORDS = [
    "[noise]", "[inaudible]", "[crosstalk]", "[static]", "[unclear]",
]

LANGUAGE_MIX_PATTERNS = {
    # Simple heuristic patterns indicating a language switch mid-answer.
    "hindi_markers":    [r"\bhaan\b", r"\bnahi\b", r"\bkya\b", r"\bmatlab\b", r"\bbas\b"],
    "malayalam_markers": [r"\bsheri\b", r"\bathe\b", r"\billa\b", r"\bappo\b"],
    "tamil_markers":    [r"\bsari\b", r"\billai\b", r"\bvanga\b"],
}

FALLBACK_RESPONSES = {
    "poor_audio": {
        "retry_1": "I'm sorry, the line was a little unclear. Could you please repeat that?",
        "retry_2": "I'm still having trouble hearing you clearly. Could you move to a quieter spot and try again?",
        "give_up": "I wasn't able to capture that clearly. I'll note this question for manual review and move on.",
    },
    "language_mixing": {
        "retry_1": "No problem at all — please feel free to answer in English or your preferred language, whichever is easier.",
        "retry_2": "That's completely fine — could you summarize your answer in just a few words?",
        "give_up": "Thank you — I've recorded your response as given and will flag it for a human reviewer to confirm.",
    },
    "missing_answer": {
        "retry_1": "I didn't quite catch a response — could you say that again?",
        "retry_2": "Take your time — whenever you're ready, please go ahead and answer.",
        "give_up": "That's alright — let's move on to the next question.",
    },
    "background_noise": {
        "retry_1": "There seems to be some background noise. Could you move somewhere quieter and repeat your answer?",
        "retry_2": "I'm still picking up some noise on the line. If possible, please mute any background sound and try once more.",
        "give_up": "I'll proceed with what I could capture and flag this response for review.",
    },
}

SAFETY_FALLBACKS = {
    "max_consecutive_failures": 3,     # same edge case repeating in a row
    "max_total_edge_cases":     6,     # across the whole call
    "hard_abort_message": (
        "I'm having ongoing trouble with the call quality today. Let's stop here — "
        "a member of our team will follow up with you directly. Thank you for your patience."
    ),
    "manual_review_message": (
        "Thank you for your answers. Some parts of this call will be reviewed manually "
        "by our team to make sure nothing was missed."
    ),
}


# ---------------------------------------------------------------------------
# EdgeCaseDetector — what went wrong with this turn?
# ---------------------------------------------------------------------------

class EdgeCaseDetector:
    """Inspects a raw answer object and classifies which edge case (if any)
    applies, before the answer ever reaches the Day 29 TurnDecisionEngine."""

    def __init__(self):
        self.thresholds = AUDIO_QUALITY_THRESHOLDS

    def detect(self, answer: dict) -> dict:
        """Return a dict describing which edge case applies, or None."""
        text = (answer.get("clean_text") or "").strip()
        confidence = answer.get("confidence", 1.0)
        raw_text = (answer.get("raw_text") or text).lower()

        # 1. Missing answer — nothing usable at all
        if answer.get("word_count", len(text.split())) == 0 or text == "":
            return self._result("missing_answer", confidence, "No transcribed text present")

        # 2. Background noise markers in the raw transcript
        if any(marker in raw_text for marker in NOISE_KEYWORDS):
            return self._result("background_noise", confidence, "Noise markers found in transcript")

        # 3. Poor audio — confidence below the reliable threshold
        if confidence < self.thresholds["min_confidence"]:
            return self._result("poor_audio", confidence, "Confidence below minimum reliability threshold")

        # 4. Language mixing — heuristic marker match across multiple languages
        if self._detect_language_mix(raw_text):
            return self._result("language_mixing", confidence, "Multiple language markers detected in one answer")

        return {"edge_case": None, "confidence": confidence, "reason": None}

    def _detect_language_mix(self, text: str) -> bool:
        hits = 0
        for _, patterns in LANGUAGE_MIX_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    hits += 1
                    break
        return hits >= 1 and bool(re.search(r"[a-zA-Z]{3,}", text))

    def _result(self, edge_case: str, confidence: float, reason: str) -> dict:
        return {
            "edge_case":  edge_case,
            "confidence": confidence,
            "reason":     reason,
            "description": EDGE_CASE_TYPES.get(edge_case, ""),
        }


# ---------------------------------------------------------------------------
# RetryClarificationManager — what should we say and do about it?
# ---------------------------------------------------------------------------

class RetryClarificationManager:
    """Tracks how many times each edge case has occurred for a given
    question and the call overall, and produces the right fallback message
    and action at each stage."""

    def __init__(self):
        self.per_question_counts = {}   # {question_id: {edge_case: count}}
        self.total_edge_cases = 0
        self.consecutive_same_case = 0
        self.last_edge_case = None

    def handle(self, question_id: str, edge_case: str) -> dict:
        self.total_edge_cases += 1

        if edge_case == self.last_edge_case:
            self.consecutive_same_case += 1
        else:
            self.consecutive_same_case = 1
        self.last_edge_case = edge_case

        q_counts = self.per_question_counts.setdefault(question_id, {})
        q_counts[edge_case] = q_counts.get(edge_case, 0) + 1
        attempt = q_counts[edge_case]

        # Safety fallback checks take priority over normal retry staging
        if self.consecutive_same_case >= SAFETY_FALLBACKS["max_consecutive_failures"]:
            return {
                "action":  "hard_abort",
                "message": SAFETY_FALLBACKS["hard_abort_message"],
                "attempt": attempt,
            }
        if self.total_edge_cases >= SAFETY_FALLBACKS["max_total_edge_cases"]:
            return {
                "action":  "manual_review",
                "message": SAFETY_FALLBACKS["manual_review_message"],
                "attempt": attempt,
            }

        responses = FALLBACK_RESPONSES.get(edge_case, FALLBACK_RESPONSES["missing_answer"])
        if attempt == 1:
            return {"action": "retry", "message": responses["retry_1"], "attempt": attempt}
        elif attempt == 2:
            return {"action": "retry", "message": responses["retry_2"], "attempt": attempt}
        else:
            return {"action": "skip_with_flag", "message": responses["give_up"], "attempt": attempt}

    def get_summary(self) -> dict:
        return {
            "total_edge_cases":        self.total_edge_cases,
            "consecutive_same_case":   self.consecutive_same_case,
            "per_question_counts":     self.per_question_counts,
        }


# ---------------------------------------------------------------------------
# RobustFlowController — wraps Day 29's controller with edge-case handling
# ---------------------------------------------------------------------------

class RobustFlowController:
    """Wraps the Day 29 ConversationFlowController. Every incoming answer is
    first screened by EdgeCaseDetector. If no edge case is found, the answer
    is passed straight through to the normal Day 29 flow logic unchanged.
    If an edge case is found, RetryClarificationManager decides the action
    and the underlying state machine and decision engine are still kept in
    sync, so the call's overall state remains consistent."""

    def __init__(self, session_id: str, candidate_name: str = "Candidate"):
        self.flow = ConversationFlowController(session_id, candidate_name)
        self.detector = EdgeCaseDetector()
        self.retry_manager = RetryClarificationManager()
        self.edge_case_log = []

    def start_call(self):
        return self.flow.start_call()

    def ask_question(self, question_id: str, question_text: str):
        return self.flow.ask_question(question_id, question_text)

    def process_answer(self, answer: dict, question_id: str, answer_type: str = "text") -> dict:
        detection = self.detector.detect(answer)

        if detection["edge_case"] is None:
            # No edge case — defer entirely to Day 29's normal turn logic.
            result = self.flow.process_answer(answer, question_id, answer_type)
            result["edge_case_handled"] = False
            return result

        # An edge case was found — handle it through the retry manager.
        edge_case = detection["edge_case"]
        decision = self.retry_manager.handle(question_id, edge_case)

        self._log(question_id, edge_case, decision)

        if decision["action"] == "hard_abort":
            if self.flow.machine.state != "aborted" and self.flow.machine.can_transition("aborted"):
                self.flow.machine.transition("aborted")
        elif decision["action"] in ("skip_with_flag", "manual_review"):
            self.flow.machine.mark_skipped(question_id)

        return {
            "edge_case_handled": True,
            "edge_case":         edge_case,
            "action":            decision["action"],
            "message":           decision["message"],
            "attempt":           decision["attempt"],
            "state":             self.flow.machine.state,
        }

    def end_call(self):
        return self.flow.end_call()

    def _log(self, question_id: str, edge_case: str, decision: dict):
        self.edge_case_log.append({
            "question_id": question_id,
            "edge_case":   edge_case,
            "action":      decision["action"],
            "attempt":     decision["attempt"],
            "timestamp":   datetime.now().isoformat(),
        })

    def get_robustness_summary(self) -> dict:
        return {
            "flow_status":      self.flow.machine.get_status(),
            "edge_case_summary": self.retry_manager.get_summary(),
            "edge_case_log":     self.edge_case_log,
            "generated_at":      datetime.now().isoformat(),
        }
