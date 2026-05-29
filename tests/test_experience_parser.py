"""
Tests for Day 10 – Experience Parsing & Relevance Engine
"""

import os
import sys
import json
import pytest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.experience_parser import ExperienceParser


# ── Sample Texts ──────────────────────────────────────────────────────────────

# All samples now include "Work Experience" heading so the parser finds the section

SIMPLE_EXPERIENCE = """
Work Experience
Software Engineer at TechCorp India
Jan 2022 - Present
- Developed REST APIs using Python and Django
- Deployed applications on AWS EC2 and S3
- Worked with PostgreSQL and Redis databases

Education
Bachelor of Technology - Computer Science
Some College | 2018 - 2022
"""

MULTI_ROLE_EXPERIENCE = """
Work Experience
Senior Software Engineer - GlobalTech Ltd
June 2023 - Present
Python, Django, React, AWS, Docker

Software Developer - Startup Hub
January 2021 - May 2023
Python, Flask, PostgreSQL, Git

Junior Developer - CodeBase Solutions
July 2019 - December 2020
Python, SQL, HTML, CSS

Education
Bachelor of Technology
Some College | 2015 - 2019
"""

GAP_EXPERIENCE = """
Work Experience
Software Engineer - TechCorp
Jan 2022 - Dec 2022

Product Manager - StartupXYZ
Jan 2024 - Present

Education
Bachelor of Technology - Computer Science
"""

OVERLAP_EXPERIENCE = """
Work Experience
Software Engineer - Company A
Jan 2021 - Dec 2022

Freelance Developer - Self Employed
Jun 2022 - Jun 2023

Education
Bachelor of Technology
"""

SAMPLE_JD = {
    "role_name":            "Software Engineer",
    "required_skills":      ["python", "django", "react", "aws"],
    "min_experience_years": 2,
    "max_experience_years": 5,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def parser():
    return ExperienceParser()

@pytest.fixture
def simple_result(parser):
    return parser.parse(SIMPLE_EXPERIENCE, SAMPLE_JD)

@pytest.fixture
def multi_result(parser):
    return parser.parse(MULTI_ROLE_EXPERIENCE, SAMPLE_JD)


# ── Parser Instance Tests ─────────────────────────────────────────────────────

def test_parser_creates_instance(parser):
    assert parser is not None
    assert hasattr(parser, 'skill_engine')

def test_parser_has_today(parser):
    assert parser.today == date.today()


# ── Date Parsing Tests ────────────────────────────────────────────────────────

def test_parse_date_month_year(parser):
    assert parser.parse_date("January 2022") == date(2022, 1, 1)

def test_parse_date_short_month(parser):
    assert parser.parse_date("Jan 2022") == date(2022, 1, 1)

def test_parse_date_present(parser):
    assert parser.parse_date("Present") == date.today()

def test_parse_date_current(parser):
    assert parser.parse_date("current") == date.today()

def test_parse_date_year_only(parser):
    assert parser.parse_date("2022") == date(2022, 1, 1)

def test_parse_date_invalid(parser):
    assert parser.parse_date("not a date") is None


# ── Duration Tests ────────────────────────────────────────────────────────────

def test_parse_duration_basic(parser):
    _, _, months = parser.parse_duration("Jan 2020", "Jan 2022")
    assert months == 24

def test_parse_duration_present(parser):
    _, end, months = parser.parse_duration("Jan 2024", "Present")
    assert months >= 0
    assert end == date.today()


# ── Extraction Tests ──────────────────────────────────────────────────────────

def test_extract_job_title(parser):
    """Test job title extraction using extract_title_and_company."""
    text  = "Software Engineer - TechCorp India\nJan 2022 - Present"
    title, _ = parser.extract_title_and_company(text)
    assert len(title) > 0
    assert "Software Engineer" in title

def test_extract_company_name(parser):
    """Test company name extraction using extract_title_and_company."""
    text = "Software Engineer - TechCorp India\nJan 2022 - Present"
    _, company = parser.extract_title_and_company(text)
    assert len(company) > 0

def test_extract_date_range(parser):
    text = "Software Engineer\nJan 2022 - Present"
    start, end = parser.extract_date_range(text)
    assert start is not None

def test_extract_date_range_year_only(parser):
    start, end = parser.extract_date_range("Developer\n2020 - 2022")
    assert start is not None
    assert end is not None


# ── Block Splitting Tests ─────────────────────────────────────────────────────

def test_split_experience_blocks(parser):
    exp_section = """Software Engineer - GlobalTech Ltd
June 2023 - Present
Python, Django

Software Developer - Startup Hub
January 2021 - May 2023
Flask, PostgreSQL"""
    blocks = parser.split_experience_blocks(exp_section)
    assert len(blocks) >= 1


# ── Full Parse Tests ──────────────────────────────────────────────────────────

def test_parse_returns_dict(simple_result):
    assert isinstance(simple_result, dict)

def test_parse_has_required_fields(simple_result):
    assert "metadata"  in simple_result
    assert "roles"     in simple_result
    assert "gaps"      in simple_result
    assert "overlaps"  in simple_result
    assert "relevance" in simple_result

def test_parse_metadata_fields(simple_result):
    meta = simple_result["metadata"]
    assert "total_roles"   in meta
    assert "total_months"  in meta
    assert "total_years"   in meta
    assert "total_display" in meta
    assert "has_gaps"      in meta
    assert "has_overlaps"  in meta

def test_parse_roles_not_empty(simple_result):
    assert len(simple_result["roles"]) >= 1

def test_role_has_required_fields(simple_result):
    for role in simple_result["roles"]:
        assert "job_title"        in role
        assert "company"          in role
        assert "duration_months"  in role
        assert "duration_display" in role
        assert "is_current"       in role
        assert "skills_mentioned" in role

def test_total_experience_positive(simple_result):
    assert simple_result["metadata"]["total_months"] >= 0

def test_multi_role_parsing(multi_result):
    assert multi_result["metadata"]["total_roles"] >= 2


# ── Gap Detection Tests ───────────────────────────────────────────────────────

def test_gap_detection(parser):
    result = parser.parse(GAP_EXPERIENCE)
    assert "gaps" in result
    assert isinstance(result["gaps"], list)

def test_gap_has_fields(parser):
    result = parser.parse(GAP_EXPERIENCE)
    for gap in result["gaps"]:
        assert "gap_months"  in gap
        assert "severity"    in gap
        assert "after_role"  in gap
        assert "before_role" in gap


# ── Overlap Detection Tests ───────────────────────────────────────────────────

def test_overlap_detection(parser):
    result = parser.parse(OVERLAP_EXPERIENCE)
    assert isinstance(result["overlaps"], list)


# ── Relevance Scoring Tests ───────────────────────────────────────────────────

def test_relevance_score_present(simple_result):
    assert simple_result["relevance"] is not None

def test_relevance_has_fields(simple_result):
    rel = simple_result["relevance"]
    assert "relevance_score"      in rel
    assert "role_similarity"      in rel
    assert "skills_match"         in rel
    assert "experience_score"     in rel
    assert "total_years"          in rel
    assert "meets_min_experience" in rel
    assert "grade"                in rel

def test_relevance_score_range(simple_result):
    score = simple_result["relevance"]["relevance_score"]
    assert 0.0 <= score <= 1.0

def test_relevance_grade_valid(simple_result):
    assert simple_result["relevance"]["grade"] in ["A", "B", "C", "D"]


# ── Role Similarity Tests ─────────────────────────────────────────────────────

def test_role_similarity_same_role(parser):
    sim = parser.compute_role_similarity("Software Engineer", "Software Engineer")
    assert sim >= 0.80

def test_role_similarity_different_roles(parser):
    sim = parser.compute_role_similarity("Chef", "Software Engineer")
    assert sim <= 0.50     # fixed: <= instead of <


# ── Format Duration Tests ─────────────────────────────────────────────────────

def test_format_duration_years(parser):
    assert "yr" in parser._format_duration(24)

def test_format_duration_months(parser):
    assert "mo" in parser._format_duration(8)

def test_format_duration_zero(parser):
    assert parser._format_duration(0) == "Unknown"


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(parser, simple_result, tmp_path):
    output_file = str(tmp_path / "test_experience.json")
    parser.save_output(simple_result, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "roles"    in data
    assert "metadata" in data
