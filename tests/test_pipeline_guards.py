import json
import uuid
from types import SimpleNamespace

import httpx
import pytest
from tenacity import wait_none

from app.core.atoms import ResearchAtom
from app.db.models import Experiment
from app.execution.sandbox import ExperimentSandbox
from app.extraction.extractor import PaperExtractor
from app.ingestion.ingest_service import run_ingestion
from app.llm.router import LLMRouter, RetryableLLMError
from app.reasoning.gap_extractor import GapExtractor


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecuteResult:
    def __init__(self, *, titles=None, paper=None, rowcount=None):
        self._titles = titles
        self._paper = paper
        self.rowcount = rowcount

    def scalars(self):
        return _ScalarResult(self._titles or [])

    def scalar_one_or_none(self):
        return self._paper


class FakeIngestionDB:
    def __init__(self, insert_outcomes):
        self.insert_outcomes = list(insert_outcomes)
        self.commit_calls = 0
        self.rollback_calls = 0
        self._execute_count = 0

    async def execute(self, stmt):
        self._execute_count += 1
        if self._execute_count == 1:
            return _ExecuteResult(titles=[])

        outcome = self.insert_outcomes[self._execute_count - 2]
        if isinstance(outcome, Exception):
            raise outcome
        return _ExecuteResult(rowcount=outcome)

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class FakeExtractionDB:
    def __init__(self, papers):
        self._papers = iter(papers)
        self.commit_calls = 0

    async def execute(self, stmt):
        return _ExecuteResult(paper=next(self._papers))

    async def commit(self):
        self.commit_calls += 1


def make_atom(paper_id: str, title: str, abstract: str) -> ResearchAtom:
    return ResearchAtom(
        paper_id=paper_id,
        title=title,
        abstract=abstract,
        authors=[{"name": "Author"}],
        published_year=2026,
        pdf_url=f"https://example.com/{paper_id}.pdf",
        methods=[],
        limitations=[],
        claims=[],
    )


@pytest.mark.asyncio
async def test_llm_router_retries_timeout_and_logs(monkeypatch):
    router = LLMRouter()
    router.fallback_provider = ""
    router.fallback_api_key = ""

    attempts = {"count": 0}
    warnings = []

    async def fake_call_ollama(prompt, force_json_object=False):
        attempts["count"] += 1
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(router, "_call_ollama", fake_call_ollama)
    monkeypatch.setattr(
        "app.llm.router.logger.warning",
        lambda event, **kwargs: warnings.append((event, kwargs)),
    )

    original_wait = router.complete.retry.wait
    router.complete.retry.wait = wait_none()
    try:
        with pytest.raises(RetryableLLMError):
            await router.complete("hello")
    finally:
        router.complete.retry.wait = original_wait

    assert attempts["count"] == 3
    retry_logs = [log for log in warnings if log[0] == "llm_retry_scheduled"]
    assert len(retry_logs) == 2


@pytest.mark.asyncio
async def test_extraction_batch_survives_llm_timeout(monkeypatch):
    extractor = PaperExtractor()
    first_atom = make_atom("paper-1", "Timeout paper", "timeout case")
    second_atom = make_atom("paper-2", "Good paper", "success case")

    async def fake_complete(prompt, expect_json=False, force_json_object=False):
        if "timeout case" in prompt:
            raise RetryableLLMError("timed out")
        return json.dumps(
            {
                "methods": ["LoRA"],
                "limitations": ["small sample size"],
                "claims": ["improves accuracy"],
            }
        )

    monkeypatch.setattr(extractor.llm, "complete", fake_complete)

    db_papers = [
        SimpleNamespace(
            methods=[],
            limitations=[],
            claims=[],
            arxiv_status="raw",
            updated_at=None,
        ),
        SimpleNamespace(
            methods=[],
            limitations=[],
            claims=[],
            arxiv_status="raw",
            updated_at=None,
        ),
    ]
    db = FakeExtractionDB(db_papers)

    results = await extractor.extract_batch([first_atom, second_atom], db)

    assert [atom.arxiv_status for atom in results] == ["extraction_failed", "processed"]
    assert db_papers[0].methods == []
    assert db_papers[0].arxiv_status == "extraction_failed"
    assert db_papers[1].methods == ["LoRA"]
    assert db_papers[1].limitations == ["small sample size"]
    assert db_papers[1].claims == ["improves accuracy"]
    assert db_papers[1].arxiv_status == "processed"
    assert db.commit_calls == 1


@pytest.mark.asyncio
async def test_run_extraction_pipeline_retries_failed_papers(monkeypatch):
    extractor = PaperExtractor()

    retry_paper = SimpleNamespace(
        id=uuid.uuid4(),
        arxiv_id="paper-retry",
        title="Retry me",
        abstract="previously failed extraction",
        authors=[],
        published_year=2026,
        pdf_url="https://example.com/retry.pdf",
        methods=[],
        limitations=[],
        claims=[],
        embedding=None,
        arxiv_status="extraction_failed",
        full_text=None,
        text_chunks=[],
        content_source="abstract",
        updated_at=None,
    )

    class RetryDB:
        def __init__(self, papers):
            self._papers = papers

        async def execute(self, stmt):
            stmt_text = str(stmt)
            if "WHERE papers.arxiv_status IN" in stmt_text:
                return _ExecuteResult(titles=self._papers)
            return _ExecuteResult(paper=self._papers[0])

        async def commit(self):
            return None

    async def fake_extract_batch(atoms, db):
        atoms[0].methods = ["LoRA"]
        atoms[0].limitations = ["small sample"]
        atoms[0].claims = ["works better"]
        atoms[0].arxiv_status = "processed"
        retry_paper.methods = atoms[0].methods
        retry_paper.limitations = atoms[0].limitations
        retry_paper.claims = atoms[0].claims
        retry_paper.arxiv_status = "processed"
        return atoms

    monkeypatch.setattr(extractor, "extract_batch", fake_extract_batch)

    summary = await extractor.run_extraction_pipeline(RetryDB([retry_paper]))

    assert summary == {"processed": 1, "failed": 0}
    assert retry_paper.arxiv_status == "processed"


def test_gap_extractor_build_limitations_block_uses_real_paper_context():
    extractor = GapExtractor()
    atoms = [
        ResearchAtom(
            paper_id="paper-1",
            title="Ablation Study",
            abstract="This study explores a narrow benchmark.",
            authors=[],
            published_year=2026,
            pdf_url="https://example.com/a.pdf",
            methods=[],
            limitations=[],
            claims=[],
        ),
        ResearchAtom(
            paper_id="paper-2",
            title="Grounded Planning",
            abstract="A planning paper.",
            authors=[],
            published_year=2026,
            pdf_url="https://example.com/b.pdf",
            methods=["MPC"],
            limitations=["Needs more diverse environments"],
            claims=["Improves semantic generalization"],
        ),
    ]

    block = extractor._build_limitations_block(atoms)

    assert "No limitations found." not in block
    assert "Paper [paper-1] title: Ablation Study" in block
    assert "Paper [paper-2] methods: MPC" in block
    assert "Needs more diverse environments" in block
    assert "Improves semantic generalization" in block


@pytest.mark.asyncio
async def test_sandbox_returns_clear_error_without_docker():
    sandbox = ExperimentSandbox()
    sandbox.client = None

    experiment = Experiment(
        hypothesis_id=uuid.uuid4(),
        experiment_dir="./experiments/test-exp",
    )

    result = await sandbox.run(experiment)

    assert result["status"] == "failed"
    assert result["container_id"] is None
    assert "Cannot run experiment safely" in result["error_log"]


@pytest.mark.asyncio
async def test_ingestion_commits_once_for_full_batch(monkeypatch):
    atoms = [make_atom(f"paper-{i}", f"Distinct ingest title {i:03d} alpha", "abstract") for i in range(50)]
    db = FakeIngestionDB([1] * 50)

    async def fake_fetch_papers(query, limit):
        return atoms

    monkeypatch.setattr("app.ingestion.ingest_service.fetch_papers", fake_fetch_papers)
    monkeypatch.setattr("app.ingestion.ingest_service.fuzz.ratio", lambda left, right: 0)

    summary = await run_ingestion(db, limit=50)

    assert summary == {"fetched": 50, "inserted": 50, "skipped": 0}
    assert db.commit_calls == 1
    assert db.rollback_calls == 0


@pytest.mark.asyncio
async def test_ingestion_rolls_back_on_mid_batch_failure(monkeypatch):
    atoms = [make_atom("paper-1", "Paper 1", "abstract"), make_atom("paper-2", "Paper 2", "abstract")]
    db = FakeIngestionDB([1, RuntimeError("insert failed")])

    async def fake_fetch_papers(query, limit):
        return atoms

    monkeypatch.setattr("app.ingestion.ingest_service.fetch_papers", fake_fetch_papers)

    with pytest.raises(RuntimeError, match="insert failed"):
        await run_ingestion(db, limit=2)

    assert db.commit_calls == 0
    assert db.rollback_calls == 1
