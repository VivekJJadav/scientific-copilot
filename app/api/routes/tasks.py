import asyncio
import copy
import inspect
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

# Task state is mirrored in memory for live SSE fan-out and in DB for durability.
_task_store = {}
_task_subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}


def _get_task_session_factory():
    from app.db.session import async_session_factory

    return async_session_factory

def _publish_task_event(task_id: str) -> None:
    payload = _task_store.get(task_id)
    if not payload:
        return
    for queue in _task_subscribers.get(task_id, []):
        queue.put_nowait(copy.deepcopy(payload))


def _build_task_payload(task_id: str, step: str | None = None) -> dict[str, Any]:
    created_at = datetime.now(UTC).isoformat()
    return {
        "task_id": task_id,
        "step": step,
        "status": "queued",
        "progress": 0,
        "message": "Queued",
        "result": None,
        "error": None,
        "created_at": created_at,
        "updated_at": created_at,
        "history": [
            {
                "status": "queued",
                "progress": 0,
                "message": "Queued",
                "error": None,
                "timestamp": created_at,
            }
        ],
    }


async def _persist_task_snapshot(task: dict[str, Any]) -> None:
    from app.db.models import PipelineTask
    import structlog
    from sqlalchemy.dialects.postgresql import insert

    session_factory = _get_task_session_factory()
    logger = structlog.get_logger(__name__)
    try:
        async with session_factory() as db:
            values = {
                "id": task["task_id"],
                "step": task.get("step"),
                "status": task["status"],
                "progress": int(task.get("progress", 0)),
                "message": task.get("message") or "",
                "result": task.get("result"),
                "error": task.get("error"),
                "history": copy.deepcopy(task.get("history", [])),
                "created_at": datetime.fromisoformat(task["created_at"]),
                "updated_at": datetime.fromisoformat(task["updated_at"]),
            }
            stmt = insert(PipelineTask).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PipelineTask.id],
                set_={
                    "step": stmt.excluded.step,
                    "status": stmt.excluded.status,
                    "progress": stmt.excluded.progress,
                    "message": stmt.excluded.message,
                    "result": stmt.excluded.result,
                    "error": stmt.excluded.error,
                    "history": stmt.excluded.history,
                    # Preserve the first-seen creation time for a task row.
                    "created_at": PipelineTask.created_at,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            await db.execute(stmt)
            await db.commit()
    except Exception as exc:
        logger.warning("task_persistence_failed", task_id=task["task_id"], error=str(exc))


def _schedule_task_persist(task: dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(_persist_task_snapshot(copy.deepcopy(task)))


def _task_from_record(record: Any) -> dict[str, Any]:
    return {
        "task_id": record.id,
        "step": record.step,
        "status": record.status,
        "progress": record.progress,
        "message": record.message,
        "result": record.result,
        "error": record.error,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "history": copy.deepcopy(record.history or []),
    }


async def _load_task_from_db(task_id: str) -> dict[str, Any] | None:
    from app.db.models import PipelineTask
    import structlog

    session_factory = _get_task_session_factory()
    logger = structlog.get_logger(__name__)
    try:
        async with session_factory() as db:
            record = await db.get(PipelineTask, task_id)
            if record is None:
                return None
            task = _task_from_record(record)
            _task_store[task_id] = task
            return task
    except Exception as exc:
        logger.warning("task_load_failed", task_id=task_id, error=str(exc))
        return None


async def _get_task_payload(task_id: str) -> dict[str, Any] | None:
    task = _task_store.get(task_id)
    if task is not None:
        return task
    return await _load_task_from_db(task_id)


def create_task(step: str | None = None) -> str:
    """Creates a new task ID and initializes its state in the store."""
    task_id = str(uuid.uuid4())
    _task_store[task_id] = _build_task_payload(task_id, step=step)
    _schedule_task_persist(_task_store[task_id])
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
        updated_at = datetime.now(UTC).isoformat()
        _task_store[task_id]["updated_at"] = updated_at
        _task_store[task_id].setdefault("history", []).append(
            {
                "status": status,
                "progress": _task_store[task_id]["progress"],
                "message": _task_store[task_id]["message"],
                "error": _task_store[task_id]["error"],
                "timestamp": updated_at,
            }
        )
        _schedule_task_persist(_task_store[task_id])
        _publish_task_event(task_id)


@router.get("/stream")
async def stream_pipeline(request: Request, task_id: str):
    task = await _get_task_payload(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _task_subscribers.setdefault(task_id, []).append(queue)

    async def event_generator():
        try:
            initial = await _get_task_payload(task_id)
            if initial:
                yield _format_sse(initial)
                if initial["status"] in {"done", "failed"}:
                    return

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
    return f"event: task\ndata: {json.dumps(payload)}\n\n"

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a background task."""
    task = await _get_task_payload(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

async def run_in_background(task_id: str, func, *args, **kwargs):
    """Executes a function in the background with its own DB session."""
    import structlog
    from app.api.error_messages import describe_runtime_error
    from app.config.settings import settings
    from app.db.session import async_session_factory
    
    logger = structlog.get_logger(__name__)
    update_task_status(task_id, "running", progress=5, message="Running")

    try:
        async with async_session_factory() as db:
            if "task_id" in inspect.signature(func).parameters and "task_id" not in kwargs:
                kwargs["task_id"] = task_id
            result = await func(db, *args, **kwargs)
        update_task_status(task_id, "done", result=result, progress=100, message="Completed")
    except Exception as e:
        logger.exception("Background task failed", task_id=task_id)
        update_task_status(
            task_id,
            "failed",
            error=describe_runtime_error(e, settings.DATABASE_URL),
            progress=100,
            message="Failed",
        )
