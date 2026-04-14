import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.db.session import engine
from app.db.models import Paper, HypothesisModel, Gap

async def main():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Paper counts
        res = await session.execute(select(Paper.arxiv_status, func.count(Paper.id)).group_by(Paper.arxiv_status))
        print("Paper counts by status:")
        for row in res.all():
            print(f"  {row[0]}: {row[1]}")
        
        # Hypothesis counts
        res2 = await session.execute(
            select(
                HypothesisModel.status, 
                HypothesisModel.debate_rounds, 
                func.count(HypothesisModel.id)
            ).group_by(HypothesisModel.status, HypothesisModel.debate_rounds)
        )
        print("\nHypothesis counts (status, debate_rounds):")
        for row in res2.all():
            print(f"  status={row[0]}, debate_rounds={row[1]}: count={row[2]}")
        
        total = await session.execute(select(func.count(HypothesisModel.id)))
        print(f"\nTotal hypotheses: {total.scalar_one()}")
        
        # Gap counts
        res3 = await session.execute(select(Gap.used, func.count(Gap.id)).group_by(Gap.used))
        print("\nGap counts (used):")
        for row in res3.all():
            print(f"  used={row[0]}: count={row[1]}")

if __name__ == "__main__":
    asyncio.run(main())
