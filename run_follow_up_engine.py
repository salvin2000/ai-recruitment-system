"""
Day 34 - Dynamic Follow-Up Logic
Runner script

Demonstrates the full follow-up engine: response analysis, all three
follow-up types (clarification, deepening, example-based), difficulty
adaptation, repetition prevention, and conversation state tracking.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.follow_up_engine import (
    ResponseAnalyzer, FollowUpEngine, ConversationStateTracker,
    FOLLOW_UP_TYPES, DIFFICULTY_LEVELS, INCOMPLETE_TRIGGERS,
    MAX_FOLLOW_UPS_PER_QUESTION,
)


def run_follow_up_engine():
    print("=" * 65)
    print("   ZECPATH AI - DYNAMIC FOLLOW-UP LOGIC v1.0")
    print("=" * 65)

    analyzer = ResponseAnalyzer()
    engine   = FollowUpEngine()

    # ── Step 1: Follow-Up Types ──────────────────────────────────────────
    print("\nStep 1: Follow-Up Types")
    print("-" * 65)
    for key, info in FOLLOW_UP_TYPES.items():
        print(f"  [{key:<14}] {info['label']}")
        print(f"                  Trigger: {info['trigger']}")

    # ── Step 2: Response Analysis ────────────────────────────────────────
    print("\nStep 2: Response Analysis — 4 Sample Answers")
    print("-" * 65)
    samples = [
        ("strengths_weaknesses", "I think I am kind of good with people maybe.",
         "Vague, short"),
        ("career_journey", "I worked at various companies doing different things for a while.",
         "Generic, no example"),
        ("career_goals", "I want to grow and become a better professional in the next few years.",
         "Moderate, no number"),
        ("teamwork_culture_fit",
         "For example, I once led a cross-functional team of 8 to deliver a product feature in 3 sprints, resolving a conflict between the design and engineering teams by running a joint workshop.",
         "Strong, specific example"),
    ]
    for category, response, label in samples:
        analysis = analyzer.analyze(response, category)
        print(f"\n  [{label}]")
        print(f"  Response   : {response[:65]}...")
        print(f"  Word Count : {analysis['word_count']}")
        print(f"  Confidence : {analysis['confidence_score']}  ({analysis['difficulty_level']})")
        print(f"  Triggers   : {analysis['incomplete_triggers'] or 'None'}")
        print(f"  Follow-up? : {analysis['needs_follow_up']}")

    # ── Step 3: Follow-Up Decision Engine ────────────────────────────────
    print("\nStep 3: Follow-Up Decision Engine")
    print("-" * 65)
    decision_tests = [
        ("I sort of struggle with time management maybe.",          "strengths_weaknesses",  "Surface response → clarification"),
        ("I have worked on several projects across different teams.", "career_journey",         "Moderate response → deepening"),
        ("I am very detail-oriented and I always meet deadlines.",   "teamwork_culture_fit",  "Confident claim → example-based"),
    ]
    for response, category, expected in decision_tests:
        decision = engine.decide(response, category, "Q-TEST", [], [])
        print(f"\n  Response   : {response[:60]}...")
        print(f"  Expected   : {expected}")
        print(f"  Decision   : [{decision['action']}] {decision['follow_up_type'] or 'N/A'}")
        print(f"  Follow-up  : {decision['follow_up_text'] or 'None'}")

    # ── Step 4: Difficulty Adaptation ────────────────────────────────────
    print("\nStep 4: Difficulty Adaptation")
    print("-" * 65)
    print(f"  {'Level':<12} {'Score Range':<18} {'Next Action'}")
    print(f"  {'-'*12} {'-'*18} {'-'*20}")
    for level, info in DIFFICULTY_LEVELS.items():
        lo, hi = info["score_range"]
        print(f"  {info['label']:<12} {str(lo)+'-'+str(hi):<18} {info['next_action']}")

    # ── Step 5: Repetition Prevention ────────────────────────────────────
    print("\nStep 5: Repetition Prevention")
    print("-" * 65)
    vague_response = "I think I am kind of good with people maybe."
    print(f"  Max follow-ups per question: {MAX_FOLLOW_UPS_PER_QUESTION}")
    history = []
    for attempt in range(1, 4):
        decision = engine.decide(vague_response, "strengths_weaknesses", "Q-TEST", history, [])
        print(f"  Attempt {attempt}: [{decision['action']:<14}] {decision.get('follow_up_type') or decision.get('reason', '')}")
        if decision["action"] == "ask_follow_up":
            history.append({"follow_up_type": decision["follow_up_type"]})

    # ── Step 6: Full Conversation State Tracking ──────────────────────────
    print("\nStep 6: Full Conversation State Tracking")
    print("-" * 65)
    tracker = ConversationStateTracker("SESS-HR-034", "Arjun Krishnan", "experienced_technical")

    interview_turns = [
        ("Q-SELF-001", "self_introduction", "Give me a brief introduction.",
         "I am a backend developer with 4 years building APIs."),
        ("Q-CARE-001", "career_journey", "Walk me through your career.",
         "I think I have done various things sort of, maybe backend, kind of frontend too."),
        ("Q-STRE-001", "strengths_weaknesses", "What is your greatest strength?",
         "For example, I once led a team of 6 to rebuild our payment API, cutting response time by 35% in 2 sprints."),
        ("Q-TEAM-001", "teamwork_culture_fit", "Tell me about working in a team.",
         "I guess I work well with others generally speaking."),
        ("Q-GOAL-001", "career_goals", "Where do you see yourself in 5 years?",
         "I want to become a senior engineer and lead a team within 3 years, then move toward an architect role."),
    ]

    for qid, cat, qtext, resp in interview_turns:
        turn = tracker.record_turn(qid, cat, qtext, resp)
        action_str = f"[{turn['action']:<14}]"
        fu = turn['follow_up_type'] or '-'
        print(f"  {action_str} {cat:<28} FU: {fu}")
        if turn["follow_up_text"]:
            print(f"                                      Q: {turn['follow_up_text'][:55]}...")

    print("\n  Confidence Profile:")
    profile = tracker.get_confidence_profile()
    print(f"    Average Confidence  : {profile['average_confidence']}")
    print(f"    Min / Max           : {profile['min_confidence']} / {profile['max_confidence']}")
    print(f"    Follow-ups Asked    : {profile['follow_ups_asked']}")
    print(f"    Level Distribution  : {profile['level_distribution']}")

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = "data/outputs/follow_up_session_state.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    state = tracker.get_full_state()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nSaved -> {output_path}")

    print("\n" + "=" * 65)
    print("Dynamic Follow-Up Logic complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_follow_up_engine()
