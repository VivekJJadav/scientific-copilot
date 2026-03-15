# scientific-copilot

Phase 1 of the scientific-copilot research agent system. Handles fetching, validating, and database insertion of ArXiv papers into PostgreSQL with pgvector.

## Run Instructions

```bash
# 1. Start Postgres
docker compose up -d postgres

# 2. Install dependencies
uv sync

# 3. Copy env file
cp .env.example .env

# 4. Run migrations
uv run alembic upgrade head

# 5. Start the API
uv run uvicorn app.main:app --reload

# 6. Trigger ingestion
curl -X POST http://localhost:8000/ingest/arxiv

# 7. View papers
curl http://localhost:8000/papers
```

## Architecture Notes

### ResearchAtom Contract
The `ResearchAtom` dataclass (in `app/core/atoms.py`) represents the internal data contract for the system. All subsystems communicate using this object. Missing fields like embedding or LLM-derived insights (`methods`, `limitations`, `claims`) stay explicitly empty or Null in Phase 1 and will be populated sequentially in future phases.

### arxiv_status Finite State Machine 
The database uses `arxiv_status` to maintain a naive state machine for processing:
- `raw`: The initial ingestion state upon first fetch.
- `processed` / `embedded`: States to be attained in future LLM reasoning phases.
