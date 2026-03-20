"""Hypothesis dataclass for grounded research hypotheses."""

import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class Hypothesis:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    motivation: str = ""
    core_claim: str = ""
    method_sketch: str = ""
    expected_outcome: str = ""
    risk_factors: list[str] = field(default_factory=list)
    novelty_score: float = 0.0
    feasibility_score: float = 0.0
    hardware_requirement: str = ""
    source_paper_ids: list[str] = field(default_factory=list)
    gap_description: str = ""
    status: str = "pending"  # pending / approved / rejected / running / done
    iteration_count: int = 0
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to a plain dict for serialization."""
        d = asdict(self)
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        return d

    def passes_threshold(self, novelty_min: float, feasibility_min: float) -> bool:
        """Check if this hypothesis meets the novelty and feasibility thresholds."""
        return self.novelty_score >= novelty_min and self.feasibility_score >= feasibility_min
