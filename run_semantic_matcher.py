"""
Day 12 - Semantic Matching Engine
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.semantic_matcher import SemanticMatchingEngine


SOFTWARE_ENGINEER_JD = """
Software Engineer

We are looking for a passionate Software Engineer with strong Python skills.

Key Responsibilities:
- Develop and maintain RESTful APIs using Python and Django
- Implement machine learning models for data processing
- Deploy applications on AWS using Docker and Kubernetes
- Work with PostgreSQL and Redis for data storage
- Collaborate with cross-functional teams using Agile methodology
- Write clean, testable code with proper documentation

Required Skills:
Python, Django, REST API, Machine Learning, AWS, Docker, PostgreSQL,
SQL, Git, Linux, TensorFlow, Flask, Kubernetes, CI/CD

Qualifications:
- Bachelor's degree in Computer Science or related field
- 2-5 years of experience in software development
- Strong problem-solving and communication skills
"""

DATA_ANALYST_JD = """
Data Analyst

We are seeking a detail-oriented Data Analyst to join our analytics team.

Key Responsibilities:
- Analyze large datasets using Python and SQL
- Build interactive dashboards using Power BI and Tableau
- Perform statistical analysis and data visualization
- Automate reporting processes using Python scripts
- Present insights to senior management

Required Skills:
Python, SQL, Power BI, Tableau, Excel, Data Analysis,
Statistical Analysis, Pandas, NumPy, Data Visualization

Qualifications:
- Bachelor's or Master's degree in Statistics, Mathematics, or related field
- 1-3 years of data analysis experience
"""


def run_matcher(input_dir="data/sample_resumes", output_dir="data/outputs"):

    print("\n" + "=" * 65)
    print("   ZECPATH AI - SEMANTIC MATCHING ENGINE v1.0")
    print("=" * 65)

    engine = SemanticMatchingEngine()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    resume_files = sorted(Path(input_dir).glob("*.txt"))
    if not resume_files:
        print(f"No .txt files found in {input_dir}")
        sys.exit(1)

    print(f"\nFound {len(resume_files)} resume(s)")
    print(f"\nMatching against: Software Engineer JD\n")

    resume_texts = [f.read_text(encoding="utf-8") for f in resume_files]
    resume_names = [f.name for f in resume_files]

    results = engine.match_batch(
        resume_texts, SOFTWARE_ENGINEER_JD,
        resume_names, "software_engineer_jd"
    )

    all_results = []
    for result, resume_file in zip(results, resume_files):
        all_results.append(result)
        print(f"{'─'*65}")
        print(f"Resume: {resume_file.name}")

        scores  = result["similarity_scores"]
        overall = result["overall_match"]

        print(f"\n   Skills Similarity     : {scores['skills']['score']}"
              f"  [{scores['skills']['level'].upper()}]")
        print(f"   Experience Similarity : {scores['experience']['score']}"
              f"  [{scores['experience']['level'].upper()}]")
        print(f"   Projects Similarity   : {scores['projects']['score']}"
              f"  [{scores['projects']['level'].upper()}]")
        print(f"\n   Overall Score         : {overall['score']}")
        print(f"   Grade                 : {overall['grade']}")
        print(f"   Recommendation        : {overall['recommendation']}")

        output_file = Path(output_dir) / f"{resume_file.stem}_semantic.json"
        engine.save_output(result, str(output_file))

    report      = engine.generate_accuracy_report(all_results)
    report_path = Path(output_dir) / "semantic_matching_accuracy_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'─'*65}")
    print("ACCURACY REPORT")
    print(f"{'─'*65}")
    avg = report["average_scores"]
    print(f"   Avg Skills Score     : {avg['skills']}")
    print(f"   Avg Experience Score : {avg['experience']}")
    print(f"   Avg Projects Score   : {avg['projects']}")
    print(f"   Avg Overall Score    : {avg['overall']}")
    print(f"   Grade Distribution   : {report['grade_distribution']}")
    print(f"\n   Report saved -> {report_path}")

    print("\n" + "=" * 65)
    print("Semantic matching complete!")
    print("=" * 65 + "\n")

    return all_results, report


if __name__ == "__main__":
    run_matcher()