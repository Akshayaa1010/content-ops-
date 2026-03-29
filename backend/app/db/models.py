# app/db/models.py
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.database import Base
import uuid

class ContentJob(Base):
    __tablename__ = "content_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief = Column(JSON, nullable=False)
    state = Column(String(50), default="briefed", nullable=False, index=True)
    draft = Column(JSON, nullable=True)
    compliance_report = Column(JSON, nullable=True)
    localised_versions = Column(JSON, nullable=True)
    submitted_by = Column(String(255), nullable=True)
    gate_mode = Column(String(50), default="async_approval")
    reviewer_decision = Column(String(50), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    violation_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)
    raw_text = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_by = Column(String(255), nullable=True)
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    chunk_index = Column(Integer, nullable=False)

class StageTiming(Base):
    __tablename__ = "stage_timings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("content_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    entered_at = Column(DateTime(timezone=True), server_default=func.now())
    exited_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    is_human_stage = Column(Boolean, default=False)

class PublishedContent(Base):
    __tablename__ = "published_content"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("content_jobs.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    published_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    performance_score = Column(Float, nullable=True)
    raw_metrics = Column(JSON, nullable=True)