"""
Day 21 - Eligibility Decision Engine
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.eligibility_engine import (
    EligibilityDecisionEngine,
    ROLE_ELIGIBILITY_CONFIGS, ELIGIBILITY_TAGS
)


CANDIDATES = [
    {
        "candidate_id":    "ZCP-CAND-ARJU",
        "name":            "Arjun Krishnan",
        "ats_score":        82.24,
        "skills":          ["python", "django", "aws", "docker", "postgresql"],
        "experience_years": 3.9,
        "location":        "bangalore",
        "notice_period_days": 30,
    },
    {
        "candidate_id":    "ZCP-CAND-PRIY",
        "name":            "Priya Sharma",
        "ats_score":        73.99,
        "skills":          ["python", "django", "react", "postgresql"],
        "experience_years": 3.5,
        "location":        "mumbai",
        "notice_period_days": 45,
    },
    {
        "candidate_id":    "ZCP-CAND-KART",
        "name":            "Karthik Nair",
        "ats_score":        65.74,
        "skills":          ["python", "aws", "docker", "kubernetes"],
        "experience_years": 2.5,
        "location":        "kochi",
        "notice_period_days": 60,
    },
    {
        "candidate_id":    "ZCP-CAND-SNEH",
        "name":            "Sneha Pillai",
        "ats_score":        44.85,
        "skills":          ["sql", "power bi", "pandas", "tableau"],
        "experience_years": 2.0,
        "location":        "pune",
        "notice_period_days": 30,
    },
    {
        "candidate_id":    "ZCP-CAND-RAHU",
        "name":            "Rahul Menon",
        "ats_score":        37.37,
        "skills":          ["python", "sql", "java", "git"],
        "experience_years": 0.0,
        "location":        "kochi",
        "notice_period_days": 0,
    },
    {
        "candidate_id":    "ZCP-CAND-VISH",
        "name":            "Vishnu Prasad",
        "ats_score":        21.50,
        "skills":          ["java", "spring", "mysql"],
        "experience_years": 2.0,
        "location":        "trivandrum",
        "notice_period_days": 60,
    },
]


def run_eligibility():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - ELIGIBILITY DECISION ENGINE v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    engine = EligibilityDecisionEngine(role_type="software_engineer")

    # ── Step 1: Show Config ───────────────────────────────────────────────────
    print("\nStep 1: Eligibility Configuration (software_engineer)")
    print("─" * 65)
    cfg = ROLE_ELIGIBILITY_CONFIGS["software_engineer"]
    print(f"  Min ATS Score       : {cfg['min_ats_score']}")
    print(f"  Review ATS Score    : {cfg['review_ats_score']}")
    print(f"  Experience Range    : {cfg['min_experience_years']} - {cfg['max_experience_years']} years")
    print(f"  Mandatory Skills    : {cfg['mandatory_skills']}")
    print(f"  Preferred Skills    : {cfg['preferred_skills']}")
    print(f"  Location Required   : {cfg['location_required']}")
    print(f"  Max Notice Period   : {cfg['max_notice_period_days']} days")

    # ── Step 2: Evaluate Each Candidate ──────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Candidate Eligibility Decisions")
    print("─" * 65)

    results = engine.decide_batch(CANDIDATES)

    print(f"\n  {'Candidate':<20} {'Score':>7} {'Tag':<12} {'Passed':>7} {'Failed Rules'}")
    print(f"  {'─'*20} {'─'*7} {'─'*12} {'─'*7} {'─'*20}")

    for r in results:
        cand = next(c for c in CANDIDATES if c["candidate_id"] == r["candidate_id"])
        failed = ", ".join(f["rule"] for f in r["failed_rules"]) or "none"
        print(f"  {cand['name']:<20} {r['ats_score']:>7} "
              f"{r['eligibility_tag']:<12} "
              f"{r['checks_passed']}/{r['total_checks']:>3}     {failed}")

    # ── Step 3: Detailed View for Each ───────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Detailed Check Results")
    print("─" * 65)

    for r in results:
        cand = next(c for c in CANDIDATES if c["candidate_id"] == r["candidate_id"])
        print(f"\n  {cand['name']} — {r['eligibility_tag'].upper()}")
        for check_name, check_data in r["checks"].items():
            status = "PASS" if check_data["passed"] else "FAIL"
            print(f"    [{status}] {check_name:<20} : {check_data['reason']}")

    # ── Step 4: Summary Report ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Eligibility Summary Report")
    print("─" * 65)

    report = engine.generate_eligibility_report(
        results, job_id="ZCP-JOB-20260529-SW01"
    )
    s = report["summary"]
    print(f"\n  Total Evaluated : {s['total']}")
    print(f"  Eligible        : {s['eligible_count']} ({s['eligible_rate']}%)")
    print(f"  Review          : {s['review_count']}")
    print(f"  Rejected        : {s['rejected_count']} ({s['rejection_rate']}%)")

    if report["eligible_candidates"]:
        print(f"\n  Eligible Candidates:")
        for c in report["eligible_candidates"]:
            print(f"    {c['candidate_id']} — Score: {c['ats_score']} — "
                  f"Checks: {c['checks_passed']}/{c['total_checks']}")

    engine.save_report(report, "data/outputs/eligibility_report.json")

    print("\n" + "=" * 65)
    print("Eligibility decision engine complete!")
    print("=" * 65 + "\n")

    return results, report


if __name__ == "__main__":
    run_eligibility()
