from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
