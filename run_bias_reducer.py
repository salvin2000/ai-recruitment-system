"""
Day 15 - Fairness, Normalization & Bias Reduction
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.bias_reducer import ResumeNormalizer, ScoreNormalizer, BiasDetector


SAMPLE_RESUMES = {
    "arjun": """Arjun Krishnan
Mr. Arjun Krishnan
arjun.krishnan@email.com | +91-9876543210
Male, Age: 26, Hindu, Married
Bangalore, Karnataka, India

Summary
Passionate and enthusiastic Software Engineer with 3 years of experience.
A true rockstar developer with innovative cutting-edge skills.

Technical Skills
Python, Django, REST API, Machine Learning, AWS, Docker, PostgreSQL

Work Experience
Software Engineer - TechCorp India Pvt Ltd, Bangalore
June 2022 - Present
- Developed RESTful APIs using Django REST Framework
- Implemented Machine Learning models for customer churn prediction

Education
Bachelor of Technology - Computer Science Engineering
RV College of Engineering, Bangalore | 2017 - 2021
CGPA: 8.4 / 10

Certifications
- AWS Certified Developer Associate (2023)
- Machine Learning Specialization - Coursera (2022)""",

    "sneha": """Sneha Pillai
Ms. Sneha Pillai
sneha.pillai@email.com | +91-9988776655
Female, DOB: 15-03-1998

Core Competencies
SQL, Python, Power BI, Tableau, Excel, Statistical Analysis

Professional Experience
Data Analyst - Analytics Corp
March 2022 - Present
- Designed dashboards using Power BI
- Performed statistical analysis on sales data

Educational Background
Master of Science - Statistics
University of Mumbai | 2019 - 2021

Certifications & Training
- Microsoft Power BI Associate (2023)""",

    "rahul": """Rahul Menon
rahul.menon@email.com | +91-9012345678

B.Tech Computer Science - Fresher
Model Engineering College, Kochi | 2020 - 2024
CGPA: 7.8 / 10

Technical Skills
Python, Java, SQL, Linux, Git, MySQL

Projects
Library Management System - Built using Python and MySQL
Student Result Analysis - Data analysis using Python and Pandas

Certifications
- Python Programming - NPTEL (2022)
- Web Development Bootcamp - Udemy (2023)""",
}

SAMPLE_SCORES = [79.87, 44.85, 39.75]
CANDIDATE_IDS = ["ZCP-CAND-ARJU", "ZCP-CAND-SNEH", "ZCP-CAND-RAHU"]


def run_bias_reducer():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - FAIRNESS & BIAS REDUCTION ENGINE v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    normalizer = ResumeNormalizer()
    detector   = BiasDetector()

    # ── Step 1: Resume Normalization ──────────────────────────────────────────
    print("\nStep 1: Resume Normalization")
    print("─" * 65)

    for name, resume_text in SAMPLE_RESUMES.items():
        result = normalizer.normalize_resume(resume_text)
        print(f"\nResume: {name.upper()}")
        print(f"  Original Length    : {result['original_length']} chars")
        print(f"  Normalized Length  : {result['normalized_length']} chars")
        print(f"  Fields Masked      : {result['total_masked']}")
        if result["masking_log"]:
            for field, count in result["masking_log"].items():
                print(f"    {field:<25} : {count} instance(s) masked")
        print(f"  Buzzwords Removed  : {result['buzzwords_removed']}")

    # ── Step 2: Score Normalization ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Score Normalization")
    print("─" * 65)

    score_normalizer = ScoreNormalizer()

    test_scores = {
        "skill_match_raw":          0.675,
        "experience_relevance_raw": 0.850,
        "semantic_similarity_raw":  0.278,
    }

    for comp, raw in test_scores.items():
        comp_name = comp.replace("_raw", "")
        normalized = score_normalizer.min_max_normalize(raw, comp_name)
        print(f"  {comp:<35} : {raw} -> {normalized}")

    # Z-score normalization
    z_scores = score_normalizer.z_score_normalize(SAMPLE_SCORES)
    print(f"\n  Z-Score Normalization of Final Scores:")
    for cid, score, z in zip(CANDIDATE_IDS, SAMPLE_SCORES, z_scores):
        outlier = " [OUTLIER]" if abs(z) > 2.0 else ""
        print(f"  {cid:<20} Score: {score:<8} Z-Score: {z}{outlier}")

    # ── Step 3: Bias Detection ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Bias Detection")
    print("─" * 65)

    for name, resume_text in SAMPLE_RESUMES.items():
        result = detector.evaluate_resume(resume_text)
        beval  = result["bias_evaluation"]
        pi     = result["personal_info"]
        buzz   = result["buzzword_analysis"]

        print(f"\nResume: {name.upper()}")
        print(f"  Bias Risk Level    : {beval['risk_level']}")
        print(f"  Flags              : {beval['total_flags']}")
        if beval["flags"]:
            for flag in beval["flags"]:
                print(f"    - {flag}")
        print(f"  Personal Info      : {pi['personal_info_count']} items "
              f"(density: {pi['density']}) "
              f"{'FLAGGED' if pi['flagged'] else 'OK'}")
        print(f"  Buzzwords          : {buzz['buzzword_count']} found "
              f"(density: {buzz['density']}) "
              f"{'FLAGGED' if buzz['flagged'] else 'OK'}")

    # ── Step 4: Batch Evaluation ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Batch Bias Evaluation")
    print("─" * 65)

    resume_texts = list(SAMPLE_RESUMES.values())
    batch_result = detector.evaluate_batch(
        resume_texts, SAMPLE_SCORES, CANDIDATE_IDS
    )
    summary = batch_result["batch_summary"]
    dist    = batch_result["score_distribution"]

    print(f"\n  Total Resumes      : {summary['total_resumes']}")
    print(f"  High Risk          : {summary['high_risk_count']}")
    print(f"  Medium Risk        : {summary['medium_risk_count']}")
    print(f"  Low Risk           : {summary['low_risk_count']}")
    print(f"\n  Score Distribution:")
    print(f"  Mean Score         : {dist.get('mean_score', 'N/A')}")
    print(f"  Std Deviation      : {dist.get('std_dev', 'N/A')}")
    print(f"  Score Range        : {dist.get('score_range', 'N/A')}")
    if dist.get("outliers"):
        print(f"  Outliers           : {dist['outliers']}")

    # Save outputs
    detector.save_output(
        batch_result, "data/outputs/bias_evaluation_report.json"
    )

    # Save normalized resume example
    norm_example = normalizer.normalize_resume(
        SAMPLE_RESUMES["arjun"]
    )
    with open("data/outputs/arjun_normalized_resume.json", "w") as f:
        json.dump(norm_example, f, indent=2)
    print("Saved -> data/outputs/arjun_normalized_resume.json")

    print("\n" + "=" * 65)
    print("Bias reduction complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_bias_reducer()
