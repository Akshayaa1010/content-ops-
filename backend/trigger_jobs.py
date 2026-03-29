import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config.settings import settings
from app.pipeline.tasks import run_pipeline_task

async def trigger():
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT id FROM content_jobs WHERE state='briefed' OR state='strategy_adjustment' LIMIT 5"))
            ids = [str(r[0]) for r in res.fetchall()]
            print(f"Triggering jobs: {ids}")
            for jid in ids:
                run_pipeline_task.delay(jid)
    except Exception as e:
        print(f"Trigger Failed: {e}")

if __name__ == "__main__":
    asyncio.run(trigger())
