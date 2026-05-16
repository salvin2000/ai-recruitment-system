import os, sys, json, pytest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.section_segmenter import ResumeSectionSegmenter, SectionType

SAMPLE_RESUME = """
Arjun Krishnan
arjun@email.com | +91-9876543210 | linkedin.com/in/arjun
Bangalore, India

Summary
Experienced Software Engineer with 3 years of experience.

Technical Skills
Python, Java, SQL, TensorFlow, Docker, AWS

Work Experience
Software Engineer - TechCorp India
June 2022 - Present
- Developed RESTful APIs using Django

Education
Bachelor of Technology - Computer Science
RV College of Engineering | 2017-2021
CGPA: 8.4/10

Certifications
- AWS Certified Developer (2023)
- Machine Learning - Coursera (2022)

Projects
AI Resume Screening System
- Built NLP-based resume parser

Achievements
- Winner of TechFest Hackathon 2023

Languages
English - Fluent
Hindi - Fluent
"""

@pytest.fixture
def segmenter():
    return ResumeSectionSegmenter()

@pytest.fixture
def result(segmenter):
    return segmenter.segment(SAMPLE_RESUME)

def test_segmenter_creates_instance(segmenter):
    assert segmenter is not None

def test_detects_skills_heading(segmenter):
    assert segmenter.is_section_heading("Technical Skills") == SectionType.SKILLS
    assert segmenter.is_section_heading("Skills") == SectionType.SKILLS

def test_detects_experience_heading(segmenter):
    assert segmenter.is_section_heading("Work Experience") == SectionType.WORK_EXPERIENCE
    assert segmenter.is_section_heading("Professional Experience") == SectionType.WORK_EXPERIENCE

def test_detects_education_heading(segmenter):
    assert segmenter.is_section_heading("Education") == SectionType.EDUCATION
    assert segmenter.is_section_heading("Educational Background") == SectionType.EDUCATION

def test_detects_certifications_heading(segmenter):
    assert segmenter.is_section_heading("Certifications") == SectionType.CERTIFICATIONS

def test_detects_projects_heading(segmenter):
    assert segmenter.is_section_heading("Projects") == SectionType.PROJECTS
    assert segmenter.is_section_heading("Academic Projects") == SectionType.PROJECTS

def test_detects_achievements_heading(segmenter):
    assert segmenter.is_section_heading("Achievements") == SectionType.ACHIEVEMENTS

def test_detects_summary_heading(segmenter):
    assert segmenter.is_section_heading("Summary") == SectionType.SUMMARY
    assert segmenter.is_section_heading("Objective") == SectionType.SUMMARY

def test_detects_languages_heading(segmenter):
    assert segmenter.is_section_heading("Languages") == SectionType.LANGUAGES

def test_unknown_heading(segmenter):
    assert segmenter.is_section_heading("Random text here.") == SectionType.UNKNOWN

def test_segment_returns_dict(result):
    assert isinstance(result, dict)

def test_segment_has_metadata(result):
    assert "metadata" in result
    assert "sections" in result

def test_metadata_fields(result):
    meta = result["metadata"]
    assert "total_sections" in meta
    assert "accuracy" in meta

def test_sections_is_list(result):
    assert isinstance(result["sections"], list)
    assert len(result["sections"]) > 0

def test_detects_multiple_sections(result):
    assert result["metadata"]["total_sections"] >= 5

def test_accuracy_is_positive(result):
    assert result["metadata"]["accuracy"] > 0

def test_detects_skills_section(result):
    types = [s["type"] for s in result["sections"]]
    assert SectionType.SKILLS.value in types

def test_detects_experience_section(result):
    types = [s["type"] for s in result["sections"]]
    assert SectionType.WORK_EXPERIENCE.value in types

def test_detects_education_section(result):
    types = [s["type"] for s in result["sections"]]
    assert SectionType.EDUCATION.value in types

def test_detects_projects_section(result):
    types = [s["type"] for s in result["sections"]]
    assert SectionType.PROJECTS.value in types

def test_header_detection(segmenter):
    header_text = "John Doe\njohn@email.com\n+91-9876543210"
    assert segmenter.is_header_block(header_text) == True

def test_header_extraction(segmenter):
    header_text = "Arjun\narjun@email.com\n+91-9876543210\nlinkedin.com/in/arjun"
    info = segmenter.extract_header_info(header_text)
    assert info["email"] == "arjun@email.com"

def test_nlp_classifies_education(segmenter):
    text = "Bachelor of Technology RV College CGPA 8.4 graduated 2021"
    assert segmenter.classify_by_nlp(text) == SectionType.EDUCATION

def test_nlp_classifies_skills(segmenter):
    text = "Python Java JavaScript SQL TensorFlow Docker AWS React"
    assert segmenter.classify_by_nlp(text) == SectionType.SKILLS

def test_accuracy_report(segmenter, result):
    report = segmenter.generate_accuracy_report([result])
    assert "resumes_processed" in report
    assert "average_accuracy" in report
    assert report["resumes_processed"] == 1

def test_save_output(segmenter, result, tmp_path):
    output_file = str(tmp_path / "test.json")
    segmenter.save_output(result, output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "sections" in data
