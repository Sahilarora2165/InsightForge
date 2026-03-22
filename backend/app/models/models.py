"""
Database Models for InternalKnowledgeHub
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from app.core.database import db


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class FeedbackType(str, Enum):
    UP = "up"
    DOWN = "down"


class CollectionMemberRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(db.Model):
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
    collections = relationship("Collection", back_populates="created_by_user", lazy="dynamic")
    collection_memberships = relationship("CollectionMember", back_populates="user", lazy="dynamic")

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


class Collection(db.Model):
    """
    A Collection is a named group of documents.
    Think of it as a smart folder — users chat scoped to one collection
    so answers never mix HR docs with engineering specs.
    """
    __tablename__ = "collections"
    __table_args__ = (
        Index('idx_collections_created_by', 'created_by'),
        Index('idx_collections_created_at', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Auto-created "My Documents" collection
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    created_by_user = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection", lazy="dynamic")
    members = relationship("CollectionMember", back_populates="collection", cascade="all, delete-orphan", lazy="dynamic")
    qa_history = relationship("QAHistory", back_populates="collection", lazy="dynamic")

    def to_dict(self, include_stats=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_stats:
            data["document_count"] = self.documents.count()
            data["member_count"] = self.members.count()
        return data


class CollectionMember(db.Model):
    """
    Maps users to collections with a role.
    Owner: created the collection, can delete it and manage members.
    Editor: can upload documents.
    Viewer: can only read and ask questions.
    """
    __tablename__ = "collection_members"
    __table_args__ = (
        Index('idx_collection_members_collection_id', 'collection_id'),
        Index('idx_collection_members_user_id', 'user_id'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    collection_id = Column(String(36), ForeignKey("collections.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(CollectionMemberRole, values_callable=lambda x: [e.value for e in x]), default=CollectionMemberRole.VIEWER, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    collection = relationship("Collection", back_populates="members")
    user = relationship("User", back_populates="collection_memberships")

    def to_dict(self):
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "added_at": self.added_at.isoformat()
        }


class Document(db.Model):
    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_documents_uploaded_by', 'uploaded_by'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_uploaded_by_status', 'uploaded_by', 'status'),
        Index('idx_documents_created_at', 'created_at'),
        Index('idx_documents_collection_id', 'collection_id'),
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
    # nullable — documents uploaded before collections existed still work
    collection_id = Column(String(36), ForeignKey("collections.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")

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
            "collection_id": self.collection_id,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }


class Chunk(db.Model):
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
    embedding_id = Column(String(255), nullable=True)
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

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
    __tablename__ = "qa_history"
    __table_args__ = (
        Index('idx_qa_user_id', 'user_id'),
        Index('idx_qa_session_id', 'session_id'),
        Index('idx_qa_user_session', 'user_id', 'session_id'),
        Index('idx_qa_created_at', 'created_at'),
        Index('idx_qa_collection_id', 'collection_id'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    # nullable — history before collections existed still works
    collection_id = Column(String(36), ForeignKey("collections.id"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    context_chunks = Column(JSON, nullable=True)
    model_name = Column(String(100), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    feedback = Column(SQLEnum(FeedbackType), nullable=True)
    feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    feedback_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="qa_history")
    collection = relationship("Collection", back_populates="qa_history")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "collection_id": self.collection_id,
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "feedback": self.feedback.value if self.feedback else None,
            "created_at": self.created_at.isoformat()
        }


class AuditLog(db.Model):
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
    __tablename__ = "revoked_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)