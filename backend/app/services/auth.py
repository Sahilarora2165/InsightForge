"""
Authentication Service
"""
from datetime import datetime
from typing import Optional, Tuple

from flask import request
from flask_jwt_extended import get_jwt

from app.core.database import db
from app.core.security import hash_password, verify_password, create_tokens, revoke_token
from app.models import User, UserRole, RevokedToken, AuditLog


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(email: str, password: str, name: str, role: UserRole = UserRole.VIEWER) -> Tuple[User, str, str]:
        """Register a new user."""
        # Check if user exists
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user
        user = User(
            email=email.lower(),
            name=name,
            hashed_password=hash_password(password),
            role=role,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token, refresh_token = create_tokens(user.id, user.role.value)
        
        # Log audit
        AuthService._log_audit(user.id, "user_registered")
        
        return user, access_token, refresh_token
    
    @staticmethod
    def login(email: str, password: str) -> Tuple[User, str, str]:
        """Authenticate a user and return tokens."""
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        if not verify_password(password, user.hashed_password):
            AuthService._log_audit(user.id, "login_failed", {"reason": "invalid_password"})
            raise ValueError("Invalid email or password")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create tokens
        access_token, refresh_token = create_tokens(user.id, user.role.value)
        
        # Log audit
        AuthService._log_audit(user.id, "user_login")
        
        return user, access_token, refresh_token
    
    @staticmethod
    def refresh_tokens(user_id: str, role: str) -> Tuple[str, str]:
        """Refresh access and refresh tokens."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Create new tokens
        access_token, refresh_token = create_tokens(user.id, user.role.value)
        
        # Log audit
        AuthService._log_audit(user.id, "token_refreshed")
        
        return access_token, refresh_token
    
    @staticmethod
    def logout(jti: str, user_id: str, expires_at: datetime) -> None:
        """Logout a user by revoking their token."""
        # Add token to revoked list
        revoked_token = RevokedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        
        db.session.add(revoked_token)
        db.session.commit()
        
        # Also add to in-memory blacklist
        revoke_token(jti)
        
        # Log audit
        AuthService._log_audit(user_id, "user_logout")
    
    @staticmethod
    def is_token_revoked(jti: str) -> bool:
        """Check if a token is revoked."""
        token = RevokedToken.query.filter_by(jti=jti).first()
        return token is not None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get a user by email."""
        return User.query.filter_by(email=email.lower()).first()
    
    @staticmethod
    def update_user(user_id: str, **kwargs) -> User:
        """Update a user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        allowed_fields = ['name', 'role', 'is_active']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(user, key, value)
        
        db.session.commit()
        
        # Log audit
        AuthService._log_audit(user_id, "user_updated", kwargs)
        
        return user
    
    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> None:
        """Change a user's password."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Invalid current password")
        
        user.hashed_password = hash_password(new_password)
        db.session.commit()
        
        # Log audit
        AuthService._log_audit(user_id, "password_changed")
    
    @staticmethod
    def _log_audit(user_id: str, action: str, details: dict = None) -> None:
        """Log an audit entry."""
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                details=details,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            # Don't fail the main operation if audit logging fails
            pass


# Initialize token checker for JWT
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if token is revoked (for JWT callback)."""
    jti = jwt_payload.get("jti")
    return AuthService.is_token_revoked(jti)
