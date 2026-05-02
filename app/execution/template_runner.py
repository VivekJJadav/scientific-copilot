import os
import json
import re
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Experiment, HypothesisModel, Paper
from app.execution.sandbox import ExperimentSandbox
from app.execution.tracker import ResultTracker
from app.config.settings import settings

logger = structlog.get_logger(__name__)

class TemplateRunner:
    def __init__(self):
        self.sandbox = ExperimentSandbox()
        self.tracker = ResultTracker()
        
    async def run_approved(
        self,
        db: AsyncSession,
        task_id: str | None = None,
    ) -> dict:
        stmt = select(Experiment).where(Experiment.status == "queued")
        result = await db.execute(stmt)
        experiments = result.scalars().all()
        
        summary = {"ran": 0, "completed": 0, "failed": 0}
        
        total_experiments = max(len(experiments), 1)
        for index, exp in enumerate(experiments, start=1):
            summary["ran"] += 1
            
            hypothesis = await db.get(HypothesisModel, exp.hypothesis_id)
            
            # 1. Prepare directory and template payload
            exp_dir = await self._prepare_experiment_dir(db, hypothesis)
            exp.experiment_dir = exp_dir
            
            # Start running
            exp.status = "running"
            await db.commit()
            
            # 2. Run inside sandbox
            sandbox_result = await self.sandbox.run(exp)
            
            exp.status = sandbox_result["status"]
            exp.container_id = sandbox_result["container_id"]
            exp.started_at = sandbox_result["started_at"]
            exp.completed_at = sandbox_result["completed_at"]
            exp.error_log = sandbox_result["error_log"]
            
            # 3. Track results
            if sandbox_result["results"]:
                tracked_ref = await self.tracker.log_results(exp, sandbox_result["results"])
                
                backend = settings.RESULTS_BACKEND.lower()
                if backend == "wandb":
                    exp.wandb_run_url = tracked_ref
                elif backend == "mlflow":
                    exp.mlflow_run_id = tracked_ref
                    
                exp.results = sandbox_result["results"]
                # In a real system, LLM might generate summary. For now, basic english.
                exp.result_summary = f"Experiment completed with metrics: {exp.results}"
            else:
                exp.result_summary = (
                    sandbox_result["error_log"]
                    or "Experiment failed to produce results."
                )
                
            await db.commit()
            
            if exp.status == "completed":
                summary["completed"] += 1
            else:
                summary["failed"] += 1

            if task_id:
                from app.api.routes.tasks import update_task_status

                progress = 15 + int((index / total_experiments) * 80)
                update_task_status(
                    task_id,
                    "running",
                    progress=min(progress, 95),
                    message=(
                        f"Completed {summary['completed']} / {summary['ran']} "
                        f"experiment runs"
                    ),
                )
                
        return summary

    async def _prepare_experiment_dir(self, db: AsyncSession, hypothesis: HypothesisModel) -> str:
        base_dir = settings.EXPERIMENT_OUTPUT_DIR
        os.makedirs(base_dir, exist_ok=True)
        
        exp_dir = os.path.join(base_dir, str(hypothesis.id))
        os.makedirs(exp_dir, exist_ok=True)

        experiment_spec = await self._build_experiment_spec(db, hypothesis)
        with open(os.path.join(exp_dir, "experiment_spec.json"), "w") as f:
            json.dump(experiment_spec, f, indent=2)

        with open(os.path.join(exp_dir, "evaluate.py"), "w") as f:
            f.write(self._build_evaluate_script())
            
        return exp_dir

    async def _build_experiment_spec(
        self,
        db: AsyncSession,
        hypothesis: HypothesisModel,
    ) -> dict:
        source_papers = await self._load_source_papers(db, hypothesis.source_paper_ids or [])

        method_keywords = self._extract_keywords(
            " ".join(
                part
                for part in [
                    hypothesis.title,
                    hypothesis.core_claim,
                    hypothesis.method_sketch,
                ]
                if part
            )
        )
        outcome_keywords = self._extract_keywords(hypothesis.expected_outcome or "")
        benchmark_candidates = self._extract_benchmark_candidates(source_papers, hypothesis)
        measurable_outcomes = self._extract_measurement_targets(hypothesis.expected_outcome or "")
        evidence_map = self._build_evidence_map(source_papers, method_keywords, outcome_keywords)

        evidence_strength = {
            "methods_supported": sum(1 for item in evidence_map["method_support"] if item["matched_terms"]),
            "claims_supported": sum(1 for item in evidence_map["claim_support"] if item["matched_terms"]),
            "papers_with_datasets": sum(1 for paper in source_papers if paper["datasets"]),
            "papers_with_limitations": sum(1 for paper in source_papers if paper["limitations"]),
        }

        return {
            "hypothesis": {
                "id": str(hypothesis.id),
                "title": hypothesis.title,
                "core_claim": hypothesis.core_claim,
                "method_sketch": hypothesis.method_sketch,
                "expected_outcome": hypothesis.expected_outcome,
                "risk_factors": list(hypothesis.risk_factors or []),
                "hardware_requirement": hypothesis.hardware_requirement or "",
                "source_paper_ids": list(hypothesis.source_paper_ids or []),
            },
            "source_papers": source_papers,
            "design": {
                "method_keywords": method_keywords,
                "outcome_keywords": outcome_keywords,
                "benchmark_candidates": benchmark_candidates,
                "measurable_outcomes": measurable_outcomes,
            },
            "evidence": {
                **evidence_strength,
                **evidence_map,
            },
        }

    async def _load_source_papers(self, db: AsyncSession, source_ids: list[str]) -> list[dict]:
        if not source_ids:
            return []

        stmt = select(Paper).where(Paper.arxiv_id.in_(source_ids))
        papers = (await db.execute(stmt)).scalars().all()
        order = {paper_id: index for index, paper_id in enumerate(source_ids)}
        papers.sort(key=lambda paper: order.get(paper.arxiv_id, len(order)))

        normalized = []
        for paper in papers:
            normalized.append(
                {
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "methods": list(paper.methods or []),
                    "claims": list(paper.claims or []),
                    "limitations": list(paper.limitations or []),
                    "datasets": self._extract_dataset_mentions(
                        paper.title,
                        paper.abstract,
                        paper.methods or [],
                        paper.claims or [],
                    ),
                }
            )
        return normalized

    def _extract_keywords(self, text: str, *, limit: int = 8) -> list[str]:
        tokens = re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())
        stop_words = {
            "that", "this", "with", "from", "into", "using", "across", "improves",
            "improve", "improved", "method", "methods", "model", "models", "based",
            "approach", "approaches", "results", "result", "paper", "study",
        }
        seen = []
        for token in tokens:
            if token in stop_words:
                continue
            if token not in seen:
                seen.append(token)
            if len(seen) >= limit:
                break
        return seen

    def _extract_dataset_mentions(
        self,
        title: str,
        abstract: str,
        methods: list[str],
        claims: list[str],
    ) -> list[str]:
        text = " ".join([title, abstract, *methods, *claims])
        matches = re.findall(
            r"\b([A-Z][A-Za-z0-9-]+(?:[- ][A-Z0-9][A-Za-z0-9-]+){0,3})\b",
            text,
        )
        blacklist = {"The", "This", "We", "Our", "Results", "Experiments"}
        datasets = []
        for match in matches:
            name = match.strip()
            if name in blacklist or len(name) < 3:
                continue
            if name not in datasets:
                datasets.append(name)
        return datasets[:6]

    def _extract_benchmark_candidates(
        self,
        source_papers: list[dict],
        hypothesis: HypothesisModel,
    ) -> list[str]:
        candidates = []
        for paper in source_papers:
            for dataset in paper["datasets"]:
                if dataset not in candidates:
                    candidates.append(dataset)
        for token in self._extract_keywords(hypothesis.expected_outcome or "", limit=5):
            if token.upper() == token or token.endswith("bench"):
                if token not in candidates:
                    candidates.append(token)
        return candidates[:8]

    def _extract_measurement_targets(self, expected_outcome: str) -> list[str]:
        metric_terms = {
            "accuracy", "f1", "precision", "recall", "auc", "latency", "throughput",
            "robustness", "calibration", "success", "reward", "loss", "error",
        }
        outcomes = []
        for token in self._extract_keywords(expected_outcome, limit=12):
            if token in metric_terms and token not in outcomes:
                outcomes.append(token)
        if not outcomes and expected_outcome:
            outcomes.append("task_success")
        return outcomes[:6]

    def _build_evidence_map(
        self,
        source_papers: list[dict],
        method_keywords: list[str],
        outcome_keywords: list[str],
    ) -> dict:
        method_support = []
        claim_support = []
        for paper in source_papers:
            method_text = " ".join(paper["methods"])
            claim_text = " ".join(paper["claims"] + [paper["abstract"]])
            method_matches = sorted(
                token for token in method_keywords if token in method_text.lower()
            )
            claim_matches = sorted(
                token for token in outcome_keywords if token in claim_text.lower()
            )
            method_support.append(
                {
                    "paper_id": paper["arxiv_id"],
                    "matched_terms": method_matches,
                }
            )
            claim_support.append(
                {
                    "paper_id": paper["arxiv_id"],
                    "matched_terms": claim_matches,
                }
            )
        return {
            "method_support": method_support,
            "claim_support": claim_support,
        }

    def _build_evaluate_script(self) -> str:
        return '''"""Deterministic experiment evaluation generated from experiment_spec.json."""
import json
from pathlib import Path


def clamp(value, lower=0.0, upper=1.0):
    return max(lower, min(upper, value))


def ratio(numerator, denominator):
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def main():
    spec = json.loads(Path("experiment_spec.json").read_text())
    source_papers = spec.get("source_papers", [])
    design = spec.get("design", {})
    evidence = spec.get("evidence", {})
    hypothesis = spec.get("hypothesis", {})

    paper_count = len(source_papers)
    method_keywords = design.get("method_keywords", [])
    outcome_keywords = design.get("outcome_keywords", [])
    benchmark_candidates = design.get("benchmark_candidates", [])
    measurable_outcomes = design.get("measurable_outcomes", [])
    risk_factors = hypothesis.get("risk_factors", [])
    hardware_requirement = (hypothesis.get("hardware_requirement") or "").lower()

    methods_supported = evidence.get("methods_supported", 0)
    claims_supported = evidence.get("claims_supported", 0)
    papers_with_datasets = evidence.get("papers_with_datasets", 0)
    papers_with_limitations = evidence.get("papers_with_limitations", 0)

    literature_support = clamp(
        0.45 * ratio(methods_supported, max(len(method_keywords), 1))
        + 0.35 * ratio(claims_supported, max(len(outcome_keywords), 1))
        + 0.20 * ratio(paper_count, 4)
    )

    hardware_penalty = 0.18 if any(token in hardware_requirement for token in ("multi", "cluster", "tpu")) else 0.0
    feasibility = clamp(
        0.70
        + 0.10 * ratio(papers_with_limitations, max(paper_count, 1))
        - 0.08 * min(len(risk_factors), 4)
        - hardware_penalty
    )

    benchmark_readiness = clamp(
        0.55 * ratio(len(benchmark_candidates), 3)
        + 0.45 * ratio(papers_with_datasets, max(paper_count, 1))
    )

    measurement_quality = clamp(
        0.50 * ratio(len(measurable_outcomes), 3)
        + 0.30 * ratio(len(outcome_keywords), 4)
        + 0.20 * ratio(papers_with_limitations, max(paper_count, 1))
    )

    overall_score = clamp(
        0.35 * literature_support
        + 0.25 * feasibility
        + 0.20 * benchmark_readiness
        + 0.20 * measurement_quality
    )

    results = {
        "literature_support": round(literature_support, 4),
        "feasibility": round(feasibility, 4),
        "benchmark_readiness": round(benchmark_readiness, 4),
        "measurement_quality": round(measurement_quality, 4),
        "overall_score": round(overall_score, 4),
        "source_paper_count": paper_count,
        "benchmark_count": len(benchmark_candidates),
        "measurable_outcome_count": len(measurable_outcomes),
        "risk_factor_count": len(risk_factors),
        "experiment_spec": spec,
    }

    Path("results.json").write_text(json.dumps(results, indent=2))
    print("Deterministic experiment evaluation completed.")


if __name__ == "__main__":
    main()
'''
