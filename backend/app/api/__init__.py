"""
API module initialization
"""
from app.api.auth import auth_bp
from app.api.documents import documents_bp
from app.api.ask import ask_bp
from app.api.feedback import feedback_bp
from app.api.admin import admin_bp

__all__ = [
    "auth_bp",
    "documents_bp",
    "ask_bp",
    "feedback_bp",
    "admin_bp"
]
