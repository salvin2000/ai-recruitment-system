"""
Day 33 - HR Interview Engine Design
Runner script

Demonstrates the complete HR Interview AI architecture: the 6 interview
categories, the role-based question generator across all 4 role profiles,
the interview state structure, and the 4 conversation phases with a full
flow design document for each profile type.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.hr_interview_engine import (
    RoleBasedQuestionGenerator, InterviewStateManager, InterviewFlowDesigner,
    HR_INTERVIEW_CATEGORIES, ROLE_PROFILES, CONVERSATION_PHASES,
    QUESTION_STATE_FIELDS, QUESTION_BANK,
)


def run_hr_interview_engine_design():
    print("=" * 65)
    print("   ZECPATH AI - HR INTERVIEW ENGINE DESIGN v1.0")
    print("=" * 65)

    # ── Step 1: Interview Categories ─────────────────────────────────────
    print("\nStep 1: HR Interview Categories (6 total)")
    print("-" * 65)
    for key, cat in HR_INTERVIEW_CATEGORIES.items():
        print(f"  [{cat['order']}] {cat['label']:<30} Phase: {cat['phase']}")
        print(f"      {cat['description']}")

    # ── Step 2: Role-Based Question Generator ────────────────────────────
    print("\nStep 2: Role-Based Question Generator")
    print("-" * 65)
    generator = RoleBasedQuestionGenerator()
    for profile_key, profile_info in ROLE_PROFILES.items():
        print(f"\n  Profile: {profile_info['label']}")
        print(f"  Focus  : {profile_info['focus']}")
        q = generator.get_question("career_journey", profile_key)
        print(f"  Q      : {q['question_text']}")
        print(f"  FU     : {q['follow_up']}")

    # ── Step 3: Interview State Structure ────────────────────────────────
    print("\nStep 3: Interview State Structure")
    print("-" * 65)
    print("  Each question in the interview tracks these fields:")
    for field in QUESTION_STATE_FIELDS:
        print(f"    - {field}")

    # Demo state creation
    print("\n  Demo — creating a state for an experienced technical candidate:")
    manager = InterviewStateManager("SESS-HR-001", "Arjun Krishnan", "experienced_technical")
    state = manager.create_question_state(
        "self_introduction",
        "Give me a brief introduction — who you are, your current role, and what you have built."
    )
    state = manager.record_response(
        state["question_id"],
        "I am a backend developer with 4 years of experience building APIs and microservices."
    )
    print(f"    Question ID    : {state['question_id']}")
    print(f"    Category       : {state['category']}")
    print(f"    Word Count     : {state['response_word_count']}")
    print(f"    Follow-up Elig.: {state['follow_up_eligible']}")

    # ── Step 4: Conversation Phases ──────────────────────────────────────
    print("\nStep 4: Conversation Phases")
    print("-" * 65)
    designer = InterviewFlowDesigner()
    for phase in designer.get_phase_flow():
        print(f"\n  Phase {phase['order']}: {phase['label']}")
        print(f"  Categories : {', '.join(phase['categories'])}")
        print(f"  Description: {phase['description']}")

    # ── Step 5: Full Question Set — All 4 Profiles ───────────────────────
    print("\nStep 5: Full Question Set Per Role Profile")
    print("-" * 65)
    for profile_key, profile_info in ROLE_PROFILES.items():
        questions = generator.get_full_interview_set(profile_key)
        print(f"\n  {profile_info['label']} ({len(questions)} questions)")
        for q in questions:
            label = HR_INTERVIEW_CATEGORIES[q["category"]]["label"]
            print(f"    [{label:<28}] {q['question_text'][:55]}...")

    # ── Step 6: Architecture Summary ─────────────────────────────────────
    print("\nStep 6: Architecture Summary")
    print("-" * 65)
    arch = designer.get_architecture_summary()
    print(f"  Total Categories         : {arch['total_categories']}")
    print(f"  Total Phases             : {arch['total_phases']}")
    print(f"  Total Role Profiles      : {arch['total_role_profiles']}")
    print(f"  Questions per Profile    : {arch['questions_per_profile']}")
    print(f"  Total Questions in Bank  : {arch['total_questions_in_bank']}")
    print(f"  Follow-up Questions      : {arch['follow_up_questions']}")

    # ── Save Flow Design Document ─────────────────────────────────────────
    output_path = "data/outputs/hr_interview_flow_design.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    flow_doc = designer.generate_flow_document("experienced_technical")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flow_doc, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved -> {output_path}")

    print("\n" + "=" * 65)
    print("HR Interview Engine Design complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_hr_interview_engine_design()
