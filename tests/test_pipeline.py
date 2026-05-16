import json
import os
import sys
import pytest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.data_pipeline import DataLifecycleManager, DataStage, ModelVersion, generate_candidate_id, generate_job_id, generate_session_id, generate_report_id, create_base_metadata, create_resume_storage, create_parsed_profile, create_ats_score, create_screening_report, create_interview_result, create_retraining_dataset_schema
from pipeline.metadata_standards import generate_metadata_standards, generate_storage_structure
@pytest.fixture
def candidate_id():
    return generate_candidate_id()
@pytest.fixture
def job_id():
    return generate_job_id()
@pytest.fixture
def manager():
    return DataLifecycleManager()
@pytest.fixture
def sample_jd():
    return {"role_name": "Data Science Trainee", "domain": "IT", "required_skills": ["Python", "SQL"], "experience": {"min_years": 0, "max_years": 2}, "education": {"min_degree": "B.Tech"}}
@pytest.fixture
def resume(candidate_id, job_id):
    return create_resume_storage(candidate_id, job_id, "test.pdf", "pdf", "Sample text", 100.0)
@pytest.fixture
def profile(candidate_id, job_id, resume):
    return create_parsed_profile(candidate_id, job_id, resume)
@pytest.fixture
def ats(candidate_id, job_id, profile, sample_jd):
    return create_ats_score(candidate_id, job_id, profile, sample_jd)
@pytest.fixture
def screening(candidate_id, job_id, ats):
    return create_screening_report(candidate_id, job_id, ats)
@pytest.fixture
def pipeline(candidate_id, job_id, manager):
    return manager.create_pipeline_record(candidate_id, job_id)
def test_candidate_id_format(candidate_id):
    assert candidate_id.startswith("ZCP-CAND-")
    assert len(candidate_id) == 22
def test_job_id_format(job_id):
    assert job_id.startswith("ZCP-JOB-")
    assert len(job_id) == 21
def test_session_id_format():
    assert generate_session_id().startswith("ZCP-SES-")
def test_report_id_format():
    assert generate_report_id().startswith("ZCP-RPT-")
def test_unique_candidate_ids():
    ids = [generate_candidate_id() for _ in range(10)]
    assert len(set(ids)) == 10
def test_base_metadata_structure(candidate_id, job_id):
    meta = create_base_metadata(candidate_id, job_id, ModelVersion.PARSER_V1.value, DataStage.UPLOADED)
    for field in ["candidate_id", "job_id", "model_version", "stage", "created_at", "updated_at", "platform"]:
        assert field in meta
def test_metadata_platform(candidate_id, job_id):
    meta = create_base_metadata(candidate_id, job_id, ModelVersion.PARSER_V1.value, DataStage.UPLOADED)
    assert meta["platform"] == "Zecpath AI Recruitment"
def test_resume_storage_structure(resume):
    assert "metadata" in resume
    assert "resume" in resume
    assert "processing" in resume
def test_resume_not_parsed(resume):
    assert resume["resume"]["is_parsed"] == False
def test_parsed_profile_structure(profile):
    for field in ["metadata", "personal_info", "skills", "experience", "education", "parse_confidence"]:
        assert field in profile
def test_parsed_profile_skills(profile):
    assert "technical" in profile["skills"]
    assert "soft" in profile["skills"]
def test_ats_score_structure(ats):
    for field in ["metadata", "ats_result", "skill_analysis", "experience_analysis", "job_reference"]:
        assert field in ats
def test_ats_result_fields(ats):
    for field in ["overall_score", "skill_match_score", "grade", "recommendation"]:
        assert field in ats["ats_result"]
def test_screening_report_structure(screening):
    for field in ["metadata", "report_id", "screening_result", "ai_analysis", "next_action"]:
        assert field in screening
def test_interview_result_structure(candidate_id, job_id):
    interview = create_interview_result(candidate_id, job_id)
    for field in ["metadata", "session_id", "interview_type", "evaluation"]:
        assert field in interview
def test_pipeline_record_structure(pipeline):
    for field in ["pipeline_id", "candidate_id", "job_id", "current_stage", "stage_history", "scores", "decisions"]:
        assert field in pipeline
def test_pipeline_initial_stage(pipeline):
    assert pipeline["current_stage"] == DataStage.UPLOADED.value
def test_pipeline_advance_stage(pipeline, manager):
    advanced = manager.advance_stage(pipeline, DataStage.PARSED)
    assert advanced["current_stage"] == DataStage.PARSED.value
def test_pipeline_stage_history(pipeline, manager):
    pipeline = manager.advance_stage(pipeline, DataStage.PARSED)
    pipeline = manager.advance_stage(pipeline, DataStage.ATS_SCORED)
    assert len(pipeline["stage_history"]) == 3
def test_pipeline_flag_retraining(pipeline, manager):
    flagged = manager.flag_for_retraining(pipeline, "Model mismatch")
    assert flagged["retraining_flags"]["flag_for_retraining"] == True
def test_retraining_schema_structure():
    schema = create_retraining_dataset_schema()
    assert "dataset_id" in schema
    assert "schema" in schema
    assert "versioning_policy" in schema
def test_metadata_standards_structure():
    standards = generate_metadata_standards()
    assert "id_standards" in standards
    assert "timestamp_standards" in standards
    assert "privacy_standards" in standards
def test_storage_structure_document():
    structure = generate_storage_structure()
    assert "folder_structure" in structure
    assert "file_naming_conventions" in structure
