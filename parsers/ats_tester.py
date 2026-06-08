"""
Day 17 – ATS System Testing
Zecpath AI Recruitment Platform

Validates ATS accuracy, reliability, and role adaptability by testing
across tech roles, non-tech roles, fresher resumes, and senior profiles.
Tracks precision, recall, and mismatch cases.
"""

import json
import math
from datetime import datetime
from typing import Optional


# ── Test Profile Categories ───────────────────────────────────────────────────

PROFILE_CATEGORIES = {
    "tech_senior":     "Senior technical profile with 5+ years experience",
    "tech_mid":        "Mid-level technical profile with 2-5 years experience",
    "tech_fresher":    "Fresh graduate with technical degree and no work experience",
    "non_tech_senior": "Senior non-technical profile (HR, Finance, Marketing)",
    "non_tech_mid":    "Mid-level non-technical profile",
    "non_tech_fresher":"Fresh graduate with non-technical background",
}

# ── Manual Review Ground Truth ────────────────────────────────────────────────
# Expected decisions based on human recruiter judgment
# Used to measure AI accuracy against human baseline

MANUAL_REVIEW_DECISIONS = {
    "shortlisted": "Candidate should be shortlisted",
    "review":      "Candidate needs manual review",
    "rejected":    "Candidate should be rejected",
}

# ── Accuracy Thresholds ───────────────────────────────────────────────────────

ACCURACY_THRESHOLDS = {
    "precision_target":     0.80,   # 80% of AI shortlists are correct
    "recall_target":        0.75,   # 75% of good candidates are caught
    "f1_target":            0.77,   # Harmonic mean target
    "accuracy_target":      0.80,   # 80% overall agreement with human
    "mismatch_tolerance":   0.20,   # Max 20% mismatch rate acceptable
}

# ── Test Cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    # Tech Senior profiles
    {
        "test_id":         "TC-001",
        "profile_category":"tech_senior",
        "candidate_id":    "ZCP-TEST-ARJU",
        "description":     "Senior Software Engineer — Python, Django, AWS, 4 years",
        "ats_score":        79.87,
        "ats_decision":    "shortlisted",
        "manual_decision": "shortlisted",
        "role_type":       "software_engineer",
        "notes":           "Strong match — skills and experience align well",
    },
    {
        "test_id":         "TC-002",
        "profile_category":"tech_senior",
        "candidate_id":    "ZCP-TEST-PRIY",
        "description":     "Senior Software Engineer — Python, React, PostgreSQL, 3.5 years",
        "ats_score":        73.99,
        "ats_decision":    "shortlisted",
        "manual_decision": "shortlisted",
        "role_type":       "software_engineer",
        "notes":           "Good match — missing some DevOps skills but core stack strong",
    },
    # Tech Mid profiles
    {
        "test_id":         "TC-003",
        "profile_category":"tech_mid",
        "candidate_id":    "ZCP-TEST-KART",
        "description":     "Mid Software Engineer — Python, AWS, Docker, 2.5 years",
        "ats_score":        65.74,
        "ats_decision":    "review",
        "manual_decision": "review",
        "role_type":       "software_engineer",
        "notes":           "Border case — experience slightly below ideal, needs human review",
    },
    {
        "test_id":         "TC-004",
        "profile_category":"tech_mid",
        "candidate_id":    "ZCP-TEST-VISH",
        "description":     "Mid Data Scientist — Python, TensorFlow, ML, 2 years",
        "ats_score":        71.20,
        "ats_decision":    "shortlisted",
        "manual_decision": "shortlisted",
        "role_type":       "data_scientist",
        "notes":           "Good match for data scientist role",
    },
    # Tech Fresher profiles
    {
        "test_id":         "TC-005",
        "profile_category":"tech_fresher",
        "candidate_id":    "ZCP-TEST-RAHU",
        "description":     "Fresher — B.Tech CS, Python, Java, SQL projects",
        "ats_score":        37.37,
        "ats_decision":    "rejected",
        "manual_decision": "rejected",
        "role_type":       "software_engineer",
        "notes":           "Fresher applying for senior role — correctly rejected",
    },
    {
        "test_id":         "TC-006",
        "profile_category":"tech_fresher",
        "candidate_id":    "ZCP-TEST-ANIT",
        "description":     "Fresher — B.Tech CS, Python, Django internship 6 months",
        "ats_score":        52.40,
        "ats_decision":    "review",
        "manual_decision": "review",
        "role_type":       "software_engineer",
        "notes":           "Has internship — border case, manual review appropriate",
    },
    # Non-Tech Senior profiles
    {
        "test_id":         "TC-007",
        "profile_category":"non_tech_senior",
        "candidate_id":    "ZCP-TEST-MANO",
        "description":     "Senior HR Manager — Recruitment, Payroll, HRIS, 6 years",
        "ats_score":        78.50,
        "ats_decision":    "shortlisted",
        "manual_decision": "shortlisted",
        "role_type":       "hr_manager",
        "notes":           "Strong HR profile for HR Manager role",
    },
    {
        "test_id":         "TC-008",
        "profile_category":"non_tech_senior",
        "candidate_id":    "ZCP-TEST-SRID",
        "description":     "Senior Data Analyst — SQL, Power BI, Excel, Statistics, 4 years",
        "ats_score":        76.30,
        "ats_decision":    "shortlisted",
        "manual_decision": "shortlisted",
        "role_type":       "data_analyst",
        "notes":           "Experienced analyst — strong tool match",
    },
    # Non-Tech Mid profiles
    {
        "test_id":         "TC-009",
        "profile_category":"non_tech_mid",
        "candidate_id":    "ZCP-TEST-SNEH",
        "description":     "Mid Data Analyst — Python, SQL, Power BI, 2 years",
        "ats_score":        44.85,
        "ats_decision":    "rejected",
        "manual_decision": "review",
        "role_type":       "software_engineer",
        "notes":           "MISMATCH — Analyst applying for SW Eng role. AI rejected, human says review.",
    },
    {
        "test_id":         "TC-010",
        "profile_category":"non_tech_mid",
        "candidate_id":    "ZCP-TEST-HARI",
        "description":     "Mid HR Executive — Recruitment, Training, 3 years",
        "ats_score":        62.10,
        "ats_decision":    "review",
        "manual_decision": "review",
        "role_type":       "hr_manager",
        "notes":           "Correct — mid-level HR needs human judgement",
    },
    # Non-Tech Fresher profiles
    {
        "test_id":         "TC-011",
        "profile_category":"non_tech_fresher",
        "candidate_id":    "ZCP-TEST-NEHA",
        "description":     "Fresher MBA — Finance, Excel, basic SQL, internship",
        "ats_score":        48.90,
        "ats_decision":    "review",
        "manual_decision": "shortlisted",
        "role_type":       "data_analyst",
        "notes":           "MISMATCH — MBA fresher with strong academics. AI review, human shortlists.",
    },
    {
        "test_id":         "TC-012",
        "profile_category":"non_tech_fresher",
        "candidate_id":    "ZCP-TEST-RAVI",
        "description":     "Fresher B.Com — Accounting, Tally, no tech skills",
        "ats_score":        21.50,
        "ats_decision":    "rejected",
        "manual_decision": "rejected",
        "role_type":       "data_analyst",
        "notes":           "Correct — no relevant skills for data analyst role",
    },
]


class ATSTester:
    """
    Tests ATS accuracy by comparing AI decisions against
    manual review ground truth. Computes precision, recall,
    F1 score, and identifies mismatch cases.
    """

    def __init__(self, thresholds: dict = None):
        self.thresholds  = thresholds or ACCURACY_THRESHOLDS
        self.test_cases  = TEST_CASES

    # ── Confusion Matrix ──────────────────────────────────────────────────────

    def build_confusion_matrix(self, results: list) -> dict:
        """
        Build a confusion matrix comparing AI decisions vs manual decisions.
        For binary shortlist/no-shortlist classification:
        TP = AI shortlisted + Manual shortlisted
        FP = AI shortlisted + Manual rejected or review
        FN = AI rejected/review + Manual shortlisted
        TN = AI rejected + Manual rejected
        """
        tp = fp = fn = tn = 0
        mismatches = []

        for r in results:
            ai     = r["ats_decision"]
            manual = r["manual_decision"]
            match  = ai == manual

            if not match:
                mismatches.append({
                    "test_id":       r["test_id"],
                    "candidate_id":  r["candidate_id"],
                    "ai_decision":   ai,
                    "manual_decision": manual,
                    "ats_score":     r["ats_score"],
                    "profile_category": r["profile_category"],
                    "notes":         r.get("notes", ""),
                })

            # Binary: shortlisted = positive, review/rejected = negative
            ai_pos     = ai     == "shortlisted"
            manual_pos = manual == "shortlisted"

            if ai_pos and manual_pos:      tp += 1
            elif ai_pos and not manual_pos:fp += 1
            elif not ai_pos and manual_pos:fn += 1
            else:                          tn += 1

        return {
            "true_positive":  tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative":  tn,
            "mismatches":     mismatches,
            "total":          len(results),
        }

    # ── Accuracy Metrics ──────────────────────────────────────────────────────

    def compute_metrics(self, confusion: dict) -> dict:
        """
        Compute precision, recall, F1, accuracy, and mismatch rate
        from the confusion matrix.
        """
        tp = confusion["true_positive"]
        fp = confusion["false_positive"]
        fn = confusion["false_negative"]
        tn = confusion["true_negative"]
        total = confusion["total"]

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall    = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1        = round(
            2 * precision * recall / (precision + recall), 4
        ) if (precision + recall) > 0 else 0.0
        accuracy  = round((tp + tn) / total, 4) if total > 0 else 0.0
        mismatch  = round(len(confusion["mismatches"]) / total, 4) if total > 0 else 0.0

        return {
            "precision":      precision,
            "recall":         recall,
            "f1_score":       f1,
            "accuracy":       accuracy,
            "mismatch_rate":  mismatch,
            "total_mismatches": len(confusion["mismatches"]),
        }

    # ── Category Analysis ─────────────────────────────────────────────────────

    def analyze_by_category(self, results: list) -> dict:
        """Analyze accuracy broken down by profile category."""
        categories = {}

        for r in results:
            cat = r["profile_category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "correct": 0, "cases": []}
            categories[cat]["total"] += 1
            if r["ats_decision"] == r["manual_decision"]:
                categories[cat]["correct"] += 1
            categories[cat]["cases"].append(r["test_id"])

        results_by_cat = {}
        for cat, data in categories.items():
            accuracy = round(data["correct"] / data["total"], 4)
            results_by_cat[cat] = {
                "total":    data["total"],
                "correct":  data["correct"],
                "accuracy": accuracy,
                "cases":    data["cases"],
                "meets_target": accuracy >= self.thresholds["accuracy_target"],
            }

        return results_by_cat

    # ── Role Analysis ─────────────────────────────────────────────────────────

    def analyze_by_role(self, results: list) -> dict:
        """Analyze accuracy broken down by role type."""
        roles = {}

        for r in results:
            role = r["role_type"]
            if role not in roles:
                roles[role] = {"total": 0, "correct": 0, "avg_score": 0.0}
            roles[role]["total"]    += 1
            roles[role]["avg_score"]+= r["ats_score"]
            if r["ats_decision"] == r["manual_decision"]:
                roles[role]["correct"] += 1

        results_by_role = {}
        for role, data in roles.items():
            total    = data["total"]
            accuracy = round(data["correct"] / total, 4)
            avg_score= round(data["avg_score"] / total, 2)
            results_by_role[role] = {
                "total":      total,
                "correct":    data["correct"],
                "accuracy":   accuracy,
                "avg_score":  avg_score,
                "meets_target": accuracy >= self.thresholds["accuracy_target"],
            }

        return results_by_role

    # ── Improvement Backlog ───────────────────────────────────────────────────

    def generate_improvement_backlog(self,
                                      metrics: dict,
                                      mismatches: list,
                                      category_results: dict) -> list:
        """
        Generate a prioritized list of improvements based on test results.
        """
        backlog = []

        # Precision below target
        if metrics["precision"] < self.thresholds["precision_target"]:
            backlog.append({
                "priority":    "High",
                "area":        "Skill Matching",
                "issue":       f"Precision {round(metrics['precision']*100,1)}% below target {round(self.thresholds['precision_target']*100,1)}%",
                "improvement": "Increase required skill weight and add partial credit for related skills",
                "metric":      "precision",
            })

        # Recall below target
        if metrics["recall"] < self.thresholds["recall_target"]:
            backlog.append({
                "priority":    "High",
                "area":        "Candidate Discovery",
                "issue":       f"Recall {round(metrics['recall']*100,1)}% below target {round(self.thresholds['recall_target']*100,1)}%",
                "improvement": "Lower auto-reject threshold and expand synonym matching for skills",
                "metric":      "recall",
            })

        # High mismatch rate
        if metrics["mismatch_rate"] > self.thresholds["mismatch_tolerance"]:
            backlog.append({
                "priority":    "High",
                "area":        "Zone Classification",
                "issue":       f"Mismatch rate {round(metrics['mismatch_rate']*100,1)}% exceeds tolerance {round(self.thresholds['mismatch_tolerance']*100,1)}%",
                "improvement": "Widen the manual review zone to capture more border cases",
                "metric":      "mismatch_rate",
            })

        # Category-specific issues
        for cat, data in category_results.items():
            if not data["meets_target"]:
                backlog.append({
                    "priority":    "Medium",
                    "area":        f"Profile Category: {cat}",
                    "issue":       f"Accuracy {round(data['accuracy']*100,1)}% below target for {cat} profiles",
                    "improvement": f"Add calibrated thresholds and weight profiles specific to {cat} profiles",
                    "metric":      "category_accuracy",
                })

        # Mismatch pattern analysis
        fresher_mismatches = [m for m in mismatches if "fresher" in m.get("profile_category","")]
        if fresher_mismatches:
            backlog.append({
                "priority":    "Medium",
                "area":        "Fresher Profiles",
                "issue":       f"{len(fresher_mismatches)} mismatch(es) in fresher profiles",
                "improvement": "Add academic performance and internship weighting for fresher profiles",
                "metric":      "fresher_accuracy",
            })

        # Always add these standard improvements
        backlog.append({
            "priority":    "Low",
            "area":        "Semantic Matching",
            "issue":       "TF-IDF semantic scores are lower than neural embeddings",
            "improvement": "Integrate a lightweight sentence transformer model to improve semantic similarity scores",
            "metric":      "semantic_quality",
        })

        backlog.append({
            "priority":    "Low",
            "area":        "Skill Synonyms",
            "issue":       "Exact keyword matching misses candidates who describe skills differently",
            "improvement": "Build a skill synonym dictionary for all major technologies and domains",
            "metric":      "skill_coverage",
        })

        return sorted(backlog, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x["priority"]])

    # ── Main Test Run ─────────────────────────────────────────────────────────

    def run_tests(self, test_cases: list = None) -> dict:
        """
        Run full ATS accuracy test suite.
        Returns complete test report with metrics, analysis, and backlog.
        """
        cases = test_cases or self.test_cases

        confusion         = self.build_confusion_matrix(cases)
        metrics           = self.compute_metrics(confusion)
        category_analysis = self.analyze_by_category(cases)
        role_analysis     = self.analyze_by_role(cases)
        backlog           = self.generate_improvement_backlog(
            metrics, confusion["mismatches"], category_analysis
        )

        meets_targets = {
            "precision":     metrics["precision"]     >= self.thresholds["precision_target"],
            "recall":        metrics["recall"]        >= self.thresholds["recall_target"],
            "f1_score":      metrics["f1_score"]      >= self.thresholds["f1_target"],
            "accuracy":      metrics["accuracy"]      >= self.thresholds["accuracy_target"],
            "mismatch_rate": metrics["mismatch_rate"] <= self.thresholds["mismatch_tolerance"],
        }

        return {
            "report_metadata": {
                "generated_at":   datetime.now().isoformat(),
                "tester_version": "1.0",
                "total_test_cases": len(cases),
                "thresholds_used":  self.thresholds,
            },
            "confusion_matrix":   confusion,
            "accuracy_metrics":   metrics,
            "meets_targets":      meets_targets,
            "overall_pass":       all(meets_targets.values()),
            "category_analysis":  category_analysis,
            "role_analysis":      role_analysis,
            "improvement_backlog":backlog,
        }

    def save_report(self, report: dict, output_path: str):
        """Save test report to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
