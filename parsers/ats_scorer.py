"""
Day 13 – ATS Scoring Formula Design
Zecpath AI Recruitment Platform

Designs a transparent, explainable candidate scoring framework.
Combines skill match, experience relevance, education alignment,
and semantic similarity into a configurable weighted score.
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import Optional


# ── Default Weight Profiles ───────────────────────────────────────────────────
# Each role type has different priorities.
# Weights must always sum to 1.0

DEFAULT_WEIGHT_PROFILES = {
    "software_engineer": {
        "skill_match":          0.35,
        "experience_relevance": 0.30,
        "education_alignment":  0.15,
        "semantic_similarity":  0.20,
    },
    "data_analyst": {
        "skill_match":          0.30,
        "experience_relevance": 0.30,
        "education_alignment":  0.20,
        "semantic_similarity":  0.20,
    },
    "management_trainee": {
        "skill_match":          0.20,
        "experience_relevance": 0.20,
        "education_alignment":  0.35,
        "semantic_similarity":  0.25,
    },
    "data_scientist": {
        "skill_match":          0.30,
        "experience_relevance": 0.25,
        "education_alignment":  0.25,
        "semantic_similarity":  0.20,
    },
    "devops_engineer": {
        "skill_match":          0.40,
        "experience_relevance": 0.35,
        "education_alignment":  0.10,
        "semantic_similarity":  0.15,
    },
    "hr_manager": {
        "skill_match":          0.25,
        "experience_relevance": 0.35,
        "education_alignment":  0.20,
        "semantic_similarity":  0.20,
    },
    "default": {
        "skill_match":          0.30,
        "experience_relevance": 0.30,
        "education_alignment":  0.20,
        "semantic_similarity":  0.20,
    },
}

# ── Grade Thresholds ──────────────────────────────────────────────────────────

GRADE_THRESHOLDS = {
    "A+": 90,
    "A":  80,
    "B+": 70,
    "B":  60,
    "C+": 50,
    "C":  40,
    "D":   0,
}

# ── Recommendation Thresholds ─────────────────────────────────────────────────

RECOMMENDATION_THRESHOLDS = {
    85: "Strong Hire — Proceed to Final Interview",
    70: "Likely Hire — Proceed to Technical Interview",
    55: "Possible Hire — Proceed to Screening Call",
    40: "Review Manually — Borderline Candidate",
     0: "Reject — Does Not Meet Minimum Requirements",
}


# ── Missing Data Penalties ────────────────────────────────────────────────────

MISSING_DATA_PENALTIES = {
    "skill_match":          0.50,   # Use 50% of weight if skills not extracted
    "experience_relevance": 0.40,   # Use 40% of weight if experience missing
    "education_alignment":  0.60,   # Use 60% of weight if education missing
    "semantic_similarity":  0.30,   # Use 30% of weight if semantic not computed
}


class WeightProfile:
    """
    Represents a configurable weight profile for ATS scoring.
    Validates that all weights sum to 1.0 and all are non-negative.
    """

    def __init__(self, weights: dict, profile_name: str = "custom"):
        self.profile_name = profile_name
        self.weights      = self._validate(weights)

    def _validate(self, weights: dict) -> dict:
        required = {"skill_match", "experience_relevance",
                    "education_alignment", "semantic_similarity"}

        # Check all required keys present
        missing = required - set(weights.keys())
        if missing:
            raise ValueError(f"Missing weight keys: {missing}")

        # Check all non-negative
        for key, val in weights.items():
            if val < 0:
                raise ValueError(f"Weight '{key}' cannot be negative: {val}")

        # Normalize to sum to 1.0
        total = sum(weights[k] for k in required)
        if total == 0:
            raise ValueError("All weights cannot be zero.")

        normalized = {k: round(weights[k] / total, 4) for k in required}
        return normalized

    def to_dict(self) -> dict:
        return {"profile_name": self.profile_name, "weights": self.weights}


class ComponentScore:
    """
    Represents a single scoring component with its raw score,
    weighted contribution, and explanation.
    """

    def __init__(self,
                 name: str,
                 raw_score: float,
                 weight: float,
                 explanation: str,
                 data_present: bool = True):
        self.name          = name
        self.raw_score     = round(min(max(raw_score, 0.0), 1.0), 4)
        self.weight        = weight
        self.explanation   = explanation
        self.data_present  = data_present

        # Apply missing data penalty if data not present
        effective_weight   = weight if data_present else (
            weight * MISSING_DATA_PENALTIES.get(name, 0.5)
        )
        self.weighted_score = round(self.raw_score * effective_weight * 100, 2)

    def to_dict(self) -> dict:
        return {
            "name":           self.name,
            "raw_score":      self.raw_score,
            "raw_score_pct":  round(self.raw_score * 100, 1),
            "weight":         self.weight,
            "weighted_score": self.weighted_score,
            "data_present":   self.data_present,
            "explanation":    self.explanation,
        }


class ATSScoringEngine:
    """
    Transparent, explainable ATS scoring engine.
    Combines skill match, experience relevance, education alignment,
    and semantic similarity into a single weighted candidate score.
    """

    def __init__(self, weight_profile: Optional[WeightProfile] = None):
        self.weight_profile = weight_profile
        self.grade_thresholds = GRADE_THRESHOLDS
        self.rec_thresholds   = RECOMMENDATION_THRESHOLDS

    # ── Weight Profile Management ─────────────────────────────────────────────

    def get_weight_profile(self, role_type: str = "default") -> WeightProfile:
        """Get weight profile for a role type. Creates custom if not found."""
        profile_weights = DEFAULT_WEIGHT_PROFILES.get(
            role_type.lower().replace(" ", "_"),
            DEFAULT_WEIGHT_PROFILES["default"]
        )
        return WeightProfile(profile_weights, role_type)

    def set_custom_weights(self,
                           skill_match: float,
                           experience_relevance: float,
                           education_alignment: float,
                           semantic_similarity: float,
                           profile_name: str = "custom") -> WeightProfile:
        """Create and set a custom weight profile."""
        weights = {
            "skill_match":          skill_match,
            "experience_relevance": experience_relevance,
            "education_alignment":  education_alignment,
            "semantic_similarity":  semantic_similarity,
        }
        self.weight_profile = WeightProfile(weights, profile_name)
        return self.weight_profile

    # ── Component Score Builders ──────────────────────────────────────────────

    def build_skill_score(self,
                           skill_data: dict,
                           job_requirements: dict,
                           weight: float) -> ComponentScore:
        """
        Build skill match component score.
        Uses skill extraction output from Day 9.
        """
        if not skill_data or not skill_data.get("skill_summary"):
            return ComponentScore(
                "skill_match", 0.0, weight,
                "Skill data not available. Score set to 0.",
                data_present=False
            )

        required_skills = [s.lower() for s in
                           job_requirements.get("required_skills", [])]
        preferred_skills= [s.lower() for s in
                           job_requirements.get("preferred_skills", [])]

        all_candidate_skills = []
        for category in skill_data["skill_summary"].values():
            all_candidate_skills.extend([s.lower() for s in category])

        # Required skills match — 70% of score
        if required_skills:
            matched_req  = sum(1 for s in required_skills
                               if s in all_candidate_skills)
            req_score    = matched_req / len(required_skills)
            matched_list = [s for s in required_skills
                            if s in all_candidate_skills]
            missing_list = [s for s in required_skills
                            if s not in all_candidate_skills]
        else:
            req_score, matched_list, missing_list = 0.5, [], []

        # Preferred skills match — 30% of score
        if preferred_skills:
            matched_pref = sum(1 for s in preferred_skills
                               if s in all_candidate_skills)
            pref_score   = matched_pref / len(preferred_skills)
        else:
            pref_score   = 0.5

        final_score = round((req_score * 0.70) + (pref_score * 0.30), 4)

        explanation = (
            f"Required skills: {len(matched_list)} of "
            f"{len(required_skills)} matched "
            f"({round(req_score*100, 1)}%). "
            f"Matched: {', '.join(matched_list[:5]) or 'None'}. "
            f"Missing: {', '.join(missing_list[:5]) or 'None'}."
        )

        return ComponentScore("skill_match", final_score, weight, explanation)

    def build_experience_score(self,
                                experience_data: dict,
                                job_requirements: dict,
                                weight: float) -> ComponentScore:
        """
        Build experience relevance component score.
        Uses experience parsing output from Day 10.
        """
        if not experience_data or not experience_data.get("metadata"):
            return ComponentScore(
                "experience_relevance", 0.0, weight,
                "Experience data not available. Score set to 0.",
                data_present=False
            )

        relevance = experience_data.get("relevance")
        if relevance:
            final_score  = relevance.get("relevance_score", 0.0)
            role_sim     = relevance.get("role_similarity", 0.0)
            skills_match = relevance.get("skills_match", 0.0)
            total_years  = relevance.get("total_years", 0.0)
            meets_min    = relevance.get("meets_min_experience", False)
            explanation  = (
                f"Total experience: {total_years} years. "
                f"Role similarity: {round(role_sim*100, 1)}%. "
                f"Skills in experience: {round(skills_match*100, 1)}%. "
                f"Meets minimum requirement: {'Yes' if meets_min else 'No'}."
            )
        else:
            meta         = experience_data.get("metadata", {})
            total_years  = meta.get("total_years", 0.0)
            min_exp      = job_requirements.get("min_experience_years", 0)
            max_exp      = job_requirements.get("max_experience_years", 99)
            if total_years >= min_exp:
                final_score = 1.0 if total_years <= max_exp else 0.8
            else:
                final_score = round(total_years / max(min_exp, 1), 2)
            explanation  = (
                f"Total experience: {total_years} years. "
                f"Required: {min_exp} to {max_exp} years."
            )

        return ComponentScore(
            "experience_relevance", final_score, weight, explanation
        )

    def build_education_score(self,
                               education_data: dict,
                               job_requirements: dict,
                               weight: float) -> ComponentScore:
        """
        Build education alignment component score.
        Uses education parsing output from Day 11.
        """
        if not education_data or not education_data.get("metadata"):
            return ComponentScore(
                "education_alignment", 0.0, weight,
                "Education data not available. Score set to 0.",
                data_present=False
            )

        relevance = education_data.get("relevance")
        if relevance:
            final_score    = relevance.get("relevance_score", 0.0)
            meets_min      = relevance.get("meets_min_degree", False)
            degree_score   = relevance.get("degree_score", 0.0)
            field_score    = relevance.get("field_score", 0.0)
        else:
            final_score  = 0.5
            meets_min    = True
            degree_score = 0.5
            field_score  = 0.5

        meta           = education_data.get("metadata", {})
        highest_degree = meta.get("highest_degree", "Not specified")
        total_certs    = meta.get("total_certifications", 0)

        explanation = (
            f"Highest degree: {highest_degree.upper()}. "
            f"Meets minimum degree: {'Yes' if meets_min else 'No'}. "
            f"Degree level score: {round(degree_score*100, 1)}%. "
            f"Field relevance: {round(field_score*100, 1)}%. "
            f"Certifications: {total_certs}."
        )

        return ComponentScore(
            "education_alignment", final_score, weight, explanation
        )

    def build_semantic_score(self,
                              semantic_data: dict,
                              weight: float) -> ComponentScore:
        """
        Build semantic similarity component score.
        Uses semantic matching output from Day 12.
        """
        if not semantic_data or not semantic_data.get("overall_match"):
            return ComponentScore(
                "semantic_similarity", 0.0, weight,
                "Semantic similarity data not available. Score set to 0.",
                data_present=False
            )

        overall         = semantic_data["overall_match"]
        scores          = semantic_data.get("similarity_scores", {})

        # Normalize semantic score to 0-1 range
        # Semantic scores use different scale (0.0 to ~0.40 for TF-IDF)
        raw_score       = overall.get("score", 0.0)
        max_expected    = 0.40   # Maximum realistic TF-IDF score
        normalized      = round(min(raw_score / max_expected, 1.0), 4)

        skills_sim      = scores.get("skills", {}).get("score", 0.0)
        exp_sim         = scores.get("experience", {}).get("score", 0.0)
        proj_sim        = scores.get("projects", {}).get("score", 0.0)

        explanation = (
            f"Overall semantic similarity: {round(raw_score, 4)} "
            f"(normalized to {round(normalized*100, 1)}%). "
            f"Skills: {skills_sim}, Experience: {exp_sim}, "
            f"Projects: {proj_sim}."
        )

        return ComponentScore(
            "semantic_similarity", normalized, weight, explanation
        )

    # ── Final Score Assembly ──────────────────────────────────────────────────

    def compute_final_score(self, components: list) -> float:
        """Compute final ATS score from component weighted scores."""
        return round(sum(c.weighted_score for c in components), 2)

    def assign_grade(self, score: float) -> str:
        """Assign letter grade based on score."""
        for grade, threshold in sorted(
            self.grade_thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return grade
        return "D"

    def assign_recommendation(self, score: float) -> str:
        """Assign hiring recommendation based on score."""
        for threshold, recommendation in sorted(
            self.rec_thresholds.items(),
            reverse=True
        ):
            if score >= threshold:
                return recommendation
        return self.rec_thresholds[0]

    def identify_strengths_gaps(self,
                                 components: list) -> tuple:
        """Identify candidate strengths and gaps from component scores."""
        strengths = []
        gaps      = []

        for comp in components:
            pct = comp.raw_score * 100
            if pct >= 70:
                strengths.append(
                    f"{comp.name.replace('_', ' ').title()}: "
                    f"{round(pct, 1)}%"
                )
            elif pct < 40:
                gaps.append(
                    f"{comp.name.replace('_', ' ').title()}: "
                    f"{round(pct, 1)}%"
                )

        return strengths, gaps

    # ── Main Scoring Function ─────────────────────────────────────────────────

    def score(self,
              candidate_id: str,
              job_id: str,
              skill_data:      Optional[dict] = None,
              experience_data: Optional[dict] = None,
              education_data:  Optional[dict] = None,
              semantic_data:   Optional[dict] = None,
              job_requirements:Optional[dict] = None,
              role_type:       str = "default") -> dict:
        """
        Main scoring function. Combines all component scores into
        a final explainable ATS score.
        """
        job_requirements = job_requirements or {}

        # Get weight profile for this role type
        profile   = (self.weight_profile or
                     self.get_weight_profile(role_type))
        weights   = profile.weights

        # Build all component scores
        skill_comp = self.build_skill_score(
            skill_data, job_requirements, weights["skill_match"]
        )
        exp_comp   = self.build_experience_score(
            experience_data, job_requirements, weights["experience_relevance"]
        )
        edu_comp   = self.build_education_score(
            education_data, job_requirements, weights["education_alignment"]
        )
        sem_comp   = self.build_semantic_score(
            semantic_data, weights["semantic_similarity"]
        )

        components  = [skill_comp, exp_comp, edu_comp, sem_comp]

        # Compute final score
        final_score = self.compute_final_score(components)
        grade       = self.assign_grade(final_score)
        rec         = self.assign_recommendation(final_score)
        strengths, gaps = self.identify_strengths_gaps(components)

        # Missing data flags
        missing_data = [c.name for c in components if not c.data_present]

        return {
            "metadata": {
                "scored_at":      datetime.now().isoformat(),
                "engine_version": "1.0",
                "candidate_id":   candidate_id,
                "job_id":         job_id,
                "role_type":      role_type,
                "weight_profile": profile.to_dict(),
            },
            "component_scores": {
                c.name: c.to_dict() for c in components
            },
            "final_score": {
                "score":          final_score,
                "grade":          grade,
                "recommendation": rec,
                "strengths":      strengths,
                "gaps":           gaps,
                "missing_data":   missing_data,
                "is_complete":    len(missing_data) == 0,
            },
            "score_breakdown": {
                "skill_match":          skill_comp.weighted_score,
                "experience_relevance": exp_comp.weighted_score,
                "education_alignment":  edu_comp.weighted_score,
                "semantic_similarity":  sem_comp.weighted_score,
                "total":                final_score,
            },
        }

    def score_batch(self,
                    candidates: list,
                    job_requirements: dict,
                    role_type: str = "default") -> list:
        """
        Score multiple candidates against one job.
        Returns results sorted by score descending.
        """
        results = []
        for candidate in candidates:
            result = self.score(
                candidate_id     = candidate.get("candidate_id", ""),
                job_id           = candidate.get("job_id", ""),
                skill_data       = candidate.get("skill_data"),
                experience_data  = candidate.get("experience_data"),
                education_data   = candidate.get("education_data"),
                semantic_data    = candidate.get("semantic_data"),
                job_requirements = job_requirements,
                role_type        = role_type,
            )
            results.append(result)

        # Sort by final score descending
        results.sort(
            key=lambda x: x["final_score"]["score"],
            reverse=True
        )
        return results

    def save_output(self, result: dict, output_path: str):
        """Save scoring result to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")

    def generate_scorecard(self, result: dict) -> str:
        """
        Generate a human-readable scorecard from a scoring result.
        """
        meta  = result["metadata"]
        final = result["final_score"]
        comp  = result["component_scores"]
        breakdown = result["score_breakdown"]

        lines = [
            "=" * 60,
            f"  ATS SCORECARD",
            f"  Candidate : {meta['candidate_id']}",
            f"  Job ID    : {meta['job_id']}",
            f"  Role      : {meta['role_type']}",
            f"  Profile   : {meta['weight_profile']['profile_name']}",
            "=" * 60,
            "",
            "  COMPONENT SCORES",
            f"  {'Component':<28} {'Raw':>8} {'Weight':>8} {'Points':>8}",
            "  " + "-" * 56,
        ]

        for name, data in comp.items():
            lines.append(
                f"  {name.replace('_',' ').title():<28} "
                f"{round(data['raw_score_pct'], 1):>7}% "
                f"{round(data['weight']*100, 1):>7}% "
                f"{data['weighted_score']:>8}"
            )

        lines += [
            "  " + "-" * 56,
            f"  {'TOTAL SCORE':<28} {'':>8} {'':>8} {final['score']:>8}",
            "",
            f"  GRADE          : {final['grade']}",
            f"  RECOMMENDATION : {final['recommendation']}",
            "",
        ]

        if final["strengths"]:
            lines.append(f"  STRENGTHS : {', '.join(final['strengths'])}")
        if final["gaps"]:
            lines.append(f"  GAPS      : {', '.join(final['gaps'])}")
        if final["missing_data"]:
            lines.append(f"  MISSING   : {', '.join(final['missing_data'])}")

        lines.append("=" * 60)
        return "\n".join(lines)
