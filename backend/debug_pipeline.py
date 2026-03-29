import asyncio
import uuid
from app.pipeline.tasks import orchestrate_job
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id FROM content_jobs WHERE state IN ('briefed', 'strategy_adjustment') LIMIT 1"))
        jid = res.scalar()
        if not jid:
            print("No jobs found")
            return
        print(f"DEBUG: Starting orchestration for {jid}")
        try:
            await orchestrate_job(str(jid))
            print("DEBUG: Orchestration finished")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(run())
