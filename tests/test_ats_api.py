"""
Tests for Day 16 – ATS API Design & Integration Planning
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.ats_api import (
    ATSAPISpecification, AsyncJobManager, JobStatus,
    API_ENDPOINTS, ERROR_CODES, ASYNC_JOB_SCHEMA,
    API_VERSION, API_BASE_PATH, HTTP_STATUS,
    SUPPORTED_FILE_TYPES, MAX_FILE_SIZE_MB, MAX_BATCH_SIZE,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def spec():
    return ATSAPISpecification()

@pytest.fixture
def manager():
    return AsyncJobManager()

@pytest.fixture
def sample_job(manager):
    return manager.create_job("upload", "ZCP-CAND-TEST", "ZCP-JOB-TEST")


# ── API Specification Tests ───────────────────────────────────────────────────

def test_spec_creates_instance(spec):
    assert spec is not None
    assert spec.version == API_VERSION

def test_spec_has_base_path(spec):
    assert spec.base_path == API_BASE_PATH

def test_spec_has_all_endpoints(spec):
    required = ["upload_resume", "parse_resume", "score_candidate",
                 "shortlist_candidates", "get_job_status",
                 "get_candidate", "batch_upload"]
    for ep in required:
        assert ep in spec.endpoints

def test_each_endpoint_has_required_fields(spec):
    for name, ep in spec.endpoints.items():
        assert "method"      in ep
        assert "path"        in ep
        assert "description" in ep
        assert "response"    in ep

def test_endpoints_have_valid_methods(spec):
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    for name, ep in spec.endpoints.items():
        assert ep["method"] in valid_methods

def test_endpoint_paths_start_with_base(spec):
    for name, ep in spec.endpoints.items():
        assert ep["path"].startswith(API_BASE_PATH)

def test_get_endpoint_returns_correct(spec):
    ep = spec.get_endpoint("upload_resume")
    assert ep["method"] == "POST"
    assert "upload" in ep["path"]

def test_get_endpoint_unknown_returns_empty(spec):
    ep = spec.get_endpoint("nonexistent_endpoint")
    assert ep == {}

def test_get_all_endpoints_returns_dict(spec):
    all_eps = spec.get_all_endpoints()
    assert isinstance(all_eps, dict)
    assert len(all_eps) >= 6


# ── Request Validation Tests ──────────────────────────────────────────────────

def test_validate_valid_upload_request(spec):
    result = spec.validate_request("upload_resume", {
        "job_id": "ZCP-JOB-001",
        "file_type": "application/pdf"
    })
    assert result["valid"] == True
    assert result["errors"] == []

def test_validate_missing_required_field(spec):
    result = spec.validate_request("upload_resume", {
        "file_type": "application/pdf"
    })
    assert result["valid"] == False
    assert len(result["errors"]) > 0

def test_validate_invalid_file_type(spec):
    result = spec.validate_request("upload_resume", {
        "job_id": "ZCP-JOB-001",
        "file_type": "image/jpeg"
    })
    assert result["valid"] == False
    assert any("ATS_001" in e for e in result["errors"])

def test_validate_valid_score_request(spec):
    result = spec.validate_request("score_candidate", {
        "candidate_id": "ZCP-CAND-001",
        "job_id":       "ZCP-JOB-001",
    })
    assert result["valid"] == True

def test_validate_invalid_custom_weights(spec):
    result = spec.validate_request("score_candidate", {
        "candidate_id": "ZCP-CAND-001",
        "job_id":       "ZCP-JOB-001",
        "custom_weights": {
            "skill_match": 0.5, "experience_relevance": 0.5,
            "education_alignment": 0.5, "semantic_similarity": 0.5
        }
    })
    assert result["valid"] == False
    assert any("ATS_013" in e for e in result["errors"])

def test_validate_valid_custom_weights(spec):
    result = spec.validate_request("score_candidate", {
        "candidate_id": "ZCP-CAND-001",
        "job_id":       "ZCP-JOB-001",
        "custom_weights": {
            "skill_match": 0.5, "experience_relevance": 0.25,
            "education_alignment": 0.15, "semantic_similarity": 0.10
        }
    })
    assert result["valid"] == True

def test_validate_unknown_endpoint(spec):
    result = spec.validate_request("unknown_endpoint", {})
    assert result["valid"] == False


# ── API Spec JSON Tests ───────────────────────────────────────────────────────

def test_generate_api_spec_returns_dict(spec):
    spec_json = spec.generate_api_spec_json()
    assert isinstance(spec_json, dict)

def test_api_spec_has_required_sections(spec):
    spec_json = spec.generate_api_spec_json()
    assert "api_info"           in spec_json
    assert "authentication"     in spec_json
    assert "endpoints"          in spec_json
    assert "error_codes"        in spec_json
    assert "async_job_schema"   in spec_json
    assert "logging_standards"  in spec_json
    assert "limits"             in spec_json

def test_api_spec_version_correct(spec):
    spec_json = spec.generate_api_spec_json()
    assert spec_json["api_info"]["version"] == API_VERSION

def test_api_spec_limits_defined(spec):
    spec_json = spec.generate_api_spec_json()
    limits    = spec_json["limits"]
    assert "max_file_size_mb" in limits
    assert "max_batch_size"   in limits
    assert "rate_limit"       in limits


# ── AsyncJobManager Tests ─────────────────────────────────────────────────────

def test_manager_creates_instance(manager):
    assert manager is not None
    assert isinstance(manager.jobs, dict)

def test_create_job_returns_dict(sample_job):
    assert isinstance(sample_job, dict)

def test_create_job_has_required_fields(sample_job):
    required = ["job_id", "job_type", "status", "progress",
                 "created_at", "retry_count", "max_retries"]
    for field in required:
        assert field in sample_job

def test_create_job_starts_pending(sample_job):
    assert sample_job["status"] == JobStatus.PENDING
    assert sample_job["progress"] == 0

def test_create_job_id_not_empty(sample_job):
    assert len(sample_job["job_id"]) > 0

def test_update_status_to_processing(manager, sample_job):
    job_id = sample_job["job_id"]
    updated = manager.update_status(job_id, JobStatus.PROCESSING, 50)
    assert updated["status"]   == JobStatus.PROCESSING
    assert updated["progress"] == 50
    assert updated["started_at"] is not None

def test_update_status_to_completed(manager, sample_job):
    job_id = sample_job["job_id"]
    manager.update_status(job_id, JobStatus.PROCESSING, 50)
    updated = manager.update_status(
        job_id, JobStatus.COMPLETED, 100,
        result_url="/api/v1/ats/candidates/ZCP-CAND-TEST"
    )
    assert updated["status"]       == JobStatus.COMPLETED
    assert updated["progress"]     == 100
    assert updated["completed_at"] is not None
    assert updated["result_url"]   is not None

def test_update_status_calculates_duration(manager, sample_job):
    job_id = sample_job["job_id"]
    manager.update_status(job_id, JobStatus.PROCESSING, 50)
    updated = manager.update_status(job_id, JobStatus.COMPLETED, 100)
    assert updated["duration_seconds"] is not None
    assert updated["duration_seconds"] >= 0

def test_update_status_with_error(manager, sample_job):
    job_id = sample_job["job_id"]
    error  = {"code": "ATS_003", "message": "File corrupted"}
    updated = manager.update_status(job_id, JobStatus.FAILED, error=error)
    assert updated["status"] == JobStatus.FAILED
    assert updated["error"]  == error

def test_get_job_returns_correct(manager, sample_job):
    job_id  = sample_job["job_id"]
    fetched = manager.get_job(job_id)
    assert fetched["job_id"] == job_id

def test_get_job_unknown_returns_empty(manager):
    result = manager.get_job("NONEXISTENT-JOB-ID")
    assert result == {}

def test_get_all_jobs_returns_list(manager, sample_job):
    jobs = manager.get_all_jobs()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1

def test_get_all_jobs_filtered_by_status(manager, sample_job):
    job_id = sample_job["job_id"]
    manager.update_status(job_id, JobStatus.COMPLETED, 100)
    completed = manager.get_all_jobs(status=JobStatus.COMPLETED)
    for j in completed:
        assert j["status"] == JobStatus.COMPLETED


# ── Pipeline Simulation Tests ─────────────────────────────────────────────────

def test_simulate_pipeline_returns_list(manager):
    jobs = manager.simulate_pipeline("ZCP-CAND-TEST", "ZCP-JOB-TEST")
    assert isinstance(jobs, list)
    assert len(jobs) == 3

def test_simulate_pipeline_all_completed(manager):
    jobs = manager.simulate_pipeline("ZCP-CAND-TEST", "ZCP-JOB-TEST")
    for job in jobs:
        fetched = manager.get_job(job["job_id"])
        assert fetched["status"] == JobStatus.COMPLETED

def test_simulate_pipeline_has_result_urls(manager):
    jobs = manager.simulate_pipeline("ZCP-CAND-TEST", "ZCP-JOB-TEST")
    for job in jobs:
        fetched = manager.get_job(job["job_id"])
        assert fetched["result_url"] is not None


# ── Constants Tests ───────────────────────────────────────────────────────────

def test_api_version_defined():
    assert API_VERSION == "v1"

def test_api_base_path_contains_version():
    assert API_VERSION in API_BASE_PATH

def test_error_codes_defined():
    required = ["ATS_001","ATS_002","ATS_003","ATS_004","ATS_005",
                 "ATS_006","ATS_007","ATS_010","ATS_011","ATS_013"]
    for code in required:
        assert code in ERROR_CODES

def test_http_status_codes_defined():
    required = [200, 201, 202, 400, 401, 404, 422, 500]
    for code in required:
        assert code in HTTP_STATUS

def test_supported_file_types_defined():
    assert len(SUPPORTED_FILE_TYPES) >= 2
    assert "application/pdf" in SUPPORTED_FILE_TYPES

def test_max_file_size_reasonable():
    assert 1 <= MAX_FILE_SIZE_MB <= 50

def test_max_batch_size_reasonable():
    assert 1 <= MAX_BATCH_SIZE <= 100

def test_async_job_schema_defined():
    required = ["job_id","job_type","status","progress",
                 "created_at","result_url","error"]
    for field in required:
        assert field in ASYNC_JOB_SCHEMA


# ── Save Output Tests ─────────────────────────────────────────────────────────

def test_save_spec(spec, tmp_path):
    output_file = str(tmp_path / "test_spec.json")
    spec.save_spec(output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert "api_info"    in data
    assert "endpoints"   in data
    assert "error_codes" in data

def test_save_jobs(manager, tmp_path):
    manager.simulate_pipeline("ZCP-CAND-TEST", "ZCP-JOB-TEST")
    output_file = str(tmp_path / "test_jobs.json")
    manager.save_jobs(output_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        data = json.load(f)
    assert len(data) > 0
