"""
Pydantic Schemas for Request/Response Validation
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator


# ====================
# Enums
# ====================

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DocumentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class FeedbackTypeEnum(str, Enum):
    UP = "up"
    DOWN = "down"


# ====================
# Auth Schemas
# ====================

class UserRegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    name: str
    role: UserRoleEnum
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Schema for updating user."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


# ====================
# Document Schemas
# ====================

class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatusEnum
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: int
    uploaded_by: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int
    pages: int


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    id: str
    filename: str
    status: DocumentStatusEnum
    message: str


# ====================
# Ask (RAG) Schemas
# ====================

class Citation(BaseModel):
    """Schema for a citation."""
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    text_snippet: str
    relevance_score: float


class AskRequest(BaseModel):
    """Schema for ask request."""
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    alpha: float = Field(default=0.7, ge=0.0, le=1.0)
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    """Schema for ask response."""
    answer: str
    citations: List[Citation]
    session_id: str
    qa_id: str
    latency_ms: int
    model_name: str


class StreamAskResponse(BaseModel):
    """Schema for streaming ask response."""
    chunk: str
    is_complete: bool
    citations: Optional[List[Citation]] = None
    session_id: Optional[str] = None
    qa_id: Optional[str] = None


# ====================
# Feedback Schemas
# ====================

class FeedbackRequest(BaseModel):
    """Schema for feedback request."""
    qa_id: str
    thumb: FeedbackTypeEnum
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    success: bool
    message: str


# ====================
# Admin Schemas
# ====================

class StatsResponse(BaseModel):
    """Schema for admin stats response."""
    total_users: int
    total_documents: int
    total_chunks: int
    total_questions: int
    total_feedback: int
    feedback_positive: int
    feedback_negative: int
    documents_by_status: Dict[str, int]
    questions_today: int
    questions_this_week: int


class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ====================
# Chat History Schemas
# ====================

class ChatMessage(BaseModel):
    """Schema for a chat message."""
    id: str
    question: str
    answer: str
    citations: List[Citation]
    feedback: Optional[FeedbackTypeEnum] = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    messages: List[ChatMessage]
    session_id: str
    total: int


# ====================
# Health Check Schemas
# ====================

class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    service: str


class ReadinessCheckResponse(BaseModel):
    """Schema for readiness check response."""
    ready: bool
    checks: Dict[str, bool]


# ====================
# Error Schemas
# ====================

class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
