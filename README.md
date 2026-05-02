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

### DebateRecord & Arbiter Memory
The arbiter — the final judge in the hypothesis debate pipeline — now carries **structured memory** across debate runs. Previously, each debate started blank; the arbiter had no knowledge of why a parent hypothesis was rejected or what objections were raised.

**How it works:**
- Every completed debate is persisted as a `DebateHistory` row in the database, capturing distilled objections, rebuttals, verdict, rejection reason, and which prior objections were addressed.
- The `DebateRecord` dataclass (in `app/core/debate_record.py`) is the in-memory representation — analogous to how `ResearchAtom` is the currency for papers, `DebateRecord` is the currency for debate history.
- The `DebateMemory` service (in `app/debate/debate_memory.py`) walks the `parent_hypothesis_id` ancestry chain (up to `DEBATE_HISTORY_MAX_DEPTH=3` levels) and loads prior debate records.
- The arbiter prompt is layered: **ancestor debate history → few-shot calibration → current debate**, so the arbiter sees rejection context before evaluating a child hypothesis.
- The arbiter self-reports `key_objections` and `addressed_prior_objections` in its verdict (zero extra LLM cost), creating an audit trail of what was fixed and what persists.

**Key constraint:** If a prior objection persists unresolved in a child hypothesis, the arbiter is instructed to escalate severity rather than re-evaluate from scratch.

### arxiv_status Finite State Machine 
The database uses `arxiv_status` to maintain a naive state machine for processing:
- `raw`: The initial ingestion state upon first fetch.
- `processed` / `embedded`: States to be attained in future LLM reasoning phases.
