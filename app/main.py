from fastapi import FastAPI
# Reload fix
from fastapi.middleware.cors import CORSMiddleware
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
from app.api.routes import feedback, clustering, tasks
from app.api.routes import admin
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.config.settings import settings

security = HTTPBasic(auto_error=False)

def verify_credentials(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if api_key and secrets.compare_digest(api_key, settings.API_KEY):
        return "api_key"

    if credentials:
        correct_username = secrets.compare_digest(credentials.username, settings.API_USER)
        correct_password = secrets.compare_digest(credentials.password, settings.API_PASSWORD)
        if correct_username and correct_password:
            return credentials.username

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic", "X-Auth-Methods": "Basic, X-API-Key"},
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Basic", "X-Auth-Methods": "Basic, X-API-Key"},
    )

app = FastAPI(
    title="Scientific Copilot API", 
    version="0.4.0",
    dependencies=[Depends(verify_credentials)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(hypotheses.router, tags=["extraction & hypotheses"])
app.include_router(debate.router, prefix="/debate", tags=["debate"])
app.include_router(review.router, prefix="/review", tags=["review"])
app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(clustering.router, prefix="/clustering", tags=["clustering"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(tasks.router, prefix="/pipeline", tags=["pipeline"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
