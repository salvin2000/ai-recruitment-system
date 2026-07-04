"""
Day 34 - Dynamic Follow-Up Logic
Zecpath AI Recruitment Platform

Builds on Day 33's HR Interview Engine to enable adaptive questioning
based on candidate responses. Detects incomplete or vague answers,
generates three types of follow-up (clarification, deepening, example-
based), adapts difficulty based on response confidence, prevents
repetitive questioning, and tracks full conversation state throughout
the interview.
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FOLLOW_UP_TYPES = {
    "clarification": {
        "label":       "Clarification",
        "description": "Ask the candidate to clarify something unclear or ambiguous in their answer",
        "trigger":     "Answer contains vague language, contradictions, or is too generic",
    },
    "deepening": {
        "label":       "Deepening Question",
        "description": "Push the candidate to go deeper on something they mentioned",
        "trigger":     "Answer is factually complete but lacks detail, context, or reasoning",
    },
    "example_based": {
        "label":       "Example-Based Prompt",
        "description": "Ask the candidate for a specific real-world example to back up their claim",
        "trigger":     "Answer makes a claim (strength, skill, achievement) without a concrete example",
    },
}

VAGUE_SIGNAL_PHRASES = [
    "i think", "maybe", "kind of", "sort of", "not sure", "i guess",
    "probably", "might", "i don't know", "hard to say", "depends",
    "somewhat", "to some extent", "generally speaking",
]

INCOMPLETE_TRIGGERS = {
    "too_short":        "Response is under 15 words",
    "no_example":       "Response makes a claim without citing a specific situation",
    "no_number":        "Response about a quantifiable topic contains no numbers",
    "vague_language":   "Response contains hedging phrases indicating low confidence",
    "generic_answer":   "Response could apply to any candidate and references nothing specific",
    "contradiction":    "Response contradicts something said earlier in the session",
}

DIFFICULTY_LEVELS = {
    "surface":   {"score_range": (0,  40),  "label": "Surface", "next_action": "clarification"},
    "moderate":  {"score_range": (41, 65),  "label": "Moderate", "next_action": "deepening"},
    "confident": {"score_range": (66, 84),  "label": "Confident", "next_action": "example_based"},
    "strong":    {"score_range": (85, 100), "label": "Strong", "next_action": "none"},
}

FOLLOW_UP_TEMPLATES = {
    "clarification": {
        "self_introduction":      "Could you clarify what you mean by {keyword}? I want to make sure I understand correctly.",
        "career_journey":         "You mentioned {keyword} — could you tell me a bit more about what that involved?",
        "strengths_weaknesses":   "When you say {keyword}, what does that look like in practice for you?",
        "teamwork_culture_fit":   "You mentioned {keyword} — could you explain what you mean by that in a team context?",
        "career_goals":           "Could you be a bit more specific about {keyword}? What does that look like concretely?",
        "availability_commitment":"Just to confirm — when you say {keyword}, are we talking days, weeks, or months?",
    },
    "deepening": {
        "self_introduction":      "That's a strong background. What has been the single most defining moment in shaping who you are professionally?",
        "career_journey":         "Of all the roles you have described, which one challenged you the most and why?",
        "strengths_weaknesses":   "You identified that weakness — what concrete steps have you taken in the last 6 months to address it?",
        "teamwork_culture_fit":   "What is the hardest team situation you have ever been in, and how did you personally resolve it?",
        "career_goals":           "What specifically about this role makes it the right next step toward those goals?",
        "availability_commitment":"What would make you walk away from an offer even if everything else was right?",
    },
    "example_based": {
        "self_introduction":      "Can you give me one specific project or achievement that best represents your professional identity?",
        "career_journey":         "Can you walk me through one specific project from your career that you are genuinely proud of?",
        "strengths_weaknesses":   "Can you give me a real example of a time that strength made a measurable difference in an outcome?",
        "teamwork_culture_fit":   "Tell me about a specific time you had to work with someone whose style was completely different from yours.",
        "career_goals":           "What is one thing you have already done in the last year that is directly moving you toward that goal?",
        "availability_commitment":"Has there ever been a time you had to choose between a great opportunity and a personal commitment? What did you do?",
    },
}

MAX_FOLLOW_UPS_PER_QUESTION = 2
MAX_SAME_TYPE_REPEATS       = 1


# ---------------------------------------------------------------------------
# ResponseAnalyzer — what kind of answer was this?
# ---------------------------------------------------------------------------

class ResponseAnalyzer:
    """Analyzes a candidate's response and produces a structured assessment
    covering word count, vagueness, confidence score, and which incomplete
    triggers (if any) apply."""

    def analyze(self, response: str, category: str, prior_responses: list = None) -> dict:
        if not response:
            return self._empty()

        words = response.split()
        word_count = len(words)
        lower = response.lower()

        vague_hits = [p for p in VAGUE_SIGNAL_PHRASES if p in lower]
        is_vague = len(vague_hits) >= 2 or (len(vague_hits) >= 1 and word_count < 20)

        has_example = any(marker in lower for marker in [
            "for example", "for instance", "one time", "in my last", "when i",
            "i once", "i worked on", "i led", "i built", "i managed",
        ])

        has_number = any(char.isdigit() for char in response)

        is_generic = word_count > 10 and not has_example and len(vague_hits) >= 1

        is_contradiction = self._check_contradiction(lower, prior_responses or [])

        triggers = []
        if word_count < 15:
            triggers.append("too_short")
        if not has_example and category in ("strengths_weaknesses", "teamwork_culture_fit", "career_journey"):
            triggers.append("no_example")
        if category in ("career_goals", "availability_commitment") and not has_number:
            triggers.append("no_number")
        if is_vague:
            triggers.append("vague_language")
        if is_generic:
            triggers.append("generic_answer")
        if is_contradiction:
            triggers.append("contradiction")

        confidence_score = self._compute_confidence(word_count, vague_hits, has_example, has_number)

        return {
            "word_count":        word_count,
            "is_vague":          is_vague,
            "has_example":       has_example,
            "has_number":        has_number,
            "is_generic":        is_generic,
            "is_contradiction":  is_contradiction,
            "vague_hits":        vague_hits,
            "incomplete_triggers": triggers,
            "needs_follow_up":   len(triggers) > 0,
            "confidence_score":  confidence_score,
            "difficulty_level":  self._difficulty_level(confidence_score),
        }

    def _compute_confidence(self, word_count, vague_hits, has_example, has_number) -> int:
        score = 50
        if word_count >= 40: score += 15
        elif word_count >= 20: score += 8
        elif word_count < 10: score -= 20
        score -= len(vague_hits) * 8
        if has_example: score += 20
        if has_number: score += 10
        return max(0, min(100, score))

    def _difficulty_level(self, score: int) -> str:
        for level, info in DIFFICULTY_LEVELS.items():
            lo, hi = info["score_range"]
            if lo <= score <= hi:
                return level
        return "moderate"

    def _check_contradiction(self, lower: str, prior: list) -> bool:
        contradiction_pairs = [
            ("no experience", "years of experience"),
            ("i work alone", "team player"),
            ("not looking to relocate", "open to relocating"),
        ]
        for claim_a, claim_b in contradiction_pairs:
            if claim_b in lower and any(claim_a in p.lower() for p in prior):
                return True
        return False

    def _empty(self) -> dict:
        return {
            "word_count": 0, "is_vague": True, "has_example": False,
            "has_number": False, "is_generic": False, "is_contradiction": False,
            "vague_hits": [], "incomplete_triggers": ["too_short"],
            "needs_follow_up": True, "confidence_score": 0,
            "difficulty_level": "surface",
        }


# ---------------------------------------------------------------------------
# FollowUpEngine — what follow-up should we ask?
# ---------------------------------------------------------------------------

class FollowUpEngine:
    """Decides what type of follow-up to ask based on the response analysis,
    the difficulty level, and the history of follow-ups already asked for
    this question — preventing repetitive or redundant questioning."""

    def __init__(self):
        self.analyzer = ResponseAnalyzer()

    def decide(self, response: str, category: str, question_id: str,
               follow_up_history: list, prior_responses: list = None) -> dict:

        analysis = self.analyzer.analyze(response, category, prior_responses)

        if not analysis["needs_follow_up"]:
            return {"action": "none", "follow_up_type": None, "follow_up_text": None,
                    "analysis": analysis, "reason": "Response is complete and confident"}

        if len(follow_up_history) >= MAX_FOLLOW_UPS_PER_QUESTION:
            return {"action": "skip", "follow_up_type": None, "follow_up_text": None,
                    "analysis": analysis, "reason": "Maximum follow-ups reached for this question"}

        follow_up_type = self._select_type(analysis, follow_up_history)

        if follow_up_type is None:
            return {"action": "skip", "follow_up_type": None, "follow_up_text": None,
                    "analysis": analysis, "reason": "No new follow-up type available — would repeat"}

        keyword = self._extract_keyword(response)
        template = FOLLOW_UP_TEMPLATES[follow_up_type].get(category, "Could you elaborate a little more on that?")
        follow_up_text = template.replace("{keyword}", keyword)

        return {
            "action":          "ask_follow_up",
            "follow_up_type":  follow_up_type,
            "follow_up_text":  follow_up_text,
            "analysis":        analysis,
            "reason":          f"{analysis['difficulty_level']} response \u2192 {follow_up_type}",
        }

    def _select_type(self, analysis: dict, history: list) -> str:
        difficulty = analysis["difficulty_level"]
        preferred = DIFFICULTY_LEVELS[difficulty]["next_action"]
        if preferred == "none":
            return None

        # Walk the priority list, skip any type that has already been used
        priority = self._build_priority(preferred, analysis)
        used_types = [h.get("follow_up_type") for h in history]
        for ft in priority:
            if used_types.count(ft) < MAX_SAME_TYPE_REPEATS:
                return ft
        return None

    def _build_priority(self, preferred: str, analysis: dict) -> list:
        if preferred == "clarification":
            return ["clarification", "deepening", "example_based"]
        elif preferred == "deepening":
            return ["deepening", "example_based", "clarification"]
        else:
            return ["example_based", "deepening", "clarification"]

    def _extract_keyword(self, response: str) -> str:
        words = response.split()
        # Return the first meaningful noun-ish word (longer than 4 chars)
        for word in words:
            cleaned = word.strip(".,!?\"'").lower()
            if len(cleaned) > 4 and cleaned not in VAGUE_SIGNAL_PHRASES:
                return cleaned
        return "that point"


# ---------------------------------------------------------------------------
# ConversationStateTracker — full session state
# ---------------------------------------------------------------------------

class ConversationStateTracker:
    """Tracks the complete conversation state for an HR interview session.
    Records every question, every response, every follow-up asked and
    answered, and the running confidence profile across the session."""

    def __init__(self, session_id: str, candidate_name: str, role_profile: str):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.role_profile = role_profile
        self.turns = []
        self.all_responses = []
        self.engine = FollowUpEngine()

    def record_turn(self, question_id: str, category: str,
                    question_text: str, response: str) -> dict:
        prior = self.all_responses[:]
        follow_up_history = [
            t for t in self.turns
            if t["question_id"] == question_id and t.get("follow_up_type")
        ]

        decision = self.engine.decide(response, category, question_id,
                                      follow_up_history, prior)
        self.all_responses.append(response)

        turn = {
            "turn_number":    len(self.turns) + 1,
            "question_id":    question_id,
            "category":       category,
            "question_text":  question_text,
            "response":       response,
            "analysis":       decision["analysis"],
            "action":         decision["action"],
            "follow_up_type": decision["follow_up_type"],
            "follow_up_text": decision["follow_up_text"],
            "reason":         decision["reason"],
            "timestamp":      datetime.now().isoformat(),
        }
        self.turns.append(turn)
        return turn

    def get_confidence_profile(self) -> dict:
        if not self.turns:
            return {}
        scores = [t["analysis"]["confidence_score"] for t in self.turns]
        levels = [t["analysis"]["difficulty_level"] for t in self.turns]
        return {
            "average_confidence": round(sum(scores) / len(scores), 1),
            "min_confidence":     min(scores),
            "max_confidence":     max(scores),
            "level_distribution": {lvl: levels.count(lvl) for lvl in set(levels)},
            "follow_ups_asked":   sum(1 for t in self.turns if t["action"] == "ask_follow_up"),
            "questions_skipped":  sum(1 for t in self.turns if t["action"] == "skip"),
        }

    def get_full_state(self) -> dict:
        return {
            "session_id":        self.session_id,
            "candidate_name":    self.candidate_name,
            "role_profile":      self.role_profile,
            "total_turns":       len(self.turns),
            "turns":             self.turns,
            "confidence_profile": self.get_confidence_profile(),
            "generated_at":      datetime.now().isoformat(),
        }
