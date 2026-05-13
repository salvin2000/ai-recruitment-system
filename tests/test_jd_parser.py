import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.jd_parser import JDParser

SAMPLE_JD = """
Business Development Manager
Job Description
A Business Development Manager drives revenue growth.

Key Responsibilities
- Develop and execute business growth strategies
- Build and maintain strong client relationships
- Negotiate contracts and close deals

Required Skills
- Sales and negotiation
- CRM tools
- Communication skills
- Market research

Qualifications
- Bachelor's degree in Business or related field
- MBA preferred

Experience
- 5-10 years

Salary Package
- $60,000 - $100,000/year
"""

@pytest.fixture
def parser():
    return JDParser()

@pytest.fixture
def parsed_jd(parser):
    return parser.parse_jd(SAMPLE_JD, "test_jd.txt")

def test_parser_creates_instance(parser):
    assert parser is not None

def test_extract_role_name(parsed_jd):
    assert parsed_jd["role_name"] != ""

def test_extract_skills(parsed_jd):
    assert isinstance(parsed_jd["required_skills"], list)
    assert len(parsed_jd["required_skills"]) > 0

def test_extract_experience(parsed_jd):
    exp = parsed_jd["experience"]
    assert exp["min_years"] == 5
    assert exp["max_years"] == 10

def test_extract_education(parsed_jd):
    edu = parsed_jd["education"]
    assert edu["mba_preferred"] == True

def test_ai_profile_built(parsed_jd):
    assert "role" in parsed_jd["ai_profile"]
    assert "skills_required" in parsed_jd["ai_profile"]

def test_full_parse_output_structure(parsed_jd):
    required_fields = ["metadata", "role_name", "required_skills",
                      "experience", "education", "salary", "ai_profile"]
    for field in required_fields:
        assert field in parsed_jd
