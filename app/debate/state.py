from typing import TypedDict, Optional
from app.db.models import HypothesisModel
from app.core.atoms import ResearchAtom

class DebateState(TypedDict):
    hypothesis_id: str
    hypothesis: HypothesisModel
    source_papers: list[ResearchAtom]
    proposal: str
    critiques: list[str]
    rebuttals: list[str]
    round: int
    arbiter_verdict: Optional[str]
    final_hypothesis: Optional[HypothesisModel]
    rejection_reason: Optional[str]
