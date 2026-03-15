from dataclasses import dataclass

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
