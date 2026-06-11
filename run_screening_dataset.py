"""
Day 22 - HR Screening Dataset Creation
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.screening_dataset import (
    ScreeningDatasetManager,
    QUESTION_CATEGORIES, ROLE_QUESTION_SETS
)


def run_screening_dataset():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - HR SCREENING DATASET v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    manager = ScreeningDatasetManager()

    # ── Step 1: Dataset Summary ───────────────────────────────────────────────
    print("\nStep 1: Dataset Summary")
    print("─" * 65)
    summary = manager.generate_dataset_summary()
    meta = summary["dataset_metadata"]
    print(f"\n  Total Questions  : {meta['total_questions']}")
    print(f"  Total Categories : {meta['total_categories']}")
    print(f"  Total Roles      : {meta['total_roles']}")
    print(f"  Total Languages  : {meta['total_languages']}")
    print(f"  Question Templates: {meta['total_templates']}")

    # ── Step 2: Questions by Category ────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Questions by Category")
    print("─" * 65)
    print(f"\n  {'Category':<18} {'Total':>6} {'Mandatory':>10} {'Optional':>9}")
    print(f"  {'─'*18} {'─'*6} {'─'*10} {'─'*9}")
    for cat, data in summary["by_category"].items():
        print(f"  {cat:<18} {data['count']:>6} {data['mandatory']:>10} {data['optional']:>9}")

    # ── Step 3: Questions by Importance ──────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Questions by Scoring Importance")
    print("─" * 65)
    for level, count in summary["by_importance"].items():
        print(f"  {level:<10} : {count} questions")

    # ── Step 4: Role Coverage ─────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Role-Specific Question Sets")
    print("─" * 65)
    print(f"\n  {'Role':<22} {'Mandatory':>10} {'Optional':>9} {'Total':>6}")
    print(f"  {'─'*22} {'─'*10} {'─'*9} {'─'*6}")
    for role, data in summary["role_coverage"].items():
        total = data["mandatory"] + data["optional"]
        print(f"  {role:<22} {data['mandatory']:>10} {data['optional']:>9} {total:>6}")

    # ── Step 5: Sample Questions ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Sample Questions per Category")
    print("─" * 65)
    for cat in QUESTION_CATEGORIES:
        qs = manager.get_questions_by_category(cat)
        if qs:
            q = qs[0]
            mand = "Mandatory" if q["mandatory"] else "Optional"
            print(f"\n  [{cat.upper()}]")
            print(f"  Q{q['question_id']}: {q['question_text'][:70]}")
            print(f"           Type: {q['answer_type']}  |  {mand}  |  Importance: {q['scoring_importance']}")

    # ── Step 6: Rendered Questions ────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Sample Rendered Questions with Context")
    print("─" * 65)

    context = {
        "candidate_name": "Arjun Krishnan",
        "time_of_day":    "morning",
        "company":        "Zescer Business LLP",
        "role_name":      "Software Engineer",
        "primary_skill":  "Python",
        "job_location":   "Bangalore",
        "min_salary":     "8",
        "max_salary":     "14",
        "max_days":       "60",
        "office_days":    "3",
    }

    for qid in ["Q001", "Q031", "Q041", "Q052", "Q064"]:
        rendered = manager.render_question(qid, context)
        print(f"\n  {qid}: {rendered}")

    # ── Step 7: Software Engineer Question Set ────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 7: Software Engineer Full Question Set")
    print("─" * 65)

    se_set = manager.get_role_question_set("software_engineer")
    print(f"\n  Mandatory Questions ({se_set['total_mandatory']}):")
    for q in se_set["mandatory_questions"]:
        print(f"    {q['question_id']}: {q['question_text'][:60]}")
    print(f"\n  Optional Questions ({se_set['total_optional']}):")
    for q in se_set["optional_questions"]:
        print(f"    {q['question_id']}: {q['question_text'][:60]}")

    # ── Save ──────────────────────────────────────────────────────────────────
    manager.save_dataset("data/outputs/screening_dataset.json")

    print("\n" + "=" * 65)
    print("HR Screening Dataset creation complete!")
    print("=" * 65 + "\n")

    return manager


if __name__ == "__main__":
    run_screening_dataset()
