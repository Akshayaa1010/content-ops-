import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Try to import from app or use hardcoded if failing
try:
    from app.config.settings import settings
    url = settings.database_url.replace("postgresql+asyncpg", "postgresql+asyncpg")
except:
    url = "postgresql+asyncpg://postgres:password@localhost:5432/contentops"

async def check():
    print(f"Checking URL: {url}")
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            print(f"DB Connection: SUCCESS (Result: {res.scalar()})")
            
            res = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
            ext = res.scalar()
            print(f"PGVector Extension: {'INSTALLED' if ext else 'MISSING'}")
    except Exception as e:
        print(f"DB Check Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check())
