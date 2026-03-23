from typing import TypedDict, Optional
from app.reasoning.hypothesis import Hypothesis
from app.core.atoms import ResearchAtom

class DebateState(TypedDict):
    hypothesis_id: str
    hypothesis: Hypothesis
    source_papers: list[ResearchAtom]
    proposal: str
    critiques: list[str]
    rebuttals: list[str]
    round: int
    arbiter_verdict: Optional[str]
    final_hypothesis: Optional[Hypothesis]
    rejection_reason: Optional[str]
