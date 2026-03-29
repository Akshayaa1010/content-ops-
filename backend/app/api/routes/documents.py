# app/api/routes/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Document
from app.agents.knowledge_agent import generate_content as generate_knowledge_content
from app.pipeline.tasks import process_document_task, run_pipeline_task
from app.pipeline.state_machine import ContentJobState
from app.db.models import Document, ContentJob
import shutil, os, pdfplumber, uuid as uuid_lib
from sqlalchemy import select, update

router = APIRouter()

@router.get("/list")
async def list_docs(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Document).limit(20))
        docs = result.scalars().all()
        return [{"id": str(d.id), "filename": d.filename, "type": d.doc_type, "chunks": d.chunk_count} for d in docs]
    except Exception as e:
        print(f"DB Error in list_docs: {e}")
        return []

@router.post("/upload")
async def upload(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    print(f"UPLOADING: {file.filename}")
    if not os.path.exists("tmp_uploads"):
        os.makedirs("tmp_uploads", exist_ok=True)
    
    filename = os.path.basename(file.filename)
    path = os.path.join("tmp_uploads", filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    
    doc_type = file.filename.split(".")[-1].lower()
    
    extracted_text = ""
    if doc_type == "pdf":
        from fastapi import HTTPException
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}. Trying fallback to plain text...")
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
            except Exception as inner_e:
                print(f"Error parsing PDF and Fallback: {inner_e}")
                raise HTTPException(status_code=400, detail=f"Invalid or corrupted PDF file: {e}")
    elif doc_type == "txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            extracted_text = f.read()

    doc = Document(
        filename=file.filename, 
        doc_type=doc_type, 
        file_size_bytes=os.path.getsize(path),
        raw_text=extracted_text
    )
    
    try:
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        doc_id = str(doc.id)
        
        # Auto-create ContentJob for PDF
        job = ContentJob(
            brief={
                "topic": file.filename,
                "content_format": "blog_post",
                "target_audience": "General",
                "tone": "Professional",
                "source_doc_ids": [doc_id]
            },
            state=ContentJobState.BRIEFED.value
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)

        try:
            process_document_task.delay(path, doc_id)
            run_pipeline_task.delay(job_id)
        except Exception as ce:
            print(f"Celery Error: {ce}")
    except Exception as e:
        print(f"DB Error in upload: {e}")
        doc_id = "demo-id"
        job_id = None
    
    print(f"UPLOAD SUCCESS: {doc_id}, JOB: {job_id}")
    return {
        "document_id": doc_id, 
        "job_id": job_id,
        "filename": file.filename, 
        "status": "indexing" if doc_id != "demo-id" else "demo-mode",
        "extracted_text": extracted_text
    }

from pydantic import BaseModel
class GenerateRequest(BaseModel):
    text: str

@router.post("/generate_content")
async def generate_content_endpoint(payload: GenerateRequest, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    import json
    from app.agents.governance_agent import sync_review_content
    from app.agents.llm_client import generate_json
    from app.pipeline.state_machine import transition
    try:
        if not payload.text:
            raise HTTPException(status_code=400, detail="No text provided")

        # Create a real ContentJob so the pipeline tab can track this generation
        job = ContentJob(
            brief={
                "topic": "Groq Content Generation",
                "content_format": "blog_post",
                "target_audience": "General",
                "tone": "Professional",
                "source_doc_ids": []
            },
            state=ContentJobState.DRAFTING.value,
            violation_count=0
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)
        print(f"Created ContentJob {job_id} for Groq generation")

        # Step 1: Generate initial content
        print("Generating content with Groq...")
        result = await generate_knowledge_content(payload.text)

        # Save initial draft & move to compliance check
        draft_text = result.get("blog", "") + "\n\n" + result.get("linkedin_post", "")
        await db.execute(
            update(ContentJob)
            .where(ContentJob.id == job.id)
            .values(draft={"text": draft_text, "blog": result.get("blog"), "linkedin_post": result.get("linkedin_post")})
        )
        await db.commit()
        await transition(db, job_id, ContentJobState.DRAFT_READY)
        await transition(db, job_id, ContentJobState.COMPLIANCE_CHECK)

        # Step 2: Governance loop — check and re-generate if violations found
        max_attempts = 3
        attempt = 1
        total_violations = 0
        governance_passed = False
        governance_message = "Content aligns with brand policies."
        last_feedback = ""

        while attempt <= max_attempts:
            print(f"Governance Check Attempt {attempt}/{max_attempts}...")
            review = await sync_review_content(result)

            if review.get("status") == "PASS":
                governance_passed = True
                governance_message = review.get("feedback", "Content fully aligns with brand policies.")
                break
            else:
                last_feedback = review.get("feedback", "Unknown violation")
                total_violations += 1
                print(f"Governance FAIL (violation #{total_violations}). Feedback: {last_feedback}")

                # Persist current violation count to DB so UI can poll updates
                await db.execute(
                    update(ContentJob)
                    .where(ContentJob.id == job.id)
                    .values(violation_count=total_violations)
                )
                await db.commit()

                if attempt < max_attempts:
                    correction_prompt = (
                        f"The content violated brand policies. Rewrite to fix:\n{last_feedback}\n\n"
                        f"Original Drafts:\n{json.dumps(result)}\n\n"
                        f"Return corrected JSON with 'blog' and 'linkedin_post' keys."
                    )
                    try:
                        corrected_json = await generate_json(
                            "You are a strict content reviser. Output MUST be valid JSON with 'blog' and 'linkedin_post' keys.",
                            correction_prompt
                        )
                        result = json.loads(corrected_json)
                        # Update draft in DB with corrected content
                        draft_text = result.get("blog", "") + "\n\n" + result.get("linkedin_post", "")
                        await db.execute(
                            update(ContentJob)
                            .where(ContentJob.id == job.id)
                            .values(draft={"text": draft_text, "blog": result.get("blog"), "linkedin_post": result.get("linkedin_post")})
                        )
                        await db.commit()
                    except Exception as e:
                        print(f"Correction failed: {e}")
                        break
                else:
                    governance_message = f"Failed policy check after {max_attempts} attempts: {last_feedback}"
            attempt += 1

        # Step 3: Save final compliance report and move to appropriate state
        compliance_report = {
            "status": "PASS" if governance_passed else "FAIL",
            "report": governance_message
        }
        final_state = ContentJobState.HUMAN_REVIEW if governance_passed else ContentJobState.HUMAN_REVIEW
        await db.execute(
            update(ContentJob)
            .where(ContentJob.id == job.id)
            .values(
                compliance_report=compliance_report,
                violation_count=total_violations
            )
        )
        await db.commit()
        await transition(db, job_id, final_state)

        print(f"Generation complete. Violations: {total_violations}, Passed: {governance_passed}")
        
        # Automatically append LinkedIn post to Google Sheets
        linkedin_post_content = result.get("linkedin_post", "")
        if linkedin_post_content:
            from app.agents.publishing_agent import publish_to_sheets
            import asyncio
            print("Automatically appending LinkedIn post to Google Sheets...")
            try:
                sheet_result = await asyncio.to_thread(publish_to_sheets, linkedin_post_content)
                print(f"Google Sheets append result: {sheet_result}")
            except Exception as e:
                print(f"Error appending to Google Sheets natively: {e}")

        result["governance_status"] = "passed" if governance_passed else "failed"
        result["governance_message"] = governance_message
        result["job_id"] = job_id
        result["violation_count"] = total_violations
        return result
    except Exception as e:
        import traceback
        print(f"Error generating content: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

class TranslateRequest(BaseModel):
    text: str
    languages: list[str]

@router.post("/translate")
async def translate_endpoint(payload: TranslateRequest):
    from fastapi import HTTPException
    from app.agents.localization_agent import translate_multiple
    try:
        if not payload.text or not payload.languages:
            raise HTTPException(status_code=400, detail="Text and languages are required")
        print(f"Translating to: {payload.languages}")
        results = await translate_multiple(payload.text, payload.languages)
        return results
    except Exception as e:
        import traceback
        print(f"Error translating content: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))