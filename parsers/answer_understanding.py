"""
Day 25 – Answer Intent & Understanding Engine
Zecpath AI Recruitment Platform

Enables AI to understand what the candidate actually meant.
Classifies answer intent, extracts structured information,
detects off-topic or vague responses, and builds semantic answer objects.
"""

import re
import json
from datetime import datetime
from typing import Optional


# ── Intent Categories ─────────────────────────────────────────────────────────

INTENT_CATEGORIES = {
    "affirmative":     "Candidate confirmed or agreed — yes, definitely, of course",
    "negative":        "Candidate declined or disagreed — no, not really, cannot",
    "experience_info": "Candidate described their work history or role",
    "skill_info":      "Candidate mentioned specific technical or soft skills",
    "availability":    "Candidate described their notice period or start date",
    "salary_info":     "Candidate mentioned current or expected compensation",
    "education_info":  "Candidate described their academic background",
    "location_info":   "Candidate described their location or relocation preference",
    "clarification":   "Candidate asked for the question to be repeated or clarified",
    "off_topic":       "Candidate's response does not relate to the question asked",
    "vague":           "Candidate's response is too unclear to extract useful information",
    "partial":         "Candidate began answering but did not complete the answer",
    "unknown":         "Intent could not be determined from the response",
}

# ── Intent Signal Patterns ────────────────────────────────────────────────────

INTENT_SIGNALS = {
    "affirmative": [
        r"\byes\b", r"\byeah\b", r"\bsure\b", r"\bdefinitely\b",
        r"\babsolutely\b", r"\bof course\b", r"\bcorrect\b", r"\bright\b",
        r"\bthat's fine\b", r"\bthat works\b", r"\bi am comfortable\b",
        r"\bi can\b", r"\bi will\b", r"\bhappy to\b",
    ],
    "negative": [
        r"\bno\b", r"\bnot\b", r"\bcannot\b", r"\bcan't\b",
        r"\bwon't\b", r"\bunable\b", r"\bdon't\b", r"\bdoesn't\b",
        r"\bnot really\b", r"\bnot at this time\b", r"\bnot interested\b",
        r"\bi am not\b", r"\bi would not\b",
    ],
    "experience_info": [
        r"\b\d+\.?\d*\s*years?\b", r"\bworked\b", r"\bworking\b",
        r"\bcurrent(?:ly)?\b", r"\bprevious(?:ly)?\b", r"\brole\b",
        r"\bposition\b", r"\bcompany\b", r"\borganization\b",
        r"\bresponsibilit\w+\b", r"\bproject\b", r"\bteam\b",
        r"\blead\b", r"\bmanaged\b", r"\bdeveloped\b",
    ],
    "skill_info": [
        r"\bpython\b", r"\bjava\b", r"\bjavascript\b", r"\breact\b",
        r"\bdjango\b", r"\baws\b", r"\bdocker\b", r"\bkubernetes\b",
        r"\bsql\b", r"\bmachine learning\b", r"\bml\b", r"\bai\b",
        r"\bproficient\b", r"\bexperienced in\b", r"\bskilled\b",
        r"\bknowledge of\b", r"\bfamiliar with\b", r"\bworked with\b",
    ],
    "availability": [
        r"\bnotice period\b", r"\bserving notice\b", r"\bcan join\b",
        r"\bavailable\b", r"\bimmediately\b", r"\bstart\b",
        r"\b\d+\s*days?\b", r"\bweeks?\b", r"\bmonths?\b",
        r"\brelieve\b", r"\bresign\b", r"\bjoin\b",
    ],
    "salary_info": [
        r"\bctc\b", r"\blpa\b", r"\blakhs?\b", r"\bsalary\b",
        r"\bcompensation\b", r"\bpackage\b", r"\bexpect\b",
        r"\bcurrent(?:ly)?\s+(?:drawing|earning|getting)\b",
        r"\b\d+\s*(?:lpa|lakhs?|lac)\b",
    ],
    "education_info": [
        r"\bb\.?tech\b", r"\bm\.?tech\b", r"\bbca\b", r"\bmca\b",
        r"\bmba\b", r"\bgraduated\b", r"\bdegree\b", r"\buniversity\b",
        r"\bcollege\b", r"\bspecializ\w+\b", r"\bcertif\w+\b",
        r"\bcomputer science\b", r"\bit\b", r"\binformation technology\b",
    ],
    "location_info": [
        r"\bbangalore\b", r"\bmumbai\b", r"\bdelhi\b", r"\bhyderabad\b",
        r"\bchennai\b", r"\bpune\b", r"\bkochi\b", r"\blocation\b",
        r"\breloc\w+\b", r"\bremote\b", r"\bhybrid\b", r"\bwork from home\b",
        r"\bwfh\b", r"\bbased in\b", r"\bcurrently in\b",
    ],
    "clarification": [
        r"\bsorry\b", r"\bpardon\b", r"\bcould you repeat\b",
        r"\bcan you repeat\b", r"\bdidn't understand\b",
        r"\bwhat did you\b", r"\bnot sure what\b", r"\bclarify\b",
        r"\bcome again\b", r"\bplease say\b",
    ],
}

# ── Vague Answer Patterns ─────────────────────────────────────────────────────

VAGUE_PATTERNS = [
    r"^(i don't know\.?|not sure\.?|maybe\.?|perhaps\.?|possibly\.?)$",
    r"^(it depends\.?|depends on\.?|not really\.?)$",
    r"^(kind of\.?|sort of\.?|more or less\.?)$",
    r"^(yes or no\.?|both\.?|neither\.?)$",
    r"^(i'll think about it\.?|let me check\.?)$",
]

# ── Off-Topic Signals ─────────────────────────────────────────────────────────

OFF_TOPIC_SIGNALS = [
    r"\bweather\b", r"\bpolitics\b", r"\bsport\w*\b", r"\bcricket\b",
    r"\bmovie\b", r"\bfilm\b", r"\bmusic\b", r"\bfood\b",
    r"\bjoke\b", r"\bfunny\b", r"\bunrelated\b",
]

# ── Structured Answer Schema ──────────────────────────────────────────────────

ANSWER_SCHEMA = {
    "answer_id":       "Unique ID for this answer: ANS-{session_id}-{question_id}",
    "session_id":      "Links to screening session",
    "question_id":     "Links to Day 22 question bank",
    "raw_text":        "Original candidate utterance",
    "clean_text":      "After Day 24 cleaning pipeline",
    "intent":          "Primary intent category from INTENT_CATEGORIES",
    "sub_intents":     "Additional intent categories detected",
    "extracted":       "Structured data extracted from the answer",
    "is_valid":        "Whether the answer is usable for scoring",
    "is_vague":        "Whether the answer is too unclear to use",
    "is_off_topic":    "Whether the answer is unrelated to the question",
    "needs_followup":  "Whether the AI should ask a follow-up",
    "confidence":      "STT confidence score for this turn",
    "scored_at":       "Timestamp of extraction",
}

# ── Extraction Rules ──────────────────────────────────────────────────────────

EXTRACTION_RULES = {
    "experience_years": {
        "patterns": [
            r"(\d+\.?\d*)\s*(?:\+\s*)?years?",
            r"(\d+\.?\d*)\s*(?:\+\s*)?yrs?",
            r"around\s+(\d+\.?\d*)",
            r"about\s+(\d+\.?\d*)",
            r"almost\s+(\d+\.?\d*)",
            r"over\s+(\d+\.?\d*)",
        ],
        "type": "float",
        "unit": "years",
    },
    "salary_lpa": {
        "patterns": [
            r"(\d+\.?\d*)\s*(?:lpa|lakhs?\s*per\s*annum|lac\s*per\s*annum)",
            r"(\d+\.?\d*)\s*lakhs?",
            r"(\d+\.?\d*)\s*lac\b",
        ],
        "type": "float",
        "unit": "LPA",
    },
    "notice_days": {
        "patterns": [
            r"(\d+)\s*days?\s*(?:notice)?",
            r"notice\s+(?:period\s+(?:is|of)\s+)?(\d+)\s*days?",
        ],
        "type": "int",
        "unit": "days",
    },
    "notice_months": {
        "patterns": [
            r"(\d+)\s*months?\s*(?:notice)?",
            r"notice\s+(?:period\s+(?:is|of)\s+)?(\d+)\s*months?",
        ],
        "type": "int",
        "unit": "months",
    },
    "skill_rating": {
        "patterns": [
            r"(\d)\s*(?:out\s+of\s+5|\/\s*5)",
            r"(\d)\s*on\s+a\s+scale",
        ],
        "type": "int",
        "unit": "out_of_5",
    },
    "team_size": {
        "patterns": [
            r"team\s+of\s+(\d+)",
            r"(\d+)\s+(?:member|people|person|developer)",
            r"(\d+)\s+(?:direct\s+)?reports?",
        ],
        "type": "int",
        "unit": "people",
    },
}


class IntentClassifier:
    """
    Classifies the intent of a candidate's answer.
    Returns the primary intent and any secondary intents detected.
    """

    def __init__(self):
        self.signals      = INTENT_SIGNALS
        self.vague        = VAGUE_PATTERNS
        self.off_topic    = OFF_TOPIC_SIGNALS
        self.categories   = INTENT_CATEGORIES

    def is_vague(self, text: str) -> bool:
        """Check if the answer matches a vague response pattern."""
        cleaned = text.strip().lower()
        for pat in self.vague:
            if re.match(pat, cleaned, re.IGNORECASE):
                return True
        word_count = len(cleaned.split())
        return word_count <= 2 and not any(
            re.search(sig, cleaned, re.IGNORECASE)
            for sigs in self.signals.values()
            for sig in sigs
        )

    def is_off_topic(self, text: str) -> bool:
        """Check if the answer contains off-topic signals."""
        text_lower = text.lower()
        return any(
            re.search(pat, text_lower, re.IGNORECASE)
            for pat in self.off_topic
        )

    def classify(self, text: str, question_category: str = "") -> dict:
        """
        Classify the intent of a candidate answer.
        Returns primary intent, sub-intents, and quality flags.
        """
        text_lower = text.lower()
        scores     = {}

        for intent, patterns in self.signals.items():
            score = sum(1 for pat in patterns
                        if re.search(pat, text_lower, re.IGNORECASE))
            if score > 0:
                scores[intent] = score

        # Determine primary intent
        if not scores:
            primary = "unknown"
        else:
            primary = max(scores, key=lambda k: scores[k])

        sub_intents = [i for i in scores if i != primary and scores[i] >= 1]

        # Quality flags
        vague     = self.is_vague(text)
        off_topic = self.is_off_topic(text)

        if vague:
            primary = "vague"
        if off_topic:
            primary = "off_topic"

        return {
            "primary_intent": primary,
            "sub_intents":    sub_intents,
            "intent_scores":  scores,
            "is_vague":       vague,
            "is_off_topic":   off_topic,
            "question_category": question_category,
        }


class AnswerExtractor:
    """
    Extracts structured values from candidate answers.
    Handles experience years, salary, notice period, skills, and ratings.
    """

    def __init__(self):
        self.rules = EXTRACTION_RULES

    def extract_experience(self, text: str) -> Optional[float]:
        """Extract years of experience from answer text."""
        for pat in self.rules["experience_years"]["patterns"]:
            m = re.search(pat, text.lower())
            if m:
                try:
                    return float(m.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def extract_salary(self, text: str) -> Optional[float]:
        """Extract salary in LPA from answer text."""
        for pat in self.rules["salary_lpa"]["patterns"]:
            m = re.search(pat, text.lower())
            if m:
                try:
                    return float(m.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def extract_notice_period(self, text: str) -> dict:
        """Extract notice period in days or months."""
        text_lower = text.lower()
        for pat in self.rules["notice_days"]["patterns"]:
            m = re.search(pat, text_lower)
            if m:
                try:
                    return {"value": int(m.group(1)), "unit": "days"}
                except (ValueError, IndexError):
                    continue
        for pat in self.rules["notice_months"]["patterns"]:
            m = re.search(pat, text_lower)
            if m:
                try:
                    months = int(m.group(1))
                    return {"value": months * 30, "unit": "days",
                            "original": f"{months} months"}
                except (ValueError, IndexError):
                    continue
        if re.search(r"\bimmediately\b|\bimmediate\b|\bno notice\b", text_lower):
            return {"value": 0, "unit": "days"}
        return {}

    def extract_skills(self, text: str) -> list:
        """Extract skill mentions from answer text."""
        skill_patterns = [
            "python", "java", "javascript", "typescript", "react", "angular",
            "vue", "node", "django", "flask", "fastapi", "spring", "aws",
            "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "machine learning", "deep learning", "tensorflow", "pytorch",
            "scikit-learn", "pandas", "numpy", "git", "linux", "ci/cd",
            "agile", "scrum", "rest api", "graphql", "microservices",
        ]
        text_lower = text.lower()
        found = [s for s in skill_patterns
                 if re.search(r"(?<!\w)" + re.escape(s) + r"(?!\w)",
                              text_lower)]
        return list(dict.fromkeys(found))

    def extract_rating(self, text: str) -> Optional[int]:
        """Extract self-rating on a 1-5 scale."""
        for pat in self.rules["skill_rating"]["patterns"]:
            m = re.search(pat, text.lower())
            if m:
                try:
                    val = int(m.group(1))
                    if 1 <= val <= 5:
                        return val
                except (ValueError, IndexError):
                    continue
        return None

    def extract_location(self, text: str) -> Optional[str]:
        """Extract city/location mention from answer text."""
        cities = [
            "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
            "chennai", "pune", "kochi", "cochin", "trivandrum",
            "kolkata", "ahmedabad", "jaipur", "noida", "gurgaon",
        ]
        text_lower = text.lower()
        for city in cities:
            if re.search(r"(?<!\w)" + city + r"(?!\w)", text_lower):
                return city.title()
        return None

    def extract_yes_no(self, text: str) -> Optional[bool]:
        """Extract a yes/no boolean from answer text."""
        text_lower = text.lower()
        yes_pats = [r"\byes\b", r"\byeah\b", r"\bsure\b", r"\bdefinitely\b",
                    r"\babsolutely\b", r"\bof course\b", r"\bi can\b",
                    r"\bi will\b", r"\bhappy to\b", r"\bcorrect\b"]
        no_pats  = [r"\bno\b", r"\bnot\b", r"\bcannot\b", r"\bcan't\b",
                    r"\bwon't\b", r"\bunable\b", r"\bnot really\b"]
        for pat in yes_pats:
            if re.search(pat, text_lower):
                return True
        for pat in no_pats:
            if re.search(pat, text_lower):
                return False
        return None

    def extract_all(self, text: str, answer_type: str = "text") -> dict:
        """
        Run all extractors and return a unified extraction result.
        Uses answer_type hint to prioritize relevant extractors.
        """
        extracted = {}

        if answer_type in ("yes_no", "confirmation"):
            val = self.extract_yes_no(text)
            if val is not None:
                extracted["boolean_value"] = val

        if answer_type in ("numeric", "text"):
            exp = self.extract_experience(text)
            if exp is not None:
                extracted["experience_years"] = exp

            sal = self.extract_salary(text)
            if sal is not None:
                extracted["salary_lpa"] = sal

            notice = self.extract_notice_period(text)
            if notice:
                extracted["notice_period"] = notice

            rating = self.extract_rating(text)
            if rating is not None:
                extracted["skill_rating"] = rating

        skills = self.extract_skills(text)
        if skills:
            extracted["skills_mentioned"] = skills

        location = self.extract_location(text)
        if location:
            extracted["location"] = location

        return extracted


class AnswerUnderstandingEngine:
    """
    Combines intent classification and answer extraction to build
    fully structured semantic answer objects for the AI scoring engine.
    """

    def __init__(self):
        self.classifier = IntentClassifier()
        self.extractor  = AnswerExtractor()

    def understand(self,
                   raw_text:          str,
                   clean_text:        str,
                   question_id:       str,
                   question_category: str,
                   answer_type:       str,
                   session_id:        str = "",
                   confidence:        float = 1.0) -> dict:
        """
        Build a fully structured semantic answer object.
        Combines intent classification with structured extraction.
        """
        intent_result = self.classifier.classify(clean_text, question_category)
        extracted     = self.extractor.extract_all(clean_text, answer_type)

        word_count    = len(clean_text.split())
        is_valid      = (
            not intent_result["is_vague"]
            and not intent_result["is_off_topic"]
            and word_count >= 1
            and confidence >= 0.50
        )
        needs_followup = (
            intent_result["is_vague"]
            or word_count < 3
            or (answer_type == "numeric" and "experience_years" not in extracted
                and "salary_lpa" not in extracted
                and "notice_period" not in extracted
                and "skill_rating" not in extracted)
        )

        answer_id = f"ANS-{session_id}-{question_id}" if session_id else f"ANS-{question_id}"

        return {
            "answer_id":        answer_id,
            "session_id":       session_id,
            "question_id":      question_id,
            "question_category":question_category,
            "answer_type":      answer_type,
            "raw_text":         raw_text,
            "clean_text":       clean_text,
            "intent":           intent_result["primary_intent"],
            "sub_intents":      intent_result["sub_intents"],
            "intent_scores":    intent_result["intent_scores"],
            "extracted":        extracted,
            "is_valid":         is_valid,
            "is_vague":         intent_result["is_vague"],
            "is_off_topic":     intent_result["is_off_topic"],
            "needs_followup":   needs_followup,
            "word_count":       word_count,
            "confidence":       confidence,
            "scored_at":        datetime.now().isoformat(),
        }

    def understand_batch(self, turns: list) -> list:
        """Process a batch of candidate turns into structured answers."""
        return [self.understand(**turn) for turn in turns]

    def save_results(self, results: list, output_path: str):
        """Save structured answer objects to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
