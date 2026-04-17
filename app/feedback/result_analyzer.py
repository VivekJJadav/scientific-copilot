"""ResultAnalyzer: Analyzes experiment results, labels outcomes, extracts lessons."""

import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field, ValidationError

from app.db.models import Experiment, ExperimentResult, Gap, HypothesisModel
from app.llm.router import LLMRouter, LLMUnavailableError
from app.llm.prompts import RESULT_ANALYSIS_PROMPT, NEGATIVE_RESULT_GAP_PROMPT

logger = structlog.get_logger(__name__)


class ResultAnalysisResponseSchema(BaseModel):
    outcome: str = "inconclusive"
    result_summary: str = "Analysis completed."
    lessons_learned: list[str] = Field(default_factory=list)
    failure_reason: str | None = None


class FailureGapResponseSchema(BaseModel):
    gap_type: str = "negative_result"
    gap_description: str


class ResultAnalyzer:
    """Analyzes completed experiment results and labels outcomes."""

    def __init__(self):
        self.llm = LLMRouter()

    async def analyze(self, results: dict, hypothesis: dict, experiment_id: str) -> dict:
        """Analyze a single experiment's results against its hypothesis.

        Returns:
            Dict with outcome, result_summary, lessons_learned, failure_reason.
        """
        prompt = RESULT_ANALYSIS_PROMPT.format(
            hypothesis_title=hypothesis.get("title", ""),
            core_claim=hypothesis.get("core_claim", ""),
            expected_outcome=hypothesis.get("expected_outcome", ""),
            results=json.dumps(results, indent=2, default=str),
        )

        try:
            response = await self.llm.complete(prompt, expect_json=True)
            parsed = ResultAnalysisResponseSchema.model_validate_json(response)

            outcome = parsed.outcome.lower()
            if outcome not in ("validated", "failed", "inconclusive"):
                outcome = "inconclusive"

            lessons = parsed.lessons_learned
            if not lessons:
                lessons = ["No specific lessons extracted."]

            return {
                "outcome": outcome,
                "result_summary": parsed.result_summary,
                "lessons_learned": lessons,
                "failure_reason": parsed.failure_reason,
            }

        except ValidationError as e:
            logger.warning(
                "result_analysis_validation_failed",
                error=str(e),
                experiment_id=experiment_id,
                raw_output=response if "response" in locals() else None,
            )
            return {
                "outcome": "inconclusive",
                "result_summary": "Error during LLM analysis of results.",
                "lessons_learned": ["Failed to extract reliable lessons from metrics."],
                "failure_reason": None,
            }
        except Exception as e:
            logger.warning("result_analysis_parse_failed", error=str(e), experiment_id=experiment_id)
            return {
                "outcome": "inconclusive",
                "result_summary": "Error during LLM analysis of results.",
                "lessons_learned": ["Failed to extract reliable lessons from metrics."],
                "failure_reason": None,
            }

    async def run_analysis_pipeline(self, db: AsyncSession) -> dict:
        """Analyze all completed experiments that haven't been analyzed yet.

        Returns:
            Summary dict: {analyzed, validated, failed, inconclusive, new_gaps}.
        """
        summary = {"analyzed": 0, "validated": 0, "failed": 0, "inconclusive": 0, "new_gaps": 0}

        # Find completed experiments without an experiment_results row
        stmt = (
            select(Experiment)
            .outerjoin(ExperimentResult, Experiment.id == ExperimentResult.experiment_id)
            .where(Experiment.status == "completed")
            .where(ExperimentResult.id.is_(None))
        )
        experiments = (await db.execute(stmt)).scalars().all()

        for exp in experiments:
            hypothesis = await db.get(HypothesisModel, exp.hypothesis_id)
            if not hypothesis:
                logger.warning("result_analysis_missing_hypothesis", experiment_id=str(exp.id))
                continue

            # If experiment has no results, mark inconclusive
            results = exp.results or {}

            analysis = await self.analyze(
                results=results,
                hypothesis={
                    "title": hypothesis.title,
                    "core_claim": hypothesis.core_claim,
                    "expected_outcome": hypothesis.expected_outcome,
                },
                experiment_id=str(exp.id),
            )

            # Persist ExperimentResult
            er = ExperimentResult(
                experiment_id=exp.id,
                hypothesis_id=hypothesis.id,
                outcome=analysis["outcome"],
                metrics=results,
                result_summary=analysis["result_summary"],
                lessons_learned=analysis["lessons_learned"],
            )
            db.add(er)
            summary["analyzed"] += 1
            summary[analysis["outcome"]] += 1

            # If failed, generate a negative-result gap
            if analysis["outcome"] == "failed":
                gap = await self._create_failure_gap(hypothesis, analysis, db)
                if gap:
                    summary["new_gaps"] += 1

        if summary["analyzed"] > 0:
            await db.commit()

        logger.info("result_analysis_pipeline_complete", **summary)
        return summary

    async def _create_failure_gap(
        self, hypothesis: HypothesisModel, analysis: dict, db: AsyncSession
    ) -> Gap | None:
        """Create a new gap from a failed experiment using LLM."""
        try:
            prompt = NEGATIVE_RESULT_GAP_PROMPT.format(
                hypothesis_title=hypothesis.title,
                core_claim=hypothesis.core_claim,
                failure_reason=analysis.get("failure_reason") or "Unknown",
                lessons_learned=", ".join(analysis.get("lessons_learned", [])),
            )
            response = await self.llm.complete(prompt, expect_json=True)
            parsed = FailureGapResponseSchema.model_validate_json(response)

            gap = Gap(
                gap_type=parsed.gap_type,
                gap_description=parsed.gap_description,
                source_paper_ids=hypothesis.source_paper_ids or [],
                similarity=0.0,
                used=False,
            )
            db.add(gap)
            logger.info("failure_gap_created", hypothesis_title=hypothesis.title)
            return gap

        except ValidationError as e:
            logger.warning(
                "failure_gap_validation_failed",
                error=str(e),
                raw_output=response if "response" in locals() else None,
            )
            # Fallback: create a simple gap without LLM
            gap = Gap(
                gap_type="negative_result",
                gap_description=f"Failed hypothesis '{hypothesis.title}': {analysis.get('result_summary', '')}",
                source_paper_ids=hypothesis.source_paper_ids or [],
                similarity=0.0,
                used=False,
            )
            db.add(gap)
            return gap
        except Exception as e:
            logger.warning("failure_gap_creation_failed", error=str(e))
            # Fallback: create a simple gap without LLM
            gap = Gap(
                gap_type="negative_result",
                gap_description=f"Failed hypothesis '{hypothesis.title}': {analysis.get('result_summary', '')}",
                source_paper_ids=hypothesis.source_paper_ids or [],
                similarity=0.0,
                used=False,
            )
            db.add(gap)
            return gap
