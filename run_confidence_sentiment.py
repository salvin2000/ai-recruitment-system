"""
Day 27 - Confidence & Sentiment Signal Analysis
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.confidence_sentiment import (
    CommunicationStrengthEngine, HesitationDetector,
    ConfidenceAnalyzer, SentimentScorer,
    HESITATION_PATTERNS, PACE_THRESHOLDS, COMMUNICATION_STRENGTH
)


SAMPLE_TURNS = [
    {
        "text":         "I have built and delivered three production Django REST APIs at Infosys, managing a team of five engineers and achieving a 40 percent reduction in response time.",
        "duration_ms":  6800,
        "question_id":  "Q022",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": False,
    },
    {
        "text":         "Um, I think I have like, you know, around three years maybe? I am not really sure, sort of three and a half perhaps.",
        "duration_ms":  7200,
        "question_id":  "Q020",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": False,
    },
    {
        "text":         "Yes, I am excited about this opportunity and I would love to contribute to the team at Zescer.",
        "duration_ms":  3800,
        "question_id":  "Q004",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": False,
    },
    {
        "text":         "My previous role was quite boring and I had a lot of issues with management. The work was tedious and I struggled with unclear requirements.",
        "duration_ms":  5500,
        "question_id":  "Q022",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": False,
    },
    {
        "text":         "I love cricket and IPL this season has been amazing.",
        "duration_ms":  2200,
        "question_id":  "Q020",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": True,
    },
    {
        "text":         "Yes I can join within 30 days. Actually wait, I cannot join within 30 days, I have a 60 day notice period.",
        "duration_ms":  5000,
        "question_id":  "Q064",
        "session_id":   "ZCP-SESS-20260612-001",
        "is_off_topic": False,
    },
]


def run_analysis():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - CONFIDENCE & SENTIMENT SIGNAL ANALYSIS v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    engine    = CommunicationStrengthEngine()
    hes_det   = HesitationDetector()
    conf_anal = ConfidenceAnalyzer()
    sent_sc   = SentimentScorer()

    # ── Step 1: Hesitation Detection ──────────────────────────────────────────
    print("\nStep 1: Hesitation Detection")
    print("─" * 65)
    hes_tests = [
        "I have three years of experience with Python and Django.",
        "Um, I think I have like, you know, around three years maybe?",
        "I am not sure, sort of three and a half perhaps, I guess.",
    ]
    for text in hes_tests:
        result = hes_det.count_hesitations(text)
        print(f"\n  Text     : {text[:65]}")
        print(f"  Count    : {result['count']}  Density: {result['density']}  "
              f"Severity: {result['severity']}  Hesitant: {result['is_hesitant']}")

    # ── Step 2: Confidence Analysis ───────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Confidence Analysis")
    print("─" * 65)
    conf_tests = [
        ("I built and led a team of 5 engineers. I delivered the project on time.", 5000),
        ("I think I maybe worked with Python, sort of, for around two years.", 6000),
        ("I am not sure exactly, probably three years roughly.", 4000),
    ]
    print(f"\n  {'Text':<55} {'Conf':>6} {'High':>5} {'Low':>5} {'Hes':>5}")
    print(f"  {'─'*55} {'─'*6} {'─'*5} {'─'*5} {'─'*5}")
    for text, dur in conf_tests:
        result = conf_anal.analyze(text, dur)
        print(f"  {text[:53]:<55} {result['confidence_score']:>6.4f} "
              f"{result['high_conf_signals']:>5} "
              f"{result['low_conf_signals']:>5} "
              f"{result['hesitation']['count']:>5}")

    # ── Step 3: Sentiment Scoring ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Sentiment Scoring")
    print("─" * 65)
    sent_tests = [
        "I am excited about this opportunity and I would love to contribute.",
        "My previous role was boring and I struggled with poor management.",
        "I have three years of experience working with Python.",
        "Yes I can join within 30 days. Actually wait, I cannot join within 30 days.",
    ]
    print(f"\n  {'Text':<55} {'Score':>7} {'Label':>10} {'Pos':>4} {'Neg':>4}")
    print(f"  {'─'*55} {'─'*7} {'─'*10} {'─'*4} {'─'*4}")
    for text in sent_tests:
        result = sent_sc.score_sentiment(text)
        print(f"  {text[:53]:<55} {result['sentiment_score']:>7.4f} "
              f"{result['sentiment_label']:>10} "
              f"{result['positive_words']:>4} "
              f"{result['negative_words']:>4}")

    # ── Step 4: Uncertainty and Contradiction Detection ───────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Uncertainty & Contradiction Detection")
    print("─" * 65)
    print("\n  Uncertainty:")
    uncert_tests = [
        "I have around three years of experience approximately.",
        "I think maybe around 12 LPA, I am not sure.",
        "I built and delivered the project on time.",
    ]
    for text in uncert_tests:
        r = sent_sc.detect_uncertainty(text)
        print(f"    [{r['uncertainty_level']:<6}] count={r['uncertainty_count']}  '{text[:55]}'")

    print("\n  Contradiction:")
    contra_tests = [
        "Yes I can join within 30 days. Actually wait, I cannot join within 30 days.",
        "I am available immediately. I am not available right now.",
        "I have three years of experience with Python.",
    ]
    for text in contra_tests:
        r = sent_sc.detect_contradiction(text)
        print(f"    [{'FOUND' if r['has_contradiction'] else 'NONE ':5}] '{text[:60]}'")
        if r["has_contradiction"]:
            print(f"            Pairs: {r['contradiction_pairs']}")

    # ── Step 5: Full Communication Strength Analysis ───────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Communication Strength Analysis")
    print("─" * 65)
    results = engine.analyze_batch(SAMPLE_TURNS)
    print(f"\n  {'Q':<6} {'Conf':>6} {'Sent':>7} {'Uncert':>7} {'Strength':>9} {'Level':>10} {'Tags'}")
    print(f"  {'─'*6} {'─'*6} {'─'*7} {'─'*7} {'─'*9} {'─'*10} {'─'*20}")
    for r in results:
        tags_str = ",".join(r["behavioral_tags"])[:25]
        print(f"  {r['question_id']:<6} "
              f"{r['confidence']['score']:>6.4f} "
              f"{r['sentiment']['score']:>7.4f} "
              f"{r['uncertainty']['uncertainty_count']:>7} "
              f"{r['communication_strength']['score']:>9.2f} "
              f"{r['communication_strength']['level']:>10}  {tags_str}")

    # ── Step 6: Behavioral Report ─────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 6: Behavioral Indicators Report")
    print("─" * 65)
    report = engine.generate_report(
        results,
        candidate_id="ZCP-CAND-ARJU",
        session_id="ZCP-SESS-20260612-001"
    )
    s = report["summary"]
    print(f"\n  Avg Confidence Score  : {s['avg_confidence_score']}")
    print(f"  Avg Sentiment Score   : {s['avg_sentiment_score']}")
    print(f"  Avg Strength Score    : {s['avg_strength_score']}")
    print(f"  Overall Strength      : {s['overall_strength_level']} — {s['overall_strength_label']}")
    print(f"  Total Hesitations     : {s['total_hesitations']}")
    print(f"  Total Uncertainties   : {s['total_uncertainties']}")

    print(f"\n  Behavioral Tag Frequency:")
    for tag, count in sorted(report["behavioral_tag_frequency"].items(),
                             key=lambda x: -x[1]):
        print(f"    {tag:<25} : {count}")

    # ── Save ──────────────────────────────────────────────────────────────────
    engine.save_report(report, "data/outputs/behavioral_indicators_report.json")

    print("\n" + "=" * 65)
    print("Confidence & Sentiment Signal Analysis complete!")
    print("=" * 65 + "\n")
    return results, report


if __name__ == "__main__":
    run_analysis()
