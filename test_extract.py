import asyncio
from sqlalchemy import select
from app.db.session import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.db.models import Paper
from app.extraction.extractor import PaperExtractor
from app.core.atoms import ResearchAtom

async def main():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Reset all failed to raw
        stmt = select(Paper).where(Paper.arxiv_status == "extraction_failed")
        res = await session.execute(stmt)
        papers = res.scalars().all()
        if not papers:
            print("No extraction_failed papers found.")
            return

        for paper in papers:
            paper.arxiv_status = "raw"
        
        await session.commit()
        print(f"Reset {len(papers)} papers to raw.")


        atom = ResearchAtom(
            paper_id=paper.arxiv_id,
            title=paper.title,
            abstract=paper.abstract,
            authors=paper.authors or [],
            published_year=paper.published_year,
            pdf_url=paper.pdf_url,
            methods=[],
            limitations=[],
            claims=[],
            embedding=None,
            arxiv_status=paper.arxiv_status,
        )

        extractor = PaperExtractor()
        try:
            res_atom = await extractor.extract_one(atom, session)
            print("Result status:", res_atom.arxiv_status)
        except Exception as e:
            print("Exception during extraction:", e)

if __name__ == "__main__":
    asyncio.run(main())
