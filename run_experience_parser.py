"""
Day 10 – Experience Parsing & Relevance Engine
Runner script
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.experience_parser import ExperienceParser


# Sample job requirements for relevance scoring
SAMPLE_JD = {
    "role_name":              "Software Engineer",
    "required_skills":        ["python", "django", "react", "postgresql", "aws", "docker"],
    "min_experience_years":   2,
    "max_experience_years":   5,
}


def run_parser(input_dir: str = "data/sample_resumes",
               output_dir: str = "data/outputs"):

    print("\n" + "=" * 65)
    print("   ZECPATH AI — EXPERIENCE PARSER v1.0")
    print("=" * 65)

    parser    = ExperienceParser()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    resume_files = list(Path(input_dir).glob("*.txt"))
    if not resume_files:
        print(f"No .txt files found in {input_dir}")
        sys.exit(1)

    print(f"\n📂 Found {len(resume_files)} resume(s)\n")

    all_results = []

    for resume_file in sorted(resume_files):
        print(f"{'─'*65}")
        print(f"📄 {resume_file.name}")

        result = parser.parse_file(str(resume_file), SAMPLE_JD)
        all_results.append(result)

        meta = result["metadata"]
        print(f"\n   Total Roles     : {meta['total_roles']}")
        print(f"   Total Experience: {meta['total_display']}")
        print(f"   Current Role    : {meta['current_role'] or 'Not specified'}")
        print(f"   Has Gaps        : {'Yes' if meta['has_gaps'] else 'No'}")
        print(f"   Has Overlaps    : {'Yes' if meta['has_overlaps'] else 'No'}")

        for role in result["roles"]:
            print(f"\n   ▸ {role['job_title']}")
            print(f"     Company  : {role['company']}")
            print(f"     Duration : {role['duration_display']}")
            if role["skills_mentioned"]:
                print(f"     Skills   : {', '.join(role['skills_mentioned'][:5])}")

        if result["gaps"]:
            print(f"\n   ⚠ Gaps Detected:")
            for gap in result["gaps"]:
                print(f"     {gap['gap_months']} months gap after {gap['after_role']}")

        if result["relevance"]:
            rel = result["relevance"]
            print(f"\n   📊 Relevance to Job:")
            print(f"     Score      : {rel['relevance_score']} / 1.0")
            print(f"     Grade      : {rel['grade']}")
            print(f"     Role Sim   : {rel['role_similarity']}")
            print(f"     Skills     : {rel['skills_match']}")

        output_file = Path(output_dir) / f"{resume_file.stem}_experience.json"
        parser.save_output(result, str(output_file))

    print(f"\n{'─'*65}")
    print("📊 SUMMARY")
    print(f"{'─'*65}")
    total_roles = sum(r["metadata"]["total_roles"] for r in all_results)
    total_gaps  = sum(len(r["gaps"]) for r in all_results)
    print(f"   Resumes processed : {len(all_results)}")
    print(f"   Total roles found : {total_roles}")
    print(f"   Total gaps found  : {total_gaps}")

    print("\n" + "=" * 65)
    print("✅ Experience parsing complete!")
    print("=" * 65 + "\n")

    return all_results


if __name__ == "__main__":
    run_parser()
