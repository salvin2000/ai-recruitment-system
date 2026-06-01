"""
Day 11 – Education & Certification Parsing
Runner script
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.education_parser import EducationParser


SAMPLE_JD = {
    "role_name":                 "Software Engineer",
    "min_education":             "b.tech",
    "field_of_study":            "computer science",
    "required_certifications":   [],
}


def run_parser(input_dir: str = "data/sample_resumes",
               output_dir: str = "data/outputs"):

    print("\n" + "=" * 65)
    print("   ZECPATH AI — EDUCATION & CERTIFICATION PARSER v1.0")
    print("=" * 65)

    parser = EducationParser()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    resume_files = list(Path(input_dir).glob("*.txt"))
    if not resume_files:
        print(f"No .txt files found in {input_dir}")
        sys.exit(1)

    print(f"\n📂 Found {len(resume_files)} resume(s)\n")
    all_results = []

    for resume_file in sorted(resume_files):
        print(f"{'─' * 65}")
        print(f"📄 {resume_file.name}")

        result = parser.parse_file(str(resume_file), SAMPLE_JD)
        all_results.append(result)

        meta = result["metadata"]
        print(f"\n   Qualifications Found : {meta['total_qualifications']}")
        print(f"   Certifications Found : {meta['total_certifications']}")
        print(f"   Highest Degree       : {meta['highest_degree']}")

        for qual in result["qualifications"]:
            print(f"\n   ▸ {qual['degree_normalized'].upper()}")
            print(f"     Field       : {qual['field_of_study']}")
            print(f"     Institution : {qual['institution']}")
            print(f"     Year        : {qual['graduation_year']}")

        if result["certifications"]:
            print(f"\n   Certifications:")
            for cert in result["certifications"]:
                print(f"     • {cert['name']}")
                print(f"       Category : {cert['category']}")
                if cert["year"]:
                    print(f"       Year     : {cert['year']}")

        if result["relevance"]:
            rel = result["relevance"]
            print(f"\n   📊 Education Relevance:")
            print(f"     Score         : {rel['relevance_score']} / 1.0")
            print(f"     Grade         : {rel['grade']}")
            print(f"     Degree Score  : {rel['degree_score']}")
            print(f"     Field Score   : {rel['field_score']}")
            print(f"     Meets Min Deg : {rel['meets_min_degree']}")

        output_file = Path(output_dir) / f"{resume_file.stem}_education.json"
        parser.save_output(result, str(output_file))

    print(f"\n{'─' * 65}")
    print("📊 SUMMARY")
    print(f"{'─' * 65}")
    total_quals  = sum(r["metadata"]["total_qualifications"] for r in all_results)
    total_certs  = sum(r["metadata"]["total_certifications"] for r in all_results)
    print(f"   Resumes processed     : {len(all_results)}")
    print(f"   Total qualifications  : {total_quals}")
    print(f"   Total certifications  : {total_certs}")
    print("\n" + "=" * 65)
    print("✅ Education parsing complete!")
    print("=" * 65 + "\n")

    return all_results


if __name__ == "__main__":
    run_parser()
