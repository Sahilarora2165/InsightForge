"""
Security utilities for authentication and authorization.
"""
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from functools import wraps

from flask import request, jsonify, g
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt
)

from app.core.config import settings
from app.core.database import db

# Token blacklist (in production, use Redis)
token_blacklist = set()


def get_current_user_info() -> dict:
    """Get user_id and role from JWT claims."""
    claims = get_jwt()
    return {
        "user_id": claims.get("user_id", get_jwt_identity()),
        "role": claims.get("role", "viewer")
    }


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt has a 72-byte limit
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # bcrypt has a 72-byte limit
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_tokens(user_id: str, role: str) -> Tuple[str, str]:
    """Create access and refresh tokens for a user."""
    # Flask-JWT-Extended requires identity to be a string
    access_token = create_access_token(
        identity=str(user_id),
        expires_delta=settings.jwt_access_expires,
        additional_claims={"type": "access", "role": role, "user_id": str(user_id)}
    )
    
    refresh_token = create_refresh_token(
        identity=str(user_id),
        expires_delta=settings.jwt_refresh_expires,
        additional_claims={"type": "refresh", "role": role, "user_id": str(user_id)}
    )
    
    return access_token, refresh_token


def revoke_token(jti: str) -> None:
    """Add a token to the blacklist."""
    token_blacklist.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Check if a token is blacklisted."""
    return jti in token_blacklist


def role_required(*roles):
    """Decorator to require specific roles for an endpoint."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_current_user_info()
            
            if identity.get("role") not in roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": "Insufficient permissions"
                }), 403
            
            g.current_user = identity
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Decorator to require admin role."""
    return role_required("admin")(fn)


def editor_required(fn):
    """Decorator to require editor or admin role."""
    return role_required("admin", "editor")(fn)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal attacks."""
    import os
    import re
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Remove multiple dots (except for extension)
    parts = filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        name = name.replace('.', '_')
        filename = f"{name}.{ext}"
    
    return filename or "unnamed_file"
