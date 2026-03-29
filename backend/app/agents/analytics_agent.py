# app/agents/analytics_agent.py
"""
Content Intelligence / Analytics Agent
=======================================
Simulation Layer — designed to be swapped with real social media API
integrations (LinkedIn API, Twitter API, etc.) without changing callers.

Simulation logic:
  likes    = base(15-80) + floor(content_length / 40)
  comments = base(2-15)  + floor(content_length / 200)
  shares   = base(1-10)  + floor(content_length / 300)

Engagement tiers:
  - High        : engagement_score >= 80
  - Moderate    : 40 <= engagement_score < 80
  - Low         : engagement_score  < 40

engagement_score = likes + (comments * 2) + (shares * 3)
"""

import random
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simulation constants — adjust here when plugging in real APIs
# ---------------------------------------------------------------------------
_LIKES_BASE_MIN    = 15
_LIKES_BASE_MAX    = 80
_COMMENTS_BASE_MIN = 2
_COMMENTS_BASE_MAX = 15
_SHARES_BASE_MIN   = 1
_SHARES_BASE_MAX   = 10

_LIKES_LENGTH_FACTOR    = 40   # 1 extra like  per N characters
_COMMENTS_LENGTH_FACTOR = 200  # 1 extra comment per N characters
_SHARES_LENGTH_FACTOR   = 300  # 1 extra share  per N characters

_HIGH_THRESHOLD     = 80
_MODERATE_THRESHOLD = 40


def generate_metrics(content: str) -> dict:
    """
    Generate simulated engagement metrics for a piece of content.

    Parameters
    ----------
    content : str
        The raw content text (LinkedIn post, blog excerpt, etc.)

    Returns
    -------
    dict with keys: likes, comments, shares, engagement_score, generated_at
    """
    if not content or not isinstance(content, str):
        logger.warning("generate_metrics called with empty/invalid content.")
        content = ""

    length = len(content)

    likes    = random.randint(_LIKES_BASE_MIN, _LIKES_BASE_MAX)    + (length // _LIKES_LENGTH_FACTOR)
    comments = random.randint(_COMMENTS_BASE_MIN, _COMMENTS_BASE_MAX) + (length // _COMMENTS_LENGTH_FACTOR)
    shares   = random.randint(_SHARES_BASE_MIN, _SHARES_BASE_MAX)   + (length // _SHARES_LENGTH_FACTOR)

    engagement_score = likes + (comments * 2) + (shares * 3)

    metrics = {
        "likes":            likes,
        "comments":         comments,
        "shares":           shares,
        "engagement_score": engagement_score,
        "content_length":   length,
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        # Metadata to make replacement with real APIs explicit
        "_source":          "simulation",
    }

    logger.info(
        "Metrics generated (simulation) | likes=%d comments=%d shares=%d score=%d content_len=%d",
        likes, comments, shares, engagement_score, length,
    )
    return metrics


def analyze_metrics(metrics: dict) -> str:
    """
    Analyse a metrics dict and return a human-readable engagement tier.

    Parameters
    ----------
    metrics : dict
        Output of generate_metrics() or a compatible metrics dict.

    Returns
    -------
    str  e.g. "High engagement", "Moderate engagement", "Low engagement"
    """
    score = metrics.get("engagement_score", 0)

    if score >= _HIGH_THRESHOLD:
        insight = "High engagement"
    elif score >= _MODERATE_THRESHOLD:
        insight = "Moderate engagement"
    else:
        insight = "Low engagement"

    logger.info("Metrics analysis | score=%d → %s", score, insight)
    return insight


def build_insight_report(metrics: dict) -> dict:
    """
    Combine raw metrics with the engagement tier into a single report dict
    suitable for API responses.
    """
    tier = analyze_metrics(metrics)
    return {
        "tier":             tier,
        "likes":            metrics.get("likes", 0),
        "comments":         metrics.get("comments", 0),
        "shares":           metrics.get("shares", 0),
        "engagement_score": metrics.get("engagement_score", 0),
        "generated_at":     metrics.get("generated_at"),
        "source":           metrics.get("_source", "simulation"),
    }
