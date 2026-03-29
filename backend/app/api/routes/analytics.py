# app/api/routes/analytics.py
"""
Analytics API — Engagement Metrics for Published Content
=========================================================
Endpoints:
  GET  /api/analytics/metrics/{content_id}          → raw metrics
  GET  /api/analytics/metrics/{content_id}/insights → engagement tier + report
  POST /api/analytics/metrics/{content_id}/generate → manually trigger metric generation
"""

import logging
import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import ContentJob, ContentMetrics
from app.agents.analytics_agent import generate_metrics, build_insight_report

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_uuid(content_id: str) -> uuid_lib.UUID:
    """Validate and parse string UUID, raising a 422-grade HTTPException on failure."""
    try:
        return uuid_lib.UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid UUID format: {content_id}")


async def _get_job_or_404(db: AsyncSession, content_id: str) -> ContentJob:
    uid = _parse_uuid(content_id)
    result = await db.execute(select(ContentJob).where(ContentJob.id == uid))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Content job {content_id} not found.")
    return job


async def _get_metrics_or_404(db: AsyncSession, content_id: str) -> ContentMetrics:
    uid = _parse_uuid(content_id)
    result = await db.execute(
        select(ContentMetrics)
        .where(ContentMetrics.content_id == uid)
        .order_by(ContentMetrics.created_at.desc())
    )
    metrics_row = result.scalar_one_or_none()
    if not metrics_row:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for content_id={content_id}. "
                   "Publish the job first or call /generate to simulate.",
        )
    return metrics_row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/metrics/{content_id}")
async def get_metrics(content_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return raw engagement metrics for a published content item.
    404 if metrics have not been generated yet.
    """
    logger.info("GET /metrics/%s — fetching raw metrics", content_id)
    metrics_row = await _get_metrics_or_404(db, content_id)

    return {
        "content_id":       content_id,
        "likes":            metrics_row.likes,
        "comments":         metrics_row.comments,
        "shares":           metrics_row.shares,
        "engagement_score": metrics_row.engagement_score,
        "content_length":   metrics_row.content_length,
        "source":           metrics_row.source,
        "created_at":       metrics_row.created_at.isoformat() if metrics_row.created_at else None,
    }


@router.get("/metrics/{content_id}/insights")
async def get_insights(content_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return engagement-tier analysis for a published content item.
    Combines raw metrics with a human-readable label.
    """
    logger.info("GET /metrics/%s/insights — fetching insight report", content_id)
    metrics_row = await _get_metrics_or_404(db, content_id)

    raw = {
        "likes":            metrics_row.likes,
        "comments":         metrics_row.comments,
        "shares":           metrics_row.shares,
        "engagement_score": metrics_row.engagement_score,
        "_source":          metrics_row.source,
        "generated_at":     metrics_row.created_at.isoformat() if metrics_row.created_at else None,
    }
    report = build_insight_report(raw)
    report["content_id"] = content_id
    return report


@router.post("/metrics/{content_id}/generate")
async def manually_generate_metrics(content_id: str, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger metric generation for any content job.
    Useful for testing or re-generating after a pipeline run.
    Idempotent — creates a new row each time (history is preserved).
    """
    logger.info("POST /metrics/%s/generate — manual metric generation", content_id)
    job = await _get_job_or_404(db, content_id)

    # Extract the best available text for metric scoring
    draft = job.draft or {}
    content_text = draft.get("linkedin_post") or draft.get("text") or job.brief.get("topic", "")

    metrics = generate_metrics(content_text)
    await _store_metrics(db, content_id, metrics)

    report = build_insight_report(metrics)
    report["content_id"] = content_id
    return {"detail": "Metrics generated successfully.", "report": report}


# ---------------------------------------------------------------------------
# Internal helper — also imported by pipeline/tasks.py after publishing
# ---------------------------------------------------------------------------

async def store_metrics_for_job(db: AsyncSession, content_id: str, content_text: str) -> dict:
    """
    Called automatically after a job reaches 'published' state.
    Generates simulated metrics and persists them to PostgreSQL.

    Returns the raw metrics dict.
    """
    metrics = generate_metrics(content_text)
    await _store_metrics(db, content_id, metrics)
    logger.info("Metrics stored for content_id=%s | score=%d", content_id, metrics["engagement_score"])
    return metrics


async def _store_metrics(db: AsyncSession, content_id: str, metrics: dict):
    uid = _parse_uuid(content_id)
    row = ContentMetrics(
        content_id       = uid,
        likes            = metrics["likes"],
        comments         = metrics["comments"],
        shares           = metrics["shares"],
        engagement_score = metrics["engagement_score"],
        content_length   = metrics.get("content_length", 0),
        source           = metrics.get("_source", "simulation"),
    )
    db.add(row)
    await db.commit()
