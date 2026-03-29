import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/contentops"

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE content_jobs ADD COLUMN violation_count INTEGER DEFAULT 0"))
            print("Migration successful: added violation_count column.")
        except Exception as e:
            print(f"Migration error (already exists?): {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
