import asyncio
import uuid
from app.pipeline.tasks import run_publish
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id, draft, state FROM content_jobs ORDER BY created_at DESC LIMIT 1"))
        job = res.fetchone()
        if not job:
            print("No jobs found")
            return
        
        jid, draft, state = job
        print(f"DEBUG: Starting publish for {jid} in state {state}")
        # if state is already published or completed, maybe it already ran?
        try:
            res = await run_publish(str(jid), ["LinkedIn"])
            print(f"DEBUG: publish finished: {res}")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(run())
