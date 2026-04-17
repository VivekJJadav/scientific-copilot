import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

# In-memory store for task status until SSE/Redis is implemented
# format: task_id: { "status": "queued"|"running"|"done"|"failed", "result": dict, "error": str }
_task_store = {}
_task_subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

def _publish_task_event(task_id: str) -> None:
    payload = _task_store.get(task_id)
    if not payload:
        return
    for queue in _task_subscribers.get(task_id, []):
        queue.put_nowait(payload.copy())


def create_task(step: str | None = None) -> str:
    """Creates a new task ID and initializes its state in the store."""
    task_id = str(uuid.uuid4())
    _task_store[task_id] = {
        "task_id": task_id,
        "step": step,
        "status": "queued",
        "progress": 0,
        "message": "Queued",
        "result": None,
        "error": None,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _publish_task_event(task_id)
    return task_id

def update_task_status(
    task_id: str,
    status: str,
    result: dict = None,
    error: str = None,
    progress: int | None = None,
    message: str | None = None,
):
    """Updates the status and optional results of a background task."""
    if task_id in _task_store:
        _task_store[task_id]["status"] = status
        if progress is not None:
            _task_store[task_id]["progress"] = progress
        if message is not None:
            _task_store[task_id]["message"] = message
        if result is not None:
            _task_store[task_id]["result"] = result
        if error is not None:
            _task_store[task_id]["error"] = error
        _task_store[task_id]["updated_at"] = datetime.now(UTC).isoformat()
        _publish_task_event(task_id)


@router.get("/stream")
async def stream_pipeline(request: Request, task_id: str):
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _task_subscribers.setdefault(task_id, []).append(queue)

    async def event_generator():
        try:
            initial = _task_store.get(task_id)
            if initial:
                yield _format_sse(initial)

            while True:
                if await request.is_disconnected():
                    break

                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield _format_sse(payload)
                    if payload["status"] in {"done", "failed"}:
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            subscribers = _task_subscribers.get(task_id, [])
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _format_sse(task: dict[str, Any]) -> str:
    created_at = datetime.fromisoformat(task["created_at"])
    updated_at = datetime.fromisoformat(task["updated_at"])
    elapsed_ms = int((updated_at - created_at).total_seconds() * 1000)
    payload = {
        "task_id": task["task_id"],
        "step": task.get("step"),
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "elapsed_ms": elapsed_ms,
        "result": task.get("result"),
        "error": task.get("error"),
    }
    import json

    return f"event: task\ndata: {json.dumps(payload)}\n\n"

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a background task."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

async def run_in_background(task_id: str, func, *args, **kwargs):
    """Executes a function in the background with its own DB session."""
    import structlog
    from app.db.session import engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    logger = structlog.get_logger(__name__)
    update_task_status(task_id, "running", progress=5, message="Running")
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            result = await func(db, *args, **kwargs)
        update_task_status(task_id, "done", result=result, progress=100, message="Completed")
    except Exception as e:
        logger.exception("Background task failed", task_id=task_id)
        update_task_status(task_id, "failed", error=str(e), progress=100, message="Failed")
