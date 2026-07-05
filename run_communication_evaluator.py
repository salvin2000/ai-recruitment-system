"""
Day 35 - Communication Skill Evaluation
Runner script

Demonstrates the full communication scoring model across 6 steps:
dimension explanations, the scoring formula, filler word detection,
structure analysis, sample outputs across 4 response types, and
the bias normalization notes.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.communication_evaluator import (
    CommunicationScorer, FluencyAnalyzer, GrammarAnalyzer,
    VocabularyAnalyzer, ClarityAnalyzer, StructureAnalyzer,
    FILLER_WORDS, SCORE_WEIGHTS, COMMUNICATION_BANDS,
)

SAMPLE_RESPONSES = {
    "weak": (
        "Um yeah I like basically do stuff and things you know. I am good at my job I think.",
        "strengths",
    ),
    "developing": (
        "I work well with others. I try to communicate clearly and I think I am a good team player. "
        "I have done many projects with different people.",
        "teamwork",
    ),
    "good": (
        "I have 4 years of experience in backend development. I usually work in agile teams and "
        "I am comfortable with code reviews, standups, and cross-functional collaboration. "
        "I try to be clear and structured when explaining technical concepts to non-technical stakeholders.",
        "experience",
    ),
    "excellent": (
        "For example, when I led a team of 6 engineers, I implemented a structured communication "
        "framework that included weekly syncs, async updates via documentation, and a clear escalation "
        "path for blockers. This improved our sprint delivery rate by 35% and reduced misalignment "
        "between engineering and product stakeholders substantially.",
        "leadership",
    ),
}


def run_communication_evaluation():
    print("=" * 65)
    print("   ZECPATH AI - COMMUNICATION SKILL EVALUATION v1.0")
    print("=" * 65)

    scorer = CommunicationScorer()

    # ── Step 1: Scoring Dimensions & Weights ────────────────────────────
    print("\nStep 1: Scoring Dimensions & Weights")
    print("-" * 65)
    print(f"  {'Dimension':<18} {'Weight'}")
    print(f"  {'-'*18} {'-'*8}")
    for dim, weight in SCORE_WEIGHTS.items():
        print(f"  {dim:<18} {int(weight*100)}%")

    # ── Step 2: Filler Word Detection ────────────────────────────────────
    print("\nStep 2: Filler Word Detection")
    print("-" * 65)
    print(f"  Tracked filler words ({len(FILLER_WORDS)} total):")
    print(f"  {', '.join(FILLER_WORDS)}")
    fluency = FluencyAnalyzer()
    test_text = "Um yeah I like basically just wanted to say you know that I am basically really good."
    fa = fluency.analyze(test_text)
    print(f"\n  Test response: \"{test_text}\"")
    print(f"  Filler words found : {fa['filler_words_found']}")
    print(f"  Filler count       : {fa['filler_count']}")
    print(f"  Filler density     : {fa['filler_density']}")
    print(f"  Fluency score      : {fa['score']}")

    # ── Step 3: Structure Analysis ───────────────────────────────────────
    print("\nStep 3: Answer Structure Analysis")
    print("-" * 65)
    structured = (
        "To begin, I have always prioritized clear communication. "
        "For example, I once led a project where I implemented daily standups. "
        "Additionally, I created async documentation for remote team members. "
        "In summary, structured communication has been central to my success."
    )
    struct = StructureAnalyzer()
    sr = struct.analyze(structured)
    print(f"  Layers found    : {sr['layers_found']} of 4")
    print(f"  Markers found   : {sr['markers_found']}")
    print(f"  Structure score : {sr['score']}")

    # ── Step 4: Communication Bands ─────────────────────────────────────
    print("\nStep 4: Communication Score Bands")
    print("-" * 65)
    print(f"  {'Band':<28} {'Score Range'}")
    print(f"  {'-'*28} {'-'*12}")
    for key, info in COMMUNICATION_BANDS.items():
        lo, hi = info["range"]
        print(f"  {info['label']:<28} {lo} \u2013 {hi}")

    # ── Step 5: Sample Communication Score Outputs ───────────────────────
    print("\nStep 5: Sample Communication Score Outputs")
    print("-" * 65)
    all_scores = []
    for level, (response, topic) in SAMPLE_RESPONSES.items():
        result = scorer.score(response, question_keywords=[topic])
        all_scores.append(result)
        dims = result["dimensions"]
        print(f"\n  [{level.upper()}]")
        print(f"  Response   : {response[:65]}...")
        print(f"  Score      : {result['communication_score']}  \u2014  {result['band']}")
        print(f"  Fluency    : {dims['fluency']['score']:<5}  Fillers: {dims['fluency']['filler_count']}, Avg sent len: {dims['fluency']['avg_sentence_len']}")
        print(f"  Grammar    : {dims['grammar']['score']:<5}  Errors: {dims['grammar']['error_count']}")
        print(f"  Vocabulary : {dims['vocabulary']['score']:<5}  Advanced: {dims['vocabulary']['advanced_words'][:3]}")
        print(f"  Clarity    : {dims['clarity']['score']:<5}  Example: {dims['clarity']['has_example']}, Specifics: {dims['clarity']['has_specifics']}")
        print(f"  Structure  : {dims['structure']['score']:<5}  Layers: {dims['structure']['layers_found']}")
        print(f"  Bias notes : {result['bias_reduction'][0]}")

    # ── Step 6: Scoring Formula ───────────────────────────────────────────
    print("\nStep 6: Scoring Formula Documentation")
    print("-" * 65)
    print("  raw_score = (fluency × 0.25) + (grammar × 0.25)")
    print("            + (vocabulary × 0.20) + (clarity × 0.20)")
    print("            + (structure × 0.10)")
    print()
    print("  normalization:")
    print("    word_count < 10  → × 0.85  (slight penalty, not catastrophic)")
    print("    word_count > 200 → × 0.95  (length alone does not reward)")
    print("    otherwise        → × 1.00")
    print()
    print("  final_score = min(100, raw_score × length_factor)")

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = "data/outputs/communication_scores.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    output = {
        "scoring_model": {
            "weights":   SCORE_WEIGHTS,
            "bands":     {k: v["label"] for k, v in COMMUNICATION_BANDS.items()},
            "filler_words_tracked": len(FILLER_WORDS),
        },
        "sample_outputs": [
            {
                "level":              level,
                "response":           resp[:80] + "...",
                "communication_score": result["communication_score"],
                "band":               result["band"],
            }
            for (level, (resp, _)), result in zip(SAMPLE_RESPONSES.items(), all_scores)
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved -> {output_path}")

    print("\n" + "=" * 65)
    print("Communication Skill Evaluation complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_communication_evaluation()
