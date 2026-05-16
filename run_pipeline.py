import json
import sys
from pathlib import Path
from pipeline.data_pipeline import DataLifecycleManager, DataStage, generate_candidate_id, generate_job_id

def run_pipeline_demo(output_dir="data/pipeline/"):
    print("\n" + "="*55)
    print("   ZECPATH AI — DATA PIPELINE DEMO")
    print("="*55)
    candidate_id = generate_candidate_id()
    job_id = generate_job_id()
    print(f"\nCandidate ID : {candidate_id}")
    print(f"Job ID       : {job_id}")
    manager = DataLifecycleManager()
    pipeline = manager.create_pipeline_record(candidate_id, job_id)
    for stage in [DataStage.PARSED, DataStage.ATS_SCORED, DataStage.SCREENED, DataStage.HIRED]:
        pipeline = manager.advance_stage(pipeline, stage)
    pipeline["decisions"]["final_decision"] = "HIRED"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = manager.save_pipeline_record(pipeline, output_dir)
    print(f"\nFinal Stage  : {pipeline['current_stage']}")
    print(f"Decision     : {pipeline['decisions']['final_decision']}")
    print(f"Saved to     : {path}")
    print("\n" + "="*55)

if __name__ == "__main__":
    run_pipeline_demo()
