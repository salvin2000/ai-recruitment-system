"""
Day 14 - Candidate Ranking & Shortlisting
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_scorer import ATSScoringEngine
from parsers.candidate_ranker import CandidateRanker


# ── Sample Job Requirements ───────────────────────────────────────────────────

SOFTWARE_ENGINEER_JD = {
    "job_id":               "ZCP-JOB-20260529-SW01",
    "role_name":            "Software Engineer",
    "required_skills":      ["python", "django", "aws", "docker",
                             "postgresql", "git", "rest api"],
    "preferred_skills":     ["kubernetes", "machine learning",
                             "react", "redis"],
    "min_experience_years": 2,
    "max_experience_years": 5,
    "min_education":        "b.tech",
    "field_of_study":       "computer science",
}


def make_candidate(cid, skills, exp_score, edu_score, sem_score):
    return {
        "candidate_id": cid,
        "job_id":       SOFTWARE_ENGINEER_JD["job_id"],
        "skill_data": {
            "skill_summary": {
                "technical": skills,
                "soft": [], "business": [], "creative": [],
            }
        },
        "experience_data": {
            "metadata": {"total_years": exp_score * 5},
            "relevance": {
                "relevance_score":      exp_score,
                "role_similarity":      exp_score,
                "skills_match":         exp_score * 0.8,
                "total_years":          exp_score * 5,
                "meets_min_experience": exp_score >= 0.5,
            }
        },
        "education_data": {
            "metadata": {"highest_degree": "b.tech", "total_certifications": 2},
            "relevance": {
                "relevance_score": edu_score,
                "meets_min_degree": True,
                "degree_score": edu_score,
                "field_score": edu_score * 0.9,
            }
        },
        "semantic_data": {
            "overall_match": {"score": sem_score * 0.35},
            "similarity_scores": {
                "skills":     {"score": sem_score * 0.40},
                "experience": {"score": sem_score * 0.25},
                "projects":   {"score": sem_score * 0.15},
            }
        }
    }


# 6 candidates with different score profiles
CANDIDATES = [
    make_candidate("ZCP-CAND-ARJU",
                   ["python","django","aws","docker","postgresql","git","machine learning"],
                   0.90, 1.0, 0.95),
    make_candidate("ZCP-CAND-PRIY",
                   ["python","django","react","postgresql","git","docker"],
                   0.80, 1.0, 0.85),
    make_candidate("ZCP-CAND-KART",
                   ["python","aws","docker","kubernetes","git"],
                   0.75, 0.90, 0.75),
    make_candidate("ZCP-CAND-SNEH",
                   ["python","sql","power bi","pandas","tableau"],
                   0.60, 0.89, 0.40),
    make_candidate("ZCP-CAND-RAHU",
                   ["python","sql","java","git"],
                   0.25, 1.0,  0.45),
    make_candidate("ZCP-CAND-VISH",
                   ["java","spring","mysql"],
                   0.20, 0.80, 0.20),
]


def run_ranker():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - CANDIDATE RANKING & SHORTLISTING v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    # Step 1: Score all candidates using Day 13 ATS Engine
    print("\nStep 1: Scoring candidates with ATS Engine...")
    scorer  = ATSScoringEngine()
    results = scorer.score_batch(
        CANDIDATES, SOFTWARE_ENGINEER_JD, "software_engineer"
    )
    print(f"         Scored {len(results)} candidates")

    # Step 2: Rank and shortlist using Day 14 Ranker
    print("Step 2: Ranking and shortlisting...")
    ranker  = CandidateRanker(role_type="software_engineer")
    ranked  = ranker.rank_candidates(results)
    report  = ranker.generate_shortlist_report(
        ranked,
        job_id    = SOFTWARE_ENGINEER_JD["job_id"],
        role_type = "software_engineer",
    )
    print(f"         Ranked {len(ranked)} candidates")

    # Step 3: Print recruiter summary
    print("\n" + ranker.generate_recruiter_summary(report))

    # Step 4: Show zone details
    shortlisted = ranker.get_shortlisted(ranked)
    review      = ranker.get_review_zone(ranked)
    rejected    = ranker.get_rejected(ranked)
    top3        = ranker.get_top_n(ranked, 3)

    print(f"\nTop 3 Candidates:")
    for c in top3:
        print(f"  Rank {c['rank']}: {c['candidate_id']} | "
              f"Score: {c['score']} | {c['zone_label']}")

    # Step 5: Save outputs
    ranker.save_report(report, "data/outputs/shortlisting_report.json")
    ranker.save_shortlist_csv(report, "data/outputs/ranked_candidates.csv")

    # Save individual ranked results
    for candidate in ranked:
        cid = candidate["candidate_id"]
        output_path = f"data/outputs/{cid}_ranked.json"
        with open(output_path, "w") as f:
            json.dump(candidate, f, indent=2, default=str)

    print("\n" + "=" * 65)
    print("Ranking and shortlisting complete!")
    print("=" * 65 + "\n")

    return ranked, report


if __name__ == "__main__":
    run_ranker()
