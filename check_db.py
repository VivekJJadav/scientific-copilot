import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.db.session import engine
from app.db.models import Paper

async def main():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        res = await session.execute(select(Paper.arxiv_status, func.count(Paper.id)).group_by(Paper.arxiv_status))
        print("Paper counts by status:")
        for row in res.all():
            print(f"- {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(main())
