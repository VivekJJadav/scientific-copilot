import json
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.clustering.cluster_service import ClusterService
from app.db.models import Gap, HypothesisModel
from app.execution.template_runner import TemplateRunner


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecuteResult:
    def __init__(self, values=None):
        self._values = values or []

    def scalars(self):
        return _ScalarResult(self._values)


class FakeTaskSession:
    def __init__(self, records):
        self.records = records

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, model, key):
        return self.records.get(key)

    def add(self, record):
        self.records[record.id] = record

    async def commit(self):
        return None


class FakePaperDB:
    def __init__(self, papers):
        self.papers = papers

    async def execute(self, stmt):
        return _ExecuteResult(self.papers)


class FakeClusterDB:
    def __init__(self):
        self.cluster_gap_rows = [{"gap_type": "cluster_insight", "id": "old-gap"}]
        self.paper_rows = [SimpleNamespace(cluster_id=uuid.uuid4()) for _ in range(2)]
        self.paper_cluster_rows = [uuid.uuid4()]
        self.persisted_gaps = []
        self.commit_calls = 0

    async def execute(self, stmt):
        table_name = stmt.table.name
        visit_name = stmt.__visit_name__

        if visit_name == "delete" and table_name == "gaps":
            self.cluster_gap_rows = [
                row for row in self.cluster_gap_rows if row["gap_type"] != "cluster_insight"
            ]
        elif visit_name == "update" and table_name == "papers":
            for paper in self.paper_rows:
                paper.cluster_id = None
        elif visit_name == "delete" and table_name == "paper_clusters":
            self.paper_cluster_rows = []

        return _ExecuteResult()

    def add(self, gap):
        self.cluster_gap_rows.append(
            {
                "gap_type": gap.gap_type,
                "cluster_id": gap.cluster_id,
                "source_paper_ids": list(gap.source_paper_ids or []),
            }
        )
        self.persisted_gaps.append(gap)

    async def commit(self):
        self.commit_calls += 1


@pytest.mark.asyncio
async def test_task_payload_can_be_recovered_from_db(monkeypatch):
    from app.api.routes import tasks

    records = {}
    monkeypatch.setattr(tasks, "_get_task_session_factory", lambda: lambda: FakeTaskSession(records))

    tasks._task_store.clear()
    task_id = tasks.create_task("cluster")
    tasks.update_task_status(task_id, "running", progress=45, message="Halfway there")
    await tasks._persist_task_snapshot(tasks._task_store[task_id])

    tasks._task_store.clear()
    recovered = await tasks._get_task_payload(task_id)

    assert recovered is not None
    assert recovered["task_id"] == task_id
    assert recovered["step"] == "cluster"
    assert recovered["progress"] == 45
    assert recovered["message"] == "Halfway there"
    assert recovered["history"][-1]["status"] == "running"


@pytest.mark.asyncio
async def test_experiment_template_generation_is_deterministic(tmp_path, monkeypatch):
    runner = TemplateRunner()
    monkeypatch.setattr("app.execution.template_runner.settings.EXPERIMENT_OUTPUT_DIR", str(tmp_path))

    hypothesis = HypothesisModel(
        id=uuid.uuid4(),
        title="Grounded evaluation for robotic manipulation",
        motivation="Need reproducible benchmarking.",
        core_claim="Grounded retrieval improves manipulation success accuracy.",
        method_sketch="Use retrieval augmented policies with offline replay analysis.",
        expected_outcome="Higher accuracy and lower latency on RoboSet benchmark.",
        risk_factors=["dataset shift", "sensor drift"],
        hardware_requirement="single_gpu_8gb",
        source_paper_ids=["paper-1", "paper-2"],
        gap_description="Benchmarks are inconsistent.",
    )
    papers = [
        SimpleNamespace(
            arxiv_id="paper-1",
            title="RoboSet Benchmark for Manipulation",
            abstract="We evaluate manipulation accuracy and latency on RoboSet.",
            methods=["offline replay analysis", "retrieval augmented control"],
            claims=["Improves accuracy on RoboSet"],
            limitations=["Needs broader sensing conditions"],
        ),
        SimpleNamespace(
            arxiv_id="paper-2",
            title="Sensor-grounded Policy Retrieval",
            abstract="Policy retrieval improves task success across benchmark suites.",
            methods=["retrieval augmented policies"],
            claims=["Lower latency and higher task success"],
            limitations=["Requires careful calibration"],
        ),
    ]

    exp_dir = await runner._prepare_experiment_dir(FakePaperDB(papers), hypothesis)
    spec_path = Path(exp_dir) / "experiment_spec.json"
    evaluate_path = Path(exp_dir) / "evaluate.py"

    first = subprocess.run(
        [sys.executable, str(evaluate_path)],
        cwd=exp_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    first_results = json.loads((Path(exp_dir) / "results.json").read_text())

    second = subprocess.run(
        [sys.executable, str(evaluate_path)],
        cwd=exp_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    second_results = json.loads((Path(exp_dir) / "results.json").read_text())
    spec = json.loads(spec_path.read_text())

    assert "Deterministic experiment evaluation completed." in first.stdout
    assert "Deterministic experiment evaluation completed." in second.stdout
    assert first_results == second_results
    assert spec["hypothesis"]["title"] == hypothesis.title
    assert spec["source_papers"][0]["arxiv_id"] == "paper-1"
    assert "RoboSet Benchmark" in spec["design"]["benchmark_candidates"]
    assert "literature_support" in first_results
    assert "measurement_quality" in first_results
    assert first_results["benchmark_count"] >= 1
    assert first_results["measurable_outcome_count"] >= 2


@pytest.mark.asyncio
async def test_clustering_pipeline_resets_previous_cluster_state(monkeypatch):
    service = ClusterService()
    db = FakeClusterDB()

    async def fake_cluster_run(_db):
        return {"clusters_created": 1, "papers_clustered": 2}

    async def fake_dataset_extract(_db):
        return {"datasets_found": 1}

    async def fake_gap_find(_db):
        return [
            {
                "gap_type": "cluster_insight",
                "description": "New pairwise gap",
                "source_paper_ids": ["paper-1", "paper-2"],
                "cluster_id": uuid.uuid4(),
                "similarity": 0.91,
            }
        ]

    monkeypatch.setattr(service.clusterer, "run", fake_cluster_run)
    monkeypatch.setattr(service.dataset_extractor, "extract_from_papers", fake_dataset_extract)
    monkeypatch.setattr(service.gap_extractor, "find_gaps_from_clusters", fake_gap_find)

    first_summary = await service.run_full_pipeline(db)
    second_summary = await service.run_full_pipeline(db)

    assert first_summary == second_summary
    assert len(db.cluster_gap_rows) == 1
    assert db.cluster_gap_rows[0]["source_paper_ids"] == ["paper-1", "paper-2"]
    assert all(paper.cluster_id is None for paper in db.paper_rows)
    assert db.paper_cluster_rows == []
    assert db.commit_calls >= 4
