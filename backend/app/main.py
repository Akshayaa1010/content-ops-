# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, jobs, documents, analytics

app = FastAPI(title="Content Ops API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router)
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])