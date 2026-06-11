"""
Day 21 – Eligibility Decision Engine
Zecpath AI Recruitment Platform

Automatically decides which candidates qualify for AI screening calls
based on ATS results and recruiter-defined job rules.
Combines rule-based and score-based eligibility logic.
"""

import json
from datetime import datetime
from typing import Optional


# ── Eligibility Tags ──────────────────────────────────────────────────────────

ELIGIBILITY_TAGS = {
    "eligible": "Candidate meets all eligibility criteria — proceed to AI screening call",
    "review":   "Candidate meets some criteria — requires human review before screening",
    "rejected": "Candidate does not meet minimum eligibility criteria",
}

# ── Default Eligibility Parameters ───────────────────────────────────────────

DEFAULT_ELIGIBILITY_PARAMS = {
    "min_ats_score":         60.0,   # Minimum ATS score to be eligible
    "review_ats_score":      45.0,   # Minimum score for review zone
    "min_experience_years":  1.0,    # Minimum years of experience
    "max_experience_years":  20.0,   # Maximum years of experience
    "mandatory_skills":      [],     # Skills ALL candidates must have
    "preferred_skills":      [],     # Nice-to-have skills
    "min_mandatory_match":   1.0,    # Fraction of mandatory skills required (1.0 = all)
    "location_required":     False,  # Whether location constraint is active
    "allowed_locations":     [],     # List of allowed locations/cities
    "availability_required": False,  # Whether availability check is active
    "max_notice_period_days":60,     # Max acceptable notice period in days
}

# ── Role-Specific Eligibility Configs ─────────────────────────────────────────

ROLE_ELIGIBILITY_CONFIGS = {
    "software_engineer": {
        "min_ats_score":        65.0,
        "review_ats_score":     50.0,
        "min_experience_years": 1.5,
        "max_experience_years": 10.0,
        "mandatory_skills":     ["python"],
        "preferred_skills":     ["django", "aws", "docker"],
        "min_mandatory_match":  1.0,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":60,
    },
    "data_analyst": {
        "min_ats_score":        60.0,
        "review_ats_score":     45.0,
        "min_experience_years": 1.0,
        "max_experience_years": 8.0,
        "mandatory_skills":     ["sql"],
        "preferred_skills":     ["python", "power bi", "tableau"],
        "min_mandatory_match":  1.0,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":60,
    },
    "data_scientist": {
        "min_ats_score":        68.0,
        "review_ats_score":     52.0,
        "min_experience_years": 2.0,
        "max_experience_years": 10.0,
        "mandatory_skills":     ["python", "machine learning"],
        "preferred_skills":     ["tensorflow", "pytorch", "scikit-learn"],
        "min_mandatory_match":  0.5,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":90,
    },
    "devops_engineer": {
        "min_ats_score":        68.0,
        "review_ats_score":     52.0,
        "min_experience_years": 2.0,
        "max_experience_years": 12.0,
        "mandatory_skills":     ["docker", "linux"],
        "preferred_skills":     ["kubernetes", "aws", "terraform", "ci/cd"],
        "min_mandatory_match":  1.0,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":60,
    },
    "hr_manager": {
        "min_ats_score":        60.0,
        "review_ats_score":     45.0,
        "min_experience_years": 3.0,
        "max_experience_years": 15.0,
        "mandatory_skills":     ["recruitment"],
        "preferred_skills":     ["hris", "payroll", "training"],
        "min_mandatory_match":  1.0,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":90,
    },
    "management_trainee": {
        "min_ats_score":        55.0,
        "review_ats_score":     40.0,
        "min_experience_years": 0.0,
        "max_experience_years": 2.0,
        "mandatory_skills":     [],
        "preferred_skills":     ["excel", "communication", "leadership"],
        "min_mandatory_match":  1.0,
        "location_required":    False,
        "allowed_locations":    [],
        "availability_required":False,
        "max_notice_period_days":30,
    },
}

# ── Rule Failure Reasons ──────────────────────────────────────────────────────

RULE_FAILURE_REASONS = {
    "low_ats_score":         "ATS score below minimum threshold",
    "missing_mandatory":     "One or more mandatory skills not found",
    "under_experience":      "Experience below minimum requirement",
    "over_experience":       "Experience above maximum limit",
    "location_mismatch":     "Candidate location not in allowed list",
    "notice_period_too_long":"Notice period exceeds maximum acceptable days",
}


class EligibilityRule:
    """
    A single configurable eligibility rule.
    Each rule has a name, check function description, and weight.
    Rules are combined to form the full eligibility decision.
    """

    def __init__(self,
                 rule_id:     str,
                 rule_type:   str,
                 description: str,
                 is_mandatory: bool = True,
                 weight:       float = 1.0):
        self.rule_id      = rule_id
        self.rule_type    = rule_type
        self.description  = description
        self.is_mandatory = is_mandatory
        self.weight       = weight

    def to_dict(self) -> dict:
        return {
            "rule_id":      self.rule_id,
            "rule_type":    self.rule_type,
            "description":  self.description,
            "is_mandatory": self.is_mandatory,
            "weight":       self.weight,
        }


class EligibilityDecisionEngine:
    """
    Evaluates candidates against recruiter-defined eligibility rules
    and ATS scores to assign an eligibility tag: eligible, review, or rejected.

    Combines:
    - Score-based logic: ATS score vs minimum thresholds
    - Rule-based logic: mandatory skills, experience range, location
    """

    def __init__(self,
                 params:    Optional[dict] = None,
                 role_type: str = "default"):
        self.role_type = role_type
        self.params    = params or ROLE_ELIGIBILITY_CONFIGS.get(
            role_type, DEFAULT_ELIGIBILITY_PARAMS
        )

    # ── Score Check ───────────────────────────────────────────────────────────

    def check_ats_score(self, ats_score: float) -> dict:
        """Check if ATS score meets eligibility threshold."""
        min_score    = self.params["min_ats_score"]
        review_score = self.params["review_ats_score"]

        if ats_score >= min_score:
            return {"passed": True,  "tag": "eligible",
                    "reason": f"ATS score {ats_score} meets minimum {min_score}"}
        elif ats_score >= review_score:
            return {"passed": False, "tag": "review",
                    "reason": f"ATS score {ats_score} below minimum {min_score} but above review threshold {review_score}"}
        else:
            return {"passed": False, "tag": "rejected",
                    "reason": f"ATS score {ats_score} below review threshold {review_score}"}

    # ── Mandatory Skills Check ────────────────────────────────────────────────

    def check_mandatory_skills(self, candidate_skills: list) -> dict:
        """Check if candidate has all mandatory skills."""
        mandatory = self.params.get("mandatory_skills", [])
        if not mandatory:
            return {"passed": True, "tag": "eligible",
                    "reason": "No mandatory skills defined",
                    "missing": [], "matched": []}

        candidate_lower = [s.lower() for s in candidate_skills]
        matched  = [s for s in mandatory if s.lower() in candidate_lower]
        missing  = [s for s in mandatory if s.lower() not in candidate_lower]
        min_frac = self.params.get("min_mandatory_match", 1.0)
        match_rate = len(matched) / len(mandatory) if mandatory else 1.0

        if match_rate >= min_frac:
            return {"passed": True,  "tag": "eligible",
                    "reason": f"Mandatory skills met ({len(matched)}/{len(mandatory)})",
                    "missing": missing, "matched": matched}
        else:
            return {"passed": False, "tag": "rejected",
                    "reason": RULE_FAILURE_REASONS["missing_mandatory"],
                    "missing": missing, "matched": matched}

    # ── Experience Check ──────────────────────────────────────────────────────

    def check_experience(self, experience_years: float) -> dict:
        """Check if candidate experience is within the required range."""
        min_exp = self.params["min_experience_years"]
        max_exp = self.params["max_experience_years"]

        if experience_years < min_exp:
            return {"passed": False, "tag": "rejected",
                    "reason": f"{RULE_FAILURE_REASONS['under_experience']}: {experience_years}yr < {min_exp}yr minimum"}
        elif experience_years > max_exp:
            return {"passed": False, "tag": "review",
                    "reason": f"{RULE_FAILURE_REASONS['over_experience']}: {experience_years}yr > {max_exp}yr maximum"}
        else:
            return {"passed": True,  "tag": "eligible",
                    "reason": f"Experience {experience_years}yr within range {min_exp}-{max_exp}yr"}

    # ── Location Check ────────────────────────────────────────────────────────

    def check_location(self, candidate_location: str) -> dict:
        """Check if candidate location is acceptable."""
        if not self.params.get("location_required", False):
            return {"passed": True, "tag": "eligible",
                    "reason": "Location constraint not active"}

        allowed = [loc.lower() for loc in self.params.get("allowed_locations", [])]
        if not allowed:
            return {"passed": True, "tag": "eligible",
                    "reason": "No location restrictions defined"}

        if candidate_location.lower() in allowed:
            return {"passed": True,  "tag": "eligible",
                    "reason": f"Location {candidate_location} is in allowed list"}
        else:
            return {"passed": False, "tag": "review",
                    "reason": f"{RULE_FAILURE_REASONS['location_mismatch']}: {candidate_location}"}

    # ── Notice Period Check ───────────────────────────────────────────────────

    def check_notice_period(self, notice_period_days: int) -> dict:
        """Check if candidate notice period is acceptable."""
        if not self.params.get("availability_required", False):
            return {"passed": True, "tag": "eligible",
                    "reason": "Availability constraint not active"}

        max_notice = self.params.get("max_notice_period_days", 60)
        if notice_period_days <= max_notice:
            return {"passed": True,  "tag": "eligible",
                    "reason": f"Notice period {notice_period_days} days within limit {max_notice}"}
        else:
            return {"passed": False, "tag": "review",
                    "reason": f"{RULE_FAILURE_REASONS['notice_period_too_long']}: {notice_period_days} days > {max_notice} days"}

    # ── Full Eligibility Decision ─────────────────────────────────────────────

    def decide(self, candidate: dict) -> dict:
        """
        Run all eligibility checks on a candidate.
        Returns final tag (eligible/review/rejected) with full audit trail.
        """
        ats_score        = candidate.get("ats_score", 0.0)
        skills           = candidate.get("skills", [])
        experience_years = candidate.get("experience_years", 0.0)
        location         = candidate.get("location", "")
        notice_period    = candidate.get("notice_period_days", 0)

        # Run all checks
        score_check    = self.check_ats_score(ats_score)
        skills_check   = self.check_mandatory_skills(skills)
        exp_check      = self.check_experience(experience_years)
        location_check = self.check_location(location)
        notice_check   = self.check_notice_period(notice_period)

        all_checks = {
            "ats_score":       score_check,
            "mandatory_skills":skills_check,
            "experience":      exp_check,
            "location":        location_check,
            "notice_period":   notice_check,
        }

        # Determine final tag — most restrictive rule wins
        # rejected > review > eligible
        final_tag = "eligible"
        failed_rules = []
        passed_rules = []

        for rule_name, check in all_checks.items():
            if not check["passed"]:
                failed_rules.append({
                    "rule":   rule_name,
                    "tag":    check["tag"],
                    "reason": check["reason"],
                })
                if check["tag"] == "rejected":
                    final_tag = "rejected"
                elif check["tag"] == "review" and final_tag != "rejected":
                    final_tag = "review"
            else:
                passed_rules.append(rule_name)

        return {
            "candidate_id":   candidate.get("candidate_id", ""),
            "ats_score":      ats_score,
            "eligibility_tag":final_tag,
            "tag_label":      ELIGIBILITY_TAGS[final_tag],
            "checks":         all_checks,
            "passed_rules":   passed_rules,
            "failed_rules":   failed_rules,
            "total_checks":   len(all_checks),
            "checks_passed":  len(passed_rules),
            "evaluated_at":   datetime.now().isoformat(),
            "role_type":      self.role_type,
            "params_used":    self.params,
        }

    def decide_batch(self, candidates: list) -> list:
        """Evaluate eligibility for a batch of candidates."""
        return [self.decide(c) for c in candidates]

    # ── Summary Report ────────────────────────────────────────────────────────

    def generate_eligibility_report(self,
                                     results: list,
                                     job_id:  str = "") -> dict:
        """Generate a summary report from batch eligibility results."""
        eligible = [r for r in results if r["eligibility_tag"] == "eligible"]
        review   = [r for r in results if r["eligibility_tag"] == "review"]
        rejected = [r for r in results if r["eligibility_tag"] == "rejected"]
        total    = len(results)

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "job_id":       job_id,
                "role_type":    self.role_type,
                "total_evaluated": total,
                "params_used":  self.params,
            },
            "summary": {
                "total":          total,
                "eligible_count": len(eligible),
                "review_count":   len(review),
                "rejected_count": len(rejected),
                "eligible_rate":  round(len(eligible)/total*100, 1) if total else 0,
                "rejection_rate": round(len(rejected)/total*100, 1) if total else 0,
            },
            "eligible_candidates": [self._result_summary(r) for r in eligible],
            "review_candidates":   [self._result_summary(r) for r in review],
            "rejected_candidates": [self._result_summary(r) for r in rejected],
        }

    def _result_summary(self, result: dict) -> dict:
        """Compact candidate summary for the report."""
        return {
            "candidate_id":    result["candidate_id"],
            "ats_score":       result["ats_score"],
            "eligibility_tag": result["eligibility_tag"],
            "checks_passed":   result["checks_passed"],
            "total_checks":    result["total_checks"],
            "failed_rules":    [r["rule"] for r in result["failed_rules"]],
        }

    def save_report(self, report: dict, output_path: str):
        """Save eligibility report to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
