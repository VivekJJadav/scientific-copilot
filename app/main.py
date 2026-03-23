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

from app.api.routes import ingest, papers, hypotheses, debate, review, experiments
from app.api.routes import feedback, clustering

app = FastAPI(title="Scientific Copilot API", version="0.4.0")

app.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(hypotheses.router, tags=["extraction & hypotheses"])
app.include_router(debate.router, prefix="/debate", tags=["debate"])
app.include_router(review.router, prefix="/review", tags=["review"])
app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(clustering.router, prefix="/clustering", tags=["clustering"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
