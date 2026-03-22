"""
Application Configuration
"""
import os
from datetime import timedelta
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Allow extra fields from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )
    
    # Application
    APP_NAME: str = "InternalKnowledgeHub"
    DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # Flask (optional, from .env)
    FLASK_APP: Optional[str] = None
    FLASK_ENV: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Ollama - support both naming conventions
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_BASE_URL: Optional[str] = None  # Alternative name
    OLLAMA_MODEL: str = "llama3"
    LLM_MODEL: Optional[str] = None  # Alternative name
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    EMBEDDING_MODEL: Optional[str] = None  # Alternative name
    OLLAMA_NUM_GPU: int = 99
    OLLAMA_KEEP_ALIVE: str = "5m"
    
    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PATH: str = "./data/chroma"
    
    # File Storage
    UPLOAD_PATH: str = "./uploads"
    UPLOAD_FOLDER: Optional[str] = None  # Alternative name
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    MAX_CONTENT_LENGTH: Optional[int] = None  # Alternative name
    ALLOWED_EXTENSIONS: str = "pdf,docx,md,txt"
    
    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800  # 7 days in seconds
    
    # RAG Settings
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 128
    RAG_TOP_K: int = 5
    RAG_HYBRID_ALPHA: float = 0.7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:80,http://localhost"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def ollama_url(self) -> str:
        """Get Ollama URL, preferring OLLAMA_BASE_URL if set."""
        return self.OLLAMA_BASE_URL or self.OLLAMA_HOST
    
    @property
    def llm_model_name(self) -> str:
        """Get LLM model name."""
        return self.LLM_MODEL or self.OLLAMA_MODEL
    
    @property
    def embed_model_name(self) -> str:
        """Get embedding model name."""
        return self.EMBEDDING_MODEL or self.OLLAMA_EMBED_MODEL
    
    @property
    def upload_directory(self) -> str:
        """Get upload directory path."""
        return self.UPLOAD_FOLDER or self.UPLOAD_PATH
    
    @property
    def jwt_access_expires(self) -> timedelta:
        """Get JWT access token expiration timedelta."""
        return timedelta(seconds=self.JWT_ACCESS_TOKEN_EXPIRES)
    
    @property
    def jwt_refresh_expires(self) -> timedelta:
        """Get JWT refresh token expiration timedelta."""
        return timedelta(seconds=self.JWT_REFRESH_TOKEN_EXPIRES)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as list."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]


settings = Settings()
