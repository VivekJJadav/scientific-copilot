from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import Paper


@dataclass
class ResearchAtom:
    paper_id: str
    title: str
    abstract: str
    authors: list[dict]
    published_year: int
    pdf_url: str
    methods: list[str]
    limitations: list[str]
    claims: list[str]
    embedding: list[float] | None = None
    arxiv_status: str = "raw"

    @classmethod
    def from_paper(cls, paper: Paper) -> ResearchAtom:
        """Construct a ResearchAtom from a Paper DB model.

        This is the single canonical conversion point — do NOT
        reconstruct ResearchAtom from Paper fields manually elsewhere.
        """
        return cls(
            paper_id=paper.arxiv_id,
            title=paper.title,
            abstract=paper.abstract,
            authors=paper.authors or [],
            published_year=paper.published_year,
            pdf_url=paper.pdf_url,
            methods=paper.methods or [],
            limitations=paper.limitations or [],
            claims=paper.claims or [],
            embedding=(
                [float(x) for x in paper.embedding]
                if paper.embedding is not None
                else None
            ),
            arxiv_status=paper.arxiv_status,
        )

    def to_dict(self) -> dict:
        return asdict(self)
