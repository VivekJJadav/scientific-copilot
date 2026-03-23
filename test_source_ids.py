import asyncio
import json
from app.db.session import get_session
from app.reasoning.hypothesis_generator import HypothesisGenerator
from app.core.atoms import ResearchAtom

async def test():
    async for db in get_session():
        generator = HypothesisGenerator()
        gap = {
            "description": "Lack of efficient embodied RL constraints for single GPU.",
            "source_paper_ids": ["2304.05678"]
        }
        atoms = [
            ResearchAtom(
                paper_id="2304.05678",
                title="Existing Paper 1",
                abstract="Test abstract",
                authors=["A"],
                published_year=2023,
                pdf_url="",
                methods=["RL"], limitations=["Slow"], claims=["Works"], arxiv_status="processed",
                embedding=None
            )
        ]
        for _ in range(5):
            h = await generator.generate(gap, atoms, db)
            if h:
                print("Generated Hypothesis with IDs:", h.source_paper_ids)
                break
            else:
                print("Failed JSON parse, retrying...")
        else:
            print("Failed to generate after 5 retries.")

if __name__ == "__main__":
    asyncio.run(test())
