"""
Day 15 – Fairness, Normalization & Bias Reduction
Zecpath AI Recruitment Platform

Improves fairness, reduces bias, and standardizes resume evaluation
by masking personal attributes, normalizing scores, and detecting
bias indicators in the ATS pipeline.
"""

import re
import json
import math
from pathlib import Path
from datetime import datetime
from typing import Optional


# ── Personal Attribute Patterns ───────────────────────────────────────────────
# These attributes are masked to prevent bias in ATS scoring.
# Gender, age, religion, nationality should not influence hiring decisions.

BIAS_MASK_PATTERNS = {
    "name": [
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b",
    ],
    "email": [
        r"[\w\.\-]+@[\w\.\-]+\.\w+",
    ],
    "phone": [
        r"(\+?[\d][\d\s\-\(\)]{8,14}\d)",
    ],
    "gender_pronouns": [
        r"\b(he|she|his|her|him|himself|herself|mr\.?|mrs\.?|ms\.?|miss)\b",
    ],
    "age_indicators": [
        r"\b(born in|date of birth|dob|age\s*:\s*\d+|year of birth)\b",
        r"\b(19[6-9]\d|200[0-5])\b",   # birth years
    ],
    "religion": [
        r"\b(hindu|muslim|christian|sikh|jain|buddhist|jewish|"
        r"church|temple|mosque|synagogue|religion)\b",
    ],
    "caste": [
        r"\b(caste|sc|st|obc|general category|category\s*:\s*\w+)\b",
    ],
    "marital_status": [
        r"\b(married|unmarried|single|divorced|widowed|marital status)\b",
    ],
    "nationality_sensitive": [
        r"\b(nationality|citizenship|passport|visa|work permit|"
        r"permanent resident)\b",
    ],
    "photo_reference": [
        r"\b(photograph|photo enclosed|see attached photo)\b",
    ],
}

# ── Keyword Over-Dependence Patterns ──────────────────────────────────────────
# These are inflated buzzwords that add no real signal.

BUZZWORD_PATTERNS = [
    r"\b(passionate|enthusiastic|hardworking|team player|go-getter|"
    r"results-driven|self-starter|detail-oriented|synergy|leverage|"
    r"proactive|dynamic|innovative|cutting-edge|world-class|"
    r"guru|ninja|rockstar|wizard|superhero|unicorn)\b",
]

# ── Score Normalization Bounds ────────────────────────────────────────────────

NORMALIZATION_BOUNDS = {
    "skill_match":          {"min": 0.0,  "max": 1.0,  "target_min": 0.0, "target_max": 1.0},
    "experience_relevance": {"min": 0.0,  "max": 1.0,  "target_min": 0.0, "target_max": 1.0},
    "education_alignment":  {"min": 0.0,  "max": 1.0,  "target_min": 0.0, "target_max": 1.0},
    "semantic_similarity":  {"min": 0.0,  "max": 0.40, "target_min": 0.0, "target_max": 1.0},
    "final_score":          {"min": 0.0,  "max": 100.0,"target_min": 0.0, "target_max": 100.0},
}

# ── Bias Indicator Thresholds ─────────────────────────────────────────────────

BIAS_INDICATOR_THRESHOLDS = {
    "personal_info_density": 0.05,   # > 5% of words are personal info = flag
    "buzzword_density":       0.03,   # > 3% of words are buzzwords = flag
    "score_variance_flag":    20.0,   # score range > 20 between similar profiles
    "keyword_dependence":     0.60,   # skill score > 60% from exact keywords only
}


class ResumeNormalizer:
    """
    Normalizes resume text to a standard format.
    Removes personal attributes that could introduce bias.
    Reduces buzzword inflation that distorts keyword matching.
    """

    def __init__(self):
        self.mask_patterns  = BIAS_MASK_PATTERNS
        self.buzz_patterns  = BUZZWORD_PATTERNS

    def mask_personal_attributes(self,
                                  text: str,
                                  mask_fields: list = None) -> dict:
        """
        Mask personal attributes from resume text.
        Returns masked text and a report of what was masked.
        """
        mask_fields  = mask_fields or list(self.mask_patterns.keys())
        masked_text  = text
        masking_log  = {}

        for field in mask_fields:
            if field not in self.mask_patterns:
                continue
            patterns = self.mask_patterns[field]
            count    = 0
            for pattern in patterns:
                matches = re.findall(pattern, masked_text, re.IGNORECASE)
                if matches:
                    count += len(matches)
                    masked_text = re.sub(
                        pattern,
                        f"[{field.upper()}_MASKED]",
                        masked_text,
                        flags=re.IGNORECASE
                    )
            if count > 0:
                masking_log[field] = count

        return {
            "masked_text":  masked_text,
            "masking_log":  masking_log,
            "total_masked": sum(masking_log.values()),
        }

    def remove_buzzwords(self, text: str) -> dict:
        """
        Remove inflated buzzwords that add no real signal.
        Returns cleaned text and count of removed buzzwords.
        """
        cleaned_text = text
        total_removed = 0

        for pattern in self.buzz_patterns:
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            total_removed += len(matches)
            cleaned_text   = re.sub(
                pattern, "", cleaned_text, flags=re.IGNORECASE
            )

        # Clean up extra whitespace
        cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text).strip()

        return {
            "cleaned_text":    cleaned_text,
            "buzzwords_removed": total_removed,
        }

    def normalize_section_headings(self, text: str) -> str:
        """
        Normalize all section headings to a standard format.
        Ensures consistent heading names across all resume styles.
        """
        heading_map = {
            r"\bprofessional experience\b": "Work Experience",
            r"\bemployment history\b":      "Work Experience",
            r"\bcareer history\b":          "Work Experience",
            r"\bacademic background\b":     "Education",
            r"\beducational background\b":  "Education",
            r"\btechnical skills\b":        "Skills",
            r"\bcore competencies\b":       "Skills",
            r"\bkey skills\b":              "Skills",
            r"\bprofessional summary\b":    "Summary",
            r"\bcareer objective\b":        "Summary",
            r"\bobjective\b":               "Summary",
            r"\bachievements\b":            "Achievements",
            r"\baccomplishments\b":         "Achievements",
            r"\bcertifications\b":          "Certifications",
            r"\bcertificates\b":            "Certifications",
        }
        normalized = text
        for pattern, replacement in heading_map.items():
            normalized = re.sub(
                pattern, replacement, normalized, flags=re.IGNORECASE
            )
        return normalized

    def normalize_dates(self, text: str) -> str:
        """
        Normalize date formats to ISO YYYY-MM format.
        Reduces variation in date representation.
        """
        # Month name to number
        month_map = {
            "january": "01", "february": "02", "march": "03",
            "april": "04",   "may": "05",      "june": "06",
            "july": "07",    "august": "08",   "september": "09",
            "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "jun": "06", "jul": "07", "aug": "08", "sep": "09",
            "oct": "10", "nov": "11", "dec": "12",
        }
        normalized = text
        for month_name, month_num in month_map.items():
            pattern     = rf"\b{month_name}\b[\s,]+(\d{{4}})"
            replacement = rf"{month_num}-\1"
            normalized  = re.sub(
                pattern, replacement, normalized, flags=re.IGNORECASE
            )
        return normalized

    def normalize_resume(self, text: str,
                          mask_fields: list = None) -> dict:
        """
        Run full normalization pipeline on a resume.
        Returns normalized text with full audit log.
        """
        # Step 1: Mask personal attributes
        mask_result   = self.mask_personal_attributes(text, mask_fields)
        masked_text   = mask_result["masked_text"]

        # Step 2: Remove buzzwords
        buzz_result   = self.remove_buzzwords(masked_text)
        cleaned_text  = buzz_result["cleaned_text"]

        # Step 3: Normalize headings
        heading_text  = self.normalize_section_headings(cleaned_text)

        # Step 4: Normalize dates
        final_text    = self.normalize_dates(heading_text)

        return {
            "normalized_text":    final_text,
            "original_length":    len(text),
            "normalized_length":  len(final_text),
            "masking_log":        mask_result["masking_log"],
            "total_masked":       mask_result["total_masked"],
            "buzzwords_removed":  buzz_result["buzzwords_removed"],
        }


class ScoreNormalizer:
    """
    Normalizes ATS scores to ensure fairness across different
    resume formats and scoring runs.
    Min-max normalization maps raw scores to a consistent 0-1 range.
    Z-score normalization identifies statistical outliers.
    """

    def __init__(self, bounds: dict = None):
        self.bounds = bounds or NORMALIZATION_BOUNDS

    def min_max_normalize(self,
                           value: float,
                           component: str) -> float:
        """
        Normalize a score to 0-1 using min-max normalization.
        Maps raw scores from their natural range to target range.
        """
        if component not in self.bounds:
            return round(max(0.0, min(1.0, value)), 4)

        b          = self.bounds[component]
        raw_min    = b["min"]
        raw_max    = b["max"]
        target_min = b["target_min"]
        target_max = b["target_max"]

        if raw_max == raw_min:
            return target_min

        normalized = (value - raw_min) / (raw_max - raw_min)
        normalized = normalized * (target_max - target_min) + target_min
        return round(max(target_min, min(target_max, normalized)), 4)

    def z_score_normalize(self,
                           scores: list,
                           mean: float = None,
                           std: float  = None) -> list:
        """
        Compute z-scores for a list of scores.
        Z-score > 2 or < -2 indicates a statistical outlier.
        """
        if not scores:
            return []

        mean  = mean or (sum(scores) / len(scores))
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std   = std or math.sqrt(variance)

        if std == 0:
            return [0.0] * len(scores)

        return [round((s - mean) / std, 4) for s in scores]

    def normalize_batch(self, ats_results: list) -> list:
        """
        Normalize all component scores across a batch of candidates.
        Ensures scores are comparable regardless of resume format.
        """
        normalized_results = []

        for result in ats_results:
            norm_result = dict(result)
            components  = result.get("component_scores", {})
            norm_scores = {}

            for comp_name, comp_data in components.items():
                raw_score      = comp_data.get("raw_score", 0.0)
                normalized_val = self.min_max_normalize(raw_score, comp_name)
                norm_scores[comp_name] = {
                    **comp_data,
                    "normalized_score": normalized_val,
                    "normalization_applied": True,
                }

            norm_result["component_scores"]      = norm_scores
            norm_result["normalization_metadata"] = {
                "normalized_at":  datetime.now().isoformat(),
                "method":         "min-max",
                "bounds_used":    self.bounds,
            }
            normalized_results.append(norm_result)

        return normalized_results


class BiasDetector:
    """
    Detects bias indicators in resumes and ATS scoring results.
    Identifies over-reliance on keywords, demographic information
    in text, and statistical anomalies in score distributions.
    """

    def __init__(self, thresholds: dict = None):
        self.thresholds = thresholds or BIAS_INDICATOR_THRESHOLDS
        self.normalizer = ResumeNormalizer()

    def detect_personal_info_density(self, text: str) -> dict:
        """
        Measure how much personal information is in the resume.
        High density of personal info may bias keyword-based scoring.
        """
        words       = text.split()
        total_words = len(words) if words else 1
        total_pi    = 0

        pi_found = {}
        for field, patterns in BIAS_MASK_PATTERNS.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                count  += len(matches)
            if count > 0:
                pi_found[field] = count
                total_pi       += count

        density  = round(total_pi / total_words, 4)
        flagged  = density > self.thresholds["personal_info_density"]

        return {
            "personal_info_count":    total_pi,
            "total_words":            total_words,
            "density":                density,
            "flagged":                flagged,
            "fields_found":           pi_found,
            "threshold":              self.thresholds["personal_info_density"],
        }

    def detect_buzzword_density(self, text: str) -> dict:
        """
        Measure buzzword density in a resume.
        High buzzword density inflates keyword scores unfairly.
        """
        words         = text.split()
        total_words   = len(words) if words else 1
        total_buzz    = 0
        found_buzzwords = []

        for pattern in BUZZWORD_PATTERNS:
            matches      = re.findall(pattern, text, re.IGNORECASE)
            total_buzz  += len(matches)
            found_buzzwords.extend(matches)

        density = round(total_buzz / total_words, 4)
        flagged = density > self.thresholds["buzzword_density"]

        return {
            "buzzword_count":   total_buzz,
            "total_words":      total_words,
            "density":          density,
            "flagged":          flagged,
            "found_buzzwords":  list(set(found_buzzwords))[:10],
            "threshold":        self.thresholds["buzzword_density"],
        }

    def detect_score_variance(self, scores: list,
                               candidate_ids: list = None) -> dict:
        """
        Detect unusual score variance in a batch of candidates.
        High variance may indicate inconsistent scoring.
        """
        if not scores:
            return {"flagged": False, "reason": "No scores provided"}

        mean     = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev  = math.sqrt(variance)
        score_range = max(scores) - min(scores)

        outliers = []
        if len(scores) >= 3:
            z_scores = [(abs(s - mean) / std_dev) if std_dev > 0 else 0
                        for s in scores]
            for i, z in enumerate(z_scores):
                if z > 2.0:
                    cid = candidate_ids[i] if candidate_ids else f"candidate_{i}"
                    outliers.append({"candidate": cid,
                                     "score": scores[i], "z_score": round(z, 2)})

        return {
            "mean_score":   round(mean, 2),
            "std_dev":      round(std_dev, 2),
            "score_range":  round(score_range, 2),
            "min_score":    round(min(scores), 2),
            "max_score":    round(max(scores), 2),
            "outliers":     outliers,
            "flagged":      len(outliers) > 0,
            "threshold":    self.thresholds["score_variance_flag"],
        }

    def detect_keyword_dependence(self, skill_result: dict) -> dict:
        """
        Check if skill scoring is over-dependent on exact keyword matches.
        Over-reliance on exact matches misses candidates who describe
        skills differently.
        """
        if not skill_result or "skills" not in skill_result:
            return {"flagged": False, "reason": "No skill data"}

        skills      = skill_result["skills"]
        total       = len(skills)
        exact_only  = sum(1 for s in skills if s.get("match_type") == "exact")

        if total == 0:
            return {"flagged": False, "exact_ratio": 0.0, "total_skills": 0}

        exact_ratio = round(exact_only / total, 4)
        flagged     = exact_ratio > self.thresholds["keyword_dependence"]

        return {
            "total_skills":        total,
            "exact_match_count":   exact_only,
            "exact_ratio":         exact_ratio,
            "flagged":             flagged,
            "threshold":           self.thresholds["keyword_dependence"],
            "recommendation":      (
                "Consider enabling synonym and context matching "
                "to reduce keyword dependence."
            ) if flagged else "Keyword balance is acceptable.",
        }

    def evaluate_resume(self, text: str, skill_result: dict = None) -> dict:
        """
        Full bias evaluation of a single resume.
        Returns all bias indicators and an overall bias risk level.
        """
        pi_result   = self.detect_personal_info_density(text)
        buzz_result = self.detect_buzzword_density(text)
        kw_result   = self.detect_keyword_dependence(
            skill_result or {}
        )

        flags = []
        if pi_result["flagged"]:
            flags.append("High personal information density")
        if buzz_result["flagged"]:
            flags.append("High buzzword density")
        if kw_result.get("flagged"):
            flags.append("Over-dependence on exact keyword matching")

        risk_level = (
            "High"   if len(flags) >= 2 else
            "Medium" if len(flags) == 1 else
            "Low"
        )

        return {
            "bias_evaluation": {
                "evaluated_at":       datetime.now().isoformat(),
                "risk_level":         risk_level,
                "flags":              flags,
                "total_flags":        len(flags),
            },
            "personal_info":      pi_result,
            "buzzword_analysis":  buzz_result,
            "keyword_dependence": kw_result,
        }

    def evaluate_batch(self, texts: list,
                        scores: list = None,
                        candidate_ids: list = None) -> dict:
        """
        Evaluate bias across a batch of resumes.
        Includes statistical score distribution analysis.
        """
        individual = []
        for i, text in enumerate(texts):
            cid    = candidate_ids[i] if candidate_ids else f"candidate_{i}"
            result = self.evaluate_resume(text)
            result["candidate_id"] = cid
            individual.append(result)

        score_variance = {}
        if scores:
            score_variance = self.detect_score_variance(
                scores, candidate_ids
            )

        total        = len(texts)
        high_risk    = sum(1 for r in individual
                           if r["bias_evaluation"]["risk_level"] == "High")
        medium_risk  = sum(1 for r in individual
                           if r["bias_evaluation"]["risk_level"] == "Medium")
        low_risk     = sum(1 for r in individual
                           if r["bias_evaluation"]["risk_level"] == "Low")

        return {
            "batch_summary": {
                "evaluated_at":    datetime.now().isoformat(),
                "total_resumes":   total,
                "high_risk_count": high_risk,
                "medium_risk_count":medium_risk,
                "low_risk_count":  low_risk,
            },
            "score_distribution": score_variance,
            "individual_results": individual,
        }

    def save_output(self, result: dict, output_path: str):
        """Save bias evaluation result to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
