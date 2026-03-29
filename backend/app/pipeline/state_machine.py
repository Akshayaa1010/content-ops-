# app/pipeline/state_machine.py
from enum import Enum
from datetime import datetime, timezone

class ContentJobState(str, Enum):
    BRIEFED          = "briefed"
    STRATEGY_ADJUST  = "strategy_adjustment"
    RETRIEVING       = "retrieving"
    DRAFTING         = "drafting"
    DRAFT_READY      = "draft_ready"
    COMPLIANCE_CHECK = "compliance_check"
    HUMAN_REVIEW     = "human_review"
    APPROVED         = "approved"
    LOCALISING       = "localising"
    SCHEDULING       = "scheduling"
    PUBLISHED        = "published"
    COMPLETED        = "completed"
    FAILED           = "failed"
    REJECTED         = "rejected"

VALID_TRANSITIONS = {
    ContentJobState.BRIEFED:          [ContentJobState.STRATEGY_ADJUST, ContentJobState.DRAFTING],
    ContentJobState.STRATEGY_ADJUST:  [ContentJobState.RETRIEVING, ContentJobState.FAILED],
    ContentJobState.RETRIEVING:       [ContentJobState.DRAFTING, ContentJobState.FAILED],
    ContentJobState.DRAFTING:         [ContentJobState.DRAFT_READY, ContentJobState.FAILED],
    ContentJobState.DRAFT_READY:      [ContentJobState.COMPLIANCE_CHECK],
    ContentJobState.COMPLIANCE_CHECK: [ContentJobState.APPROVED, ContentJobState.HUMAN_REVIEW],
    ContentJobState.HUMAN_REVIEW:     [ContentJobState.APPROVED, ContentJobState.REJECTED],
    ContentJobState.APPROVED:         [ContentJobState.LOCALISING, ContentJobState.SCHEDULING, ContentJobState.PUBLISHED],
    ContentJobState.LOCALISING:       [ContentJobState.SCHEDULING, ContentJobState.FAILED],
    ContentJobState.SCHEDULING:       [ContentJobState.PUBLISHED],
    ContentJobState.PUBLISHED:        [ContentJobState.COMPLETED],
}

async def transition(db, job_id: str, new_state: ContentJobState):
    from app.db.models import ContentJob, StageTiming
    from sqlalchemy import select, update
    import uuid

    result = await db.execute(
        select(ContentJob).where(ContentJob.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    current = ContentJobState(job.state)
    if current == new_state:
        return # Idempotent transition
        
    if new_state not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(f"Illegal transition: {current} -> {new_state}")

    now = datetime.now(timezone.utc)

    await db.execute(
        update(StageTiming)
        .where(StageTiming.job_id == uuid.UUID(job_id))
        .where(StageTiming.stage == current.value)
        .where(StageTiming.exited_at == None)
        .values(exited_at=now,
                duration_seconds=(now - datetime.now(timezone.utc)).total_seconds() * -1)
    )

    db.add(StageTiming(
        job_id=uuid.UUID(job_id),
        stage=new_state.value,
        entered_at=now,
        is_human_stage=(new_state == ContentJobState.HUMAN_REVIEW)
    ))

    await db.execute(
        update(ContentJob)
        .where(ContentJob.id == uuid.UUID(job_id))
        .values(state=new_state.value, updated_at=now)
    )
    await db.commit()