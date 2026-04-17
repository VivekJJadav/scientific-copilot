import asyncio
import json
import time
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.rate_limit import _REQUEST_LOGS
from app.api.routes.debate import _process_debate
from app.api.routes.feedback import requeue_failed
from app.api.routes.tasks import _task_store, create_task, update_task_status, _format_sse
from app.core.atoms import ResearchAtom
from app.db.models import ExperimentResult, Gap, HypothesisModel, Paper
from app.extraction.extractor import PaperExtractor
from app.main import app
from app.reasoning.hypothesis_generator import HypothesisGenerator


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values

    def first(self):
        return self._values[0] if self._values else None


class _ExecuteResult:
    def __init__(self, *, values=None, paper=None):
        self._values = values or []
        self._paper = paper

    def scalars(self):
        return _ScalarResult(self._values)

    def scalar_one_or_none(self):
        return self._paper


class FakeDebateDB:
    def __init__(self, hypothesis, papers):
        self.hypothesis = hypothesis
        self.papers = papers
        self.committed = False

    async def get(self, model, identifier):
        if model is HypothesisModel:
            return self.hypothesis
        return None

    async def execute(self, stmt):
        return _ExecuteResult(values=self.papers)

    async def commit(self):
        self.committed = True


class FakeFeedbackDB:
    def __init__(self, results, hypotheses):
        self.results = results
        self.hypotheses = hypotheses
        self.gaps: list[Gap] = []
        self.commits = 0

    async def execute(self, stmt):
        text = str(stmt)
        if "FROM experiment_results" in text:
            return _ExecuteResult(values=self.results)
        if "FROM gaps" in text:
            marker = "[failure:"
            matches = [g for g in self.gaps if marker in g.gap_description]
            return _ExecuteResult(values=matches)
        return _ExecuteResult(values=[])

    async def get(self, model, identifier):
        if model is HypothesisModel:
            return self.hypotheses.get(identifier)
        return None

    def add(self, item):
        if isinstance(item, Gap):
            self.gaps.append(item)

    async def commit(self):
        self.commits += 1


class FakePipelineDB:
    def __init__(self, paper):
        self.paper = paper
        self.hypotheses = []
        self.commit_calls = 0

    async def execute(self, stmt):
        stmt_text = str(stmt)
        if "WHERE papers.arxiv_id =" in stmt_text:
            return _ExecuteResult(paper=self.paper)
        return _ExecuteResult(values=[])

    async def commit(self):
        self.commit_calls += 1

    def add(self, hypothesis):
        self.hypotheses.append(hypothesis)


@pytest.fixture(autouse=True)
def clear_task_state():
    _task_store.clear()
    _REQUEST_LOGS.clear()
    yield
    _task_store.clear()
    _REQUEST_LOGS.clear()


def test_auth_required_and_api_key_works(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("app.api.routes.tasks.run_in_background", lambda *args, **kwargs: None)

    unauth = client.get("/health")
    assert unauth.status_code == 401

    authed = client.get("/health", headers={"X-API-Key": "dev-api-key"})
    assert authed.status_code == 200


def test_extract_endpoint_rate_limited(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("app.api.routes.tasks.run_in_background", lambda *args, **kwargs: None)

    headers = {"X-API-Key": "dev-api-key"}
    statuses = [client.post("/extract", headers=headers).status_code for _ in range(6)]
    assert statuses[:5] == [200, 200, 200, 200, 200]
    assert statuses[5] == 429


@pytest.mark.asyncio
async def test_debate_round_count_and_transcript_numbers(monkeypatch):
    hypothesis = HypothesisModel(
        id=uuid.uuid4(),
        title="Hypothesis",
        motivation="Motivation",
        core_claim="Claim",
        method_sketch="Method",
        expected_outcome="Outcome",
        risk_factors=[],
        source_paper_ids=["paper-1"],
        gap_description="Gap",
        status="pending",
        debate_rounds=0,
    )
    paper = Paper(
        arxiv_id="paper-1",
        title="Paper 1",
        abstract="Abstract",
        authors=[],
        published_year=2026,
        pdf_url="https://example.com/paper.pdf",
    )
    db = FakeDebateDB(hypothesis, [paper])

    async def fake_complete(self, prompt, expect_json=False, force_json_object=False):
        if force_json_object:
            return json.dumps(
                {
                    "verdict": "PASS",
                    "final_novelty_score": 0.7,
                    "final_feasibility_score": 0.8,
                    "surviving_risks": [],
                    "rejection_reason": "",
                    "arbiter_notes": "PASS",
                }
            )
        if "Critic's objection" in prompt:
            return "Rebuttal"
        if "Proposer's argument" in prompt:
            return "Critique"
        return "Proposal"

    monkeypatch.setattr("app.debate.agents.LLMRouter.complete", fake_complete)
    monkeypatch.setattr("app.config.settings.settings.DEBATE_MAX_ROUNDS", 3)

    result = await _process_debate(hypothesis.id, db)

    assert result["rounds_completed"] == 3
    assert hypothesis.debate_rounds == 3
    rounds = [entry["round"] for entry in hypothesis.debate_transcript if entry["role"] != "proposer" or entry["round"] != 0]
    assert rounds == [1, 1, 2, 2, 3, 3]


@pytest.mark.asyncio
async def test_requeue_failed_deduplicates_same_failure():
    experiment_id = uuid.uuid4()
    hypothesis_id = uuid.uuid4()
    result = ExperimentResult(
        experiment_id=experiment_id,
        hypothesis_id=hypothesis_id,
        outcome="failed",
        metrics={},
        result_summary="It failed",
        lessons_learned=["Try again"],
    )
    hypothesis = HypothesisModel(
        id=hypothesis_id,
        title="Hypothesis",
        motivation="Motivation",
        core_claim="Claim",
        method_sketch="Method",
        expected_outcome="Outcome",
        risk_factors=[],
        source_paper_ids=["paper-1"],
        gap_description="Gap",
        status="pending",
    )
    db = FakeFeedbackDB([result], {hypothesis_id: hypothesis})

    first = await requeue_failed(db)
    second = await requeue_failed(db)

    assert first["new_gaps_created"] == 1
    assert second["new_gaps_created"] == 0
    assert len(db.gaps) == 1


@pytest.mark.asyncio
async def test_extract_batch_concurrency_and_full_text_storage(monkeypatch):
    extractor = PaperExtractor()
    atoms = [
        ResearchAtom(
            paper_id=f"paper-{i}",
            title=f"Paper {i}",
            abstract="Abstract",
            authors=[],
            published_year=2026,
            pdf_url=f"https://example.com/{i}.pdf",
            methods=[],
            limitations=[],
            claims=[],
        )
        for i in range(10)
    ]

    papers = [
        SimpleNamespace(
            methods=[],
            limitations=[],
            claims=[],
            full_text=None,
            text_chunks=[],
            content_source="abstract",
            arxiv_status="raw",
            updated_at=None,
        )
        for _ in atoms
    ]

    class FakeDB:
        def __init__(self, papers):
            self._papers = iter(papers)
            self.commit_calls = 0

        async def execute(self, stmt):
            return _ExecuteResult(paper=next(self._papers))

        async def commit(self):
            self.commit_calls += 1

    async def fake_complete(prompt, expect_json=False, force_json_object=False):
        await asyncio.sleep(0.05)
        return json.dumps({"methods": ["LoRA"], "limitations": ["Limit"], "claims": ["Claim"]})

    async def fake_fetch_pdf_text(pdf_url):
        return ("Full PDF text", ["chunk-1", "chunk-2"], "pdf")

    monkeypatch.setattr(extractor.llm, "complete", fake_complete)
    monkeypatch.setattr("app.extraction.extractor.fetch_pdf_text", fake_fetch_pdf_text)

    start = time.monotonic()
    await extractor.extract_batch(atoms, FakeDB(papers))
    elapsed = time.monotonic() - start

    assert elapsed < 0.3
    assert all(p.full_text == "Full PDF text" for p in papers)
    assert all(p.text_chunks == ["chunk-1", "chunk-2"] for p in papers)
    assert all(p.content_source == "pdf" for p in papers)


@pytest.mark.asyncio
async def test_mocked_llm_pipeline_ingest_extract_hypothesize(monkeypatch):
    paper = Paper(
        arxiv_id="1234.5678",
        title="Pipeline Paper",
        abstract="Abstract",
        authors=[],
        published_year=2026,
        pdf_url="https://example.com/paper.pdf",
    )
    db = FakePipelineDB(paper)

    extractor = PaperExtractor()
    generator = HypothesisGenerator()
    atom = ResearchAtom.from_paper(paper)

    async def fake_pdf(pdf_url):
        return ("Full text", ["chunk"], "pdf")

    async def fake_extract(prompt, expect_json=False, force_json_object=False):
        if "novelty_score" in prompt:
            return json.dumps({"novelty_score": 0.9, "reasoning": "novel"})
        return json.dumps(
            {
                "methods": ["Transformer"],
                "limitations": ["Small benchmark"],
                "claims": ["Improves accuracy"],
            }
        )

    async def fake_generate(prompt, expect_json=False, force_json_object=False):
        if "Novelty score rules" in prompt:
            return json.dumps({"novelty_score": 0.9, "reasoning": "new"})
        return json.dumps(
            {
                "title": "Generated Hypothesis",
                "motivation": "Motivation",
                "core_claim": "Core claim",
                "method_sketch": "Method sketch",
                "expected_outcome": "Expected outcome",
                "risk_factors": ["risk"],
                "novelty_score": 0.7,
                "feasibility_score": 0.8,
                "hardware_requirement": "single_gpu_8gb",
            }
        )

    monkeypatch.setattr("app.extraction.extractor.fetch_pdf_text", fake_pdf)
    monkeypatch.setattr(extractor.llm, "complete", fake_extract)
    monkeypatch.setattr(generator.llm, "complete", fake_generate)
    monkeypatch.setattr(generator, "_retrieve_similar_papers", lambda query, db: asyncio.sleep(0, result=("", [])))
    monkeypatch.setattr(generator, "_get_dataset_context", lambda db: asyncio.sleep(0, result=""))
    monkeypatch.setattr(generator, "_persist_hypothesis", lambda hypothesis, db: asyncio.sleep(0, result=db.add(hypothesis)))

    await extractor.extract_batch([atom], db)
    hypothesis = await generator.generate(
        {"description": "Test gap", "source_paper_ids": ["1234.5678"], "gap_type": "generalization"},
        [atom],
        db,
    )

    assert paper.full_text == "Full text"
    assert paper.text_chunks == ["chunk"]
    assert paper.content_source == "pdf"
    assert hypothesis is not None
    assert hypothesis.title == "Generated Hypothesis"
    assert db.hypotheses


def test_task_sse_payload_contains_progress_and_elapsed():
    task_id = create_task("extract")
    update_task_status(task_id, "running", progress=50, message="Halfway")
    payload = _format_sse(_task_store[task_id])

    assert "event: task" in payload
    assert '"step": "extract"' in payload
    assert '"progress": 50' in payload
    assert '"elapsed_ms":' in payload
