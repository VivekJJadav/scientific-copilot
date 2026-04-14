import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine
from app.db.models import Paper

async def main():
    async with AsyncSession(engine) as s:
        res = await s.execute(select(Paper.id, Paper.arxiv_id, Paper.cluster_id).where(Paper.cluster_id.isnot(None)))
        print(res.all())

if __name__ == '__main__':
    asyncio.run(main())
