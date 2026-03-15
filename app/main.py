from fastapi import FastAPI
from app.api.routes import ingest, papers

app = FastAPI(title="Scientific Copilot API", version="0.1.0")

app.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
