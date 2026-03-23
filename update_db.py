import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import engine
from app.db.models import Experiment

async def update_exp():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(Experiment).limit(1)
        exp = (await db.execute(stmt)).scalars().first()
        if not exp:
            print("No experiment found! Run an experiment first.")
            return
        
        exp.status = "completed"
        exp.results = {"accuracy": 0.82, "loss": 0.34}
        await db.commit()
        print(f"EXPERIMENT_ID={exp.id}")

asyncio.run(update_exp())
