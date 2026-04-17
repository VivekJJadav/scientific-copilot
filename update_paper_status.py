import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.session import engine
from app.db.models import Paper

async def reset_failed_papers():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await db.execute(update(Paper).where(Paper.arxiv_status == 'extraction_failed').values(arxiv_status='embedded'))
        await db.commit()
    print("Done resetting extraction_failed to embedded")

asyncio.run(reset_failed_papers())
