import os
import json
import structlog
from app.db.models import Experiment
from app.config.settings import settings

logger = structlog.get_logger(__name__)

class ResultTracker:
    async def log_results(self, experiment: Experiment, results: dict) -> str:
        backend = settings.RESULTS_BACKEND.lower()
        log_reference = ""
        
        if backend == "wandb":
            try:
                import wandb
                # Initialize wandb run
                run = wandb.init(
                    project="scientific-copilot",
                    name=f"exp-{str(experiment.id)[:8]}",
                    config={"hypothesis_id": str(experiment.hypothesis_id)},
                    reinit=True
                )
                wandb.log(results)
                log_reference = run.get_url()
                run.finish()
            except ImportError:
                logger.error("tracker_wandb_import_error", msg="wandb not installed")
                backend = "local"
        
        elif backend == "mlflow":
            try:
                import mlflow
                mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
                mlflow.set_experiment("scientific-copilot")
                with mlflow.start_run(run_name=f"exp-{str(experiment.id)[:8]}") as run:
                    mlflow.log_param("hypothesis_id", str(experiment.hypothesis_id))
                    # MLflow requires flattening dicts or specifically logging metrics
                    # For simplicity, if values are numeric, log them as metrics.
                    metrics = {k: float(v) for k,v in results.items() if isinstance(v, (int, float))}
                    mlflow.log_metrics(metrics)
                    log_reference = run.info.run_id
            except ImportError:
                logger.error("tracker_mlflow_import_error", msg="mlflow not installed")
                backend = "local"
                
        if backend == "local":
            results_path = os.path.join(experiment.experiment_dir, "results.json")
            # Usually the container already wrote this file, but we'll ensure it has the final state
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            log_reference = results_path
            
        logger.info(
            "tracker_logged_results",
            backend=backend,
            experiment_id=str(experiment.id),
            keys_logged=list(results.keys())
        )
        
        return log_reference
