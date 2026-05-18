"""
Day 9 – Skill Extraction Engine
Main runner script
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.skill_extractor import SkillExtractionEngine


def run_extractor(input_dir: str = "data/sample_resumes",
                  output_dir: str = "data/outputs"):
    """Run skill extraction on all sample resumes."""

    print("\n" + "=" * 65)
    print("   ZECPATH AI — SKILL EXTRACTION ENGINE v1.0")
    print("=" * 65)

    engine = SkillExtractionEngine()
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

        result = engine.extract_from_file(str(resume_file))
        all_results.append(result)

        meta = result["metadata"]
        print(f"\n   Total skills extracted : {meta['total_skills']}")
        print(f"   High confidence (≥0.85): {meta['high_confidence']}")
        print(f"   Medium confidence      : {meta['medium_confidence']}")
        print(f"   Low confidence         : {meta['low_confidence']}")

        # Print top skills by category
        by_cat = result["skills_by_category"]
        for category, skills in by_cat.items():
            if skills:
                top = skills[:5]
                skill_names = ", ".join(
                    f"{s['skill']} ({s['confidence']})"
                    for s in top
                )
                print(f"\n   {category}:")
                print(f"   {skill_names}")

        # Save output
        output_file = Path(output_dir) / f"{resume_file.stem}_skills.json"
        engine.save_output(result, str(output_file))

    # Summary
    print(f"\n{'─'*65}")
    print("📊 SUMMARY")
    print(f"{'─'*65}")
    total_skills = sum(r["metadata"]["total_skills"] for r in all_results)
    avg_skills = round(total_skills / len(all_results), 1) if all_results else 0
    print(f"   Resumes processed    : {len(all_results)}")
    print(f"   Total skills found   : {total_skills}")
    print(f"   Avg skills/resume    : {avg_skills}")

    print("\n" + "=" * 65)
    print("✅ Skill extraction complete!")
    print("=" * 65 + "\n")

    return all_results


if __name__ == "__main__":
    run_extractor()
