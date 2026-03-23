import os
import json
import uuid
import time
import asyncio
import docker
import structlog
from datetime import datetime

from app.db.models import Experiment
from app.config.settings import settings

logger = structlog.get_logger(__name__)

class ExperimentSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.image = "python:3.11-slim"
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS

    async def run(self, experiment: Experiment) -> dict:
        """Run an experiment in an isolated Docker container and return execution metadata."""
        await self._pull_image(self.image)
        
        start_time = datetime.utcnow()
        container_id = None
        exit_code = -1
        logs = ""
        results = None
        status = "failed"
        
        try:
            # We assume experiment_dir contains at minimum evaluate.py and requirements.txt (if any)
            # Volume mount has to be absolute path ON THE HOST because we are using the host's docker daemon
            abs_exp_dir = os.path.abspath(experiment.experiment_dir)
            
            host_project_dir = os.environ.get("HOST_PROJECT_DIR", "/Users/vicky/Desktop/scientific-copilot")
            # If inside container, abs_exp_dir starts with /app. We find relative path to /app or cwd
            if abs_exp_dir.startswith("/app"):
                rel_path = os.path.relpath(abs_exp_dir, "/app")
            else:
                rel_path = os.path.relpath(abs_exp_dir, os.getcwd())
                
            host_mount_dir = os.path.join(host_project_dir, rel_path)
            
            # Spin up container in detached mode
            nano_cpus = int(float(settings.SANDBOX_CPU_LIMIT) * 1e9)
            
            container = self.client.containers.run(
                self.image,
                command="sh -c 'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi && python evaluate.py'",
                volumes={host_mount_dir: {'bind': '/app', 'mode': 'rw'}},
                working_dir='/app',
                nano_cpus=nano_cpus,
                mem_limit=settings.SANDBOX_MEMORY_LIMIT,
                detach=True,
                remove=False
            )
            container_id = container.id
            
            # Wait for container with timeout
            # Docker python SDK wait() is blocking, so we'll wrap it via asyncio
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait), 
                    timeout=self.timeout
                )
                exit_code = result["StatusCode"]
                logs_bytes = container.logs()
                logs = logs_bytes.decode('utf-8', errors='replace')
                
                if exit_code == 0:
                    status = "completed"
                    # Read results.json if it exists
                    results_path = os.path.join(abs_exp_dir, "results.json")
                    if os.path.exists(results_path):
                        with open(results_path, 'r') as f:
                            try:
                                results = json.load(f)
                            except json.JSONDecodeError:
                                logs += "\nError: results.json was not valid JSON."
                                status = "failed"
                    else:
                        logs += "\nError: results.json not found."
                        status = "failed"
                        
            except asyncio.TimeoutError:
                logs = "Error: Container execution timed out."
                exit_code = 124
                
        except Exception as e:
            logs = f"Error starting container: {str(e)}"
            
        finally:
            if container_id:
                await self._cleanup(container_id)
                
        completed_at = datetime.utcnow()
        
        return {
            "status": status,
            "container_id": container_id,
            "exit_code": exit_code,
            "error_log": logs if status == "failed" else None,
            "results": results,
            "started_at": start_time,
            "completed_at": completed_at
        }
        
    async def _pull_image(self, image: str) -> None:
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            # Could block, but to_thread makes it safe
            logger.info("sandbox_pulling_image", image=image)
            await asyncio.to_thread(self.client.images.pull, image)

    async def _run_container(self, experiment_dir: str) -> tuple[int, str, str]:
        # Implementation is in line within run() for easier resource cleanup
        pass

    async def _cleanup(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            await asyncio.to_thread(container.stop, timeout=2)
            await asyncio.to_thread(container.remove, force=True)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error("sandbox_cleanup_failed", container_id=container_id, error=str(e))
