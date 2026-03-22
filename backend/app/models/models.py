"""
Database Models for InternalKnowledgeHub
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import db


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DocumentStatus(str, Enum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class FeedbackType(str, Enum):
    """Feedback type enumeration."""
    UP = "up"
    DOWN = "down"


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="uploaded_by_user", lazy="dynamic")
    qa_history = relationship("QAHistory", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


class Document(db.Model):
    """Document model for storing uploaded files."""
    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_documents_uploaded_by', 'uploaded_by'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_uploaded_by_status', 'uploaded_by', 'status'),
        Index('idx_documents_created_at', 'created_at'),
    )
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")
    
    def __repr__(self):
        return f"<Document {self.filename}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status.value,
            "error_message": self.error_message,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }


class Chunk(db.Model):
    """Chunk model for storing document chunks."""
    __tablename__ = "chunks"
    __table_args__ = (
        Index('idx_chunks_document_id', 'document_id'),
        Index('idx_chunks_embedding_id', 'embedding_id'),
    )
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    paragraph_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding_id = Column(String(255), nullable=True)  # ID in ChromaDB
    chunk_metadata = Column(JSON, nullable=True)  # Renamed from metadata to avoid conflict
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk {self.id} from {self.document_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "page_number": self.page_number,
            "paragraph_number": self.paragraph_number,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "metadata": self.chunk_metadata
        }


class QAHistory(db.Model):
    """QA History model for storing questions and answers."""
    __tablename__ = "qa_history"
    __table_args__ = (
        Index('idx_qa_user_id', 'user_id'),
        Index('idx_qa_session_id', 'session_id'),
        Index('idx_qa_user_session', 'user_id', 'session_id'),
        Index('idx_qa_created_at', 'created_at'),
    )
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # List of citation objects
    context_chunks = Column(JSON, nullable=True)  # IDs of chunks used
    model_name = Column(String(100), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    feedback = Column(SQLEnum(FeedbackType), nullable=True)
    feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    feedback_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="qa_history")
    
    def __repr__(self):
        return f"<QAHistory {self.id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "feedback": self.feedback.value if self.feedback else None,
            "created_at": self.created_at.isoformat()
        }


class AuditLog(db.Model):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat()
        }


class RevokedToken(db.Model):
    """Revoked JWT tokens for logout functionality."""
    __tablename__ = "revoked_tokens"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<RevokedToken {self.jti}>"
