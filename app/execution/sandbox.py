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
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            logger.warning("docker_not_found", error=str(e))
            self.client = None
        self.image = "python:3.11-slim"
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS

    async def run(self, experiment: Experiment) -> dict:
        """Run an experiment in an isolated Docker container and return execution metadata."""
        start_time = datetime.utcnow()
        container_id = None
        exit_code = -1
        logs = ""
        results = None
        status = "failed"
        abs_exp_dir = os.path.abspath(experiment.experiment_dir)

        if not self.client:
            logger.warning("docker_not_available_simulating_run")
            await asyncio.sleep(2)
            import subprocess
            process = await asyncio.create_subprocess_shell(
                "python evaluate.py",
                cwd=abs_exp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            exit_code = process.returncode
            if exit_code == 0:
                status = "completed"
                results_path = os.path.join(abs_exp_dir, "results.json")
                if os.path.exists(results_path):
                    with open(results_path, 'r') as f:
                        results = json.load(f)
            else:
                logs = stderr.decode('utf-8', errors='replace')
                
            return {
                "status": status,
                "container_id": "simulated",
                "exit_code": exit_code,
                "error_log": logs if status == "failed" else None,
                "results": results,
                "started_at": start_time,
                "completed_at": datetime.utcnow()
            }

        await self._pull_image(self.image)
        exit_code = -1
        logs = ""
        results = None
        status = "failed"
        
        try:
            # We assume experiment_dir contains at minimum evaluate.py and requirements.txt (if any)
            # Volume mount has to be absolute path ON THE HOST because we are using the host's docker daemon
            abs_exp_dir = os.path.abspath(experiment.experiment_dir)
            
            # Get project root from env or default to current directory
            host_project_dir = os.environ.get("HOST_PROJECT_DIR", os.getcwd())
            
            # If inside a container (backend running in docker), we need to find the relative path
            # from the project root. If running on host, it's just the absolute path.
            if abs_exp_dir.startswith("/app"):
                rel_path = os.path.relpath(abs_exp_dir, "/app")
                host_mount_dir = os.path.join(host_project_dir, rel_path)
            else:
                # Running directly on host, the absolute path is what we want for volume mount
                host_mount_dir = abs_exp_dir
            
            # Docker Desktop on Windows sometimes requires specific path formats, 
            # but usually the absolute path works if it's shared.
            
            # Spin up container in detached mode
            
            container = self.client.containers.run(
                self.image,
                command="sh -c 'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi && python evaluate.py'",
                volumes={host_mount_dir: {'bind': '/app', 'mode': 'rw'}},
                working_dir='/app',
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
