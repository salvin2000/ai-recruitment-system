"""
Day 13 - ATS Scoring Formula Design
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_scorer import ATSScoringEngine, WeightProfile


# ── Sample Job Requirements ───────────────────────────────────────────────────

SOFTWARE_ENGINEER_JD = {
    "job_id":                "ZCP-JOB-20260529-SW01",
    "role_name":             "Software Engineer",
    "required_skills":       ["python", "django", "aws", "docker",
                              "postgresql", "git", "rest api"],
    "preferred_skills":      ["kubernetes", "machine learning",
                              "react", "redis"],
    "min_experience_years":  2,
    "max_experience_years":  5,
    "min_education":         "b.tech",
    "field_of_study":        "computer science",
}


def make_candidate(name, skills, exp_score, edu_score, sem_score):
    """Helper to build a candidate dict with mock component data."""
    return {
        "candidate_id": f"ZCP-CAND-{name.upper()[:4]}",
        "job_id":       SOFTWARE_ENGINEER_JD["job_id"],
        "skill_data": {
            "skill_summary": {
                "technical": skills,
                "soft":       [],
                "business":   [],
                "creative":   [],
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
            "metadata": {
                "highest_degree":       "b.tech",
                "total_certifications": 2,
            },
            "relevance": {
                "relevance_score": edu_score,
                "meets_min_degree":True,
                "degree_score":    edu_score,
                "field_score":     edu_score * 0.9,
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


CANDIDATES = [
    make_candidate("Arjun",  ["python","django","aws","docker","postgresql",
                               "git","machine learning"],    0.85, 1.0, 0.90),
    make_candidate("Sneha",  ["python","sql","power bi","pandas","tableau"],
                              0.70, 0.89, 0.40),
    make_candidate("Rahul",  ["python","sql","java","git"],  0.30, 1.0, 0.50),
]


def run_scorer():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - ATS SCORING ENGINE v1.0")
    print("=" * 65)

    engine = ATSScoringEngine()
    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    print(f"\nRole     : {SOFTWARE_ENGINEER_JD['role_name']}")
    print(f"Profile  : software_engineer weights")
    print(f"Candidates: {len(CANDIDATES)}\n")

    # Score all candidates
    results = engine.score_batch(
        CANDIDATES, SOFTWARE_ENGINEER_JD, "software_engineer"
    )

    print(f"{'─'*65}")
    print(f"RANKED RESULTS")
    print(f"{'─'*65}")

    for rank, result in enumerate(results, 1):
        meta  = result["metadata"]
        final = result["final_score"]
        bd    = result["score_breakdown"]

        print(f"\nRank {rank}: {meta['candidate_id']}")
        print(f"  Score          : {final['score']} / 100")
        print(f"  Grade          : {final['grade']}")
        print(f"  Recommendation : {final['recommendation']}")
        print(f"  Breakdown:")
        print(f"    Skill Match         : {bd['skill_match']}")
        print(f"    Experience Relevance: {bd['experience_relevance']}")
        print(f"    Education Alignment : {bd['education_alignment']}")
        print(f"    Semantic Similarity : {bd['semantic_similarity']}")
        if final["strengths"]:
            print(f"  Strengths: {', '.join(final['strengths'])}")
        if final["gaps"]:
            print(f"  Gaps: {', '.join(final['gaps'])}")

        # Print scorecard for top candidate
        if rank == 1:
            print("\n" + engine.generate_scorecard(result))

        output_file = f"data/outputs/{meta['candidate_id']}_ats_score.json"
        engine.save_output(result, output_file)

    # Demonstrate custom weights
    print(f"\n{'─'*65}")
    print("CUSTOM WEIGHT DEMO — Skill-Heavy Profile")
    print(f"{'─'*65}")
    engine.set_custom_weights(0.50, 0.25, 0.10, 0.15, "skill_heavy")
    custom_result = engine.score(
        candidate_id     = "ZCP-CAND-ARJUN",
        job_id           = SOFTWARE_ENGINEER_JD["job_id"],
        skill_data       = CANDIDATES[0]["skill_data"],
        experience_data  = CANDIDATES[0]["experience_data"],
        education_data   = CANDIDATES[0]["education_data"],
        semantic_data    = CANDIDATES[0]["semantic_data"],
        job_requirements = SOFTWARE_ENGINEER_JD,
        role_type        = "skill_heavy",
    )
    print(f"Score with skill_heavy weights: "
          f"{custom_result['final_score']['score']} "
          f"(Grade: {custom_result['final_score']['grade']})")

    print("\n" + "=" * 65)
    print("ATS scoring complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_scorer()
