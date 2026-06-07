"""
Tests for Day 14 – Candidate Ranking & Shortlisting
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.candidate_ranker import (
    CandidateRanker, DEFAULT_THRESHOLDS, ROLE_THRESHOLDS, ZONE_LABELS
)


# ── Sample ATS Results ────────────────────────────────────────────────────────

def make_ats_result(candidate_id, score, grade="B"):
    return {
        "metadata": {
            "candidate_id": candidate_id,
            "job_id":       "ZCP-JOB-TEST",
            "role_type":    "software_engineer",
        },
        "final_score": {
            "score":          score,
            "grade":          grade,
            "recommendation": "Test recommendation",
            "strengths":      ["Experience Relevance: 85.0%"] if score >= 70 else [],
            "gaps":           ["Skill Match: 20.0%"] if score < 50 else [],
            "is_complete":    True,
        },
        "score_breakdown": {
            "skill_match":          score * 0.35,
            "experience_relevance": score * 0.30,
            "education_alignment":  score * 0.15,
            "semantic_similarity":  score * 0.20,
            "total":                score,
        },
    }


# ── Sample Results Set ────────────────────────────────────────────────────────

HIGH_SCORE_RESULT    = make_ats_result("ZCP-CAND-HIGH",  82.0, "A")
MED_SCORE_RESULT     = make_ats_result("ZCP-CAND-MED",   60.0, "B")
REVIEW_SCORE_RESULT  = make_ats_result("ZCP-CAND-REV",   55.0, "C+")
LOW_SCORE_RESULT     = make_ats_result("ZCP-CAND-LOW",   30.0, "D")
BORDER_HIGH_RESULT   = make_ats_result("ZCP-CAND-BHI",   72.0, "B+")
BORDER_LOW_RESULT    = make_ats_result("ZCP-CAND-BLO",   48.0, "C")

ALL_RESULTS = [
    HIGH_SCORE_RESULT, MED_SCORE_RESULT, REVIEW_SCORE_RESULT,
    LOW_SCORE_RESULT, BORDER_HIGH_RESULT, BORDER_LOW_RESULT,
]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ranker():
    return CandidateRanker(role_type="software_engineer")

@pytest.fixture
def ranked(ranker):
    return ranker.rank_candidates(ALL_RESULTS)

@pytest.fixture
def report(ranker, ranked):
    return ranker.generate_shortlist_report(
        ranked, "ZCP-JOB-TEST", "software_engineer"
    )


# ── Ranker Instance Tests ─────────────────────────────────────────────────────

def test_ranker_creates_instance(ranker):
    assert ranker is not None
    assert ranker.thresholds is not None

def test_ranker_uses_role_thresholds():
    ranker = CandidateRanker(role_type="software_engineer")
    assert ranker.thresholds == ROLE_THRESHOLDS["software_engineer"]

def test_ranker_falls_back_to_default():
    ranker = CandidateRanker(role_type="unknown_role_xyz")
    assert ranker.thresholds == DEFAULT_THRESHOLDS

def test_ranker_accepts_custom_thresholds():
    custom = {"auto_shortlist": 80, "manual_review": 60, "auto_reject": 59}
    ranker = CandidateRanker(thresholds=custom)
    assert ranker.thresholds == custom


# ── Zone Classification Tests ─────────────────────────────────────────────────

def test_classify_shortlisted(ranker):
    assert ranker.classify_zone(75.0) == "shortlisted"

def test_classify_review(ranker):
    assert ranker.classify_zone(55.0) == "review"

def test_classify_rejected(ranker):
    assert ranker.classify_zone(30.0) == "rejected"

def test_classify_at_shortlist_boundary(ranker):
    threshold = ranker.thresholds["auto_shortlist"]
    assert ranker.classify_zone(threshold) == "shortlisted"

def test_classify_below_shortlist_boundary(ranker):
    threshold = ranker.thresholds["auto_shortlist"]
    assert ranker.classify_zone(threshold - 1) == "review"

def test_classify_at_review_boundary(ranker):
    threshold = ranker.thresholds["manual_review"]
    assert ranker.classify_zone(threshold) == "review"

def test_classify_at_reject_boundary(ranker):
    threshold = ranker.thresholds["auto_reject"]
    assert ranker.classify_zone(threshold) == "rejected"

def test_zone_labels_defined():
    assert "shortlisted" in ZONE_LABELS
    assert "review"      in ZONE_LABELS
    assert "rejected"    in ZONE_LABELS


# ── Ranking Tests ─────────────────────────────────────────────────────────────

def test_rank_candidates_returns_list(ranked):
    assert isinstance(ranked, list)

def test_rank_candidates_correct_count(ranked):
    assert len(ranked) == len(ALL_RESULTS)

def test_rank_candidates_sorted_descending(ranked):
    scores = [c["score"] for c in ranked]
    assert scores == sorted(scores, reverse=True)

def test_rank_candidates_starts_at_one(ranked):
    assert ranked[0]["rank"] == 1

def test_rank_candidates_sequential(ranked):
    ranks = [c["rank"] for c in ranked]
    assert ranks == list(range(1, len(ALL_RESULTS) + 1))

def test_ranked_candidate_has_required_fields(ranked):
    for c in ranked:
        assert "rank"           in c
        assert "candidate_id"   in c
        assert "score"          in c
        assert "grade"          in c
        assert "zone"           in c
        assert "zone_label"     in c
        assert "recommendation" in c
        assert "strengths"      in c
        assert "gaps"           in c
        assert "is_complete"    in c
        assert "score_breakdown"in c

def test_top_candidate_is_highest_score(ranked):
    assert ranked[0]["candidate_id"] == "ZCP-CAND-HIGH"

def test_last_candidate_is_lowest_score(ranked):
    assert ranked[-1]["candidate_id"] == "ZCP-CAND-LOW"


# ── Filtering Tests ───────────────────────────────────────────────────────────

def test_get_shortlisted_returns_correct_zone(ranker, ranked):
    shortlisted = ranker.get_shortlisted(ranked)
    for c in shortlisted:
        assert c["zone"] == "shortlisted"

def test_get_review_returns_correct_zone(ranker, ranked):
    review = ranker.get_review_zone(ranked)
    for c in review:
        assert c["zone"] == "review"

def test_get_rejected_returns_correct_zone(ranker, ranked):
    rejected = ranker.get_rejected(ranked)
    for c in rejected:
        assert c["zone"] == "rejected"

def test_zones_cover_all_candidates(ranker, ranked):
    shortlisted = ranker.get_shortlisted(ranked)
    review      = ranker.get_review_zone(ranked)
    rejected    = ranker.get_rejected(ranked)
    assert len(shortlisted) + len(review) + len(rejected) == len(ranked)

def test_get_top_n(ranker, ranked):
    top3 = ranker.get_top_n(ranked, 3)
    assert len(top3) == 3
    assert top3[0]["rank"] == 1

def test_get_top_n_default_five(ranker, ranked):
    top = ranker.get_top_n(ranked)
    assert len(top) == min(5, len(ranked))

def test_filter_by_min_score(ranker, ranked):
    filtered = ranker.filter_by_min_score(ranked, 60.0)
    for c in filtered:
        assert c["score"] >= 60.0

def test_filter_complete_data(ranker, ranked):
    complete = ranker.filter_complete_data(ranked)
    for c in complete:
        assert c["is_complete"] == True


# ── Report Tests ──────────────────────────────────────────────────────────────

def test_report_returns_dict(report):
    assert isinstance(report, dict)

def test_report_has_required_sections(report):
    assert "report_metadata"       in report
    assert "summary"               in report
    assert "shortlisted_candidates"in report
    assert "review_candidates"     in report
    assert "rejected_candidates"   in report
    assert "full_ranked_list"      in report

def test_report_summary_fields(report):
    summary = report["summary"]
    assert "total_candidates"   in summary
    assert "shortlisted_count"  in summary
    assert "review_count"       in summary
    assert "rejected_count"     in summary
    assert "shortlist_rate"     in summary
    assert "rejection_rate"     in summary
    assert "avg_score"          in summary
    assert "top_score"          in summary

def test_report_counts_sum_to_total(report):
    summary = report["summary"]
    total   = summary["total_candidates"]
    counted = (summary["shortlisted_count"] +
               summary["review_count"] +
               summary["rejected_count"])
    assert total == counted

def test_report_metadata_fields(report):
    meta = report["report_metadata"]
    assert "generated_at"  in meta
    assert "job_id"        in meta
    assert "role_type"     in meta
    assert "thresholds"    in meta

def test_report_full_ranked_list_ordered(report):
    scores = [c["score"] for c in report["full_ranked_list"]]
    assert scores == sorted(scores, reverse=True)

def test_candidate_summary_has_breakdown(report):
    for c in report["full_ranked_list"]:
        assert "breakdown" in c
        bd = c["breakdown"]
        assert "skill_match"          in bd
        assert "experience_relevance" in bd
        assert "education_alignment"  in bd
        assert "semantic_similarity"  in bd


# ── Recruiter Summary Tests ───────────────────────────────────────────────────

def test_recruiter_summary_is_string(ranker, report):
    summary = ranker.generate_recruiter_summary(report)
    assert isinstance(summary, str)

def test_recruiter_summary_has_key_sections(ranker, report):
    summary = ranker.generate_recruiter_summary(report)
    assert "CANDIDATE SHORTLISTING REPORT" in summary
    assert "SUMMARY"                        in summary
    assert "THRESHOLDS"                     in summary
    assert "FULL RANKED LIST"               in summary


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_report(ranker, report, tmp_path):
    output_file = str(tmp_path / "test_report.json")
    ranker.save_report(report, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "summary"               in data
    assert "shortlisted_candidates"in data

def test_save_csv(ranker, report, tmp_path):
    output_file = str(tmp_path / "test_ranked.csv")
    ranker.save_shortlist_csv(report, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        lines = f.readlines()
    assert len(lines) > 1  # Header + at least one data row
    assert "Rank" in lines[0]
    assert "Score" in lines[0]


# ── Role Threshold Tests ──────────────────────────────────────────────────────

def test_all_role_thresholds_defined():
    for role in ["software_engineer","data_analyst","management_trainee",
                 "data_scientist","devops_engineer","hr_manager","default"]:
        assert role in ROLE_THRESHOLDS

def test_thresholds_logical_ordering():
    for role, t in ROLE_THRESHOLDS.items():
        assert t["auto_shortlist"] > t["manual_review"]
        assert t["manual_review"]  > t["auto_reject"]


# ── Edge Case Tests ───────────────────────────────────────────────────────────

def test_empty_candidates_list(ranker):
    ranked = ranker.rank_candidates([])
    assert ranked == []

def test_single_candidate(ranker):
    single = [HIGH_SCORE_RESULT]
    ranked = ranker.rank_candidates(single)
    assert len(ranked) == 1
    assert ranked[0]["rank"] == 1

def test_all_same_score(ranker):
    same = [make_ats_result(f"C{i}", 60.0) for i in range(3)]
    ranked = ranker.rank_candidates(same)
    assert len(ranked) == 3
    assert [c["rank"] for c in ranked] == [1, 2, 3]
