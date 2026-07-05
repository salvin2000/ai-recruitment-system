"""
Day 36 - Confidence & Stress Indicators
Runner script

Demonstrates the full confidence scoring system: hesitation detection,
sentiment analysis, stress markers, contradiction detection, and the
full behavioral confidence score across 4 response types.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.confidence_analyzer import (
    HesitationDetector, SentimentAnalyzer, StressIndicatorAnalyzer,
    ContradictionDetector, ConfidenceScorer,
    UNCERTAINTY_PHRASES, CONFIDENCE_PHRASES, STRESS_MARKERS,
    CONFIDENCE_BANDS, CONFIDENCE_SCORE_WEIGHTS,
)

SAMPLE_RESPONSES = {
    "stressed": (
        "I'm sorry, I'm not sure... maybe I think I might be wrong. "
        "I'm not the best at this sort of thing honestly.",
        "Heavily hedged, self-deprecating, apologetic",
    ),
    "uncertain": (
        "I guess I have worked in teams. I think I do well. "
        "I probably communicate clearly. I suppose I am a team player.",
        "Mostly uncertain phrases, no confidence signals",
    ),
    "neutral": (
        "I have 4 years of experience working in agile teams. "
        "I try to communicate clearly and I think I do a decent job.",
        "Balanced — some uncertainty but no strong stress markers",
    ),
    "confident": (
        "I am confident in my abilities. I successfully led a team of 8 and "
        "delivered 3 major projects on time. I have proven results and I am "
        "absolutely committed to this role.",
        "Clear confidence signals, positive sentiment, no hesitation",
    ),
}


def run_confidence_analysis():
    print("=" * 65)
    print("   ZECPATH AI - CONFIDENCE & STRESS INDICATORS v1.0")
    print("=" * 65)

    scorer = ConfidenceScorer()

    # ── Step 1: Behavioral Signal Categories ────────────────────────────
    print("\nStep 1: Behavioral Signal Categories")
    print("-" * 65)
    print("  4 dimensions, each weighted 25%:")
    for dim, weight in CONFIDENCE_SCORE_WEIGHTS.items():
        print(f"    [{dim:<15}] {int(weight*100)}%")

    # ── Step 2: Hesitation Detection ────────────────────────────────────
    print("\nStep 2: Hesitation Pattern Detection")
    print("-" * 65)
    detector = HesitationDetector()
    hesitation_test = (
        "I'm not sure... maybe I think possibly I could have done better. "
        "I... I guess it went okay."
    )
    h_result = detector.analyze(hesitation_test)
    print(f"  Response      : {hesitation_test[:60]}...")
    print(f"  Pause count   : {h_result['pause_count']}")
    print(f"  Repeated words: {h_result['repeated_words']}")
    print(f"  Uncertainty   : {h_result['uncertainty_phrases']}")
    print(f"  Total signals : {h_result['hesitation_signals']}")
    print(f"  Score         : {h_result['score']}")

    # ── Step 3: Sentiment Analysis ───────────────────────────────────────
    print("\nStep 3: Sentiment Analysis")
    print("-" * 65)
    sentiment = SentimentAnalyzer()
    sentiment_tests = [
        "I am excited and passionate about this role. I love working with teams and I thrive under pressure.",
        "I have worked here for a few years doing various tasks.",
        "I have struggled with this and found it difficult. I feel overwhelmed and uncertain.",
    ]
    for text in sentiment_tests:
        s = sentiment.analyze(text)
        print(f"  [{s['label']:<9}] score={s['score']} | pos={s['positive_words']} | neg={s['negative_words']}")

    # ── Step 4: Stress Marker Categories ────────────────────────────────
    print("\nStep 4: Stress Marker Categories")
    print("-" * 65)
    for category, phrases in STRESS_MARKERS.items():
        print(f"  [{category:<22}] e.g.: {phrases[0]}")

    stress = StressIndicatorAnalyzer()
    stress_test = "I'm sorry, I'm not the best at this. Let me think about that. I just want to say I might not be ideal."
    s_result = stress.analyze(stress_test)
    print(f"\n  Test response: {stress_test[:60]}...")
    print(f"  Stress categories found : {s_result['stress_categories']}")
    print(f"  Total stress hits       : {s_result['stress_hit_count']}")
    print(f"  Stress score            : {s_result['score']}")

    # ── Step 5: Contradiction Detection ─────────────────────────────────
    print("\nStep 5: Contradiction Detection")
    print("-" * 65)
    contra = ContradictionDetector()
    internal_test = "I never lead teams but I led a project last year with 5 people."
    c1 = contra.analyze(internal_test)
    print(f"  Internal contradiction test:")
    print(f"    Response      : {internal_test}")
    print(f"    Contradictions: {c1['contradiction_count']}  {c1['contradictions']}")
    print(f"    Score         : {c1['score']}")

    prior = ["I work alone and I am not really a team player."]
    cross_test = "I am a strong team player and I enjoy collaboration."
    c2 = contra.analyze(cross_test, prior)
    print(f"\n  Cross-session contradiction test:")
    print(f"    Prior         : \"{prior[0]}\"")
    print(f"    Current       : \"{cross_test}\"")
    print(f"    Contradictions: {c2['contradiction_count']}")
    print(f"    Score         : {c2['score']}")

    # ── Step 6: Full Behavioral Confidence Scores ────────────────────────
    print("\nStep 6: Full Behavioral Confidence Score Outputs")
    print("-" * 65)
    all_scores = []
    for level, (response, description) in SAMPLE_RESPONSES.items():
        result = scorer.score(response)
        all_scores.append(result)
        dims = result["dimensions"]
        print(f"\n  [{level.upper()}] — {description}")
        print(f"  Response   : {response[:65]}...")
        print(f"  Score      : {result['confidence_score']}  \u2014  {result['band']}")
        print(f"  Hesitation : {dims['hesitation']['score']:<5}  Signals: {dims['hesitation']['hesitation_signals']}, Uncertainty: {len(dims['hesitation']['uncertainty_phrases'])}")
        print(f"  Sentiment  : {dims['sentiment']['score']:<5}  Label: {dims['sentiment']['label']}")
        print(f"  Stress     : {dims['stress']['score']:<5}  Hits: {dims['stress']['stress_hit_count']}, Categories: {len(dims['stress']['stress_categories'])}")
        print(f"  Contradiction: {dims['contradiction']['score']:<3}  Found: {dims['contradiction']['contradiction_count']}")
        print(f"  Notes      : {result['signal_notes'][0]}")

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = "data/outputs/confidence_scores.json"
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    output = {
        "scoring_model": {
            "weights": CONFIDENCE_SCORE_WEIGHTS,
            "bands": {k: v["label"] for k, v in CONFIDENCE_BANDS.items()},
        },
        "sample_outputs": [
            {
                "level": level,
                "confidence_score": result["confidence_score"],
                "band": result["band"],
            }
            for (level, _), result in zip(SAMPLE_RESPONSES.items(), all_scores)
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved -> {output_path}")

    print("\n" + "=" * 65)
    print("Confidence & Stress Indicators complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_confidence_analysis()
