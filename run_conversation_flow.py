"""
Day 29 - AI Conversation Flow Design
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.conversation_flow import (
    ConversationFlowController, ConversationStateMachine, TurnDecisionEngine,
    CONVERSATION_STATES, STATE_TRANSITIONS, TURN_OUTCOMES,
    SILENCE_HANDLING, RETRY_CONFIG, POLITE_MESSAGES
)


SAMPLE_ANSWERS = [
    {
        "question_id": "Q001", "answer_type": "yes_no",
        "question_text": "Good morning, Arjun. I am an AI from Zecpath. Are you ready to proceed?",
        "answer": {
            "clean_text": "Yes I am ready.", "intent": "affirmative",
            "extracted": {"boolean_value": True},
            "is_valid": True, "is_vague": False, "is_off_topic": False,
            "needs_followup": False, "word_count": 4, "confidence": 0.93,
        },
    },
    {
        "question_id": "Q020", "answer_type": "numeric",
        "question_text": "How many years of total professional experience do you have?",
        "answer": {
            "clean_text": "I have around 3.5 years of Python experience.",
            "intent": "experience_info",
            "extracted": {"experience_years": 3.5},
            "is_valid": True, "is_vague": False, "is_off_topic": False,
            "needs_followup": False, "word_count": 8, "confidence": 0.91,
        },
    },
    {
        "question_id": "Q021", "answer_type": "text",
        "question_text": "What is your current job title and company?",
        "answer": {
            "clean_text": "It depends.", "intent": "vague",
            "extracted": {},
            "is_valid": False, "is_vague": True, "is_off_topic": False,
            "needs_followup": True, "word_count": 2, "confidence": 0.85,
        },
    },
    {
        "question_id": "Q021", "answer_type": "text",
        "question_text": "Let me try that again — what is your current role and employer?",
        "answer": {
            "clean_text": "", "intent": "unknown",
            "extracted": {},
            "is_valid": False, "is_vague": False, "is_off_topic": False,
            "needs_followup": False, "word_count": 0, "confidence": 0.0,
        },
    },
    {
        "question_id": "Q030", "answer_type": "text",
        "question_text": "What are your top three technical skills?",
        "answer": {
            "clean_text": "I love cricket and the IPL this season is amazing.",
            "intent": "off_topic",
            "extracted": {},
            "is_valid": False, "is_vague": False, "is_off_topic": True,
            "needs_followup": True, "word_count": 10, "confidence": 0.95,
        },
    },
    {
        "question_id": "Q030", "answer_type": "text",
        "question_text": "No problem — could you name the technologies you use most at work?",
        "answer": {
            "clean_text": "I mainly work with Python, Django, and AWS.",
            "intent": "skill_info",
            "extracted": {"skills_mentioned": ["python", "django", "aws"]},
            "is_valid": True, "is_vague": False, "is_off_topic": False,
            "needs_followup": False, "word_count": 8, "confidence": 0.94,
        },
    },
    {
        "question_id": "Q031", "answer_type": "numeric",
        "question_text": "How many years of experience do you have with Python?",
        "answer": {
            "clean_text": "Around three.", "intent": "experience_info",
            "extracted": {},
            "is_valid": True, "is_vague": False, "is_off_topic": False,
            "needs_followup": True, "word_count": 2, "confidence": 0.89,
        },
    },
]


def run_flow():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - CONVERSATION FLOW DESIGN v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    # ── Step 1: State Machine Demo ────────────────────────────────────────────
    print("\nStep 1: Conversation State Machine")
    print("─" * 65)
    machine = ConversationStateMachine("ZCP-SESS-20260612-001", "Arjun Krishnan")
    print(f"\n  Initial State: {machine.state}")

    transitions = ["greeting", "asking", "listening", "processing", "transitioning"]
    for new_state in transitions:
        result = machine.transition(new_state)
        if result["success"]:
            print(f"  {result['previous']:<15} -> {result['state']}")
        else:
            print(f"  [BLOCKED] {result['reason']}")

    invalid = machine.transition("greeting")
    print(f"  Invalid transition attempt: {invalid['reason']}")

    # ── Step 2: Turn Decision Engine ──────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Turn Decision Engine")
    print("─" * 65)
    engine = TurnDecisionEngine()
    test_turns = [
        ({"clean_text": "I have 3.5 years of Python experience.", "is_valid": True,
          "is_vague": False, "is_off_topic": False, "needs_followup": False,
          "word_count": 8, "intent": "experience_info", "extracted": {"experience_years": 3.5}},
         "Q020", "numeric", 0, "Valid complete answer"),
        ({"clean_text": "Around three.", "is_valid": True,
          "is_vague": False, "is_off_topic": False, "needs_followup": True,
          "word_count": 2, "intent": "experience_info", "extracted": {}},
         "Q031", "numeric", 0, "Partial numeric answer"),
        ({"clean_text": "It depends.", "is_valid": False,
          "is_vague": True, "is_off_topic": False, "needs_followup": True,
          "word_count": 2, "intent": "vague", "extracted": {}},
         "Q021", "text", 0, "Vague answer"),
        ({"clean_text": "I love cricket.", "is_valid": False,
          "is_vague": False, "is_off_topic": True, "needs_followup": True,
          "word_count": 3, "intent": "off_topic", "extracted": {}},
         "Q030", "text", 0, "Off-topic answer"),
        ({"clean_text": "", "is_valid": False,
          "is_vague": False, "is_off_topic": False, "needs_followup": False,
          "word_count": 0, "intent": "unknown", "extracted": {}},
         "Q021", "text", 0, "Silence"),
        ({"clean_text": "It depends.", "is_valid": False,
          "is_vague": True, "is_off_topic": False, "needs_followup": True,
          "word_count": 2, "intent": "vague", "extracted": {}},
         "Q021", "text", 2, "Vague at max retries -> skip"),
    ]
    print(f"\n  {'Scenario':<32} {'Action':<15} {'Outcome':<20} {'Next State'}")
    print(f"  {'─'*32} {'─'*15} {'─'*20} {'─'*15}")
    for ans, qid, atype, retry, label in test_turns:
        decision = engine.classify_turn(ans, qid, atype, retry)
        print(f"  {label:<32} {decision['action']:<15} "
              f"{decision['outcome']:<20} {decision['next_state']}")

    # ── Step 3: Silence & Retry Handling ─────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Silence & Retry Handling")
    print("─" * 65)
    print("\n  Silence progression:")
    for retry in range(4):
        ans = {"clean_text": "", "is_valid": False, "is_vague": False,
               "is_off_topic": False, "needs_followup": False,
               "word_count": 0, "intent": "unknown", "extracted": {}}
        d = engine.classify_turn(ans, "Q020", "numeric", retry)
        print(f"    Retry {retry}: [{d['action']:<6}] {d['message']}")

    # ── Step 4: Full Call Simulation ──────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Full Call Simulation")
    print("─" * 65)
    controller = ConversationFlowController("ZCP-SESS-20260612-001", "Arjun Krishnan")

    start = controller.start_call()
    print(f"\n  [{start['state'].upper():<14}] {start['message'][:60]}")

    for turn in SAMPLE_ANSWERS:
        ask = controller.ask_question(turn["question_id"], turn["question_text"])
        print(f"\n  [{ask['state'].upper():<14}] ASK {turn['question_id']}: {turn['question_text'][:45]}")

        result = controller.process_answer(
            turn["answer"], turn["question_id"], turn["answer_type"]
        )
        print(f"  [{result['state'].upper():<14}] {result['action'].upper():<15} "
              f"{result['outcome']:<22} '{result['message'][:35]}'")

        if result.get("should_abort"):
            print("  [ABORT] Session aborted due to too many failures.")
            break

    end = controller.end_call()
    print(f"\n  [{end['state'].upper():<14}] {end['message'][:60]}")

    # ── Step 5: Session Status ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Session Summary")
    print("─" * 65)
    status = end["status"]
    print(f"\n  State           : {status['state']}")
    print(f"  Turn Count      : {status['turn_count']}")
    print(f"  Skip Count      : {status['skip_count']}")
    print(f"  Total Failures  : {status['total_failures']}")
    print(f"  Asked Questions : {status['asked_questions']}")
    print(f"  Skipped         : {status['skipped_questions']}")

    # ── Save ──────────────────────────────────────────────────────────────────
    controller.save_flow("data/outputs/conversation_flow_log.json")

    print("\n" + "=" * 65)
    print("AI Conversation Flow Design complete!")
    print("=" * 65 + "\n")
    return controller


if __name__ == "__main__":
    run_flow()
