"""
Day 7 – AI Data Pipeline & Storage Design
Zecpath AI Recruitment Platform
Defines storage formats, metadata standards, and data lifecycle.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class DataStage(Enum):
    UPLOADED        = "uploaded"
    PARSED          = "parsed"
    ATS_SCORED      = "ats_scored"
    SCREENED        = "screened"
    INTERVIEW_READY = "interview_ready"
    INTERVIEWED     = "interviewed"
    HIRED           = "hired"
    REJECTED        = "rejected"
    ARCHIVED        = "archived"


class ModelVersion(Enum):
    PARSER_V1       = "parser_v1.0"
    PARSER_V2       = "parser_v2.0"
    ATS_V1          = "ats_v1.0"
    SCREENING_V1    = "screening_v1.0"
    INTERVIEW_V1    = "interview_v1.0"
    SCORING_V1      = "scoring_v1.0"


# ── ID Generators ─────────────────────────────────────────────────────────────

def generate_candidate_id() -> str:
    """Generate unique Candidate ID: ZCP-CAND-YYYYMMDD-XXXX"""
    date = datetime.now().strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:4].upper()
    return f"ZCP-CAND-{date}-{unique}"


def generate_job_id() -> str:
    """Generate unique Job ID: ZCP-JOB-YYYYMMDD-XXXX"""
    date = datetime.now().strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:4].upper()
    return f"ZCP-JOB-{date}-{unique}"


def generate_session_id() -> str:
    """Generate unique Session ID for interview/screening."""
    return f"ZCP-SES-{str(uuid.uuid4())[:8].upper()}"


def generate_report_id() -> str:
    """Generate unique Report ID."""
    return f"ZCP-RPT-{str(uuid.uuid4())[:8].upper()}"


# ── Metadata Standards ────────────────────────────────────────────────────────

def create_base_metadata(
    candidate_id: str,
    job_id: str,
    model_version: str,
    stage: DataStage,
    created_by: str = "system"
) -> dict:
    """
    Create standard metadata block used across all AI data objects.

    Args:
        candidate_id: Unique candidate identifier
        job_id: Unique job identifier
        model_version: AI model version used
        stage: Current data lifecycle stage
        created_by: Who created this record

    Returns:
        dict: Standard metadata block
    """
    now = datetime.now().isoformat()
    return {
        "candidate_id":   candidate_id,
        "job_id":         job_id,
        "model_version":  model_version,
        "stage":          stage.value,
        "created_at":     now,
        "updated_at":     now,
        "created_by":     created_by,
        "schema_version": "1.0",
        "platform":       "Zecpath AI Recruitment",
    }


# ── Storage Format Definitions ────────────────────────────────────────────────

def create_resume_storage(
    candidate_id: str,
    job_id: str,
    file_name: str,
    file_type: str,
    raw_text: str = "",
    file_size_kb: float = 0.0
) -> dict:
    """
    Storage format for uploaded resumes.

    Stage: UPLOADED → PARSED
    Location: data/resumes/raw/
    """
    return {
        "metadata": create_base_metadata(
            candidate_id, job_id,
            ModelVersion.PARSER_V1.value,
            DataStage.UPLOADED
        ),
        "resume": {
            "file_name":    file_name,
            "file_type":    file_type,  # pdf, docx, txt
            "file_size_kb": file_size_kb,
            "upload_path":  f"data/resumes/raw/{candidate_id}/{file_name}",
            "raw_text":     raw_text,
            "page_count":   0,
            "language":     "en",
            "is_parsed":    False,
        },
        "processing": {
            "parse_attempts": 0,
            "last_error":     None,
            "processing_time_ms": 0,
        }
    }


def create_parsed_profile(
    candidate_id: str,
    job_id: str,
    raw_resume: dict
) -> dict:
    """
    Storage format for parsed candidate profiles.

    Stage: PARSED
    Location: data/profiles/parsed/
    """
    return {
        "metadata": create_base_metadata(
            candidate_id, job_id,
            ModelVersion.PARSER_V2.value,
            DataStage.PARSED
        ),
        "personal_info": {
            "full_name":    "",
            "email":        "",
            "phone":        "",
            "location":     "",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        "professional_summary": "",
        "skills": {
            "technical":    [],
            "soft":         [],
            "tools":        [],
            "languages":    [],
            "certifications": [],
        },
        "experience": {
            "total_years":  0,
            "positions": [
                {
                    "title":        "",
                    "company":      "",
                    "start_date":   "",
                    "end_date":     "",
                    "duration_months": 0,
                    "responsibilities": [],
                    "achievements": [],
                }
            ],
        },
        "education": [
            {
                "degree":       "",
                "field":        "",
                "institution":  "",
                "year":         "",
                "grade":        "",
            }
        ],
        "source_resume": {
            "candidate_id": candidate_id,
            "file_name":    raw_resume.get("resume", {}).get("file_name", ""),
            "parsed_at":    datetime.now().isoformat(),
        },
        "parse_confidence": 0.0,  # 0.0 to 1.0
    }


def create_ats_score(
    candidate_id: str,
    job_id: str,
    parsed_profile: dict,
    jd_profile: dict
) -> dict:
    """
    Storage format for ATS scoring results.

    Stage: ATS_SCORED
    Location: data/ats_scores/
    """
    return {
        "metadata": create_base_metadata(
            candidate_id, job_id,
            ModelVersion.ATS_V1.value,
            DataStage.ATS_SCORED
        ),
        "ats_result": {
            "overall_score":      0.0,   # 0-100
            "skill_match_score":  0.0,   # 0-100
            "experience_score":   0.0,   # 0-100
            "education_score":    0.0,   # 0-100
            "keyword_score":      0.0,   # 0-100
            "grade":              "",    # A, B, C, D, F
            "recommendation":     "",    # PROCEED, REVIEW, REJECT
        },
        "skill_analysis": {
            "required_skills":    jd_profile.get("required_skills", []),
            "candidate_skills":   parsed_profile.get("skills", {}).get("technical", []),
            "matched_skills":     [],
            "missing_skills":     [],
            "match_percentage":   0.0,
        },
        "experience_analysis": {
            "required_years":     jd_profile.get("experience", {}).get("min_years", 0),
            "candidate_years":    parsed_profile.get("experience", {}).get("total_years", 0),
            "meets_requirement":  False,
        },
        "education_analysis": {
            "required_degree":    jd_profile.get("education", {}).get("min_degree", ""),
            "candidate_degree":   "",
            "meets_requirement":  False,
        },
        "job_reference": {
            "job_id":       job_id,
            "role_name":    jd_profile.get("role_name", ""),
            "domain":       jd_profile.get("domain", ""),
        },
    }


def create_screening_report(
    candidate_id: str,
    job_id: str,
    ats_score: dict
) -> dict:
    """
    Storage format for AI screening reports.

    Stage: SCREENED
    Location: data/screening_reports/
    """
    report_id = generate_report_id()
    return {
        "metadata": create_base_metadata(
            candidate_id, job_id,
            ModelVersion.SCREENING_V1.value,
            DataStage.SCREENED
        ),
        "report_id": report_id,
        "screening_result": {
            "status":           "",     # SHORTLISTED, HOLD, REJECTED
            "confidence":       0.0,    # 0.0 to 1.0
            "screening_score":  0.0,    # 0-100
            "rank":             0,      # Rank among all candidates for this job
        },
        "ai_analysis": {
            "strengths":        [],
            "weaknesses":       [],
            "red_flags":        [],
            "key_observations": [],
        },
        "criteria_evaluation": {
            "skill_fit":        False,
            "experience_fit":   False,
            "education_fit":    False,
            "culture_fit":      None,   # Optional
            "salary_fit":       None,   # Optional
        },
        "ats_reference": {
            "ats_score":        ats_score.get("ats_result", {}).get("overall_score", 0),
            "grade":            ats_score.get("ats_result", {}).get("grade", ""),
        },
        "next_action":          "",     # SCHEDULE_INTERVIEW, SEND_REJECTION, ON_HOLD
    }


def create_interview_result(
    candidate_id: str,
    job_id: str,
    interview_type: str = "technical"
) -> dict:
    """
    Storage format for interview results.

    Stage: INTERVIEWED
    Location: data/interview_results/
    """
    session_id = generate_session_id()
    return {
        "metadata": create_base_metadata(
            candidate_id, job_id,
            ModelVersion.INTERVIEW_V1.value,
            DataStage.INTERVIEWED
        ),
        "session_id":       session_id,
        "interview_type":   interview_type,  # technical, hr, managerial
        "interview_details": {
            "scheduled_at":     "",
            "conducted_at":     "",
            "duration_minutes": 0,
            "interviewer_id":   "",
            "mode":             "",  # online, offline, hybrid
        },
        "questions_asked": [
            {
                "question_id":  "",
                "question":     "",
                "category":     "",  # technical, behavioral, situational
                "answer":       "",
                "ai_score":     0.0,
                "feedback":     "",
            }
        ],
        "evaluation": {
            "technical_score":      0.0,  # 0-100
            "communication_score":  0.0,  # 0-100
            "problem_solving_score":0.0,  # 0-100
            "cultural_fit_score":   0.0,  # 0-100
            "overall_score":        0.0,  # 0-100
            "recommendation":       "",   # HIRE, NEXT_ROUND, REJECT
        },
        "ai_summary":       "",
        "interviewer_notes": "",
    }


# ── Data Lifecycle Manager ────────────────────────────────────────────────────

class DataLifecycleManager:
    """
    Manages the complete lifecycle of candidate data from
    upload to hiring decision on the Zecpath platform.
    """

    LIFECYCLE_STAGES = [
        DataStage.UPLOADED,
        DataStage.PARSED,
        DataStage.ATS_SCORED,
        DataStage.SCREENED,
        DataStage.INTERVIEW_READY,
        DataStage.INTERVIEWED,
        DataStage.HIRED,
    ]

    STORAGE_PATHS = {
        DataStage.UPLOADED:         "data/resumes/raw/",
        DataStage.PARSED:           "data/profiles/parsed/",
        DataStage.ATS_SCORED:       "data/ats_scores/",
        DataStage.SCREENED:         "data/screening_reports/",
        DataStage.INTERVIEW_READY:  "data/interview_queue/",
        DataStage.INTERVIEWED:      "data/interview_results/",
        DataStage.HIRED:            "data/hired/",
        DataStage.REJECTED:         "data/rejected/",
        DataStage.ARCHIVED:         "data/archive/",
    }

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)

    def get_next_stage(self, current_stage: DataStage) -> DataStage:
        """Get the next stage in the lifecycle."""
        try:
            idx = self.LIFECYCLE_STAGES.index(current_stage)
            if idx < len(self.LIFECYCLE_STAGES) - 1:
                return self.LIFECYCLE_STAGES[idx + 1]
        except ValueError:
            pass
        return DataStage.ARCHIVED

    def get_storage_path(self, stage: DataStage, candidate_id: str) -> str:
        """Get storage path for a candidate at a given stage."""
        base = self.STORAGE_PATHS.get(stage, "data/unknown/")
        return f"{base}{candidate_id}/"

    def create_pipeline_record(
        self,
        candidate_id: str,
        job_id: str
    ) -> dict:
        """Create a complete pipeline tracking record for a candidate."""
        now = datetime.now().isoformat()
        return {
            "pipeline_id":    f"ZCP-PIPE-{str(uuid.uuid4())[:8].upper()}",
            "candidate_id":   candidate_id,
            "job_id":         job_id,
            "created_at":     now,
            "updated_at":     now,
            "current_stage":  DataStage.UPLOADED.value,
            "stage_history": [
                {
                    "stage":      DataStage.UPLOADED.value,
                    "entered_at": now,
                    "exited_at":  None,
                    "duration_hours": None,
                    "triggered_by": "candidate_upload",
                }
            ],
            "scores": {
                "ats_score":        None,
                "screening_score":  None,
                "interview_score":  None,
                "final_score":      None,
            },
            "decisions": {
                "ats_decision":         None,
                "screening_decision":   None,
                "interview_decision":   None,
                "final_decision":       None,
                "decision_maker":       None,
                "decision_date":        None,
            },
            "versioning": {
                "parser_version":       ModelVersion.PARSER_V2.value,
                "ats_version":          ModelVersion.ATS_V1.value,
                "screening_version":    ModelVersion.SCREENING_V1.value,
                "interview_version":    ModelVersion.INTERVIEW_V1.value,
            },
            "retraining_flags": {
                "flag_for_retraining":  False,
                "reason":               None,
                "flagged_at":           None,
            },
        }

    def advance_stage(
        self,
        pipeline_record: dict,
        new_stage: DataStage,
        triggered_by: str = "system"
    ) -> dict:
        """Advance a candidate to the next pipeline stage."""
        now = datetime.now().isoformat()

        # Close current stage
        if pipeline_record["stage_history"]:
            pipeline_record["stage_history"][-1]["exited_at"] = now

        # Add new stage
        pipeline_record["stage_history"].append({
            "stage":        new_stage.value,
            "entered_at":   now,
            "exited_at":    None,
            "duration_hours": None,
            "triggered_by": triggered_by,
        })

        pipeline_record["current_stage"] = new_stage.value
        pipeline_record["updated_at"] = now

        return pipeline_record

    def flag_for_retraining(
        self,
        pipeline_record: dict,
        reason: str
    ) -> dict:
        """Flag a candidate record for AI model retraining."""
        pipeline_record["retraining_flags"] = {
            "flag_for_retraining":  True,
            "reason":               reason,
            "flagged_at":           datetime.now().isoformat(),
        }
        return pipeline_record

    def save_pipeline_record(
        self,
        pipeline_record: dict,
        output_dir: str = "data/pipeline/"
    ):
        """Save pipeline record to JSON file."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        candidate_id = pipeline_record["candidate_id"]
        output_path = Path(output_dir) / f"{candidate_id}_pipeline.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_record, f, indent=2, ensure_ascii=False)

        return str(output_path)


# ── Versioning & Retraining Dataset Design ────────────────────────────────────

def create_retraining_dataset_schema() -> dict:
    """
    Define schema for versioning and retraining datasets.
    Used to improve AI models over time.
    """
    return {
        "dataset_id":       f"ZCP-DS-{str(uuid.uuid4())[:8].upper()}",
        "created_at":       datetime.now().isoformat(),
        "version":          "1.0",
        "description":      "Zecpath AI Retraining Dataset",
        "schema": {
            "resume_parser_dataset": {
                "input":    "raw_resume_text",
                "output":   "parsed_profile_json",
                "size":     0,
                "format":   "jsonl",
                "path":     "data/retraining/parser/",
            },
            "ats_scoring_dataset": {
                "input":    "parsed_profile + jd_profile",
                "output":   "ats_score + human_verified_score",
                "size":     0,
                "format":   "jsonl",
                "path":     "data/retraining/ats/",
            },
            "screening_dataset": {
                "input":    "ats_score + parsed_profile",
                "output":   "screening_decision + outcome",
                "size":     0,
                "format":   "jsonl",
                "path":     "data/retraining/screening/",
            },
            "interview_dataset": {
                "input":    "questions + answers",
                "output":   "scores + hire_decision",
                "size":     0,
                "format":   "jsonl",
                "path":     "data/retraining/interview/",
            },
        },
        "versioning_policy": {
            "retrain_threshold":        100,   # Retrain after 100 new records
            "model_update_frequency":   "monthly",
            "validation_split":         0.2,
            "test_split":               0.1,
            "min_accuracy_threshold":   0.85,
        },
        "data_quality_rules": {
            "min_confidence_score":     0.7,
            "require_human_validation": True,
            "exclude_flagged_records":  True,
            "anonymize_pii":            True,
        },
    }
