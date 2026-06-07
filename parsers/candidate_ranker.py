"""
Day 14 – Candidate Ranking & Shortlisting
Zecpath AI Recruitment Platform

Automates ranking, filtering, and shortlisting of candidates
based on ATS scores from Day 13.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# ── Shortlisting Thresholds ───────────────────────────────────────────────────

DEFAULT_THRESHOLDS = {
    "auto_shortlist": 70,    # Score >= 70 → Auto Shortlisted
    "manual_review":  45,    # Score 45-69 → Manual Review
    "auto_reject":    44,    # Score <= 44 → Auto Rejected
}

# ── Zone Labels ───────────────────────────────────────────────────────────────

ZONE_LABELS = {
    "shortlisted": "Shortlisted",
    "review":      "Manual Review",
    "rejected":    "Rejected",
}

# ── Role-Specific Thresholds ──────────────────────────────────────────────────

ROLE_THRESHOLDS = {
    "software_engineer": {
        "auto_shortlist": 72,
        "manual_review":  48,
        "auto_reject":    47,
    },
    "data_analyst": {
        "auto_shortlist": 68,
        "manual_review":  45,
        "auto_reject":    44,
    },
    "management_trainee": {
        "auto_shortlist": 65,
        "manual_review":  42,
        "auto_reject":    41,
    },
    "data_scientist": {
        "auto_shortlist": 72,
        "manual_review":  48,
        "auto_reject":    47,
    },
    "devops_engineer": {
        "auto_shortlist": 75,
        "manual_review":  50,
        "auto_reject":    49,
    },
    "hr_manager": {
        "auto_shortlist": 65,
        "manual_review":  42,
        "auto_reject":    41,
    },
    "default": DEFAULT_THRESHOLDS,
}


class CandidateRanker:
    """
    Ranks, filters, and shortlists candidates based on ATS scores.
    Supports configurable thresholds per role type.
    Generates recruiter-friendly output with ranked lists,
    zone classification, and summary reports.
    """

    def __init__(self,
                 thresholds: Optional[dict] = None,
                 role_type: str = "default"):
        self.role_type  = role_type
        self.thresholds = thresholds or ROLE_THRESHOLDS.get(
            role_type, DEFAULT_THRESHOLDS
        )

    # ── Zone Classification ───────────────────────────────────────────────────

    def classify_zone(self, score: float) -> str:
        """Classify a candidate into shortlisted, review, or rejected zone."""
        if score >= self.thresholds["auto_shortlist"]:
            return "shortlisted"
        elif score >= self.thresholds["manual_review"]:
            return "review"
        else:
            return "rejected"

    def get_zone_label(self, zone: str) -> str:
        """Get human-readable label for a zone."""
        return ZONE_LABELS.get(zone, zone)

    # ── Ranking ───────────────────────────────────────────────────────────────

    def rank_candidates(self, ats_results: list) -> list:
        """
        Sort candidates by ATS score descending.
        Adds rank number, zone classification, and zone label.
        Returns ranked list with all candidates.
        """
        # Sort by score descending
        sorted_results = sorted(
            ats_results,
            key=lambda x: x["final_score"]["score"],
            reverse=True
        )

        ranked = []
        for rank, result in enumerate(sorted_results, 1):
            score = result["final_score"]["score"]
            zone  = self.classify_zone(score)

            ranked.append({
                "rank":            rank,
                "candidate_id":    result["metadata"]["candidate_id"],
                "score":           score,
                "grade":           result["final_score"]["grade"],
                "zone":            zone,
                "zone_label":      self.get_zone_label(zone),
                "recommendation":  result["final_score"]["recommendation"],
                "strengths":       result["final_score"].get("strengths", []),
                "gaps":            result["final_score"].get("gaps", []),
                "is_complete":     result["final_score"].get("is_complete", True),
                "score_breakdown": result.get("score_breakdown", {}),
                "ats_result":      result,
            })

        return ranked

    # ── Filtering ─────────────────────────────────────────────────────────────

    def get_shortlisted(self, ranked: list) -> list:
        """Return only auto-shortlisted candidates."""
        return [c for c in ranked if c["zone"] == "shortlisted"]

    def get_review_zone(self, ranked: list) -> list:
        """Return only candidates in the manual review zone."""
        return [c for c in ranked if c["zone"] == "review"]

    def get_rejected(self, ranked: list) -> list:
        """Return only auto-rejected candidates."""
        return [c for c in ranked if c["zone"] == "rejected"]

    def get_top_n(self, ranked: list, n: int = 5) -> list:
        """Return top N candidates regardless of zone."""
        return ranked[:n]

    def filter_by_min_score(self,
                             ranked: list,
                             min_score: float) -> list:
        """Return candidates with score above a minimum threshold."""
        return [c for c in ranked if c["score"] >= min_score]

    def filter_complete_data(self, ranked: list) -> list:
        """Return only candidates with complete data across all components."""
        return [c for c in ranked if c["is_complete"]]

    # ── Shortlisting Report ───────────────────────────────────────────────────

    def generate_shortlist_report(self,
                                   ranked: list,
                                   job_id: str = "",
                                   role_type: str = "") -> dict:
        """
        Generate a complete shortlisting report.
        Includes zone distribution, top candidates, and summary stats.
        """
        shortlisted = self.get_shortlisted(ranked)
        review      = self.get_review_zone(ranked)
        rejected    = self.get_rejected(ranked)
        total       = len(ranked)

        scores = [c["score"] for c in ranked]
        avg_score = round(sum(scores) / total, 2) if total > 0 else 0.0
        top_score = round(max(scores), 2)         if scores else 0.0
        low_score = round(min(scores), 2)         if scores else 0.0

        return {
            "report_metadata": {
                "generated_at":  datetime.now().isoformat(),
                "job_id":        job_id,
                "role_type":     role_type or self.role_type,
                "engine_version":"1.0",
                "thresholds":    self.thresholds,
            },
            "summary": {
                "total_candidates":  total,
                "shortlisted_count": len(shortlisted),
                "review_count":      len(review),
                "rejected_count":    len(rejected),
                "shortlist_rate":    round(len(shortlisted)/total*100, 1) if total>0 else 0,
                "rejection_rate":    round(len(rejected)/total*100, 1)   if total>0 else 0,
                "avg_score":         avg_score,
                "top_score":         top_score,
                "lowest_score":      low_score,
            },
            "shortlisted_candidates": [
                self._candidate_summary(c) for c in shortlisted
            ],
            "review_candidates": [
                self._candidate_summary(c) for c in review
            ],
            "rejected_candidates": [
                self._candidate_summary(c) for c in rejected
            ],
            "full_ranked_list": [
                self._candidate_summary(c) for c in ranked
            ],
        }

    def _candidate_summary(self, candidate: dict) -> dict:
        """Build a concise candidate summary for the report."""
        bd = candidate.get("score_breakdown", {})
        return {
            "rank":           candidate["rank"],
            "candidate_id":   candidate["candidate_id"],
            "score":          candidate["score"],
            "grade":          candidate["grade"],
            "zone":           candidate["zone"],
            "zone_label":     candidate["zone_label"],
            "recommendation": candidate["recommendation"],
            "strengths":      candidate["strengths"],
            "gaps":           candidate["gaps"],
            "is_complete":    candidate["is_complete"],
            "breakdown": {
                "skill_match":          bd.get("skill_match", 0),
                "experience_relevance": bd.get("experience_relevance", 0),
                "education_alignment":  bd.get("education_alignment", 0),
                "semantic_similarity":  bd.get("semantic_similarity", 0),
            },
        }

    # ── Recruiter Output ──────────────────────────────────────────────────────

    def generate_recruiter_summary(self, report: dict) -> str:
        """
        Generate a human-readable recruiter summary.
        Shows ranked candidates with scores and zones clearly.
        """
        meta    = report["report_metadata"]
        summary = report["summary"]
        lines   = [
            "=" * 65,
            "  ZECPATH AI - CANDIDATE SHORTLISTING REPORT",
            f"  Job ID    : {meta['job_id']}",
            f"  Role      : {meta['role_type']}",
            f"  Generated : {meta['generated_at'][:19]}",
            "=" * 65,
            "",
            "  SUMMARY",
            f"  Total Candidates   : {summary['total_candidates']}",
            f"  Shortlisted        : {summary['shortlisted_count']} "
            f"({summary['shortlist_rate']}%)",
            f"  Manual Review      : {summary['review_count']}",
            f"  Auto Rejected      : {summary['rejected_count']} "
            f"({summary['rejection_rate']}%)",
            f"  Average Score      : {summary['avg_score']}",
            f"  Top Score          : {summary['top_score']}",
            "",
            "  THRESHOLDS",
            f"  Auto Shortlist     : >= {meta['thresholds']['auto_shortlist']}",
            f"  Manual Review      : {meta['thresholds']['manual_review']} "
            f"- {meta['thresholds']['auto_shortlist'] - 1}",
            f"  Auto Reject        : <= {meta['thresholds']['auto_reject']}",
            "",
            "  FULL RANKED LIST",
            f"  {'Rank':<6} {'Candidate':<20} {'Score':>7} "
            f"{'Grade':>6} {'Zone':<18} {'Complete'}",
            "  " + "-" * 63,
        ]

        for c in report["full_ranked_list"]:
            complete = "Yes" if c["is_complete"] else "No"
            lines.append(
                f"  {c['rank']:<6} {c['candidate_id']:<20} "
                f"{c['score']:>7} {c['grade']:>6} "
                f"{c['zone_label']:<18} {complete}"
            )

        if report["shortlisted_candidates"]:
            lines += [
                "",
                "  SHORTLISTED CANDIDATES",
                "  " + "-" * 63,
            ]
            for c in report["shortlisted_candidates"]:
                lines.append(
                    f"  Rank {c['rank']}: {c['candidate_id']} "
                    f"| Score: {c['score']} | {c['recommendation']}"
                )
                if c["strengths"]:
                    lines.append(
                        f"    Strengths: {', '.join(c['strengths'][:3])}"
                    )

        if report["review_candidates"]:
            lines += [
                "",
                "  MANUAL REVIEW CANDIDATES",
                "  " + "-" * 63,
            ]
            for c in report["review_candidates"]:
                lines.append(
                    f"  Rank {c['rank']}: {c['candidate_id']} "
                    f"| Score: {c['score']} | {c['zone_label']}"
                )
                if c["gaps"]:
                    lines.append(
                        f"    Gaps: {', '.join(c['gaps'][:3])}"
                    )

        lines.append("=" * 65)
        return "\n".join(lines)

    # ── Save Output ───────────────────────────────────────────────────────────

    def save_report(self, report: dict, output_path: str):
        """Save shortlisting report to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")

    def save_shortlist_csv(self, report: dict, output_path: str):
        """Save ranked candidate list as a simple CSV file."""
        lines = [
            "Rank,Candidate ID,Score,Grade,Zone,Complete,"
            "Skill Match,Experience,Education,Semantic,Recommendation"
        ]
        for c in report["full_ranked_list"]:
            bd = c["breakdown"]
            lines.append(
                f"{c['rank']},{c['candidate_id']},{c['score']},"
                f"{c['grade']},{c['zone_label']},"
                f"{'Yes' if c['is_complete'] else 'No'},"
                f"{bd.get('skill_match',0)},"
                f"{bd.get('experience_relevance',0)},"
                f"{bd.get('education_alignment',0)},"
                f"{bd.get('semantic_similarity',0)},"
                f"{c['recommendation']}"
            )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved -> {output_path}")
