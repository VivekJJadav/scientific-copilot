import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_copilot")
    try:
        async with e.connect() as c:
            r = await c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            tables = r.fetchall()
            print(f"Found {len(tables)} tables:")
            for t in tables:
                print(f"  - {t[0]}")
    except Exception as ex:
        print(f"ERROR: {type(ex).__name__}: {ex}")
    finally:
        await e.dispose()

asyncio.run(test())
