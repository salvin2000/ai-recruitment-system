"""
Day 24 – Speech-to-Text Integration & Cleaning
Zecpath AI Recruitment Platform

Converts raw voice input into clean, structured text for AI analysis.
Handles filler words, punctuation correction, case normalization,
interrupted speech, partial answers, and silence detection.
"""

import re
import json
from datetime import datetime
from typing import Optional


# ── STT Provider Config ───────────────────────────────────────────────────────

STT_PROVIDER_CONFIG = {
    "primary":   "google_stt",
    "fallback":  "azure_stt",
    "languages": ["en-IN", "hi-IN", "ml-IN", "ta-IN", "te-IN", "kn-IN"],
    "sample_rate_hz":    16000,
    "encoding":          "LINEAR16",
    "model":             "latest_long",
    "enable_diarization": True,
    "diarization_speakers": 2,
    "enable_punctuation": True,
    "enable_word_times":  True,
}

# ── Filler Word Dictionary ────────────────────────────────────────────────────

FILLER_WORDS = [
    "um", "uh", "hmm", "hm", "er", "erm",
    "you know", "i mean", "like", "basically",
    "actually", "literally", "right", "okay so",
    "so yeah", "and yeah", "kind of", "sort of",
    "let me think", "how do i say", "what do you call",
]

# ── Punctuation Correction Rules ─────────────────────────────────────────────

PUNCTUATION_RULES = [
    {"pattern": r"\s+([.,!?;:])",          "replacement": r"\1",       "desc": "Remove space before punctuation"},
    {"pattern": r"([.!?])\s*([A-Z])",      "replacement": r"\1 \2",    "desc": "Ensure space after sentence end"},
    {"pattern": r",\s*,",                  "replacement": ",",          "desc": "Remove double commas"},
    {"pattern": r"\.{4,}",                 "replacement": "...",        "desc": "Normalize ellipsis to 3 dots"},
    {"pattern": r"\s{2,}",                 "replacement": " ",          "desc": "Collapse multiple spaces"},
    {"pattern": r"([a-z])([A-Z])",         "replacement": r"\1. \2",   "desc": "Add period between sentences missing punctuation"},
]

# ── Accent Normalization Map ──────────────────────────────────────────────────

ACCENT_NORMALIZATION = {
    "kannot":      "cannot",
    "wont":        "won't",
    "dont":        "don't",
    "doesnt":      "doesn't",
    "im":          "I'm",
    "ive":         "I've",
    "id":          "I'd",
    "theyre":      "they're",
    "yrs":         "years",
    "yr":          "year",
    "exp":         "experience",
    "tech":        "technology",
    "dev":         "developer",
    "mgr":         "manager",
    "sr":          "senior",
    "jr":          "junior",
    "dept":        "department",
    "org":         "organization",
    "approx":      "approximately",
    "max":         "maximum",
    "min":         "minimum",
    "curr":        "current",
    "prev":        "previous",
}

# ── Silence / Interruption Thresholds ────────────────────────────────────────

SPEECH_THRESHOLDS = {
    "silence_flag_seconds":    5,    # Flag if candidate silent for 5+ seconds
    "silence_skip_seconds":    15,   # Skip question if silent for 15+ seconds
    "min_answer_words":        3,    # Minimum words for a valid answer
    "partial_answer_words":    10,   # Fewer than this = likely partial
    "interruption_gap_ms":     500,  # Overlap of 500ms = interruption
    "max_turn_duration_sec":   120,  # Flag turns longer than 2 minutes
}

# ── Accent Test Profiles ──────────────────────────────────────────────────────

ACCENT_TEST_PROFILES = [
    {"profile": "neutral_indian_english",  "region": "Bangalore/Hyderabad", "expected_wer": 0.08},
    {"profile": "south_indian_accent",     "region": "Kerala/Tamil Nadu",   "expected_wer": 0.12},
    {"profile": "north_indian_accent",     "region": "Delhi/UP",            "expected_wer": 0.10},
    {"profile": "mixed_hindi_english",     "region": "Pan-India",           "expected_wer": 0.15},
    {"profile": "fast_speaker",            "region": "Any",                 "expected_wer": 0.14},
    {"profile": "soft_speaker",            "region": "Any",                 "expected_wer": 0.18},
    {"profile": "background_noise",        "region": "Any",                 "expected_wer": 0.20},
    {"profile": "phone_quality_audio",     "region": "Any",                 "expected_wer": 0.22},
]

# ── STT Test Cases ────────────────────────────────────────────────────────────

STT_TEST_CASES = [
    {
        "test_id":    "STT-001",
        "category":   "filler_removal",
        "raw":        "Um, so I have like, you know, around five years of experience with Python.",
        "expected":   "I have around five years of experience with Python.",
        "accent":     "neutral_indian_english",
        "confidence": 0.92,
    },
    {
        "test_id":    "STT-002",
        "category":   "abbreviation_expansion",
        "raw":        "I have 3 yrs exp as a sr dev in a tech org.",
        "expected":   "I have 3 years experience as a senior developer in a technology organization.",
        "accent":     "neutral_indian_english",
        "confidence": 0.88,
    },
    {
        "test_id":    "STT-003",
        "category":   "yes_no_normalization",
        "raw":        "Yeah definitely that works for me absolutely.",
        "expected":   "Yes that works for me.",
        "accent":     "south_indian_accent",
        "confidence": 0.85,
    },
    {
        "test_id":    "STT-004",
        "category":   "pii_redaction",
        "raw":        "You can reach me at john@email.com or call 9876543210.",
        "expected":   "You can reach me at [EMAIL_REDACTED] or call [PHONE_REDACTED].",
        "accent":     "neutral_indian_english",
        "confidence": 0.94,
    },
    {
        "test_id":    "STT-005",
        "category":   "numeric_normalization",
        "raw":        "My CTC is around ten LPA and I expect fourteen to fifteen LPA.",
        "expected":   "My CTC is around 10 LPA and I expect 14 to 15 LPA.",
        "accent":     "north_indian_accent",
        "confidence": 0.87,
    },
    {
        "test_id":    "STT-006",
        "category":   "interrupted_speech",
        "raw":        "I have been working with— I mean my current role involves Python and Django.",
        "expected":   "My current role involves Python and Django.",
        "accent":     "neutral_indian_english",
        "confidence": 0.79,
    },
    {
        "test_id":    "STT-007",
        "category":   "partial_answer",
        "raw":        "Around three.",
        "expected":   "Around three.",
        "accent":     "south_indian_accent",
        "confidence": 0.91,
        "is_partial": True,
    },
    {
        "test_id":    "STT-008",
        "category":   "background_noise",
        "raw":        "I have [inaudible] years of experience with [noise] and Docker.",
        "expected":   "I have [inaudible] years of experience with [noise] and Docker.",
        "accent":     "background_noise",
        "confidence": 0.61,
        "flagged":    True,
    },
    {
        "test_id":    "STT-009",
        "category":   "mixed_language",
        "raw":        "Mera experience almost teen saal ka hai with Python.",
        "expected":   "Mera experience almost teen saal ka hai with Python.",
        "accent":     "mixed_hindi_english",
        "confidence": 0.76,
        "mixed_language": True,
    },
    {
        "test_id":    "STT-010",
        "category":   "punctuation_correction",
        "raw":        "i work at infosys i have been there for two years i use python and java",
        "expected":   "I work at Infosys. I have been there for two years. I use Python and Java.",
        "accent":     "neutral_indian_english",
        "confidence": 0.89,
    },
]


class STTCleaner:
    """
    Cleans raw Speech-to-Text output for AI analysis.
    Handles filler removal, punctuation correction, case normalization,
    interrupted speech, partial answers, and silence detection.
    """

    def __init__(self):
        self.fillers    = FILLER_WORDS
        self.punct_rules= PUNCTUATION_RULES
        self.accent_map = ACCENT_NORMALIZATION
        self.thresholds = SPEECH_THRESHOLDS

    # ── Filler Removal ────────────────────────────────────────────────────────

    def remove_fillers(self, text: str) -> str:
        """Remove filler words and phrases from text."""
        result = text
        sorted_fillers = sorted(self.fillers, key=len, reverse=True)
        for filler in sorted_fillers:
            pattern = r"(?<!\w)" + re.escape(filler) + r"(?!\w)"
            result  = re.sub(pattern, "", result, flags=re.IGNORECASE)
        result = re.sub(r"\s{2,}", " ", result).strip()
        result = re.sub(r"^[,\s]+", "", result)
        return result

    # ── Punctuation Correction ────────────────────────────────────────────────

    def fix_punctuation(self, text: str) -> str:
        """Apply punctuation correction rules."""
        result = text
        for rule in self.punct_rules:
            result = re.sub(rule["pattern"], rule["replacement"], result)
        if result and result[-1] not in ".!?":
            result = result.rstrip(",;:") + "."
        return result.strip()

    # ── Case Normalization ────────────────────────────────────────────────────

    def normalize_case(self, text: str) -> str:
        """Capitalize first letter of each sentence."""
        sentences = re.split(r"([.!?]\s+)", text)
        result = []
        for part in sentences:
            if part and not re.match(r"[.!?]\s+", part):
                part = part[0].upper() + part[1:] if part else part
            result.append(part)
        return "".join(result)

    # ── Abbreviation Expansion ────────────────────────────────────────────────

    def expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations to full words."""
        result = text
        for abbr, full in self.accent_map.items():
            pattern = r"(?<!\w)" + re.escape(abbr) + r"(?!\w)"
            result  = re.sub(pattern, full, result, flags=re.IGNORECASE)
        return result

    # ── PII Redaction ─────────────────────────────────────────────────────────

    def redact_pii(self, text: str) -> str:
        """Redact phone numbers, emails, and PAN/Aadhaar patterns."""
        text = re.sub(r"\b[6-9]\d{9}\b", "[PHONE_REDACTED]", text)
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                      "[EMAIL_REDACTED]", text)
        text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN_REDACTED]", text)
        text = re.sub(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[AADHAAR_REDACTED]", text)
        return text

    # ── Numeric Normalization ─────────────────────────────────────────────────

    def normalize_numbers(self, text: str) -> str:
        """Convert spoken numbers to digits."""
        word_to_num = {
            "zero": "0", "one": "1", "two": "2", "three": "3",
            "four": "4", "five": "5", "six": "6", "seven": "7",
            "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
            "twelve": "12", "thirteen": "13", "fourteen": "14",
            "fifteen": "15", "sixteen": "16", "seventeen": "17",
            "eighteen": "18", "nineteen": "19", "twenty": "20",
            "thirty": "30", "forty": "40", "fifty": "50",
            "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90",
        }
        result = text
        for word, digit in word_to_num.items():
            result = re.sub(r"(?<!\w)" + word + r"(?!\w)", digit,
                            result, flags=re.IGNORECASE)
        return result

    # ── Interruption Handling ─────────────────────────────────────────────────

    def handle_interruption(self, text: str) -> str:
        """
        Clean interrupted speech patterns.
        Removes incomplete sentence fragments ending with — or ...
        """
        text = re.sub(r"\b\w+\s*[\u2014\-]{1,2}\s*", "", text)
        text = re.sub(r"\b\w+\s*\.\.\.\s*", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text

    # ── Partial Answer Detection ──────────────────────────────────────────────

    def classify_answer_completeness(self, text: str) -> dict:
        """
        Classify whether an answer is complete, partial, or empty.
        Returns completeness tag and word count.
        """
        words    = [w for w in text.split() if w.strip()]
        count    = len(words)
        min_w    = self.thresholds["min_answer_words"]
        partial_w= self.thresholds["partial_answer_words"]

        if count == 0:
            tag = "empty"
        elif count < min_w:
            tag = "too_short"
        elif count < partial_w:
            tag = "partial"
        else:
            tag = "complete"

        return {
            "completeness": tag,
            "word_count":   count,
            "is_partial":   tag in ("partial", "too_short", "empty"),
            "needs_followup": tag in ("partial", "too_short"),
        }

    # ── Silence Detection ─────────────────────────────────────────────────────

    def classify_silence(self, silence_seconds: float) -> dict:
        """
        Classify a silence gap and return the recommended action.
        """
        flag_threshold = self.thresholds["silence_flag_seconds"]
        skip_threshold = self.thresholds["silence_skip_seconds"]

        if silence_seconds < flag_threshold:
            action = "continue"
            flag   = False
        elif silence_seconds < skip_threshold:
            action = "prompt_candidate"
            flag   = True
        else:
            action = "skip_question"
            flag   = True

        return {
            "silence_seconds": silence_seconds,
            "action":          action,
            "flagged":         flag,
            "message": (
                "Normal pause — continue"
                if action == "continue" else
                "Extended silence — prompt candidate to respond"
                if action == "prompt_candidate" else
                "Candidate unresponsive — skip to next question"
            ),
        }

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    def clean(self, raw_text: str,
              apply_pii_redaction: bool = True,
              apply_number_norm:   bool = True) -> dict:
        """
        Run the complete STT cleaning pipeline on raw text.
        Returns the cleaned text and a processing log.
        """
        steps = []

        text = raw_text
        steps.append({"step": "input",              "text": text})

        text = self.handle_interruption(text)
        steps.append({"step": "interruption_clean", "text": text})

        text = self.remove_fillers(text)
        steps.append({"step": "filler_removal",     "text": text})

        text = self.expand_abbreviations(text)
        steps.append({"step": "abbreviation_expand","text": text})

        if apply_number_norm:
            text = self.normalize_numbers(text)
            steps.append({"step": "number_normalize", "text": text})

        if apply_pii_redaction:
            text = self.redact_pii(text)
            steps.append({"step": "pii_redaction",    "text": text})

        text = self.fix_punctuation(text)
        steps.append({"step": "punctuation_fix",    "text": text})

        text = self.normalize_case(text)
        steps.append({"step": "case_normalize",     "text": text})

        completeness = self.classify_answer_completeness(text)

        return {
            "raw_text":    raw_text,
            "clean_text":  text,
            "steps":       steps,
            "completeness":completeness,
            "cleaned_at":  datetime.now().isoformat(),
        }


class STTAccuracyTester:
    """
    Runs STT accuracy tests against predefined test cases.
    Computes Word Error Rate (WER) and category-level pass rates.
    """

    def __init__(self):
        self.cleaner    = STTCleaner()
        self.test_cases = STT_TEST_CASES
        self.profiles   = ACCENT_TEST_PROFILES

    def compute_wer(self, reference: str, hypothesis: str) -> float:
        """
        Compute Word Error Rate (WER) between reference and hypothesis.
        WER = (substitutions + deletions + insertions) / total_reference_words
        """
        ref  = reference.lower().split()
        hyp  = hypothesis.lower().split()
        if not ref:
            return 0.0

        # Simple edit distance approach
        d = [[0]*(len(hyp)+1) for _ in range(len(ref)+1)]
        for i in range(len(ref)+1):
            d[i][0] = i
        for j in range(len(hyp)+1):
            d[0][j] = j
        for i in range(1, len(ref)+1):
            for j in range(1, len(hyp)+1):
                cost = 0 if ref[i-1] == hyp[j-1] else 1
                d[i][j] = min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+cost)

        return round(d[len(ref)][len(hyp)] / len(ref), 4)

    def run_test(self, test_case: dict) -> dict:
        """Run a single STT test case and return the result."""
        result   = self.cleaner.clean(test_case["raw"])
        cleaned  = result["clean_text"]
        wer      = self.compute_wer(test_case["expected"], cleaned)
        passed   = wer <= 0.25

        return {
            "test_id":    test_case["test_id"],
            "category":   test_case["category"],
            "accent":     test_case["accent"],
            "confidence": test_case["confidence"],
            "raw":        test_case["raw"],
            "expected":   test_case["expected"],
            "cleaned":    cleaned,
            "wer":        wer,
            "passed":     passed,
            "is_partial": test_case.get("is_partial", False),
            "flagged":    test_case.get("flagged", False),
        }

    def run_all_tests(self) -> dict:
        """Run all STT test cases and return a full accuracy report."""
        results  = [self.run_test(tc) for tc in self.test_cases]
        passed   = [r for r in results if r["passed"]]
        failed   = [r for r in results if not r["passed"]]

        by_category = {}
        for r in results:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0}
            by_category[cat]["total"]  += 1
            if r["passed"]:
                by_category[cat]["passed"] += 1

        avg_wer = round(sum(r["wer"] for r in results) / len(results), 4)

        return {
            "report_metadata": {
                "generated_at":  datetime.now().isoformat(),
                "total_tests":   len(results),
                "passed":        len(passed),
                "failed":        len(failed),
                "pass_rate":     round(len(passed)/len(results)*100, 1),
                "avg_wer":       avg_wer,
            },
            "by_category": by_category,
            "test_results": results,
            "accent_profiles": self.profiles,
        }

    def save_report(self, report: dict, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
