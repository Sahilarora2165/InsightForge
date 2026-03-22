"""
Audit logging service for tracking user actions.

Provides comprehensive audit trail for compliance and debugging.
"""

import json
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from app.core.database import db


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"
    
    # Document actions
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_PROCESS = "document_process"
    
    # Query actions
    QUERY_ASK = "query_ask"
    QUERY_FEEDBACK = "query_feedback"
    
    # Admin actions
    ADMIN_USER_UPDATE = "admin_user_update"
    ADMIN_USER_DELETE = "admin_user_delete"
    ADMIN_STATS_VIEW = "admin_stats_view"
    ADMIN_SYSTEM_CONFIG = "admin_system_config"
    
    # System actions
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_HIT = "rate_limit_hit"


class AuditLog:
    """
    In-memory audit log entry before persistence.
    
    Uses SQLite/PostgreSQL for persistence, with optional
    Redis pub/sub for real-time streaming.
    """
    
    def __init__(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        self.timestamp = datetime.utcnow()
        self.action = action
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.success = success
        self.error_message = error_message
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message
        }


class AuditLogger:
    """
    Audit logging service.
    
    Logs user actions to database with optional real-time streaming.
    """
    
    def __init__(self):
        pass
    
    def log(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        request: Optional[Any] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            action: The type of action
            user_id: ID of user performing action
            resource_type: Type of resource affected (e.g., 'document', 'user')
            resource_id: ID of affected resource
            details: Additional details about the action
            request: Flask request object for IP/user agent extraction
            success: Whether action succeeded
            error_message: Error message if action failed
            
        Returns:
            The created audit log entry
        """
        # Extract request info
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent')
        
        # Create log entry
        log_entry = AuditLog(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        # Persist to database
        self._persist(log_entry)
        
        return log_entry
    
    def _persist(self, log_entry: AuditLog) -> None:
        """Persist audit log to database."""
        from app.models.models import AuditLog as AuditLogModel
        
        try:
            db_log = AuditLogModel(
                action=log_entry.action.value,
                user_id=str(log_entry.user_id) if log_entry.user_id else None,
                resource_type=log_entry.resource_type,
                resource_id=log_entry.resource_id,
                details=log_entry.details,
                ip_address=log_entry.ip_address,
                user_agent=log_entry.user_agent
            )
            db.session.add(db_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log to stderr as fallback
            import sys
            print(f"Failed to persist audit log: {e}", file=sys.stderr)
    
    def query(
        self,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """
        Query audit logs.
        
        Args:
            user_id: Filter by user
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Start of time range
            end_date: End of time range
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of audit log entries as dicts
        """
        from app.models.models import AuditLog as AuditLogModel
        
        query = AuditLogModel.query
        
        if user_id:
            query = query.filter(AuditLogModel.user_id == str(user_id))
        if action:
            query = query.filter(AuditLogModel.action == action.value)
        if resource_type:
            query = query.filter(AuditLogModel.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLogModel.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLogModel.created_at <= end_date)
        
        logs = query.order_by(AuditLogModel.created_at.desc())\
                   .offset(offset)\
                   .limit(limit)\
                   .all()
        
        return [log.to_dict() for log in logs]


# Convenience functions
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    action: AuditAction,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Any] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Convenience function to log an audit event."""
    return get_audit_logger().log(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        request=request,
        success=success,
        error_message=error_message
    )
