"""DebateRecord: Structured representation of a completed debate.

This is the semantic 'currency' the arbiter reasons over when evaluating
child hypotheses — analogous to how ResearchAtom is the currency for papers.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import DebateHistory


@dataclass
class DebateRecord:
    """Immutable snapshot of a single completed debate."""

    hypothesis_id: str
    hypothesis_title: str
    core_claim: str
    objections: list[str]            # distilled 1-sentence critic objections
    rebuttals: list[str]             # distilled 1-sentence rebuttal summaries
    verdict: str                     # "PASS" | "FAIL"
    rejection_reason: str | None
    arbiter_notes: str | None
    surviving_risks: list[str]
    novelty_score: float
    feasibility_score: float
    addressed_prior_objections: list[str]  # which parent objections were resolved
    created_at: datetime | None = None

    @classmethod
    def from_db(cls, row: DebateHistory, hypothesis_title: str, core_claim: str) -> DebateRecord:
        """Construct a DebateRecord from a DebateHistory DB row.

        This is the single canonical conversion point — do NOT
        reconstruct DebateRecord from DebateHistory fields manually elsewhere.
        """
        return cls(
            hypothesis_id=str(row.hypothesis_id),
            hypothesis_title=hypothesis_title,
            core_claim=core_claim,
            objections=row.objections or [],
            rebuttals=row.rebuttals or [],
            verdict=row.verdict,
            rejection_reason=row.rejection_reason,
            arbiter_notes=row.arbiter_notes,
            surviving_risks=row.surviving_risks or [],
            novelty_score=row.final_novelty_score,
            feasibility_score=row.final_feasibility_score,
            addressed_prior_objections=row.addressed_prior_objections or [],
            created_at=row.created_at,
        )

    def to_dict(self) -> dict:
        return asdict(self)
