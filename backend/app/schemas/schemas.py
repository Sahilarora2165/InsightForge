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


class CollectionMemberRoleEnum(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


# ====================
# Auth Schemas
# ====================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
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
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


# ====================
# Collection Schemas
# ====================

class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionMemberResponse(BaseModel):
    membership_id: str
    user_id: str
    user_name: str
    user_email: str
    role: CollectionMemberRoleEnum
    added_at: datetime


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_by: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = None
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class CollectionListResponse(BaseModel):
    collections: List[CollectionResponse]
    total: int


class AddMemberRequest(BaseModel):
    user_id: str
    role: CollectionMemberRoleEnum = CollectionMemberRoleEnum.VIEWER

    @field_validator('role')
    @classmethod
    def role_cannot_be_owner(cls, v):
        if v == CollectionMemberRoleEnum.OWNER:
            raise ValueError('Cannot assign owner role via this endpoint')
        return v


# ====================
# Document Schemas
# ====================

class DocumentResponse(BaseModel):
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
    collection_id: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int
    pages: int


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatusEnum
    message: str
    collection_id: Optional[str] = None


# ====================
# Ask (RAG) Schemas
# ====================

class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    text_snippet: str
    relevance_score: float


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    alpha: float = Field(default=0.7, ge=0.0, le=1.0)
    session_id: Optional[str] = None
    # Scope the search to a specific collection.
    # If None, search across all documents the user has access to.
    collection_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: str
    qa_id: str
    latency_ms: int
    model_name: str
    collection_id: Optional[str] = None


class StreamAskResponse(BaseModel):
    chunk: str
    is_complete: bool
    citations: Optional[List[Citation]] = None
    session_id: Optional[str] = None
    qa_id: Optional[str] = None


# ====================
# Feedback Schemas
# ====================

class FeedbackRequest(BaseModel):
    qa_id: str
    thumb: FeedbackTypeEnum
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    success: bool
    message: str


# ====================
# Admin Schemas
# ====================

class StatsResponse(BaseModel):
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
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ====================
# Chat History Schemas
# ====================

class ChatMessage(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[Citation]
    feedback: Optional[FeedbackTypeEnum] = None
    collection_id: Optional[str] = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    session_id: str
    total: int


# ====================
# Health Check Schemas
# ====================

class HealthCheckResponse(BaseModel):
    status: str
    service: str


class ReadinessCheckResponse(BaseModel):
    ready: bool
    checks: Dict[str, bool]


# ====================
# Error Schemas
# ====================

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None