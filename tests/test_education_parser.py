"""
Tests for Day 11 – Education & Certification Parsing
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.education_parser import EducationParser, DEGREE_HIERARCHY, CERTIFICATION_CATEGORIES


# ── Sample Texts ──────────────────────────────────────────────────────────────

SIMPLE_RESUME = """
Work Experience
Software Engineer - TechCorp India
June 2022 - Present

Education
Bachelor of Technology - Computer Science Engineering
RV College of Engineering, Bangalore | 2017 - 2021
CGPA: 8.4 / 10

Certifications
- AWS Certified Developer Associate (2023)
- Machine Learning Specialization - Coursera (2022)
- Python Programming - Udemy (2021)

Skills
Python, Django, AWS
"""

MULTI_DEGREE_RESUME = """
Work Experience
Data Scientist - Analytics Corp
March 2022 - Present

Education
Master of Science - Data Science
IIT Bombay | 2019 - 2021

Bachelor of Technology - Computer Science
NIT Trichy | 2015 - 2019
CGPA: 8.9 / 10

Certifications
- TensorFlow Developer Certificate - Google (2022)
- AWS Machine Learning Specialty (2023)
- Tableau Desktop Specialist (2022)

Skills
Python, TensorFlow, SQL
"""

FRESHER_RESUME = """
Education
Bachelor of Technology - Computer Science
Anna University | 2020 - 2024
CGPA: 7.8 / 10

Certifications
- Python Programming - Coursera (2023)
- Web Development Bootcamp - Udemy (2023)

Skills
Python, Java, SQL
"""

NO_CERT_RESUME = """
Education
Bachelor of Commerce - Accounting
Mumbai University | 2018 - 2021

Skills
Tally, Excel, Communication
"""

SAMPLE_JD = {
    "role_name":              "Software Engineer",
    "min_education":          "b.tech",
    "field_of_study":         "computer science",
    "required_certifications": [],
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def parser():
    return EducationParser()

@pytest.fixture
def simple_result(parser):
    return parser.parse(SIMPLE_RESUME, SAMPLE_JD)

@pytest.fixture
def multi_result(parser):
    return parser.parse(MULTI_DEGREE_RESUME, SAMPLE_JD)

@pytest.fixture
def fresher_result(parser):
    return parser.parse(FRESHER_RESUME, SAMPLE_JD)


# ── Parser Instance Tests ─────────────────────────────────────────────────────

def test_parser_creates_instance(parser):
    assert parser is not None
    assert hasattr(parser, 'skill_engine')

def test_parser_has_today(parser):
    from datetime import date
    assert parser.today == date.today()


# ── Degree Normalization Tests ────────────────────────────────────────────────

def test_normalize_btech(parser):
    assert parser.normalize_degree("btech") == "b.tech"

def test_normalize_btech_full(parser):
    assert parser.normalize_degree("bachelor of technology") == "b.tech"

def test_normalize_mba(parser):
    assert parser.normalize_degree("mba") == "m.b.a"

def test_normalize_msc(parser):
    assert parser.normalize_degree("master of science") == "m.sc"

def test_normalize_phd(parser):
    assert parser.normalize_degree("phd") == "ph.d"

def test_normalize_bsc(parser):
    assert parser.normalize_degree("bsc") == "b.sc"


# ── Degree Extraction Tests ───────────────────────────────────────────────────

def test_extract_degree_btech(parser):
    text = "Bachelor of Technology - Computer Science\nRV College | 2017-2021"
    assert parser.extract_degree(text) == "b.tech"

def test_extract_degree_msc(parser):
    text = "Master of Science - Data Science\nIIT Bombay | 2019-2021"
    assert parser.extract_degree(text) == "m.sc"

def test_extract_degree_not_specified(parser):
    text = "Some random text without degree info"
    assert parser.extract_degree(text) == "Not specified"


# ── Field of Study Tests ──────────────────────────────────────────────────────

def test_extract_field_cs(parser):
    text = "Bachelor of Technology - Computer Science Engineering"
    assert parser.extract_field_of_study(text) == "Computer Science"

def test_extract_field_data_science(parser):
    text = "Master of Science - Data Science and Analytics"
    assert parser.extract_field_of_study(text) == "Data Science"

def test_extract_field_business(parser):
    text = "Master of Business Administration - Finance"
    assert parser.extract_field_of_study(text) == "Business"

def test_extract_field_not_specified(parser):
    text = "Some degree without clear field"
    result = parser.extract_field_of_study(text)
    assert isinstance(result, str)


# ── Graduation Year Tests ─────────────────────────────────────────────────────

def test_extract_year_range(parser):
    text = "RV College of Engineering | 2017 - 2021"
    assert parser.extract_graduation_year(text) == "2021"

def test_extract_year_single(parser):
    text = "Graduated in 2022 from Mumbai University"
    assert parser.extract_graduation_year(text) == "2022"

def test_extract_year_not_found(parser):
    text = "Some text without any year"
    assert parser.extract_graduation_year(text) == "Not specified"


# ── Institution Extraction Tests ──────────────────────────────────────────────

def test_extract_institution(parser):
    text = "Bachelor of Technology\nRV College of Engineering, Bangalore\n2017-2021"
    inst = parser.extract_institution(text)
    assert len(inst) > 0

def test_extract_institution_iit(parser):
    text = "Master of Science\nIIT Bombay | 2019-2021"
    inst = parser.extract_institution(text)
    assert len(inst) > 0


# ── Full Parse Tests ──────────────────────────────────────────────────────────

def test_parse_returns_dict(simple_result):
    assert isinstance(simple_result, dict)

def test_parse_has_required_fields(simple_result):
    assert "metadata"       in simple_result
    assert "qualifications" in simple_result
    assert "certifications" in simple_result
    assert "relevance"      in simple_result

def test_parse_metadata_fields(simple_result):
    meta = simple_result["metadata"]
    assert "total_qualifications" in meta
    assert "total_certifications" in meta
    assert "highest_degree"       in meta

def test_parse_finds_qualification(simple_result):
    assert len(simple_result["qualifications"]) >= 1

def test_qualification_has_fields(simple_result):
    for qual in simple_result["qualifications"]:
        assert "degree_raw"        in qual
        assert "degree_normalized" in qual
        assert "field_of_study"    in qual
        assert "institution"       in qual
        assert "graduation_year"   in qual

def test_multi_degree_parsing(multi_result):
    assert multi_result["metadata"]["total_qualifications"] >= 2

def test_highest_degree_is_highest(multi_result):
    highest = multi_result["metadata"]["highest_degree"]
    assert DEGREE_HIERARCHY.get(highest, 0) >= 5


# ── Certification Tests ───────────────────────────────────────────────────────

def test_finds_certifications(simple_result):
    assert simple_result["metadata"]["total_certifications"] >= 1

def test_certification_has_fields(simple_result):
    for cert in simple_result["certifications"]:
        assert "name"     in cert
        assert "category" in cert
        assert "year"     in cert

def test_no_certifications_fresher(parser):
    result = parser.parse(NO_CERT_RESUME, SAMPLE_JD)
    assert result["metadata"]["total_certifications"] == 0

def test_certification_categorization_cloud(parser):
    cat = parser.categorize_certification("AWS Certified Developer Associate")
    assert cat == "Cloud"

def test_certification_categorization_ml(parser):
    cat = parser.categorize_certification("Machine Learning Specialization Coursera")
    assert cat == "Data Science Ml"

def test_certification_categorization_general(parser):
    cat = parser.categorize_certification("Some Random Unknown Certificate")
    assert cat == "General"


# ── Relevance Scoring Tests ───────────────────────────────────────────────────

def test_relevance_present(simple_result):
    assert simple_result["relevance"] is not None

def test_relevance_has_fields(simple_result):
    rel = simple_result["relevance"]
    assert "relevance_score"       in rel
    assert "degree_score"          in rel
    assert "field_score"           in rel
    assert "certification_score"   in rel
    assert "grade"                 in rel
    assert "meets_min_degree"      in rel

def test_relevance_score_range(simple_result):
    score = simple_result["relevance"]["relevance_score"]
    assert 0.0 <= score <= 1.0

def test_relevance_grade_valid(simple_result):
    assert simple_result["relevance"]["grade"] in ["A", "B", "C", "D"]

def test_btech_meets_btech_requirement(simple_result):
    assert simple_result["relevance"]["meets_min_degree"] == True


# ── Degree Hierarchy Tests ────────────────────────────────────────────────────

def test_phd_higher_than_mtech(parser):
    assert DEGREE_HIERARCHY["ph.d"] > DEGREE_HIERARCHY["m.tech"]

def test_mtech_higher_than_btech(parser):
    assert DEGREE_HIERARCHY["m.tech"] > DEGREE_HIERARCHY["b.tech"]

def test_btech_higher_than_diploma(parser):
    assert DEGREE_HIERARCHY["b.tech"] > DEGREE_HIERARCHY["diploma"]


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_output(parser, simple_result, tmp_path):
    output_file = str(tmp_path / "test_education.json")
    parser.save_output(simple_result, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "qualifications" in data
    assert "certifications" in data
    assert "metadata"       in data
