"""
Day 7 – Metadata Standards Document Generator
Generates the official metadata standards for Zecpath AI Platform
"""

import json
from datetime import datetime
from pathlib import Path


def generate_metadata_standards() -> dict:
    """Generate complete metadata standards document."""

    return {
        "document": {
            "title":        "Zecpath AI Platform — Metadata Standards",
            "version":      "1.0",
            "created_at":   datetime.now().isoformat(),
            "author":       "AI Recruitment System",
            "status":       "Active",
        },

        "id_standards": {
            "candidate_id": {
                "format":       "ZCP-CAND-YYYYMMDD-XXXX",
                "example":      "ZCP-CAND-20260515-A3F2",
                "description":  "Unique identifier for each candidate",
                "auto_generated": True,
                "immutable":    True,
            },
            "job_id": {
                "format":       "ZCP-JOB-YYYYMMDD-XXXX",
                "example":      "ZCP-JOB-20260515-B7D1",
                "description":  "Unique identifier for each job posting",
                "auto_generated": True,
                "immutable":    True,
            },
            "pipeline_id": {
                "format":       "ZCP-PIPE-XXXXXXXX",
                "example":      "ZCP-PIPE-4A2F8B1C",
                "description":  "Tracks one candidate through one job pipeline",
                "auto_generated": True,
                "immutable":    True,
            },
            "session_id": {
                "format":       "ZCP-SES-XXXXXXXX",
                "example":      "ZCP-SES-9D3E1A2F",
                "description":  "Unique identifier for each interview/screening session",
                "auto_generated": True,
                "immutable":    True,
            },
            "report_id": {
                "format":       "ZCP-RPT-XXXXXXXX",
                "example":      "ZCP-RPT-7C4B2D1E",
                "description":  "Unique identifier for each generated report",
                "auto_generated": True,
                "immutable":    True,
            },
        },

        "model_version_standards": {
            "format":       "module_name_vX.Y",
            "examples": {
                "parser_v2.0":      "Resume Parser version 2.0",
                "ats_v1.0":         "ATS Engine version 1.0",
                "screening_v1.0":   "Screening AI version 1.0",
                "interview_v1.0":   "Interview AI version 1.0",
                "scoring_v1.0":     "Scoring Engine version 1.0",
            },
            "versioning_rules": {
                "major_version":    "Breaking changes or full model retraining",
                "minor_version":    "New features or significant improvements",
                "patch_version":    "Bug fixes or small adjustments",
            },
        },

        "timestamp_standards": {
            "format":       "ISO 8601",
            "example":      "2026-05-15T14:30:00.000000",
            "timezone":     "UTC",
            "fields": {
                "created_at":   "When the record was first created",
                "updated_at":   "When the record was last modified",
                "parsed_at":    "When the resume was parsed",
                "scored_at":    "When ATS scoring was completed",
                "screened_at":  "When screening was completed",
                "interviewed_at": "When interview was conducted",
                "decided_at":   "When hiring decision was made",
            },
        },

        "schema_version_standards": {
            "current_version":  "1.0",
            "format":           "X.Y",
            "description":      "Version of the data schema itself",
            "migration_policy": "Backward compatible for minor versions",
        },

        "data_retention_policy": {
            "active_candidates":    "2 years",
            "hired_candidates":     "5 years",
            "rejected_candidates":  "1 year",
            "archived_data":        "3 years",
            "retraining_datasets":  "Indefinite",
            "interview_recordings": "6 months",
        },

        "privacy_standards": {
            "pii_fields": [
                "full_name", "email", "phone",
                "location", "linkedin_url", "portfolio_url"
            ],
            "anonymization_method":     "SHA-256 hashing for PII in retraining data",
            "gdpr_compliant":           True,
            "data_encryption":          "AES-256",
            "access_control":           "Role-based access control (RBAC)",
        },

        "quality_standards": {
            "parse_confidence_threshold":   0.7,
            "ats_score_range":              "0-100",
            "screening_confidence_range":   "0.0-1.0",
            "required_fields_completion":   "90% minimum",
            "data_validation":              "JSON Schema validation on all records",
        },
    }


def generate_storage_structure() -> dict:
    """Generate complete storage structure documentation."""

    return {
        "document": {
            "title":    "Zecpath AI Platform — Storage Structure",
            "version":  "1.0",
            "created_at": datetime.now().isoformat(),
        },

        "folder_structure": {
            "data/": {
                "resumes/": {
                    "raw/":         "Original uploaded resume files (PDF, DOCX)",
                    "processed/":   "Pre-processed resume files",
                },
                "profiles/": {
                    "parsed/":      "Parsed candidate profiles (JSON)",
                    "enriched/":    "AI-enriched profiles with additional insights",
                },
                "ats_scores/":      "ATS scoring results (JSON)",
                "screening_reports/": "AI screening reports (JSON)",
                "interview_queue/": "Candidates ready for interview",
                "interview_results/": "Interview evaluation results (JSON)",
                "pipeline/":        "Pipeline tracking records (JSON)",
                "hired/":           "Hired candidate records",
                "rejected/":        "Rejected candidate records",
                "archive/":         "Archived old records",
                "sample_jds/":      "Sample job description PDFs",
                "outputs/": {
                    "cleaned/":     "Cleaned resume text files",
                    "parsed_jds.json": "Parsed job descriptions",
                },
                "retraining/": {
                    "parser/":      "Parser retraining datasets",
                    "ats/":         "ATS retraining datasets",
                    "screening/":   "Screening retraining datasets",
                    "interview/":   "Interview retraining datasets",
                },
            },
        },

        "file_naming_conventions": {
            "resumes":          "{candidate_id}_resume.{ext}",
            "parsed_profiles":  "{candidate_id}_profile.json",
            "ats_scores":       "{candidate_id}_{job_id}_ats.json",
            "screening_reports": "{candidate_id}_{job_id}_screening.json",
            "interview_results": "{candidate_id}_{job_id}_{session_id}_interview.json",
            "pipeline_records": "{candidate_id}_pipeline.json",
        },

        "file_formats": {
            "resumes":          ["pdf", "docx", "txt"],
            "profiles":         "json",
            "scores":           "json",
            "reports":          "json",
            "logs":             "txt",
            "retraining_data":  "jsonl",
        },

        "size_limits": {
            "resume_file":          "10 MB",
            "parsed_profile":       "1 MB",
            "ats_score_file":       "500 KB",
            "screening_report":     "1 MB",
            "interview_result":     "5 MB",
            "retraining_batch":     "1 GB",
        },
    }


def save_documentation(output_dir: str = "docs/"):
    """Generate and save all documentation files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save metadata standards
    metadata_standards = generate_metadata_standards()
    metadata_path = Path(output_dir) / "metadata_standards.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_standards, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved metadata standards → {metadata_path}")

    # Save storage structure
    storage_structure = generate_storage_structure()
    storage_path = Path(output_dir) / "storage_structure.json"
    with open(storage_path, "w", encoding="utf-8") as f:
        json.dump(storage_structure, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved storage structure → {storage_path}")

    return metadata_standards, storage_structure


if __name__ == "__main__":
    save_documentation()
