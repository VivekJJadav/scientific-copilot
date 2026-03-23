import asyncio
import arxiv
import structlog
from app.core.atoms import ResearchAtom

logger = structlog.get_logger(__name__)

async def fetch_papers(query: str, max_results: int) -> list[ResearchAtom]:
    logger.info("fetching_papers_from_arxiv", query=query, max_results=max_results)
    print(f"DEBUG: ARXIV_MAX_RESULTS = {max_results}")
    
    def _fetch():
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        return list(client.results(search))

    results = await asyncio.to_thread(_fetch)
    logger.info("arxiv_fetch_complete", result_count=len(results))

    atoms = []
    for res in results:
        # Strip version from format "2301.00001v2"
        arxiv_id = res.get_short_id().split("v")[0]
        
        authors = [{"name": author.name} for author in res.authors]
        
        atom = ResearchAtom(
            paper_id=arxiv_id,
            title=res.title,
            abstract=res.summary,
            authors=authors,
            published_year=res.published.year,
            pdf_url=res.pdf_url,
            methods=[],
            limitations=[],
            claims=[],
            embedding=None,
            arxiv_status="raw"
        )
        atoms.append(atom)

    return atoms
