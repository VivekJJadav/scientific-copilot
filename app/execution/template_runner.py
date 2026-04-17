import os
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Experiment, HypothesisModel
from app.execution.sandbox import ExperimentSandbox
from app.execution.tracker import ResultTracker
from app.config.settings import settings

logger = structlog.get_logger(__name__)

class TemplateRunner:
    def __init__(self):
        self.sandbox = ExperimentSandbox()
        self.tracker = ResultTracker()
        
    async def run_approved(self, db: AsyncSession) -> dict:
        stmt = select(Experiment).where(Experiment.status == "queued")
        result = await db.execute(stmt)
        experiments = result.scalars().all()
        
        summary = {"ran": 0, "completed": 0, "failed": 0}
        
        for exp in experiments:
            summary["ran"] += 1
            
            hypothesis = await db.get(HypothesisModel, exp.hypothesis_id)
            
            # 1. Prepare directory and template payload
            exp_dir = await self._prepare_experiment_dir(hypothesis)
            exp.experiment_dir = exp_dir
            
            # Start running
            exp.status = "running"
            await db.commit()
            
            # 2. Run inside sandbox
            sandbox_result = await self.sandbox.run(exp)
            
            exp.status = sandbox_result["status"]
            exp.container_id = sandbox_result["container_id"]
            exp.started_at = sandbox_result["started_at"]
            exp.completed_at = sandbox_result["completed_at"]
            exp.error_log = sandbox_result["error_log"]
            
            # 3. Track results
            if sandbox_result["results"]:
                tracked_ref = await self.tracker.log_results(exp, sandbox_result["results"])
                
                backend = settings.RESULTS_BACKEND.lower()
                if backend == "wandb":
                    exp.wandb_run_url = tracked_ref
                elif backend == "mlflow":
                    exp.mlflow_run_id = tracked_ref
                    
                exp.results = sandbox_result["results"]
                # In a real system, LLM might generate summary. For now, basic english.
                exp.result_summary = f"Experiment completed with metrics: {exp.results}"
            else:
                exp.result_summary = (
                    sandbox_result["error_log"]
                    or "Experiment failed to produce results."
                )
                
            await db.commit()
            
            if exp.status == "completed":
                summary["completed"] += 1
            else:
                summary["failed"] += 1
                
        return summary

    async def _prepare_experiment_dir(self, hypothesis: HypothesisModel) -> str:
        base_dir = settings.EXPERIMENT_OUTPUT_DIR
        os.makedirs(base_dir, exist_ok=True)
        
        exp_dir = os.path.join(base_dir, str(hypothesis.id))
        os.makedirs(exp_dir, exist_ok=True)
        
        # Write dummy evaluate.py as requested (simulate real run)
        evaluate_script = f'''"""
Auto-generated evaluation script for hypothesis:
{hypothesis.title}

Method Sketch:
{hypothesis.method_sketch}
"""
import json
import time
import random

def main():
    print("Starting experiment evaluation...")
    time.sleep(2) # simulate work
    print("Processing datasets...")
    
    # Simulate an evaluation metric
    accuracy = 0.80 + (random.random() * 0.15)
    loss = 0.5 - (random.random() * 0.3)
    
    results = {{
        "accuracy": round(accuracy, 4),
        "loss": round(loss, 4),
        "throughput_fps": random.randint(30, 120)
    }}
    
    with open("results.json", "w") as f:
        json.dump(results, f)
        
    print("Experiment finished successfully.")

if __name__ == "__main__":
    main()
'''
        
        with open(os.path.join(exp_dir, "evaluate.py"), "w") as f:
            f.write(evaluate_script)
            
        return exp_dir
