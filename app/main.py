from fastapi import FastAPI
import structlog
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

from app.api.routes import ingest, papers

app = FastAPI(title="Scientific Copilot API", version="0.1.0")

app.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
