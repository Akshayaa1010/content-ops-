import asyncio
import uuid
import json
from app.db.database import AsyncSessionLocal
from app.db.models import ContentJob
from sqlalchemy import select, update
from app.pipeline.tasks import run_publish

async def main():
    async with AsyncSessionLocal() as db:
        # Create a mock job representing Groq generation
        job_id = uuid.uuid4()
        job = ContentJob(
            id=job_id,
            brief={"topic": "Direct test of linkedin post!", "target_channels": ["LinkedIn"]},
            state="human_review",
            draft={"text": "Full draft text here.", "linkedin_post": "Direct test of linkedin post! Groq generated output here!"}
        )
        db.add(job)
        await db.commit()
        
        # Now trigger run_publish directly to bypass celery
        print(f"Triggering publish for {job_id}")
        res = await run_publish(str(job_id), ["LinkedIn"])
        print("Publish result:", res)

if __name__ == "__main__":
    asyncio.run(main())
