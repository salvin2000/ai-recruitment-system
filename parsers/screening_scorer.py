"""
Day 26 – Screening Scoring Engine
Zecpath AI Recruitment Platform

Objectively evaluates candidate screening responses.
Scores each answer on Clarity, Relevance, Completeness, and Consistency,
normalizes scores, aggregates a final screening score, and produces
explainable scoring outputs.
"""

import json
from datetime import datetime
from typing import Optional


# ── Scoring Dimensions ────────────────────────────────────────────────────────

SCORING_DIMENSIONS = {
    "clarity": {
        "description": "How clearly the candidate communicated their answer",
        "weight":      0.20,
        "factors":     ["word_count", "confidence_score", "is_vague", "filler_ratio"],
    },
    "relevance": {
        "description": "How well the answer addressed the question asked",
        "weight":      0.30,
        "factors":     ["intent_match", "is_off_topic", "question_category_match"],
    },
    "completeness": {
        "description": "Whether the answer contained all expected information",
        "weight":      0.30,
        "factors":     ["extracted_values_present", "min_word_count", "needs_followup"],
    },
    "consistency": {
        "description": "Whether the answer is consistent with ATS profile data",
        "weight":      0.20,
        "factors":     ["experience_match", "skill_match", "salary_range_match"],
    },
}

# ── Per-Question Scoring Config ───────────────────────────────────────────────

QUESTION_SCORING_CONFIG = {
    "Q001": {"category": "introduction",  "max_score": 5,  "mandatory": True,  "weight": 0.03},
    "Q002": {"category": "introduction",  "max_score": 5,  "mandatory": True,  "weight": 0.03},
    "Q003": {"category": "introduction",  "max_score": 10, "mandatory": True,  "weight": 0.05},
    "Q010": {"category": "education",     "max_score": 10, "mandatory": True,  "weight": 0.07},
    "Q011": {"category": "education",     "max_score": 5,  "mandatory": False, "weight": 0.03},
    "Q020": {"category": "experience",    "max_score": 20, "mandatory": True,  "weight": 0.12},
    "Q021": {"category": "experience",    "max_score": 10, "mandatory": True,  "weight": 0.08},
    "Q022": {"category": "experience",    "max_score": 10, "mandatory": True,  "weight": 0.08},
    "Q030": {"category": "skills",        "max_score": 20, "mandatory": True,  "weight": 0.12},
    "Q031": {"category": "skills",        "max_score": 15, "mandatory": True,  "weight": 0.10},
    "Q041": {"category": "location",      "max_score": 10, "mandatory": True,  "weight": 0.06},
    "Q051": {"category": "salary",        "max_score": 10, "mandatory": False, "weight": 0.06},
    "Q052": {"category": "salary",        "max_score": 10, "mandatory": True,  "weight": 0.06},
    "Q061": {"category": "notice_period", "max_score": 10, "mandatory": True,  "weight": 0.06},
    "Q064": {"category": "notice_period", "max_score": 10, "mandatory": True,  "weight": 0.05},
}

# ── Scoring Grade Thresholds ──────────────────────────────────────────────────

GRADE_THRESHOLDS = {
    "A+": {"min": 90, "label": "Exceptional — Strong Hire",         "outcome": "advance"},
    "A":  {"min": 80, "label": "Excellent — Recommend for Interview","outcome": "advance"},
    "B+": {"min": 70, "label": "Good — Likely Hire",                "outcome": "advance"},
    "B":  {"min": 60, "label": "Satisfactory — Consider",           "outcome": "hold"},
    "C+": {"min": 50, "label": "Below Average — Borderline",        "outcome": "hold"},
    "C":  {"min": 40, "label": "Weak — Needs Review",               "outcome": "hold"},
    "D":  {"min":  0, "label": "Poor — Reject",                     "outcome": "reject"},
}

# ── Category Weights ──────────────────────────────────────────────────────────

CATEGORY_WEIGHTS = {
    "introduction":  0.08,
    "education":     0.10,
    "experience":    0.28,
    "skills":        0.30,
    "location":      0.06,
    "salary":        0.10,
    "notice_period": 0.08,
}

# ── Scoring Rules ─────────────────────────────────────────────────────────────

SCORING_RULES = {
    "vague_penalty":        0.20,  # Multiply score by (1 - penalty) if vague
    "off_topic_penalty":    1.00,  # Zero score if off-topic
    "low_confidence_factor":0.85,  # Multiply by this if confidence < 0.65
    "partial_factor":       0.70,  # Multiply by this if answer is partial
    "min_words_threshold":  5,     # Fewer words = partial factor applied
    "max_score_cap":        1.0,   # Dimension scores capped at 1.0
}


class DimensionScorer:
    """
    Scores a single answer across the 4 dimensions:
    Clarity, Relevance, Completeness, Consistency.
    """

    def __init__(self):
        self.dimensions = SCORING_DIMENSIONS
        self.rules      = SCORING_RULES

    def score_clarity(self, answer: dict) -> dict:
        """
        Score how clearly the candidate communicated.
        Factors: word count, STT confidence, vague flag.
        """
        score  = 1.0
        reason = []

        if answer.get("is_vague"):
            score *= (1 - self.rules["vague_penalty"])
            reason.append("Vague answer — penalty applied")

        confidence = answer.get("confidence", 1.0)
        if confidence < 0.65:
            score *= self.rules["low_confidence_factor"]
            reason.append(f"Low STT confidence ({confidence:.2f}) — factor applied")

        word_count = answer.get("word_count", 0)
        if word_count < self.rules["min_words_threshold"]:
            score *= self.rules["partial_factor"]
            reason.append(f"Short answer ({word_count} words) — partial factor applied")
        elif word_count >= 15:
            score = min(score * 1.05, self.rules["max_score_cap"])
            reason.append("Detailed answer — clarity bonus")

        if not reason:
            reason.append("Clear, well-phrased answer")

        return {"score": round(score, 4), "reasons": reason}

    def score_relevance(self, answer: dict, question_category: str) -> dict:
        """
        Score how relevant the answer was to the question.
        Factors: intent match, off-topic flag.
        """
        score  = 1.0
        reason = []

        if answer.get("is_off_topic"):
            score = 0.0
            reason.append("Off-topic response — zero score")
            return {"score": score, "reasons": reason}

        intent          = answer.get("intent", "unknown")
        category_intent_map = {
            "introduction":  ["affirmative", "negative", "unknown"],
            "education":     ["education_info"],
            "experience":    ["experience_info"],
            "skills":        ["skill_info", "experience_info"],
            "location":      ["affirmative", "negative", "location_info"],
            "salary":        ["salary_info", "affirmative", "negative"],
            "notice_period": ["availability", "affirmative", "negative"],
        }
        expected = category_intent_map.get(question_category, [])

        if intent in expected:
            reason.append(f"Intent '{intent}' matches expected for {question_category}")
        elif intent == "vague":
            score *= 0.5
            reason.append("Vague intent — relevance halved")
        elif intent == "unknown":
            score *= 0.7
            reason.append("Unknown intent — relevance reduced")
        else:
            score *= 0.8
            reason.append(f"Intent '{intent}' partially matches {question_category}")

        return {"score": round(score, 4), "reasons": reason}

    def score_completeness(self, answer: dict, answer_type: str) -> dict:
        """
        Score whether the answer contained all expected information.
        Factors: extracted values present, word count, needs_followup.
        """
        score  = 1.0
        reason = []
        extracted = answer.get("extracted", {})

        if answer.get("needs_followup"):
            score *= 0.6
            reason.append("Incomplete answer — follow-up needed")

        type_expected_keys = {
            "numeric":      ["experience_years", "salary_lpa", "notice_period",
                             "skill_rating", "boolean_value"],
            "yes_no":       ["boolean_value"],
            "choice":       [],
            "text":         ["skills_mentioned", "experience_years", "location"],
            "confirmation": ["boolean_value"],
        }
        expected_keys = type_expected_keys.get(answer_type, [])

        if expected_keys:
            matched = [k for k in expected_keys if k in extracted]
            if matched:
                reason.append(f"Extracted: {', '.join(matched)}")
            else:
                score *= 0.7
                reason.append(f"No structured values extracted for {answer_type} question")

        if not answer.get("is_vague") and not answer.get("needs_followup"):
            if not reason or all("Extracted" in r for r in reason):
                reason.append("Complete answer with expected information")

        return {"score": round(score, 4), "reasons": reason}

    def score_consistency(self, answer: dict,
                          ats_profile: dict,
                          question_id:  str) -> dict:
        """
        Score consistency between answer and ATS profile.
        Factors: experience match, skills match, salary within range.
        """
        score    = 1.0
        reason   = []
        extracted= answer.get("extracted", {})

        # Experience consistency
        if "experience_years" in extracted and "experience_years" in ats_profile:
            ans_exp = extracted["experience_years"]
            ats_exp = ats_profile["experience_years"]
            diff    = abs(ans_exp - ats_exp)
            if diff <= 0.5:
                reason.append(f"Experience consistent with ATS ({ans_exp}yr vs {ats_exp}yr)")
            elif diff <= 1.5:
                score *= 0.9
                reason.append(f"Experience slight mismatch ({ans_exp}yr vs {ats_exp}yr)")
            else:
                score *= 0.75
                reason.append(f"Experience mismatch ({ans_exp}yr vs {ats_exp}yr)")

        # Skills consistency
        if "skills_mentioned" in extracted and "skills" in ats_profile:
            ans_skills = set(s.lower() for s in extracted["skills_mentioned"])
            ats_skills = set(s.lower() for s in ats_profile.get("skills", []))
            overlap    = ans_skills & ats_skills
            if overlap:
                reason.append(f"Skills consistent: {', '.join(list(overlap)[:3])}")
            else:
                score *= 0.85
                reason.append("Mentioned skills not in ATS profile")

        # Salary consistency
        if "salary_lpa" in extracted and "expected_salary_lpa" in ats_profile:
            ans_sal = extracted["salary_lpa"]
            ats_sal = ats_profile["expected_salary_lpa"]
            if abs(ans_sal - ats_sal) <= 2.0:
                reason.append(f"Salary expectation consistent ({ans_sal} vs {ats_sal} LPA)")
            else:
                score *= 0.85
                reason.append(f"Salary expectation mismatch ({ans_sal} vs {ats_sal} LPA)")

        if not reason:
            reason.append("No ATS comparison data available — neutral score")

        return {"score": round(score, 4), "reasons": reason}


class ScreeningScorer:
    """
    Scores a complete AI screening session.
    Produces per-question breakdowns and a final aggregated score.
    """

    def __init__(self):
        self.dim_scorer  = DimensionScorer()
        self.q_config    = QUESTION_SCORING_CONFIG
        self.grade_map   = GRADE_THRESHOLDS
        self.cat_weights = CATEGORY_WEIGHTS
        self.dimensions  = SCORING_DIMENSIONS

    def score_answer(self,
                     answer:           dict,
                     question_id:      str,
                     question_category:str,
                     answer_type:      str,
                     ats_profile:      dict = None) -> dict:
        """Score a single answer across all 4 dimensions."""
        ats_profile = ats_profile or {}
        cfg         = self.q_config.get(question_id, {
            "max_score": 10, "mandatory": False, "weight": 0.05
        })

        # Score each dimension
        clarity     = self.dim_scorer.score_clarity(answer)
        relevance   = self.dim_scorer.score_relevance(answer, question_category)
        completeness= self.dim_scorer.score_completeness(answer, answer_type)
        consistency = self.dim_scorer.score_consistency(answer, ats_profile, question_id)

        # Weighted composite
        w = SCORING_DIMENSIONS
        raw_score = (
            clarity["score"]      * w["clarity"]["weight"] +
            relevance["score"]    * w["relevance"]["weight"] +
            completeness["score"] * w["completeness"]["weight"] +
            consistency["score"]  * w["consistency"]["weight"]
        )

        # Apply off-topic zero penalty
        if answer.get("is_off_topic"):
            raw_score = 0.0

        # Scale to max_score
        scaled = round(raw_score * cfg["max_score"], 2)

        return {
            "question_id":    question_id,
            "category":       question_category,
            "answer_type":    answer_type,
            "mandatory":      cfg["mandatory"],
            "max_score":      cfg["max_score"],
            "raw_score_0_1":  round(raw_score, 4),
            "scaled_score":   scaled,
            "weight":         cfg["weight"],
            "weighted_score": round(scaled * cfg["weight"], 4),
            "dimensions": {
                "clarity":      clarity,
                "relevance":    relevance,
                "completeness": completeness,
                "consistency":  consistency,
            },
            "is_valid":        answer.get("is_valid", True),
            "scored_at":       datetime.now().isoformat(),
        }

    def aggregate_scores(self,
                         question_scores: list,
                         session_id:      str = "",
                         candidate_id:    str = "") -> dict:
        """
        Aggregate per-question scores into a final screening score.
        Normalizes to 100, assigns grade, and determines outcome.
        """
        if not question_scores:
            return {}

        total_weighted = sum(q["weighted_score"] for q in question_scores)
        total_weight   = sum(q["weight"] for q in question_scores)
        normalized     = round((total_weighted / total_weight) * 10, 2) if total_weight else 0.0

        # Category breakdown
        by_category = {}
        for qs in question_scores:
            cat = qs["category"]
            if cat not in by_category:
                by_category[cat] = {"scores": [], "max_scores": [], "weight": self.cat_weights.get(cat, 0.1)}
            by_category[cat]["scores"].append(qs["scaled_score"])
            by_category[cat]["max_scores"].append(qs["max_score"])

        category_summary = {}
        for cat, data in by_category.items():
            total_s   = sum(data["scores"])
            total_max = sum(data["max_scores"])
            pct       = round(total_s / total_max * 100, 1) if total_max else 0.0
            category_summary[cat] = {
                "total_score":  round(total_s, 2),
                "max_score":    total_max,
                "percentage":   pct,
                "weight":       data["weight"],
            }

        # Dimension summary
        dimension_summary = {dim: [] for dim in SCORING_DIMENSIONS}
        for qs in question_scores:
            for dim in SCORING_DIMENSIONS:
                dimension_summary[dim].append(qs["dimensions"][dim]["score"])

        dim_averages = {
            dim: round(sum(scores)/len(scores), 4)
            for dim, scores in dimension_summary.items() if scores
        }

        # Grade and outcome
        grade, grade_data = self._get_grade(normalized)
        mandatory_failed  = [
            q["question_id"] for q in question_scores
            if q["mandatory"] and q["raw_score_0_1"] < 0.40
        ]

        return {
            "score_metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_id":   session_id,
                "candidate_id": candidate_id,
                "total_questions_scored": len(question_scores),
            },
            "final_score":       normalized,
            "max_possible":      100.0,
            "grade":             grade,
            "grade_label":       grade_data["label"],
            "outcome":           grade_data["outcome"],
            "category_scores":   category_summary,
            "dimension_averages":dim_averages,
            "mandatory_failed":  mandatory_failed,
            "per_question":      question_scores,
            "explanation":       self._build_explanation(
                normalized, grade, grade_data, category_summary,
                dim_averages, mandatory_failed
            ),
        }

    def _get_grade(self, score: float) -> tuple:
        """Return grade letter and grade data for a given score."""
        for grade, data in GRADE_THRESHOLDS.items():
            if score >= data["min"]:
                return grade, data
        return "D", GRADE_THRESHOLDS["D"]

    def _build_explanation(self,
                            score:      float,
                            grade:      str,
                            grade_data: dict,
                            categories: dict,
                            dimensions: dict,
                            failed_q:   list) -> list:
        """Build human-readable explanation of the final score."""
        lines = []
        lines.append(f"Final screening score: {score}/100 — Grade {grade} — {grade_data['label']}")

        # Strongest and weakest category
        sorted_cats = sorted(categories.items(), key=lambda x: x[1]["percentage"], reverse=True)
        if sorted_cats:
            best  = sorted_cats[0]
            worst = sorted_cats[-1]
            lines.append(f"Strongest area: {best[0]} ({best[1]['percentage']}%)")
            lines.append(f"Weakest area:   {worst[0]} ({worst[1]['percentage']}%)")

        # Dimension highlights
        if dimensions:
            best_dim  = max(dimensions, key=lambda k: dimensions[k])
            worst_dim = min(dimensions, key=lambda k: dimensions[k])
            lines.append(f"Best dimension:  {best_dim} ({dimensions[best_dim]:.2f})")
            lines.append(f"Worst dimension: {worst_dim} ({dimensions[worst_dim]:.2f})")

        if failed_q:
            lines.append(f"Mandatory questions with low scores: {', '.join(failed_q)}")
        else:
            lines.append("All mandatory questions answered adequately")

        return lines

    def save_results(self, result: dict, output_path: str):
        """Save screening score result to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
