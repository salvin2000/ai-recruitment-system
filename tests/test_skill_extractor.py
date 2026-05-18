"""
Tests for Day 9 – Skill Extraction Engine
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.skill_extractor import SkillExtractionEngine
from parsers.skill_dictionary import MASTER_SKILL_DICT, SKILL_STACKS


# ── Sample Texts ──────────────────────────────────────────────────────────────

TECH_RESUME = """
Technical Skills:
Python, Java, JavaScript, SQL, React, Django, Flask
Machine Learning, TensorFlow, Pandas, NumPy
AWS, Docker, Git, Linux, PostgreSQL, MongoDB

Work Experience:
Developed RESTful APIs using Django REST Framework
Implemented machine learning models using scikit-learn
Built frontend using React and deployed on AWS EC2
Experience with Docker containerization and Kubernetes
"""

BUSINESS_RESUME = """
Core Competencies:
Project Management, Agile, Scrum, Business Analysis
CRM, Salesforce, SAP ERP, Stakeholder Management
Strategic Planning, Risk Management, Budgeting
Six Sigma, Process Improvement

Communication skills and leadership experience.
Strong problem solving and time management abilities.
"""

CREATIVE_RESUME = """
Skills:
UI/UX Design, Figma, Adobe Photoshop, Graphic Design
Digital Marketing, SEO, Social Media Management
Content Writing, Video Editing

Experience with user interface design and prototyping in Figma.
Proficient in Adobe Photoshop and Illustrator.
"""

MERN_RESUME = """
Tech Stack: MERN Stack
Built full-stack web applications using MERN stack.
Experience with MongoDB, Express, React, and Node.js.
"""

SYNONYM_RESUME = """
Skills:
py, reactjs, nodejs, postgres, sklearn
Worked with tensorflow keras and numpy library
Experience in ml and deep learning projects
"""

SPELLING_RESUME = """
Skills:
Pyhton, Javascrpit, Postgresq, Djnago
Experience with machne learning and data anlysis
"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return SkillExtractionEngine()


@pytest.fixture
def tech_result(engine):
    return engine.extract(TECH_RESUME)


@pytest.fixture
def business_result(engine):
    return engine.extract(BUSINESS_RESUME)


@pytest.fixture
def creative_result(engine):
    return engine.extract(CREATIVE_RESUME)


# ── Engine Instance Tests ─────────────────────────────────────────────────────

def test_engine_creates_instance(engine):
    """Test engine instantiates correctly."""
    assert engine is not None
    assert hasattr(engine, 'master_dict')
    assert hasattr(engine, 'flat_lookup')


def test_flat_lookup_built(engine):
    """Test flat lookup dictionary is built."""
    assert len(engine.flat_lookup) > 0
    assert "python" in engine.flat_lookup
    assert "machine learning" in engine.flat_lookup


def test_flat_lookup_has_synonyms(engine):
    """Test synonyms are in flat lookup."""
    assert "reactjs" in engine.flat_lookup
    assert "sklearn" in engine.flat_lookup
    assert "nodejs" in engine.flat_lookup


# ── Exact Match Tests ─────────────────────────────────────────────────────────

def test_exact_match_python(engine):
    """Test Python is extracted with exact match."""
    matches = engine.exact_match("python developer with 3 years experience")
    skills = [m[0] for m in matches]
    assert "python" in skills


def test_exact_match_confidence(engine):
    """Test exact match has high confidence."""
    matches = engine.exact_match("python java sql")
    for match in matches:
        assert match[2] >= 0.90


def test_synonym_match(engine):
    """Test synonym matching works."""
    matches = engine.exact_match("reactjs nodejs postgresql postgres")
    skills = [m[0] for m in matches]
    assert "react" in skills or "node" in skills


# ── Skill Stack Tests ─────────────────────────────────────────────────────────

def test_mern_stack_expansion(engine):
    """Test MERN stack is expanded to individual skills."""
    matches = engine.expand_skill_stacks("built using mern stack")
    skills = [m[0] for m in matches]
    assert "react" in skills
    assert "node" in skills
    assert "mongodb" in skills


def test_mean_stack_expansion(engine):
    """Test MEAN stack is expanded."""
    matches = engine.expand_skill_stacks("mean stack developer")
    skills = [m[0] for m in matches]
    assert "angular" in skills
    assert "mongodb" in skills


def test_stack_confidence(engine):
    """Test stack matches have correct confidence."""
    matches = engine.expand_skill_stacks("mern stack")
    for match in matches:
        assert match[2] == 0.85


# ── Context Match Tests ───────────────────────────────────────────────────────

def test_context_match_experience_in(engine):
    """Test context pattern 'experience in X'."""
    matches = engine.context_match("experience in python and machine learning")
    skills = [m[0] for m in matches]
    assert len(skills) > 0


def test_context_match_tech_stack(engine):
    """Test context pattern 'tech stack: X, Y'."""
    matches = engine.context_match("tech stack: python, react, mongodb")
    skills = [m[0] for m in matches]
    assert len(skills) > 0


# ── Full Extraction Tests ─────────────────────────────────────────────────────

def test_extract_returns_dict(tech_result):
    """Test extraction returns a dictionary."""
    assert isinstance(tech_result, dict)


def test_extract_has_required_fields(tech_result):
    """Test result has all required fields."""
    assert "metadata" in tech_result
    assert "skills" in tech_result
    assert "skills_by_category" in tech_result
    assert "skill_summary" in tech_result


def test_extract_metadata_fields(tech_result):
    """Test metadata has required fields."""
    meta = tech_result["metadata"]
    assert "total_skills" in meta
    assert "high_confidence" in meta
    assert "medium_confidence" in meta
    assert "low_confidence" in meta


def test_extracts_python(tech_result):
    """Test Python is extracted from tech resume."""
    skills = [s["skill"] for s in tech_result["skills"]]
    assert "python" in skills


def test_extracts_multiple_tech_skills(tech_result):
    """Test multiple tech skills are extracted."""
    assert tech_result["metadata"]["total_skills"] >= 5


def test_skills_have_confidence(tech_result):
    """Test all skills have confidence scores."""
    for skill in tech_result["skills"]:
        assert "confidence" in skill
        assert 0.0 <= skill["confidence"] <= 1.0


def test_skills_have_category(tech_result):
    """Test all skills have categories."""
    for skill in tech_result["skills"]:
        assert "category" in skill
        assert skill["category"] in ["Technical", "Business", "Soft", "Creative"]


def test_skills_sorted_by_confidence(tech_result):
    """Test skills are sorted by confidence (highest first)."""
    confidences = [s["confidence"] for s in tech_result["skills"]]
    assert confidences == sorted(confidences, reverse=True)


def test_technical_skills_detected(tech_result):
    """Test technical skills are in result."""
    assert len(tech_result["skill_summary"]["technical"]) > 0


def test_business_skills_detected(business_result):
    """Test business skills are extracted."""
    assert business_result["metadata"]["total_skills"] > 0


def test_soft_skills_detected(business_result):
    """Test soft skills are extracted."""
    assert len(business_result["skill_summary"]["soft"]) > 0


def test_creative_skills_detected(creative_result):
    """Test creative skills are extracted."""
    assert creative_result["metadata"]["total_skills"] > 0


# ── Deduplication Tests ───────────────────────────────────────────────────────

def test_no_duplicate_skills(tech_result):
    """Test no duplicate skills in result."""
    skills = [s["skill"].lower() for s in tech_result["skills"]]
    assert len(skills) == len(set(skills))


# ── Confidence Scoring Tests ──────────────────────────────────────────────────

def test_confidence_calculation(engine):
    """Test confidence calculation works."""
    occurrences = [(0.90, "exact"), (0.90, "exact")]
    conf = engine.calculate_final_confidence("python", occurrences, "python python")
    assert conf > 0.90  # Should be higher due to multiple occurrences


def test_high_confidence_exact_match(engine):
    """Test exact matches have high confidence."""
    result = engine.extract("python java sql react django")
    high_conf = [s for s in result["skills"] if s["confidence"] >= 0.85]
    assert len(high_conf) > 0


# ── Skill Dictionary Tests ────────────────────────────────────────────────────

def test_master_dict_has_categories(engine):
    """Test master dictionary has all categories."""
    categories = list(engine.master_dict.keys())
    assert "programming_languages" in categories
    assert "web_frameworks" in categories
    assert "ai_ml" in categories
    assert "soft_skills" in categories


def test_skill_stacks_defined():
    """Test skill stacks are defined."""
    assert "mern" in SKILL_STACKS
    assert "mean" in SKILL_STACKS
    assert "data science stack" in SKILL_STACKS


# ── Preprocess Tests ──────────────────────────────────────────────────────────

def test_preprocess_lowercase(engine):
    """Test preprocessing converts to lowercase."""
    result = engine.preprocess("PYTHON JAVA SQL")
    assert result == result.lower()


def test_preprocess_removes_bullets(engine):
    """Test preprocessing removes bullet points."""
    result = engine.preprocess("• Python\n- Java\n* SQL")
    assert "•" not in result
    assert result.strip() != ""


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(engine, tech_result, tmp_path):
    """Test saving output to JSON."""
    output_file = str(tmp_path / "test_skills.json")
    engine.save_output(tech_result, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "skills" in data
    assert "metadata" in data
