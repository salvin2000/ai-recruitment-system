"""
Day 16 - ATS API Design & Integration Planning
Runner script
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.ats_api import ATSAPISpecification, AsyncJobManager, JobStatus


def run_api_design():
    print("\n" + "=" * 65)
    print("   ZECPATH AI - ATS API DESIGN & INTEGRATION v1.0")
    print("=" * 65)

    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    spec    = ATSAPISpecification()
    manager = AsyncJobManager()

    # ── Step 1: Show API Endpoints ────────────────────────────────────────────
    print("\nStep 1: API Endpoints Defined")
    print("─" * 65)
    for name, ep in spec.get_all_endpoints().items():
        print(f"  {ep['method']:<6} {ep['path']}")
        print(f"         {ep['description']}")

    # ── Step 2: Show Request/Response Contracts ───────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 2: Request/Response Contracts")
    print("─" * 65)

    for ep_name in ["upload_resume", "score_candidate", "shortlist_candidates"]:
        ep = spec.get_endpoint(ep_name)
        print(f"\n  [{ep['method']}] {ep['path']}")
        req = ep.get("request", {})
        if "body" in req:
            required = [k for k, v in req["body"].items()
                        if isinstance(v, dict) and v.get("required")]
            optional = [k for k, v in req["body"].items()
                        if isinstance(v, dict) and not v.get("required")]
            if required: print(f"  Required: {', '.join(required)}")
            if optional: print(f"  Optional: {', '.join(optional)}")
        responses = ep.get("response", {})
        for code, resp in responses.items():
            print(f"  {code}: {resp.get('description', '')}")

    # ── Step 3: Validate Sample Requests ─────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 3: Request Validation")
    print("─" * 65)

    test_cases = [
        ("upload_resume", {"job_id": "ZCP-JOB-001", "file_type": "application/pdf"}, "Valid upload"),
        ("upload_resume", {"file_type": "application/pdf"}, "Missing job_id"),
        ("upload_resume", {"job_id": "ZCP-JOB-001", "file_type": "image/jpeg"}, "Wrong file type"),
        ("score_candidate", {"candidate_id": "ZCP-CAND-001", "job_id": "ZCP-JOB-001",
                              "custom_weights": {"skill_match": 0.5, "experience_relevance": 0.3,
                                                  "education_alignment": 0.1, "semantic_similarity": 0.1}},
         "Valid score with custom weights"),
        ("score_candidate", {"candidate_id": "ZCP-CAND-001", "job_id": "ZCP-JOB-001",
                              "custom_weights": {"skill_match": 0.5, "experience_relevance": 0.5,
                                                  "education_alignment": 0.5, "semantic_similarity": 0.5}},
         "Invalid weights — do not sum to 1.0"),
    ]

    for ep_name, data, label in test_cases:
        result = spec.validate_request(ep_name, data)
        status = "VALID" if result["valid"] else "INVALID"
        print(f"\n  [{status}] {label}")
        if not result["valid"]:
            for err in result["errors"]:
                print(f"    Error: {err}")

    # ── Step 4: Async Job Simulation ──────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 4: Async Job Pipeline Simulation")
    print("─" * 65)

    pipeline_jobs = manager.simulate_pipeline(
        "ZCP-CAND-ARJU", "ZCP-JOB-20260529-SW01"
    )

    for job in pipeline_jobs:
        j = manager.get_job(job["job_id"])
        print(f"\n  Job: {j['job_id']}")
        print(f"  Type      : {j['job_type']}")
        print(f"  Status    : {j['status']}")
        print(f"  Progress  : {j['progress']}%")
        print(f"  Result URL: {j['result_url']}")

    # ── Step 5: Show Error Codes ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("Step 5: Error Code Reference")
    print("─" * 65)
    for code, msg in spec.error_codes.items():
        print(f"  {code}: {msg}")

    # ── Save Outputs ──────────────────────────────────────────────────────────
    spec.save_spec("data/outputs/ats_api_specification.json")
    manager.save_jobs("data/outputs/async_jobs_log.json")

    print("\n" + "=" * 65)
    print("API design and integration planning complete!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_api_design()
