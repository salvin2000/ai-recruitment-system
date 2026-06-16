"""
Day 29 – AI Conversation Flow Design
Zecpath AI Recruitment Platform

Defines how AI interacts dynamically during screening calls.
Implements the conversation state machine, decision tree,
fallback questions, follow-up triggers, and error-handling flow.
"""

import json
from datetime import datetime
from typing import Optional


# ── Conversation States ───────────────────────────────────────────────────────

CONVERSATION_STATES = {
    "idle":           "Call not yet started",
    "greeting":       "AI is delivering the opening greeting",
    "asking":         "AI has asked a question and is waiting for response",
    "listening":      "Candidate is speaking — STT is capturing",
    "processing":     "AI is processing the candidate's answer",
    "follow_up":      "AI is asking a follow-up for an incomplete answer",
    "retry":          "AI is retrying after silence, confusion, or off-topic",
    "transitioning":  "AI is moving to the next question",
    "clarifying":     "AI is asking for clarification on a confusing answer",
    "wrapping_up":    "AI has asked all questions and is closing the call",
    "completed":      "Call completed successfully",
    "aborted":        "Call ended due to repeated failures or candidate request",
}

# ── State Transitions ─────────────────────────────────────────────────────────

STATE_TRANSITIONS = {
    "idle":          ["greeting"],
    "greeting":      ["asking"],
    "asking":        ["listening"],
    "listening":     ["processing"],
    "processing":    ["transitioning", "follow_up", "retry", "clarifying", "wrapping_up"],
    "follow_up":     ["listening"],
    "retry":         ["listening", "aborted"],
    "transitioning": ["asking", "wrapping_up"],
    "clarifying":    ["listening"],
    "wrapping_up":   ["completed"],
    "completed":     [],
    "aborted":       [],
}

# ── Turn Outcomes ─────────────────────────────────────────────────────────────

TURN_OUTCOMES = {
    "valid_complete":     "Answer is valid and complete — move to next question",
    "valid_partial":      "Answer is valid but incomplete — ask follow-up",
    "vague":              "Answer is too vague to use — retry with rephrasing",
    "off_topic":          "Answer is off-topic — redirect politely",
    "silence":            "Candidate did not respond — prompt and retry",
    "confusion":          "Candidate asked for clarification — clarify and re-ask",
    "repeat_request":     "Candidate asked to repeat — repeat the question",
    "contradiction":      "Candidate contradicted earlier answer — note and continue",
    "max_retries_reached":"Maximum retries exceeded — skip question",
    "call_abort_request": "Candidate requested to end the call",
}

# ── Fallback Questions ────────────────────────────────────────────────────────

FALLBACK_QUESTIONS = {
    "experience": [
        "Let me rephrase — approximately how many years have you been working in a professional role?",
        "To help me understand your background, could you tell me which year you started your career?",
        "That's fine — can you give me a rough number of years you have been working?",
    ],
    "skills": [
        "No problem — could you name just one or two technologies you use most frequently at work?",
        "Let me ask differently — what does a typical day of technical work look like for you?",
        "Could you mention the programming languages or tools you are most comfortable with?",
    ],
    "salary": [
        "I understand salary can be sensitive — could you share a rough expected range?",
        "No pressure — our budget for this role is flexible. What would make this move worthwhile for you?",
        "Could you share your current compensation so we can check alignment with our range?",
    ],
    "notice_period": [
        "That's fine — roughly how soon could you start if you were selected?",
        "Could you give me a ballpark — are we talking days, weeks, or months before you could join?",
        "Is your notice period negotiable at all with your current employer?",
    ],
    "location": [
        "Let me clarify — this role is based in {location}. Would that work for you?",
        "Are you open to discussing location flexibility if the role is a good fit?",
        "Would working from {location} be possible, even with some remote days?",
    ],
    "general": [
        "I did not quite catch that — could you repeat your answer?",
        "Could you please elaborate a little more on that?",
        "I want to make sure I understand correctly — could you rephrase that?",
    ],
}

# ── Follow-Up Triggers ────────────────────────────────────────────────────────

FOLLOW_UP_TRIGGERS = {
    "too_short":       "Answer has fewer than 3 words — ask for elaboration",
    "partial":         "Answer has 3-9 words — may be incomplete",
    "no_numeric":      "Numeric question answered with no number — ask for specific value",
    "no_boolean":      "Yes/no question answered without clear affirmative or negative",
    "vague_qualifier": "Answer contains maybe, perhaps, sort of, kind of — ask for specifics",
    "missing_skill":   "Asked about primary skill but skill not mentioned in answer",
    "generic_answer":  "Answer is generic and does not reference the specific question",
}

# ── Follow-Up Messages ────────────────────────────────────────────────────────

FOLLOW_UP_MESSAGES = {
    "too_short":       "Could you tell me a little more about that?",
    "partial":         "That's helpful — could you give me a bit more detail?",
    "no_numeric":      "Could you give me a specific number for that?",
    "no_boolean":      "Just to confirm — would you say yes or no to that?",
    "vague_qualifier": "I want to make sure I understand — could you be more specific?",
    "missing_skill":   "Could you confirm whether you have experience with {skill}?",
    "generic_answer":  "Could you relate that specifically to the question I asked?",
}

# ── Silence Handling ──────────────────────────────────────────────────────────

SILENCE_HANDLING = {
    "prompt_1":  {
        "trigger_sec": 5,
        "message":     "Take your time — I am still listening.",
        "action":      "continue_listening",
    },
    "prompt_2":  {
        "trigger_sec": 10,
        "message":     "No rush — whenever you are ready, please go ahead.",
        "action":      "continue_listening",
    },
    "retry":     {
        "trigger_sec": 15,
        "message":     "I did not hear a response. Let me ask that again.",
        "action":      "retry_question",
    },
    "skip":      {
        "trigger_sec": 25,
        "message":     "That's alright — let's move on to the next question.",
        "action":      "skip_question",
    },
}

# ── Retry Config ──────────────────────────────────────────────────────────────

RETRY_CONFIG = {
    "max_retries_per_question": 2,
    "max_skips_per_session":    3,
    "abort_threshold":          5,   # Abort if total failures exceed this
    "retry_delay_seconds":      2,
    "politeness_prefix": [
        "No problem — ",
        "That's alright — ",
        "Let me try that again — ",
    ],
}

# ── Polite Messages ───────────────────────────────────────────────────────────

POLITE_MESSAGES = {
    "off_topic_redirect":   "That's interesting! Let's refocus — {original_question}",
    "contradiction_note":   "Just to clarify — earlier you mentioned {earlier_answer}. Could you confirm your answer?",
    "repeat_question":      "Of course — {question_text}",
    "max_retries_skip":     "No worries — let's move on to the next question.",
    "call_closing":         "Thank you so much for your time, {candidate_name}. We have completed the screening. Our recruiter will review and get back to you shortly.",
    "call_abort":           "I understand. Thank you for your time today, {candidate_name}. We will follow up with you soon.",
    "clarification_offer":  "Let me clarify — {clarification_text}",
    "encouragement":        "Great, thank you! Let's continue.",
    "technical_issue":      "I'm sorry, I did not catch that clearly. Could you please repeat your answer?",
}


class ConversationStateMachine:
    """
    Manages the state of a single AI screening call.
    Tracks current state, turn count, retry count, and skip count.
    Validates all state transitions.
    """

    def __init__(self, session_id: str, candidate_name: str):
        self.session_id      = session_id
        self.candidate_name  = candidate_name
        self.state           = "idle"
        self.previous_state  = None
        self.turn_count      = 0
        self.retry_count     = {}   # Per question
        self.skip_count      = 0
        self.total_failures  = 0
        self.question_queue  = []
        self.asked_questions = []
        self.skipped_questions = []
        self.state_history   = []
        self.created_at      = datetime.now().isoformat()

    def can_transition(self, new_state: str) -> bool:
        """Check if transition from current state to new_state is valid."""
        return new_state in STATE_TRANSITIONS.get(self.state, [])

    def transition(self, new_state: str) -> dict:
        """
        Transition to a new state if valid.
        Returns transition result with success flag and reason.
        """
        if not self.can_transition(new_state):
            return {
                "success": False,
                "reason":  f"Invalid transition: {self.state} -> {new_state}",
                "state":   self.state,
            }

        self.state_history.append({
            "from":       self.previous_state,
            "to":         new_state,
            "turn":       self.turn_count,
            "timestamp":  datetime.now().isoformat(),
        })
        self.previous_state = self.state
        self.state          = new_state

        return {"success": True, "state": self.state, "previous": self.previous_state}

    def increment_retry(self, question_id: str) -> int:
        """Increment retry count for a question and return new count."""
        self.retry_count[question_id] = self.retry_count.get(question_id, 0) + 1
        self.total_failures += 1
        return self.retry_count[question_id]

    def should_abort(self) -> bool:
        """Check if the session should be aborted due to too many failures."""
        return self.total_failures >= RETRY_CONFIG["abort_threshold"]

    def should_skip(self, question_id: str) -> bool:
        """Check if a question should be skipped due to max retries."""
        retries = self.retry_count.get(question_id, 0)
        return retries >= RETRY_CONFIG["max_retries_per_question"]

    def mark_asked(self, question_id: str):
        """Record a question as asked."""
        if question_id not in self.asked_questions:
            self.asked_questions.append(question_id)
        self.turn_count += 1

    def mark_skipped(self, question_id: str):
        """Record a question as skipped."""
        self.skipped_questions.append(question_id)
        self.skip_count += 1

    def get_status(self) -> dict:
        """Return current session status."""
        return {
            "session_id":          self.session_id,
            "candidate_name":      self.candidate_name,
            "state":               self.state,
            "turn_count":          self.turn_count,
            "skip_count":          self.skip_count,
            "total_failures":      self.total_failures,
            "asked_questions":     self.asked_questions,
            "skipped_questions":   self.skipped_questions,
            "should_abort":        self.should_abort(),
            "retry_counts":        self.retry_count,
        }

    def to_dict(self) -> dict:
        return {
            **self.get_status(),
            "previous_state": self.previous_state,
            "state_history":  self.state_history,
            "created_at":     self.created_at,
        }


class TurnDecisionEngine:
    """
    Decides what the AI should do next based on the candidate's answer.
    Returns a turn action: next_question, follow_up, retry, clarify, or skip.
    """

    def __init__(self):
        self.outcomes        = TURN_OUTCOMES
        self.follow_triggers = FOLLOW_UP_TRIGGERS
        self.silence_cfg     = SILENCE_HANDLING
        self.retry_cfg       = RETRY_CONFIG

    def classify_turn(self,
                      answer:        dict,
                      question_id:   str,
                      answer_type:   str,
                      retry_count:   int = 0) -> dict:
        """
        Classify what happened in this turn and decide the next action.
        Returns action, message, next_state, and reason.
        """
        # Silence
        if not answer.get("clean_text", "").strip():
            return self._handle_silence(question_id, retry_count)

        # Off-topic
        if answer.get("is_off_topic"):
            return {
                "action":     "retry",
                "outcome":    "off_topic",
                "next_state": "retry",
                "message":    POLITE_MESSAGES["off_topic_redirect"],
                "reason":     TURN_OUTCOMES["off_topic"],
            }

        # Confusion / clarification request
        if answer.get("intent") == "clarification":
            return {
                "action":     "clarify",
                "outcome":    "confusion",
                "next_state": "clarifying",
                "message":    POLITE_MESSAGES["clarification_offer"],
                "reason":     TURN_OUTCOMES["confusion"],
            }

        # Vague answer
        if answer.get("is_vague"):
            if retry_count >= self.retry_cfg["max_retries_per_question"]:
                return self._skip_action(question_id)
            return {
                "action":     "retry",
                "outcome":    "vague",
                "next_state": "retry",
                "message":    FOLLOW_UP_MESSAGES["no_boolean"]
                              if answer_type == "yes_no"
                              else FOLLOW_UP_MESSAGES["vague_qualifier"],
                "reason":     TURN_OUTCOMES["vague"],
            }

        # Needs follow-up
        if answer.get("needs_followup"):
            trigger = self._identify_followup_trigger(answer, answer_type)
            return {
                "action":     "follow_up",
                "outcome":    "valid_partial",
                "next_state": "follow_up",
                "message":    FOLLOW_UP_MESSAGES.get(trigger, FOLLOW_UP_MESSAGES["partial"]),
                "reason":     FOLLOW_UP_TRIGGERS.get(trigger, ""),
                "trigger":    trigger,
            }

        # Valid complete
        return {
            "action":     "next_question",
            "outcome":    "valid_complete",
            "next_state": "transitioning",
            "message":    POLITE_MESSAGES["encouragement"],
            "reason":     TURN_OUTCOMES["valid_complete"],
        }

    def _handle_silence(self, question_id: str, retry_count: int) -> dict:
        """Handle a silent turn."""
        if retry_count == 0:
            cfg = self.silence_cfg["prompt_1"]
        elif retry_count == 1:
            cfg = self.silence_cfg["prompt_2"]
        elif retry_count == 2:
            cfg = self.silence_cfg["retry"]
        else:
            cfg = self.silence_cfg["skip"]
            return self._skip_action(question_id)

        return {
            "action":     "wait" if "listening" in cfg["action"] else "retry",
            "outcome":    "silence",
            "next_state": "retry" if "retry" in cfg["action"] else "listening",
            "message":    cfg["message"],
            "reason":     TURN_OUTCOMES["silence"],
        }

    def _skip_action(self, question_id: str) -> dict:
        """Return a skip action."""
        return {
            "action":     "skip",
            "outcome":    "max_retries_reached",
            "next_state": "transitioning",
            "message":    POLITE_MESSAGES["max_retries_skip"],
            "reason":     TURN_OUTCOMES["max_retries_reached"],
        }

    def _identify_followup_trigger(self, answer: dict, answer_type: str) -> str:
        """Identify the most specific follow-up trigger."""
        word_count = answer.get("word_count", 0)
        extracted  = answer.get("extracted", {})

        if word_count < 3:
            return "too_short"
        if answer_type == "yes_no" and "boolean_value" not in extracted:
            return "no_boolean"
        if answer_type == "numeric" and not any(
            k in extracted for k in
            ["experience_years", "salary_lpa", "notice_period", "skill_rating"]
        ):
            return "no_numeric"
        return "partial"

    def handle_contradiction(self,
                              current_answer: dict,
                              earlier_answer: dict) -> dict:
        """Handle a contradiction between current and earlier answers."""
        return {
            "action":     "note_and_continue",
            "outcome":    "contradiction",
            "next_state": "transitioning",
            "message":    POLITE_MESSAGES["contradiction_note"],
            "reason":     TURN_OUTCOMES["contradiction"],
        }


class ConversationFlowController:
    """
    Orchestrates the full AI screening call flow.
    Uses ConversationStateMachine and TurnDecisionEngine together.
    """

    def __init__(self, session_id: str, candidate_name: str):
        self.machine   = ConversationStateMachine(session_id, candidate_name)
        self.engine    = TurnDecisionEngine()
        self.session_id= session_id
        self.call_log  = []

    def start_call(self) -> dict:
        """Start the screening call."""
        self.machine.transition("greeting")
        greeting = POLITE_MESSAGES["call_closing"].replace(
            "We have completed the screening. Our recruiter will review and get back to you shortly.",
            "I am an AI screening assistant from Zecpath. This call will take about 10 minutes. Are you ready to proceed?"
        ).replace("{candidate_name}", self.machine.candidate_name)

        self._log("start_call", {"state": self.machine.state, "message": greeting})
        return {"state": self.machine.state, "message": greeting}

    def ask_question(self, question_id: str, question_text: str) -> dict:
        """Transition to asking state and deliver the question."""
        self.machine.transition("asking")
        self.machine.transition("listening")
        self.machine.mark_asked(question_id)
        self._log("ask_question", {"question_id": question_id, "text": question_text})
        return {
            "state":       self.machine.state,
            "question_id": question_id,
            "message":     question_text,
        }

    def process_answer(self,
                        answer:       dict,
                        question_id:  str,
                        answer_type:  str) -> dict:
        """Process a candidate's answer and decide next action."""
        self.machine.transition("processing")
        retry_count = self.machine.retry_count.get(question_id, 0)
        decision    = self.engine.classify_turn(
            answer, question_id, answer_type, retry_count
        )

        if decision["action"] in ("retry", "clarify"):
            self.machine.increment_retry(question_id)

        if decision["action"] == "skip" or \
           decision["outcome"] == "max_retries_reached":
            self.machine.mark_skipped(question_id)

        if self.machine.should_abort():
            self.machine.transition("aborted")
            decision["action"]     = "abort"
            decision["next_state"] = "aborted"
            decision["message"]    = POLITE_MESSAGES["call_abort"].replace(
                "{candidate_name}", self.machine.candidate_name
            )

        self.machine.transition(decision["next_state"])
        self._log("process_answer", {
            "question_id": question_id,
            "action":      decision["action"],
            "outcome":     decision["outcome"],
        })

        return {
            "action":      decision["action"],
            "outcome":     decision["outcome"],
            "message":     decision["message"],
            "state":       self.machine.state,
            "should_abort":self.machine.should_abort(),
        }

    def end_call(self) -> dict:
        """End the screening call."""
        if self.machine.state not in ("completed", "aborted"):
            self.machine.transition("wrapping_up")
            self.machine.transition("completed")

        closing = POLITE_MESSAGES["call_closing"].replace(
            "{candidate_name}", self.machine.candidate_name
        )
        self._log("end_call", {"state": self.machine.state})
        return {
            "state":   self.machine.state,
            "message": closing,
            "status":  self.machine.get_status(),
        }

    def _log(self, event: str, data: dict):
        """Add an event to the call log."""
        self.call_log.append({
            "event":     event,
            "state":     self.machine.state,
            "timestamp": datetime.now().isoformat(),
            **data,
        })

    def get_flow_summary(self) -> dict:
        """Return a summary of the conversation flow."""
        return {
            "session_id":   self.session_id,
            "final_status": self.machine.get_status(),
            "call_log":     self.call_log,
            "generated_at": datetime.now().isoformat(),
        }

    def save_flow(self, output_path: str):
        """Save conversation flow summary to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.get_flow_summary(), f, indent=2,
                      default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
