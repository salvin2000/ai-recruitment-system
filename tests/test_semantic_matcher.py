"""
Tests for Day 12 – Semantic Matching Engine
"""

import os
import sys
import json
import math
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.semantic_matcher import (
    SemanticMatchingEngine, TFIDFEmbedder,
    cosine_similarity, jaccard_similarity,
    SIMILARITY_THRESHOLDS, COMPONENT_WEIGHTS
)


# ── Sample Texts ──────────────────────────────────────────────────────────────

TECH_RESUME = """
Technical Skills
Python, Django, REST API, Machine Learning, TensorFlow, AWS, Docker,
PostgreSQL, SQL, Git, Linux, Flask, Kubernetes

Work Experience
Software Engineer - TechCorp India
June 2022 - Present
- Developed RESTful APIs using Django REST Framework
- Implemented Machine Learning models using scikit-learn
- Deployed applications on AWS EC2 using Docker
- Worked with PostgreSQL and Redis databases

Projects
AI Resume Screening System
- Built NLP-based resume parser using Python and spaCy
- Tech Stack: Python, Flask, PostgreSQL
"""

DATA_RESUME = """
Core Competencies
SQL, Python, Power BI, Tableau, Excel, Statistical Analysis, Pandas

Professional Experience
Data Analyst - Analytics Corp
March 2022 - Present
- Designed Power BI dashboards for senior management
- Automated reporting using Python and Pandas
- Performed statistical analysis on sales data

Projects
Sales Dashboard Automation
- Built automated reporting pipeline using Python
- Created interactive Tableau dashboards
"""

SOFTWARE_JD = """
Software Engineer
Required Skills: Python, Django, REST API, Machine Learning, AWS, Docker,
PostgreSQL, SQL, Git, TensorFlow

Key Responsibilities:
- Develop RESTful APIs using Python and Django
- Implement machine learning models
- Deploy applications on AWS using Docker
- Work with PostgreSQL databases
"""

DATA_JD = """
Data Analyst
Required Skills: Python, SQL, Power BI, Tableau, Excel, Statistical Analysis

Key Responsibilities:
- Analyze large datasets using Python and SQL
- Build Power BI dashboards
- Perform statistical analysis
- Automate reporting processes
"""

UNRELATED_RESUME = """
Skills: Cooking, Gardening, Painting, Music, Photography

Experience:
Chef at Restaurant ABC
2020 - Present
- Prepared Italian cuisine
- Managed kitchen operations
"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def embedder():
    e = TFIDFEmbedder()
    e.fit([TECH_RESUME, DATA_RESUME, SOFTWARE_JD, DATA_JD])
    return e

@pytest.fixture
def engine():
    eng = SemanticMatchingEngine()
    eng.build_corpus([TECH_RESUME, DATA_RESUME], [SOFTWARE_JD, DATA_JD])
    return eng

@pytest.fixture
def tech_match(engine):
    return engine.match(TECH_RESUME, SOFTWARE_JD, "tech_resume", "sw_jd")

@pytest.fixture
def data_match(engine):
    return engine.match(DATA_RESUME, DATA_JD, "data_resume", "data_jd")

@pytest.fixture
def unrelated_match(engine):
    return engine.match(UNRELATED_RESUME, SOFTWARE_JD,
                        "unrelated_resume", "sw_jd")


# ── TF-IDF Embedder Tests ─────────────────────────────────────────────────────

def test_embedder_creates_instance():
    e = TFIDFEmbedder()
    assert e is not None
    assert not e.is_fitted

def test_embedder_fits_on_corpus(embedder):
    assert embedder.is_fitted
    assert len(embedder.vocabulary) > 0
    assert len(embedder.idf_scores) > 0

def test_embedder_tokenizes_correctly():
    e = TFIDFEmbedder()
    tokens = e._tokenize("Python Django AWS Machine Learning")
    assert "python" in tokens
    assert "django" in tokens
    assert "aws" in tokens

def test_embedder_removes_stopwords():
    e = TFIDFEmbedder()
    tokens = e._tokenize("the and for with from will can")
    assert len(tokens) == 0

def test_embedder_transform_returns_dict(embedder):
    vec = embedder.transform("Python Django AWS")
    assert isinstance(vec, dict)
    assert len(vec) > 0

def test_embedder_transform_has_scores(embedder):
    vec = embedder.transform("Python Django Machine Learning")
    for score in vec.values():
        assert score > 0.0

def test_embedder_unfitted_raises_error():
    e = TFIDFEmbedder()
    with pytest.raises(RuntimeError):
        e.transform("Python")


# ── Cosine Similarity Tests ───────────────────────────────────────────────────

def test_cosine_similarity_identical_vectors():
    vec = {"python": 0.5, "django": 0.3}
    sim = cosine_similarity(vec, vec)
    assert sim == 1.0

def test_cosine_similarity_empty_vectors():
    assert cosine_similarity({}, {}) == 0.0
    assert cosine_similarity({"python": 0.5}, {}) == 0.0

def test_cosine_similarity_range(embedder):
    vec1 = embedder.transform(TECH_RESUME)
    vec2 = embedder.transform(SOFTWARE_JD)
    sim  = cosine_similarity(vec1, vec2)
    assert 0.0 <= sim <= 1.0

def test_cosine_higher_for_similar_texts(embedder):
    vec_tech = embedder.transform(TECH_RESUME)
    vec_sw   = embedder.transform(SOFTWARE_JD)
    vec_unr  = embedder.transform(UNRELATED_RESUME)
    sim_rel  = cosine_similarity(vec_tech, vec_sw)
    sim_unr  = cosine_similarity(vec_unr, vec_sw)
    assert sim_rel > sim_unr


# ── Jaccard Similarity Tests ──────────────────────────────────────────────────

def test_jaccard_identical_text():
    sim = jaccard_similarity("python django aws", "python django aws")
    assert sim == 1.0

def test_jaccard_empty_text():
    assert jaccard_similarity("", "") == 0.0
    assert jaccard_similarity("python", "") == 0.0

def test_jaccard_range():
    sim = jaccard_similarity(TECH_RESUME, SOFTWARE_JD)
    assert 0.0 <= sim <= 1.0

def test_jaccard_higher_for_similar():
    sim_rel = jaccard_similarity(TECH_RESUME, SOFTWARE_JD)
    sim_unr = jaccard_similarity(UNRELATED_RESUME, SOFTWARE_JD)
    assert sim_rel > sim_unr


# ── Engine Tests ──────────────────────────────────────────────────────────────

def test_engine_creates_instance():
    eng = SemanticMatchingEngine()
    assert eng is not None
    assert not eng._fitted

def test_engine_builds_corpus(engine):
    assert engine._fitted
    assert engine.embedder.is_fitted

def test_engine_match_returns_dict(tech_match):
    assert isinstance(tech_match, dict)

def test_match_has_required_fields(tech_match):
    assert "metadata"          in tech_match
    assert "similarity_scores" in tech_match
    assert "overall_match"     in tech_match

def test_match_metadata_fields(tech_match):
    meta = tech_match["metadata"]
    assert "matched_at"     in meta
    assert "engine_version" in meta
    assert "resume_file"    in meta
    assert "embedding_type" in meta

def test_similarity_scores_fields(tech_match):
    scores = tech_match["similarity_scores"]
    assert "skills"     in scores
    assert "experience" in scores
    assert "projects"   in scores

def test_each_score_has_fields(tech_match):
    for component in ["skills", "experience", "projects"]:
        score = tech_match["similarity_scores"][component]
        assert "score"   in score
        assert "cosine"  in score
        assert "jaccard" in score
        assert "level"   in score

def test_score_in_range(tech_match):
    for component in ["skills", "experience", "projects"]:
        score = tech_match["similarity_scores"][component]["score"]
        assert 0.0 <= score <= 1.0

def test_level_is_valid(tech_match):
    for component in ["skills", "experience", "projects"]:
        level = tech_match["similarity_scores"][component]["level"]
        assert level in ["high", "medium", "low"]

def test_overall_match_fields(tech_match):
    overall = tech_match["overall_match"]
    assert "score"          in overall
    assert "level"          in overall
    assert "grade"          in overall
    assert "recommendation" in overall

def test_overall_score_in_range(tech_match):
    score = tech_match["overall_match"]["score"]
    assert 0.0 <= score <= 1.0

def test_grade_is_valid(tech_match):
    grade = tech_match["overall_match"]["grade"]
    assert grade in ["A", "B", "C", "D"]

def test_tech_resume_matches_sw_jd_better(engine):
    tech_result = engine.match(TECH_RESUME, SOFTWARE_JD)
    data_result = engine.match(DATA_RESUME, SOFTWARE_JD)
    tech_score  = tech_result["overall_match"]["score"]
    data_score  = data_result["overall_match"]["score"]
    assert tech_score > data_score

def test_data_resume_matches_data_jd_better(engine):
    data_result = engine.match(DATA_RESUME, DATA_JD)
    tech_result = engine.match(TECH_RESUME, DATA_JD)
    data_score  = data_result["overall_match"]["score"]
    tech_score  = tech_result["overall_match"]["score"]
    assert data_score >= tech_score

def test_unrelated_resume_scores_low(unrelated_match):
    score = unrelated_match["overall_match"]["score"]
    assert score < 0.50


# ── Batch Match Tests ─────────────────────────────────────────────────────────

def test_batch_match_returns_list(engine):
    results = engine.match_batch(
        [TECH_RESUME, DATA_RESUME], SOFTWARE_JD
    )
    assert isinstance(results, list)
    assert len(results) == 2

def test_batch_match_all_have_fields(engine):
    results = engine.match_batch(
        [TECH_RESUME, DATA_RESUME], SOFTWARE_JD
    )
    for r in results:
        assert "overall_match"     in r
        assert "similarity_scores" in r


# ── Accuracy Report Tests ─────────────────────────────────────────────────────

def test_accuracy_report_structure(engine):
    results = engine.match_batch(
        [TECH_RESUME, DATA_RESUME, UNRELATED_RESUME], SOFTWARE_JD
    )
    report = engine.generate_accuracy_report(results)
    assert "total_resumes"      in report
    assert "grade_distribution" in report
    assert "average_scores"     in report
    assert "thresholds_used"    in report

def test_accuracy_report_total(engine):
    results = engine.match_batch(
        [TECH_RESUME, DATA_RESUME, UNRELATED_RESUME], SOFTWARE_JD
    )
    report = engine.generate_accuracy_report(results)
    assert report["total_resumes"] == 3

def test_accuracy_avg_scores_in_range(engine):
    results = engine.match_batch(
        [TECH_RESUME, DATA_RESUME], SOFTWARE_JD
    )
    report = engine.generate_accuracy_report(results)
    for score in report["average_scores"].values():
        assert 0.0 <= score <= 1.0


# ── Threshold Tests ───────────────────────────────────────────────────────────

def test_thresholds_defined():
    for component in ["skills", "experience", "projects", "overall"]:
        assert component in SIMILARITY_THRESHOLDS
        assert "high"   in SIMILARITY_THRESHOLDS[component]
        assert "medium" in SIMILARITY_THRESHOLDS[component]
        assert "low"    in SIMILARITY_THRESHOLDS[component]

def test_threshold_ordering():
    for component, thresholds in SIMILARITY_THRESHOLDS.items():
        assert thresholds["high"] > thresholds["medium"] > thresholds["low"]

def test_weights_sum_to_one():
    total = sum(COMPONENT_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(engine, tech_match, tmp_path):
    output_file = str(tmp_path / "test_semantic.json")
    engine.save_output(tech_match, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "overall_match"     in data
    assert "similarity_scores" in data
