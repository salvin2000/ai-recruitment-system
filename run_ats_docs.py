"""
Day 19 - ATS Documentation & Knowledge Transfer
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_docs import ATSDocumentationGenerator


def run_documentation():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - DOCUMENTATION & KNOWLEDGE TRANSFER v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    gen = ATSDocumentationGenerator()

    # ── Step 1: Architecture Summary ─────────────────────────────────────────
    print("\nStep 1: Pipeline Architecture Summary")
    print("─" * 65)
    arch = gen.generate_architecture_summary()
    print(f"  Pipeline   : {arch['pipeline_name']} v{arch['version']}")
    print(f"  Total Days : {arch['total_days']}")
    print(f"  Layers     : {arch['total_layers']}")
    print(f"  Modules    : {arch['total_modules']}")
    print()
    for layer_name, layer in arch["layers"].items():
        days = ", ".join(f"Day {d}" for d in layer["days"])
        print(f"  [{layer_name.upper().replace('_',' ')}] ({days})")
        print(f"    {layer['description']}")

    # ── Step 2: ASCII Architecture Diagram ────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Architecture Diagram")
    print("─" * 65)
    print(gen.generate_ascii_architecture())

    # ── Step 3: Module Registry ───────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Module Registry")
    print("─" * 65)
    print(f"\n  {'Module':<28} {'Day':>4} {'Layer':<20} Class")
    print(f"  {'─'*28} {'─'*4} {'─'*20} {'─'*20}")
    for name, data in gen.get_module_docs().items():
        print(f"  {name:<28} {data['day']:>4} {data['layer']:<20} {data['class'][:30]}")

    # ── Step 4: Scoring Logic ─────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Scoring Logic Documentation")
    print("─" * 65)
    scorer = gen.generate_scoring_explainer()
    print(f"\n  Formula: {scorer['formula']}")
    print(f"\n  Component Weights (software_engineer profile):")
    for comp, data in scorer["components"].items():
        print(f"    {comp:<28} weight={data['weight_default']}  source={data['source']}")
    ex = scorer["example"]
    print(f"\n  Worked Example: {ex['candidate']}")
    calc = ex["calculation"]
    print(f"    Skill Match       : {ex['component_scores']['skill_match']} x 35% = {calc['skill_contribution']}")
    print(f"    Experience        : {ex['component_scores']['experience_relevance']} x 30% = {calc['experience_contribution']}")
    print(f"    Education         : {ex['component_scores']['education_alignment']} x 15% = {calc['education_contribution']}")
    print(f"    Semantic          : {ex['component_scores']['semantic_similarity']} x 20% = {calc['semantic_contribution']}")
    print(f"    Final Score       : {ex['final_score']}  Grade: {ex['grade']}")

    # ── Step 5: Troubleshooting Guide ─────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Troubleshooting Guide")
    print("─" * 65)
    for i, entry in enumerate(gen.get_troubleshooting_guide(), 1):
        code = entry["error_code"] or "N/A"
        print(f"\n  [{i}] {entry['issue']}  (Error: {code})")
        print(f"    Causes   : {', '.join(entry['causes'][:2])}")
        print(f"    Solution : {entry['solutions'][0]}")

    # ── Step 6: Developer Guide ───────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Developer Quick Reference")
    print("─" * 65)
    for task_key, task in gen.get_developer_guide().items():
        print(f"\n  HOW TO: {task['title']}")
        for step in task["steps"]:
            print(f"    -> {step}")

    # ── Save Full Documentation ───────────────────────────────────────────────
    gen.save_documentation("data/outputs/ats_technical_documentation.json")

    print("\n" + "=" * 65)
    print("Documentation and knowledge transfer complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_documentation()
