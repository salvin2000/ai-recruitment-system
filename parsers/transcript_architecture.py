"""
Day 23 – Transcript Data Architecture
Zecpath AI Recruitment Platform

Defines how voice conversations are converted into structured,
AI-processable data. Covers transcript storage structure, metadata
standards, normalization rules, and the database schema for
all screening interactions.
"""

import json
import re
from datetime import datetime
from typing import Optional


# ── Transcript Storage Format ─────────────────────────────────────────────────

TRANSCRIPT_STORAGE_FORMAT = {
    "version":     "1.0",
    "description": "Zecpath voice transcript storage format",
    "fields": {
        "transcript_id":   "Unique identifier for this transcript: ZCP-TR-{YYYYMMDD}-{seq}",
        "candidate_id":    "Links to candidate profile: ZCP-CAND-{code}",
        "job_id":          "Links to job posting: ZCP-JOB-{YYYYMMDD}-{code}",
        "session_id":      "Links to the screening session: ZCP-SESS-{YYYYMMDD}-{seq}",
        "created_at":      "ISO 8601 timestamp when transcript was created",
        "duration_seconds":"Total duration of the voice call in seconds",
        "language":        "BCP-47 language code — en-IN, hi-IN, ml-IN etc.",
        "status":          "completed / partial / failed / interrupted",
        "turns":           "Ordered list of conversation turns (utterances)",
        "metadata":        "Call-level metadata object",
        "summary":         "AI-generated summary of the screening outcome",
    },
}

# ── Metadata Standards ────────────────────────────────────────────────────────

METADATA_STANDARDS = {
    "candidate_id": {
        "format":      "ZCP-CAND-{4-char-code}",
        "example":     "ZCP-CAND-ARJU",
        "source":      "Generated at candidate registration",
        "required":    True,
        "description": "Unique identifier linking transcript to candidate profile",
    },
    "job_id": {
        "format":      "ZCP-JOB-{YYYYMMDD}-{role-code}",
        "example":     "ZCP-JOB-20260529-SW01",
        "source":      "Generated at job posting creation",
        "required":    True,
        "description": "Links transcript to the specific job the candidate applied for",
    },
    "question_id": {
        "format":      "Q{3-digit-number}",
        "example":     "Q031",
        "source":      "Day 22 screening dataset question bank",
        "required":    True,
        "description": "Links each turn to the question from the Day 22 dataset",
    },
    "session_id": {
        "format":      "ZCP-SESS-{YYYYMMDD}-{seq}",
        "example":     "ZCP-SESS-20260610-001",
        "source":      "Generated at session start",
        "required":    True,
        "description": "Unique identifier for one complete screening call session",
    },
    "timestamp": {
        "format":      "ISO 8601 — YYYY-MM-DDTHH:MM:SS.ffffff",
        "example":     "2026-06-10T10:15:32.442000",
        "source":      "Recorded at turn start by voice engine",
        "required":    True,
        "description": "Exact moment the AI or candidate began speaking this turn",
    },
    "confidence_level": {
        "format":      "float 0.0 to 1.0",
        "example":     "0.87",
        "source":      "Speech-to-text engine output",
        "required":    True,
        "description": "STT engine confidence in the transcription accuracy for this turn",
        "thresholds": {
            "high":    "0.85 and above — text used as-is",
            "medium":  "0.65 to 0.84 — text used with a low-confidence flag",
            "low":     "0.50 to 0.64 — human review recommended",
            "rejected":"Below 0.50 — turn marked unclear, not used in scoring",
        },
    },
    "speaker": {
        "format":      "ai / candidate",
        "example":     "candidate",
        "source":      "Speaker diarization from voice engine",
        "required":    True,
        "description": "Identifies whether the AI or the candidate spoke this turn",
    },
    "turn_index": {
        "format":      "integer starting at 0",
        "example":     "4",
        "source":      "Incremented sequentially during the call",
        "required":    True,
        "description": "Position of this turn in the conversation sequence",
    },
    "duration_ms": {
        "format":      "integer — milliseconds",
        "example":     "4200",
        "source":      "Measured by voice engine from start to end of utterance",
        "required":    False,
        "description": "Duration of this specific utterance in milliseconds",
    },
}

# ── Transcript Normalization Rules ────────────────────────────────────────────

NORMALIZATION_RULES = {
    "text_cleaning": [
        {"rule": "lowercase_trim",        "description": "Strip leading/trailing whitespace and lowercase for analysis"},
        {"rule": "remove_fillers",        "description": "Remove filler words: um, uh, hmm, you know, like, basically"},
        {"rule": "normalize_numbers",     "description": "Convert spoken numbers to digits: five -> 5, ten lakh -> 1000000"},
        {"rule": "normalize_currency",    "description": "Standardize salary mentions: 10 LPA, 10 lakhs per annum -> 1000000"},
        {"rule": "expand_abbreviations",  "description": "Expand: yrs -> years, exp -> experience, CTC -> cost to company"},
        {"rule": "remove_repetitions",    "description": "Remove immediate word repetitions: I I work -> I work"},
        {"rule": "normalize_punctuation", "description": "Add sentence-ending punctuation where missing using pause detection"},
        {"rule": "redact_pii",            "description": "Mask phone numbers, email addresses, and Aadhaar/PAN patterns"},
    ],
    "answer_extraction": [
        {"rule": "yes_no_detection",      "description": "Map affirmative/negative phrases to boolean: yeah/sure/of course -> yes"},
        {"rule": "numeric_extraction",    "description": "Extract numbers from text: around three years -> 3, about 8 LPA -> 800000"},
        {"rule": "skill_normalization",   "description": "Map skill variants: ML -> machine learning, JS -> javascript"},
        {"rule": "date_normalization",    "description": "Convert relative dates: next month -> YYYY-MM-DD from call date"},
        {"rule": "confidence_flagging",   "description": "Flag turns with STT confidence below 0.65 for human review"},
    ],
    "quality_checks": [
        {"rule": "min_word_count",        "description": "Flag text answers with fewer than 5 words as potentially incomplete"},
        {"rule": "language_detection",    "description": "Detect code-switching and tag turns with mixed language"},
        {"rule": "silence_detection",     "description": "Flag turns where candidate was silent for more than 5 seconds"},
        {"rule": "interruption_handling", "description": "Handle turns where AI and candidate spoke simultaneously"},
    ],
}

# ── Database Schema ───────────────────────────────────────────────────────────

DATABASE_SCHEMA = {
    "screening_sessions": {
        "description": "One record per screening call",
        "fields": {
            "session_id":        {"type": "VARCHAR(40)",  "pk": True,  "nullable": False},
            "transcript_id":     {"type": "VARCHAR(40)",  "pk": False, "nullable": False},
            "candidate_id":      {"type": "VARCHAR(20)",  "pk": False, "nullable": False, "fk": "candidates.candidate_id"},
            "job_id":            {"type": "VARCHAR(30)",  "pk": False, "nullable": False, "fk": "jobs.job_id"},
            "started_at":        {"type": "TIMESTAMP",    "pk": False, "nullable": False},
            "ended_at":          {"type": "TIMESTAMP",    "pk": False, "nullable": True},
            "duration_seconds":  {"type": "INTEGER",      "pk": False, "nullable": True},
            "status":            {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "language":          {"type": "VARCHAR(10)",  "pk": False, "nullable": False},
            "total_turns":       {"type": "INTEGER",      "pk": False, "nullable": True},
            "ai_version":        {"type": "VARCHAR(10)",  "pk": False, "nullable": True},
            "created_at":        {"type": "TIMESTAMP",    "pk": False, "nullable": False},
        },
    },
    "transcript_turns": {
        "description": "One record per utterance in the conversation",
        "fields": {
            "turn_id":           {"type": "VARCHAR(50)",  "pk": True,  "nullable": False},
            "session_id":        {"type": "VARCHAR(40)",  "pk": False, "nullable": False, "fk": "screening_sessions.session_id"},
            "turn_index":        {"type": "INTEGER",      "pk": False, "nullable": False},
            "speaker":           {"type": "VARCHAR(10)",  "pk": False, "nullable": False},
            "question_id":       {"type": "VARCHAR(10)",  "pk": False, "nullable": True, "fk": "screening_questions.question_id"},
            "raw_text":          {"type": "TEXT",         "pk": False, "nullable": False},
            "normalized_text":   {"type": "TEXT",         "pk": False, "nullable": True},
            "confidence_score":  {"type": "FLOAT",        "pk": False, "nullable": True},
            "confidence_level":  {"type": "VARCHAR(10)",  "pk": False, "nullable": True},
            "duration_ms":       {"type": "INTEGER",      "pk": False, "nullable": True},
            "started_at":        {"type": "TIMESTAMP",    "pk": False, "nullable": False},
            "is_flagged":        {"type": "BOOLEAN",      "pk": False, "nullable": False},
            "flag_reason":       {"type": "VARCHAR(100)", "pk": False, "nullable": True},
            "language":          {"type": "VARCHAR(10)",  "pk": False, "nullable": True},
        },
    },
    "extracted_answers": {
        "description": "Structured answers extracted from candidate turns",
        "fields": {
            "answer_id":         {"type": "VARCHAR(50)",  "pk": True,  "nullable": False},
            "turn_id":           {"type": "VARCHAR(50)",  "pk": False, "nullable": False, "fk": "transcript_turns.turn_id"},
            "session_id":        {"type": "VARCHAR(40)",  "pk": False, "nullable": False},
            "candidate_id":      {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "question_id":       {"type": "VARCHAR(10)",  "pk": False, "nullable": False},
            "answer_type":       {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "raw_answer":        {"type": "TEXT",         "pk": False, "nullable": False},
            "extracted_value":   {"type": "TEXT",         "pk": False, "nullable": True},
            "normalized_value":  {"type": "TEXT",         "pk": False, "nullable": True},
            "is_valid":          {"type": "BOOLEAN",      "pk": False, "nullable": False},
            "validation_notes":  {"type": "VARCHAR(200)", "pk": False, "nullable": True},
            "extracted_at":      {"type": "TIMESTAMP",    "pk": False, "nullable": False},
        },
    },
    "screening_scores": {
        "description": "Per-question and total scores from the screening call",
        "fields": {
            "score_id":          {"type": "VARCHAR(50)",  "pk": True,  "nullable": False},
            "session_id":        {"type": "VARCHAR(40)",  "pk": False, "nullable": False, "fk": "screening_sessions.session_id"},
            "candidate_id":      {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "question_id":       {"type": "VARCHAR(10)",  "pk": False, "nullable": False},
            "score":             {"type": "FLOAT",        "pk": False, "nullable": False},
            "max_score":         {"type": "FLOAT",        "pk": False, "nullable": False},
            "score_reason":      {"type": "VARCHAR(200)", "pk": False, "nullable": True},
            "scored_at":         {"type": "TIMESTAMP",    "pk": False, "nullable": False},
        },
    },
    "screening_results": {
        "description": "Final screening outcome per session",
        "fields": {
            "result_id":         {"type": "VARCHAR(50)",  "pk": True,  "nullable": False},
            "session_id":        {"type": "VARCHAR(40)",  "pk": False, "nullable": False, "fk": "screening_sessions.session_id"},
            "candidate_id":      {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "job_id":            {"type": "VARCHAR(30)",  "pk": False, "nullable": False},
            "total_score":       {"type": "FLOAT",        "pk": False, "nullable": False},
            "max_possible":      {"type": "FLOAT",        "pk": False, "nullable": False},
            "percentage":        {"type": "FLOAT",        "pk": False, "nullable": False},
            "outcome":           {"type": "VARCHAR(20)",  "pk": False, "nullable": False},
            "outcome_reason":    {"type": "VARCHAR(500)", "pk": False, "nullable": True},
            "ai_summary":        {"type": "TEXT",         "pk": False, "nullable": True},
            "reviewed_by":       {"type": "VARCHAR(50)",  "pk": False, "nullable": True},
            "reviewed_at":       {"type": "TIMESTAMP",    "pk": False, "nullable": True},
            "created_at":        {"type": "TIMESTAMP",    "pk": False, "nullable": False},
        },
    },
}

# ── Transcript Status Values ──────────────────────────────────────────────────

TRANSCRIPT_STATUS = {
    "completed":    "All questions were asked and candidate responses recorded",
    "partial":      "Call ended before all mandatory questions were answered",
    "failed":       "Technical failure prevented transcript creation",
    "interrupted":  "Candidate or AI disconnected mid-call",
    "rescheduled":  "Candidate requested to reschedule before call started",
}

# ── Screening Outcome Values ──────────────────────────────────────────────────

SCREENING_OUTCOMES = {
    "advance":       "Candidate passed screening — proceed to technical interview",
    "hold":          "Borderline result — requires human review before decision",
    "reject":        "Candidate did not meet screening criteria",
    "incomplete":    "Insufficient data to make a decision — reschedule",
    "no_show":       "Candidate did not attend the screening call",
}


class TranscriptArchitecture:
    """
    Manages the Zecpath transcript data architecture.
    Provides methods to create, validate, normalize, and query
    transcript records across the database schema.
    """

    def __init__(self):
        self.storage_format  = TRANSCRIPT_STORAGE_FORMAT
        self.metadata_std    = METADATA_STANDARDS
        self.norm_rules      = NORMALIZATION_RULES
        self.schema          = DATABASE_SCHEMA
        self.status_values   = TRANSCRIPT_STATUS
        self.outcome_values  = SCREENING_OUTCOMES

    # ── ID Generators ─────────────────────────────────────────────────────────

    def generate_transcript_id(self, date_str: str, seq: int) -> str:
        """Generate a transcript ID: ZCP-TR-YYYYMMDD-NNN"""
        return f"ZCP-TR-{date_str}-{seq:03d}"

    def generate_session_id(self, date_str: str, seq: int) -> str:
        """Generate a session ID: ZCP-SESS-YYYYMMDD-NNN"""
        return f"ZCP-SESS-{date_str}-{seq:03d}"

    def generate_turn_id(self, session_id: str, turn_index: int) -> str:
        """Generate a turn ID: {session_id}-T{NNN}"""
        return f"{session_id}-T{turn_index:03d}"

    # ── Confidence Classification ─────────────────────────────────────────────

    def classify_confidence(self, score: float) -> str:
        """Classify a confidence score into high/medium/low/rejected."""
        if score >= 0.85:
            return "high"
        elif score >= 0.65:
            return "medium"
        elif score >= 0.50:
            return "low"
        else:
            return "rejected"

    # ── Text Normalization ────────────────────────────────────────────────────

    def normalize_text(self, raw_text: str) -> str:
        """
        Apply normalization rules to raw STT output.
        Returns cleaned, analysis-ready text.
        """
        text = raw_text.strip().lower()

        # Remove filler words
        fillers = [r"\bum\b", r"\buh\b", r"\bhmm\b", r"\byou know\b",
                   r"\bbasically\b", r"\blike\b", r"\bso\b"]
        for filler in fillers:
            text = re.sub(filler, "", text)

        # Normalize yes/no variants
        text = re.sub(r"\b(yeah|yep|yup|sure|absolutely|of course|definitely)\b", "yes", text)
        text = re.sub(r"\b(nope|nah|no way|not really)\b", "no", text)

        # Normalize experience mentions
        text = re.sub(r"\b(\d+)\s+yrs?\b", r"\1 years", text)
        text = re.sub(r"\b(\d+)\s+exp\b", r"\1 years experience", text)

        # Redact PII patterns
        text = re.sub(r"\b\d{10}\b", "[PHONE_REDACTED]", text)         # phone
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]", text)
        text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN_REDACTED]", text)  # PAN

        # Clean up extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── Answer Extraction ─────────────────────────────────────────────────────

    def extract_yes_no(self, text: str) -> Optional[bool]:
        """Extract yes/no answer from normalized text."""
        text = text.lower()
        yes_patterns = [r"\byes\b", r"\byeah\b", r"\bsure\b", r"\bof course\b",
                        r"\bdefinitely\b", r"\babsolutely\b", r"\bcorrect\b", r"\bright\b"]
        no_patterns  = [r"\bno\b", r"\bnot\b", r"\bnope\b", r"\bcan't\b",
                        r"\bcannot\b", r"\bwon't\b", r"\bunable\b"]
        for pat in yes_patterns:
            if re.search(pat, text):
                return True
        for pat in no_patterns:
            if re.search(pat, text):
                return False
        return None

    def extract_numeric(self, text: str) -> Optional[float]:
        """Extract a numeric value from text."""
        patterns = [
            r"(\d+\.?\d*)\s*(?:years?|yrs?)",
            r"(\d+\.?\d*)\s*(?:lpa|lakhs?|lac)",
            r"\b(\d+\.?\d*)\b",
        ]
        for pat in patterns:
            match = re.search(pat, text.lower())
            if match:
                return float(match.group(1))
        return None

    # ── Transcript Record Builders ────────────────────────────────────────────

    def build_turn(self,
                   session_id:   str,
                   turn_index:   int,
                   speaker:      str,
                   raw_text:     str,
                   question_id:  Optional[str] = None,
                   confidence:   float = 1.0,
                   duration_ms:  int   = 0,
                   language:     str   = "en-IN") -> dict:
        """Build a single transcript turn record."""
        turn_id       = self.generate_turn_id(session_id, turn_index)
        normalized    = self.normalize_text(raw_text) if speaker == "candidate" else raw_text
        conf_level    = self.classify_confidence(confidence)
        is_flagged    = conf_level in ("low", "rejected")
        flag_reason   = (
            "STT confidence below 0.65 — human review recommended"
            if conf_level == "low" else
            "STT confidence below 0.50 — turn not used in scoring"
            if conf_level == "rejected" else None
        )

        return {
            "turn_id":          turn_id,
            "session_id":       session_id,
            "turn_index":       turn_index,
            "speaker":          speaker,
            "question_id":      question_id,
            "raw_text":         raw_text,
            "normalized_text":  normalized,
            "confidence_score": round(confidence, 4),
            "confidence_level": conf_level,
            "duration_ms":      duration_ms,
            "started_at":       datetime.now().isoformat(),
            "is_flagged":       is_flagged,
            "flag_reason":      flag_reason,
            "language":         language,
        }

    def build_transcript(self,
                          candidate_id: str,
                          job_id:       str,
                          turns:        list,
                          language:     str = "en-IN",
                          status:       str = "completed") -> dict:
        """Build a complete transcript record from a list of turns."""
        now      = datetime.now()
        date_str = now.strftime("%Y%m%d")
        tr_id    = self.generate_transcript_id(date_str, 1)
        sess_id  = self.generate_session_id(date_str, 1)

        cand_turns = [t for t in turns if t["speaker"] == "candidate"]
        avg_conf   = (
            round(sum(t["confidence_score"] for t in cand_turns) / len(cand_turns), 4)
            if cand_turns else 0.0
        )

        return {
            "transcript_id":   tr_id,
            "session_id":      sess_id,
            "candidate_id":    candidate_id,
            "job_id":          job_id,
            "created_at":      now.isoformat(),
            "duration_seconds":sum(t.get("duration_ms", 0) for t in turns) // 1000,
            "language":        language,
            "status":          status,
            "total_turns":     len(turns),
            "ai_turns":        sum(1 for t in turns if t["speaker"] == "ai"),
            "candidate_turns": len(cand_turns),
            "avg_confidence":  avg_conf,
            "flagged_turns":   sum(1 for t in turns if t["is_flagged"]),
            "turns":           turns,
        }

    # ── Schema Summary ────────────────────────────────────────────────────────

    def get_schema_summary(self) -> dict:
        """Return a summary of the database schema."""
        return {
            "tables":        list(self.schema.keys()),
            "total_tables":  len(self.schema),
            "field_counts":  {t: len(d["fields"]) for t, d in self.schema.items()},
            "total_fields":  sum(len(d["fields"]) for d in self.schema.values()),
            "primary_keys":  {
                t: [f for f, m in d["fields"].items() if m.get("pk")]
                for t, d in self.schema.items()
            },
            "foreign_keys":  {
                t: {f: m["fk"] for f, m in d["fields"].items() if "fk" in m}
                for t, d in self.schema.items()
            },
        }

    def validate_turn(self, turn: dict) -> dict:
        """Validate a turn record against the schema."""
        required = ["turn_id","session_id","turn_index","speaker",
                    "raw_text","confidence_score","started_at","is_flagged"]
        missing  = [f for f in required if f not in turn]
        valid_speakers = ["ai", "candidate"]
        errors = []
        if missing:
            errors.append(f"Missing required fields: {missing}")
        if turn.get("speaker") not in valid_speakers:
            errors.append(f"Invalid speaker: {turn.get('speaker')}")
        if not (0.0 <= turn.get("confidence_score", -1) <= 1.0):
            errors.append("confidence_score must be between 0.0 and 1.0")
        return {"valid": len(errors) == 0, "errors": errors}

    def save_architecture(self, output_path: str):
        """Save the complete architecture definition to JSON."""
        architecture = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version":      "1.0",
                "project":      "Zecpath AI Recruitment System",
                "day":          23,
            },
            "transcript_storage_format": self.storage_format,
            "metadata_standards":        self.metadata_std,
            "normalization_rules":       self.norm_rules,
            "database_schema":           self.schema,
            "transcript_status":         self.status_values,
            "screening_outcomes":        self.outcome_values,
            "schema_summary":            self.get_schema_summary(),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(architecture, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
