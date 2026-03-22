"""
Core module initialization
"""
from app.core.config import settings
from app.core.database import db
from app.core.extensions import jwt, migrate
from app.core.security import (
    hash_password,
    verify_password,
    create_tokens,
    revoke_token,
    is_token_revoked,
    role_required,
    admin_required,
    editor_required,
    compute_file_hash,
    sanitize_filename
)

__all__ = [
    "settings",
    "db",
    "jwt",
    "migrate",
    "hash_password",
    "verify_password",
    "create_tokens",
    "revoke_token",
    "is_token_revoked",
    "role_required",
    "admin_required",
    "editor_required",
    "compute_file_hash",
    "sanitize_filename"
]
