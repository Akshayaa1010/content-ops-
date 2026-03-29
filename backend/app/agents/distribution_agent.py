# app/agents/distribution_agent.py
import uuid
from datetime import datetime, timezone
from app.db.database import AsyncSessionLocal
from app.db.models import PublishedContent

async def publish_content(job_id: str, channel: str, content: str, language: str = "en"):
    # Mocking external API calls (e.g., WordPress, LinkedIn)
    # In a real app, this would use httpx to hit those APIs
    
    mock_urls = {
        "CMS": f"https://blog.example.com/posts/{uuid.uuid4().hex[:8]}",
        "LinkedIn": f"https://linkedin.com/feed/update/{uuid.uuid4().hex[:8]}"
    }
    
    published_url = mock_urls.get(channel, f"https://example.com/content/{uuid.uuid4().hex[:8]}")
    
    async with AsyncSessionLocal() as db:
        published = PublishedContent(
            id=uuid.uuid4(),
            job_id=uuid.UUID(job_id),
            channel=channel,
            language=language,
            published_url=published_url,
            published_at=datetime.now(timezone.utc),
            performance_score=0.0  # Will be updated by IntelligenceAgent later
        )
        db.add(published)
        await db.commit()
    
    return published_url
