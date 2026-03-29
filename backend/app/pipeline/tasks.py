# app/pipeline/tasks.py
import asyncio
import json
import uuid
from app.pipeline.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.db.models import ContentJob
from app.pipeline.state_machine import transition, ContentJobState
from app.pipeline.embeddings import embed_query
from sqlalchemy import select, update

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, file_path: str, document_id: str):
    print(f"TASK START: Processing Document {document_id}")
    import asyncio
    return asyncio.run(process_document(file_path, document_id))

@celery_app.task(bind=True, max_retries=3)
def run_pipeline_task(self, job_id: str):
    print(f"TASK START: Pipeline for {job_id}")
    import asyncio
    try:
        return asyncio.run(orchestrate_job(job_id))
    except Exception as e:
        print(f"TASK ERROR: {e}")
        raise e

async def orchestrate_job(job_id: str):
    print(f"PIPELINE START: {job_id}")
    from app.agents.intelligence_agent import suggest_strategy
    from app.agents.knowledge_agent import search_knowledge, process_document, index_policy_file
    from app.agents.governance_agent import check_compliance
    from app.agents.localisation_agent import localise_all
    from app.agents.llm_client import generate
    from app.agents.distribution_agent import publish_content
    from app.agents.publishing_agent import publish_to_sheets

    # Ensure policies are indexed
    print(f"STEP: Indexing policies")
    await index_policy_file("app/policies/brand_policies.txt")
    
    async with AsyncSessionLocal() as db:
        # Fetch job initially
        result = await db.execute(select(ContentJob).where(ContentJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if not job: return {"error": "Job not found"}

        # 1. Strategy Adjustment (Intelligence)
        print(f"STEP: Suggesting Strategy for {job.brief.get('topic')}")
        await transition(db, job_id, ContentJobState.STRATEGY_ADJUST)
        
        try:
            strategy = await suggest_strategy(job.brief)
            refined_brief = strategy.get("adjusted_brief", job.brief)
            print(f"STEP: Strategy refined. Suggested channels: {strategy.get('suggested_channels')}")
        except Exception as e:
            print(f"WARNING: Strategy refinement failed, using original brief: {e}")
            refined_brief = job.brief
        
        # Save refined brief
        await db.execute(
            update(ContentJob)
            .where(ContentJob.id == uuid.UUID(job_id))
            .values(brief=refined_brief)
        )
        await db.commit()
        
        brief = refined_brief
        target_langs = brief.get("target_languages", [])
        if not target_langs or "ta" not in target_langs:
            target_langs = list(set((target_langs or []) + ["ta", "hi", "bn", "te", "ml"])) # Default to Indian language pack
            print(f"STEP: Target languages expanded to: {target_langs}")
        
        # 3. Retrieving Context
        await transition(db, job_id, ContentJobState.RETRIEVING)
        
        source_doc_ids = brief.get("source_doc_ids", [])
        context_chunks = []
        
        if source_doc_ids:
            # Fetch specifically from selected docs
            from app.db.models import DocumentChunk
            doc_uuids = [uuid.UUID(did) for did in source_doc_ids]
            result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id.in_(doc_uuids))
                .limit(10)
            )
            context_chunks = [row.chunk_text for row in result.scalars().all()]
        else:
            # Fallback to general vector search
            query_text = f"{brief.get('topic')} {brief.get('audience')}"
            query_emb = await embed_query(query_text)
            context_chunks = await search_knowledge(query_emb, limit=3)
        
        context_str = "\n---\n".join(context_chunks)

        # 3. Drafting
        print(f"STEP: Generating Content Draft with Groq...")
        await transition(db, job_id, ContentJobState.DRAFTING)
        system_prompt = "You are a world-class copywriter. Create a deep-dive blog post and a matching LinkedIn post based on the brief and context provided. Return both distinctly."
        user_message = f"Brief: {json.dumps(brief)}\n\nContext:\n{context_str}"
        
        try:
            draft_text = await generate(system_prompt, user_message)
            print(f"STEP: Content draft generated (length: {len(draft_text)})")
            
            # --- AUTOMATED ARCHIVAL TO GOOGLE SHEETS (DEPRECATED: Move to publish step) ---
            # print(f"STEP: Archiving generated draft to Google Sheets (Column A)...")
            # publish_to_sheets(draft_text)
            
            await db.execute(update(ContentJob).where(ContentJob.id == uuid.UUID(job_id)).values(draft={"text": draft_text}))
            await db.commit()
            await transition(db, job_id, ContentJobState.DRAFT_READY)
        except Exception as e:
            print(f"CRITICAL ERROR: Groq generation failed: {e}")
            await transition(db, job_id, ContentJobState.FAILED)
            return {"status": "failed", "error": f"Groq generation failed: {str(e)}"}

        # 4. Compliance Check (Governance)
        # 4. Compliance Check (Governance) with Self-Correction Loop
        await transition(db, job_id, ContentJobState.COMPLIANCE_CHECK)
        
        attempts = 0
        max_attempts = 3
        total_violations = 0
        final_compliance_report = {}
        fixed_draft = draft_text
        
        while attempts < max_attempts:
            print(f"COMPLIANCE ATTEMPT {attempts + 1}")
            compliance_report = await check_compliance(fixed_draft, brief)
            final_compliance_report = compliance_report
            
            # Record violations from this run
            current_violations = compliance_report.get("violation_count", 0)
            if compliance_report.get("status") == "FAIL" or current_violations > 0:
                total_violations += (current_violations if current_violations > 0 else 1)
                print(f"Violations found: {current_violations}. Self-correcting...")
                
                # Re-draft with feedback if failed
                system_prompt = "You are a world-class copywriter and compliance expert. Rewrite the draft to fix the following brand policy violations."
                user_message = f"Violations Report: {compliance_report.get('report')}\n\nCurrent Draft: {fixed_draft}"
                fixed_draft = await generate(system_prompt, user_message)
                attempts += 1
            else:
                print("Compliance PASS.")
                break

        # Save the final results and the cumulative violation count
        await db.execute(update(ContentJob).where(ContentJob.id == uuid.UUID(job_id)).values(
            compliance_report=final_compliance_report,
            draft={"text": fixed_draft},
            violation_count=total_violations
        ))
        await db.commit()
        
        # Transition to APPROVED to allow localisation/publishing
        await transition(db, job_id, ContentJobState.APPROVED)

        # 5. Localisation (Parallel)
        if target_langs:
            print(f"STEP: Localising into {target_langs}...")
            await transition(db, job_id, ContentJobState.LOCALISING)
            try:
                localised = await localise_all(fixed_draft, target_langs)
                await db.execute(update(ContentJob).where(ContentJob.id == uuid.UUID(job_id)).values(localised_versions=localised))
                await db.commit()
                print(f"STEP: Localization complete ({len(localised)} versions)")
            except Exception as e:
                print(f"WARNING: Localization failed for some/all languages: {e}")
                # We don't fail the whole job if localization has issues
        
        # 6. Human Review Gate
        print(f"STEP: Pipeline complete. Job {job_id} is in HUMAN_REVIEW.")
        await transition(db, job_id, ContentJobState.HUMAN_REVIEW)
        
        # At this point, the task ends and waits for the user to "approve" via API.
        # The 'approve' API will then trigger a separate 'publish' task or resume this flow.
        return {"status": "waiting_for_review", "job_id": job_id}

@celery_app.task
def publish_job_task(job_id: str, channels: list[str]):
    import asyncio
    return asyncio.run(run_publish(job_id, channels))

async def run_publish(job_id: str, channels: list[str]):
    from app.agents.distribution_agent import publish_content
    from app.agents.publishing_agent import publish_to_sheets
    async with AsyncSessionLocal() as db:
        await transition(db, job_id, ContentJobState.APPROVED)
        
        result = await db.execute(select(ContentJob).where(ContentJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        
        draft_text = job.draft.get("text", "") if job.draft else ""
        
        for channel in channels:
            # 1. Standard publishing logs/records
            await publish_content(job_id, channel, draft_text)
            
            # 2. Automated Publishing via Google Sheets/Zapier per requirements
            if channel.lower() == "linkedin":
                print(f"PIPELINE: Sending Job {job_id} to Google Sheets for Zapier...")
                linkedin_content = job.draft.get("linkedin_post") if job.draft else None
                publish_res = publish_to_sheets(linkedin_content or draft_text)
                if publish_res.get("status") == "error":
                    print(f"PIPELINE ERROR: Failed to publish to sheets: {publish_res.get('message')}")
                    # We continue but maybe log it prominently
            
        # Finalize job status per requirement 8
        await transition(db, job_id, ContentJobState.PUBLISHED)
        await transition(db, job_id, ContentJobState.COMPLETED)
        return {"status": "published", "job_id": job_id}