"""
Day 16 – ATS API Design & Integration Planning
Zecpath AI Recruitment Platform

Designs REST API specifications, request/response contracts,
async job handling, and error/logging standards for the ATS AI system.
"""

import json
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional


# ── API Version ───────────────────────────────────────────────────────────────

API_VERSION    = "v1"
API_BASE_PATH  = f"/api/{API_VERSION}/ats"

# ── HTTP Status Codes ─────────────────────────────────────────────────────────

HTTP_STATUS = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

# ── Job Status ────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    CANCELLED  = "cancelled"

# ── Supported File Types ──────────────────────────────────────────────────────

SUPPORTED_FILE_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE_MB     = 5
MAX_BATCH_SIZE       = 50

# ── API Endpoint Definitions ──────────────────────────────────────────────────

API_ENDPOINTS = {

    # ── Resume Upload ─────────────────────────────────────────────────────────
    "upload_resume": {
        "method":      "POST",
        "path":        f"{API_BASE_PATH}/resumes/upload",
        "description": "Upload a resume file for processing. Returns a job_id for tracking.",
        "auth":        "Bearer token required",
        "request": {
            "content_type": "multipart/form-data",
            "fields": {
                "file":        {"type": "file",   "required": True,  "description": "PDF or DOCX resume file, max 5MB"},
                "job_id":      {"type": "string", "required": True,  "description": "Job posting ID to match against"},
                "role_type":   {"type": "string", "required": False, "description": "Role type for weight profile selection"},
                "candidate_id":{"type": "string", "required": False, "description": "Candidate ID — auto-generated if not provided"},
            }
        },
        "response": {
            "201": {
                "description": "Resume uploaded successfully. Processing job queued.",
                "schema": {
                    "job_id":        "ZCP-JOB-20260607-A1B2",
                    "candidate_id":  "ZCP-CAND-20260607-C3D4",
                    "status":        "pending",
                    "upload_time":   "2026-06-07T10:00:00Z",
                    "estimated_time_seconds": 30,
                    "tracking_url":  "/api/v1/ats/jobs/ZCP-JOB-20260607-A1B2/status",
                }
            },
            "400": {"description": "Invalid file type or missing required fields"},
            "413": {"description": "File exceeds 5MB size limit"},
            "422": {"description": "File is corrupted or cannot be parsed"},
        }
    },

    # ── Parse Resume ──────────────────────────────────────────────────────────
    "parse_resume": {
        "method":      "POST",
        "path":        f"{API_BASE_PATH}/resumes/{{candidate_id}}/parse",
        "description": "Trigger full parsing pipeline — extract skills, experience, education. Async operation.",
        "auth":        "Bearer token required",
        "request": {
            "content_type": "application/json",
            "body": {
                "candidate_id":    {"type": "string", "required": True},
                "job_id":          {"type": "string", "required": True},
                "pipeline_stages": {"type": "array",  "required": False,
                                    "description": "Stages to run: skills, experience, education, semantic, bias",
                                    "default": ["skills", "experience", "education", "semantic"]},
            }
        },
        "response": {
            "202": {
                "description": "Parsing job accepted. Returns job_id for status tracking.",
                "schema": {
                    "job_id":      "ZCP-PARSE-20260607-E5F6",
                    "candidate_id":"ZCP-CAND-20260607-C3D4",
                    "status":      "processing",
                    "stages":      ["skills", "experience", "education", "semantic"],
                    "tracking_url":"/api/v1/ats/jobs/ZCP-PARSE-20260607-E5F6/status",
                }
            },
            "404": {"description": "Candidate not found"},
            "409": {"description": "Parsing already in progress for this candidate"},
        }
    },

    # ── Score Candidate ───────────────────────────────────────────────────────
    "score_candidate": {
        "method":      "POST",
        "path":        f"{API_BASE_PATH}/candidates/{{candidate_id}}/score",
        "description": "Run ATS scoring formula for a candidate against a job. Requires parsing to be completed first.",
        "auth":        "Bearer token required",
        "request": {
            "content_type": "application/json",
            "body": {
                "candidate_id":    {"type": "string", "required": True},
                "job_id":          {"type": "string", "required": True},
                "role_type":       {"type": "string", "required": False, "default": "default"},
                "custom_weights":  {"type": "object", "required": False,
                                    "description": "Override default weight profile",
                                    "schema": {
                                        "skill_match":          "float 0-1",
                                        "experience_relevance": "float 0-1",
                                        "education_alignment":  "float 0-1",
                                        "semantic_similarity":  "float 0-1",
                                    }},
            }
        },
        "response": {
            "200": {
                "description": "Scoring completed. Returns full score breakdown.",
                "schema": {
                    "candidate_id":   "ZCP-CAND-20260607-C3D4",
                    "job_id":         "ZCP-JOB-20260529-SW01",
                    "final_score":    79.87,
                    "grade":          "B+",
                    "recommendation": "Likely Hire - Proceed to Technical Interview",
                    "component_scores": {
                        "skill_match":          {"raw_score": 0.675, "weighted_score": 23.62},
                        "experience_relevance": {"raw_score": 0.850, "weighted_score": 25.50},
                        "education_alignment":  {"raw_score": 1.000, "weighted_score": 15.00},
                        "semantic_similarity":  {"raw_score": 0.788, "weighted_score": 15.75},
                    },
                    "strengths": ["Experience Relevance: 85.0%"],
                    "gaps":      [],
                    "scored_at": "2026-06-07T10:00:30Z",
                }
            },
            "404": {"description": "Candidate or job not found"},
            "412": {"description": "Parsing not completed for this candidate"},
        }
    },

    # ── Shortlist Candidates ──────────────────────────────────────────────────
    "shortlist_candidates": {
        "method":      "POST",
        "path":        f"{API_BASE_PATH}/jobs/{{job_id}}/shortlist",
        "description": "Run ranking and shortlisting for all candidates of a job. Returns ranked list with zone classification.",
        "auth":        "Bearer token required",
        "request": {
            "content_type": "application/json",
            "body": {
                "job_id":      {"type": "string", "required": True},
                "role_type":   {"type": "string", "required": False, "default": "default"},
                "thresholds":  {"type": "object", "required": False,
                                "description": "Override default zone thresholds",
                                "schema": {
                                    "auto_shortlist": "int",
                                    "manual_review":  "int",
                                    "auto_reject":    "int",
                                }},
                "top_n":       {"type": "int", "required": False, "default": 10,
                                "description": "Return top N candidates only"},
            }
        },
        "response": {
            "200": {
                "description": "Shortlisting completed. Returns ranked candidate list.",
                "schema": {
                    "job_id":   "ZCP-JOB-20260529-SW01",
                    "summary": {
                        "total_candidates":  6,
                        "shortlisted_count": 2,
                        "review_count":      1,
                        "rejected_count":    3,
                        "shortlist_rate":    33.3,
                        "avg_score":         53.78,
                    },
                    "shortlisted": [
                        {"rank": 1, "candidate_id": "ZCP-CAND-ARJU",
                         "score": 82.24, "grade": "A", "zone": "shortlisted"},
                    ],
                    "review":    [],
                    "rejected":  [],
                    "generated_at": "2026-06-07T10:01:00Z",
                }
            },
            "404": {"description": "Job not found"},
            "412": {"description": "No scored candidates found for this job"},
        }
    },

    # ── Get Job Status ────────────────────────────────────────────────────────
    "get_job_status": {
        "method":      "GET",
        "path":        f"{API_BASE_PATH}/jobs/{{job_id}}/status",
        "description": "Poll the status of any async job — upload, parse, score, or shortlist.",
        "auth":        "Bearer token required",
        "request": {
            "path_params": {"job_id": "string — the job tracking ID"}
        },
        "response": {
            "200": {
                "description": "Job status returned.",
                "schema": {
                    "job_id":      "ZCP-JOB-20260607-A1B2",
                    "job_type":    "parse_resume",
                    "status":      "completed",
                    "progress":    100,
                    "started_at":  "2026-06-07T10:00:05Z",
                    "completed_at":"2026-06-07T10:00:28Z",
                    "duration_seconds": 23,
                    "result_url":  "/api/v1/ats/candidates/ZCP-CAND-C3D4/score",
                    "error":       None,
                }
            },
            "404": {"description": "Job not found"},
        }
    },

    # ── Get Candidate Profile ─────────────────────────────────────────────────
    "get_candidate": {
        "method":      "GET",
        "path":        f"{API_BASE_PATH}/candidates/{{candidate_id}}",
        "description": "Retrieve full structured candidate profile including parsed skills, experience, education.",
        "auth":        "Bearer token required",
        "response": {
            "200": {
                "schema": {
                    "candidate_id":    "ZCP-CAND-ARJU",
                    "parsed_at":       "2026-06-07T10:00:28Z",
                    "skills":          ["python", "django", "aws"],
                    "experience_years":3.9,
                    "highest_degree":  "b.tech",
                    "certifications":  2,
                    "bias_risk":       "Medium",
                }
            },
            "404": {"description": "Candidate not found"},
        }
    },

    # ── Batch Upload ──────────────────────────────────────────────────────────
    "batch_upload": {
        "method":      "POST",
        "path":        f"{API_BASE_PATH}/resumes/batch",
        "description": "Upload up to 50 resumes at once. Returns a batch_job_id for tracking all uploads.",
        "auth":        "Bearer token required",
        "request": {
            "content_type": "multipart/form-data",
            "fields": {
                "files":     {"type": "file[]",  "required": True,  "description": "Up to 50 PDF or DOCX files"},
                "job_id":    {"type": "string",  "required": True},
                "role_type": {"type": "string",  "required": False},
            }
        },
        "response": {
            "202": {
                "schema": {
                    "batch_job_id":     "ZCP-BATCH-20260607-G7H8",
                    "total_files":      10,
                    "accepted_files":   10,
                    "rejected_files":   0,
                    "status":           "processing",
                    "tracking_url":     "/api/v1/ats/jobs/ZCP-BATCH-20260607-G7H8/status",
                }
            },
        }
    },
}

# ── Error Response Schema ─────────────────────────────────────────────────────

ERROR_RESPONSE_SCHEMA = {
    "error": {
        "code":      "ATS_001",
        "message":   "Human-readable error description",
        "field":     "The field that caused the error (if applicable)",
        "timestamp": "2026-06-07T10:00:00Z",
        "request_id":"REQ-20260607-X9Y0",
    }
}

# ── Error Codes ───────────────────────────────────────────────────────────────

ERROR_CODES = {
    "ATS_001": "Invalid file type. Only PDF and DOCX are supported.",
    "ATS_002": "File size exceeds 5MB limit.",
    "ATS_003": "Resume text extraction failed. File may be corrupted.",
    "ATS_004": "Candidate not found in the system.",
    "ATS_005": "Job posting not found in the system.",
    "ATS_006": "Parsing not completed. Cannot score before parsing.",
    "ATS_007": "Scoring not completed. Cannot shortlist before scoring.",
    "ATS_008": "Async job not found or expired.",
    "ATS_009": "Batch size exceeds 50 file limit.",
    "ATS_010": "Authentication token invalid or expired.",
    "ATS_011": "Rate limit exceeded. Maximum 100 requests per minute.",
    "ATS_012": "Parsing already in progress for this candidate.",
    "ATS_013": "Invalid weight profile. Weights must sum to 1.0.",
    "ATS_014": "No candidates found for this job posting.",
    "ATS_015": "Service temporarily unavailable. Retry after 60 seconds.",
}

# ── Async Job Schema ──────────────────────────────────────────────────────────

ASYNC_JOB_SCHEMA = {
    "job_id":           "string — unique job tracking ID",
    "job_type":         "string — upload | parse | score | shortlist | batch",
    "candidate_id":     "string — candidate being processed",
    "job_posting_id":   "string — job posting being matched against",
    "status":           "string — pending | processing | completed | failed | cancelled",
    "progress":         "int — 0 to 100 percent completion",
    "created_at":       "ISO datetime",
    "started_at":       "ISO datetime or null",
    "completed_at":     "ISO datetime or null",
    "duration_seconds": "int or null",
    "result_url":       "string — URL to fetch result when completed",
    "error":            "object or null — error details if failed",
    "retry_count":      "int — number of retries attempted",
    "max_retries":      3,
}

# ── Logging Standards ─────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

LOG_LEVELS = {
    "INFO":    "Normal operations — resume uploaded, job queued, scoring completed",
    "WARNING": "Potential issues — file size near limit, slow processing, retries",
    "ERROR":   "Failures — extraction failed, scoring error, job timed out",
    "DEBUG":   "Detailed tracing — individual parsing steps, score calculations",
}

LOG_EVENT_TEMPLATES = {
    "upload":    "UPLOAD | candidate={candidate_id} job={job_id} size={size_kb}KB status={status}",
    "parse":     "PARSE  | candidate={candidate_id} stage={stage} duration={duration}ms",
    "score":     "SCORE  | candidate={candidate_id} job={job_id} score={score} grade={grade}",
    "shortlist": "SHORTLIST | job={job_id} total={total} shortlisted={shortlisted} rejected={rejected}",
    "error":     "ERROR  | code={error_code} candidate={candidate_id} message={message}",
    "job_queue": "JOB    | job_id={job_id} type={job_type} status={status} duration={duration}s",
}


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up a structured logger for an ATS module."""
    logger  = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


class ATSAPISpecification:
    """
    Defines and validates the complete ATS API specification.
    Generates request/response schemas and integration flow documentation.
    """

    def __init__(self):
        self.version    = API_VERSION
        self.base_path  = API_BASE_PATH
        self.endpoints  = API_ENDPOINTS
        self.error_codes= ERROR_CODES
        self.logger     = setup_logger("ATSAPISpecification")

    def get_endpoint(self, name: str) -> dict:
        """Get the full specification for a named endpoint."""
        return self.endpoints.get(name, {})

    def get_all_endpoints(self) -> dict:
        """Get all endpoint specifications."""
        return self.endpoints

    def validate_request(self,
                          endpoint_name: str,
                          request_data: dict) -> dict:
        """
        Validate a request against the endpoint specification.
        Returns validation result with any errors found.
        """
        endpoint = self.get_endpoint(endpoint_name)
        if not endpoint:
            return {"valid": False, "errors": [f"Unknown endpoint: {endpoint_name}"]}

        errors     = []
        req_schema = endpoint.get("request", {})
        body_schema= req_schema.get("body", {})

        # Check required fields from body OR fields schema
        fields_schema = req_schema.get("fields", {})
        combined = {**body_schema, **fields_schema}
        for field, spec in combined.items():
            if isinstance(spec, dict) and spec.get("required", False) and field != "file":
                if field not in request_data:
                    errors.append(f"Missing required field: {field}")

        # Validate file type for upload endpoints
        file_type = request_data.get("file_type", "")
        if file_type and file_type not in SUPPORTED_FILE_TYPES:
            errors.append("ATS_001: " + ERROR_CODES["ATS_001"])

        # Validate custom weights
        if "custom_weights" in request_data:
            weights = request_data["custom_weights"]
            total   = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                errors.append(f"ATS_013: {ERROR_CODES['ATS_013']}")

        return {"valid": len(errors) == 0, "errors": errors}

    def generate_api_spec_json(self) -> dict:
        """Generate the full API specification as a structured JSON document."""
        return {
            "api_info": {
                "title":       "Zecpath ATS AI REST API",
                "version":     self.version,
                "base_path":   self.base_path,
                "description": "REST API for the Zecpath AI Recruitment System ATS pipeline",
                "generated_at":datetime.now().isoformat(),
            },
            "authentication": {
                "type":        "Bearer Token",
                "header":      "Authorization: Bearer <token>",
                "description": "All endpoints require a valid JWT Bearer token",
            },
            "endpoints":      self.endpoints,
            "error_codes":    self.error_codes,
            "async_job_schema": ASYNC_JOB_SCHEMA,
            "logging_standards": {
                "format":      LOG_FORMAT,
                "levels":      LOG_LEVELS,
                "templates":   LOG_EVENT_TEMPLATES,
            },
            "limits": {
                "max_file_size_mb":  MAX_FILE_SIZE_MB,
                "max_batch_size":    MAX_BATCH_SIZE,
                "rate_limit":        "100 requests per minute per API key",
                "job_ttl_hours":     24,
                "max_retries":       3,
            },
        }

    def save_spec(self, output_path: str):
        """Save full API specification to JSON file."""
        spec = self.generate_api_spec_json()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"Saved -> {output_path}")


class AsyncJobManager:
    """
    Manages async job lifecycle for the ATS pipeline.
    Tracks job status, handles retries, and generates tracking IDs.
    """

    def __init__(self):
        self.jobs   = {}
        self.logger = setup_logger("AsyncJobManager")

    def create_job(self,
                   job_type: str,
                   candidate_id: str = "",
                   job_posting_id: str = "") -> dict:
        """Create a new async job and return its tracking record."""
        job_id = f"ZCP-{job_type.upper()[:5]}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        job = {
            "job_id":           job_id,
            "job_type":         job_type,
            "candidate_id":     candidate_id,
            "job_posting_id":   job_posting_id,
            "status":           JobStatus.PENDING,
            "progress":         0,
            "created_at":       datetime.now().isoformat(),
            "started_at":       None,
            "completed_at":     None,
            "duration_seconds": None,
            "result_url":       None,
            "error":            None,
            "retry_count":      0,
            "max_retries":      3,
        }
        self.jobs[job_id] = job
        self.logger.info(
            LOG_EVENT_TEMPLATES["job_queue"].format(
                job_id=job_id, job_type=job_type,
                status="pending", duration=0
            )
        )
        return job

    def update_status(self,
                       job_id: str,
                       status: JobStatus,
                       progress: int = None,
                       result_url: str = None,
                       error: dict = None) -> dict:
        """Update the status of an existing job."""
        if job_id not in self.jobs:
            return {}

        job = self.jobs[job_id]
        job["status"]   = status

        if progress is not None:
            job["progress"] = progress

        if status == JobStatus.PROCESSING and not job["started_at"]:
            job["started_at"] = datetime.now().isoformat()

        if status in (JobStatus.COMPLETED, JobStatus.FAILED):
            job["completed_at"] = datetime.now().isoformat()
            if job["started_at"]:
                start = datetime.fromisoformat(job["started_at"])
                end   = datetime.fromisoformat(job["completed_at"])
                job["duration_seconds"] = round((end - start).total_seconds(), 2)

        if result_url:
            job["result_url"] = result_url

        if error:
            job["error"] = error

        return job

    def get_job(self, job_id: str) -> dict:
        """Get a job by its tracking ID."""
        return self.jobs.get(job_id, {})

    def get_all_jobs(self, status: str = None) -> list:
        """Get all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        return jobs

    def simulate_pipeline(self,
                           candidate_id: str,
                           job_posting_id: str) -> list:
        """
        Simulate a complete ATS pipeline run for demonstration.
        Creates and updates jobs for each pipeline stage.
        """
        pipeline_jobs = []

        # Stage 1: Upload
        upload_job = self.create_job("upload", candidate_id, job_posting_id)
        self.update_status(upload_job["job_id"], JobStatus.PROCESSING, 50)
        self.update_status(upload_job["job_id"], JobStatus.COMPLETED, 100,
                           result_url=f"/api/v1/ats/candidates/{candidate_id}")
        pipeline_jobs.append(upload_job)

        # Stage 2: Parse
        parse_job = self.create_job("parse", candidate_id, job_posting_id)
        self.update_status(parse_job["job_id"], JobStatus.PROCESSING, 25)
        self.update_status(parse_job["job_id"], JobStatus.PROCESSING, 75)
        self.update_status(parse_job["job_id"], JobStatus.COMPLETED, 100,
                           result_url=f"/api/v1/ats/candidates/{candidate_id}/profile")
        pipeline_jobs.append(parse_job)

        # Stage 3: Score
        score_job = self.create_job("score", candidate_id, job_posting_id)
        self.update_status(score_job["job_id"], JobStatus.PROCESSING, 50)
        self.update_status(score_job["job_id"], JobStatus.COMPLETED, 100,
                           result_url=f"/api/v1/ats/candidates/{candidate_id}/score")
        pipeline_jobs.append(score_job)

        return pipeline_jobs

    def save_jobs(self, output_path: str):
        """Save all job records to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.jobs, f, indent=2, default=str, ensure_ascii=False)
        print(f"Saved -> {output_path}")
