"""
Admin API Routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.core.database import db
from app.core.security import admin_required, get_current_user_info
from app.models import User, UserRole, Document, DocumentStatus, Chunk, QAHistory, FeedbackType, AuditLog
from app.services.auth import AuthService
from app.services.rag import RAGService
from app.main import api_metrics

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get admin statistics."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can view stats
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    # Calculate stats
    total_users = User.query.count()
    total_documents = Document.query.count()
    total_chunks = Chunk.query.count()
    total_questions = QAHistory.query.count()
    
    # Feedback stats
    total_feedback = QAHistory.query.filter(QAHistory.feedback.isnot(None)).count()
    feedback_positive = QAHistory.query.filter(QAHistory.feedback == FeedbackType.UP).count()
    feedback_negative = QAHistory.query.filter(QAHistory.feedback == FeedbackType.DOWN).count()
    
    # Documents by status
    documents_by_status = {}
    for status in DocumentStatus:
        count = Document.query.filter_by(status=status).count()
        documents_by_status[status.value] = count
    
    # Questions today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    questions_today = QAHistory.query.filter(QAHistory.created_at >= today).count()
    
    # Questions this week
    week_ago = today - timedelta(days=7)
    questions_this_week = QAHistory.query.filter(QAHistory.created_at >= week_ago).count()
    
    return jsonify({
        'total_users': total_users,
        'total_documents': total_documents,
        'total_chunks': total_chunks,
        'total_questions': total_questions,
        'total_feedback': total_feedback,
        'feedback_positive': feedback_positive,
        'feedback_negative': feedback_negative,
        'documents_by_status': documents_by_status,
        'questions_today': questions_today,
        'questions_this_week': questions_this_week
    }), 200


@admin_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_stats():
    """Get API performance and cache statistics."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    if user_role != 'admin':
        return jsonify({'error': 'Forbidden', 'message': 'Admin access required'}), 403
    
    # Get cache stats
    cache_stats = RAGService.get_cache_stats()
    
    # Get API metrics
    total_requests = api_metrics['requests']
    avg_time = api_metrics['total_time'] / total_requests if total_requests > 0 else 0
    
    endpoint_stats = {}
    for endpoint, stats in api_metrics['endpoints'].items():
        if stats['count'] > 0:
            endpoint_stats[endpoint] = {
                'count': stats['count'],
                'avg_ms': round(stats['total_time'] / stats['count'], 2),
                'min_ms': round(stats['min_time'], 2) if stats['min_time'] != float('inf') else 0,
                'max_ms': round(stats['max_time'], 2)
            }
    
    return jsonify({
        'api_metrics': {
            'total_requests': total_requests,
            'avg_response_time_ms': round(avg_time, 2),
            'endpoints': endpoint_stats
        },
        'cache_stats': cache_stats
    }), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can view all users
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Validate per_page
    per_page = min(per_page, 100)
    
    query = User.query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id: str):
    """Get a user by ID."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can view other users
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404
    
    return jsonify(user.to_dict()), 200


@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id: str):
    """Update a user."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    current_user_id = identity.get('user_id')
    
    # Only admins can update users
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    data = request.get_json()
    
    # Process role if provided
    if 'role' in data:
        try:
            data['role'] = UserRole(data['role'])
        except ValueError:
            return jsonify({
                'error': 'Validation Error',
                'message': f'Invalid role. Must be one of: {", ".join([r.value for r in UserRole])}'
            }), 400
    
    try:
        user = AuthService.update_user(user_id, **data)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({
            'error': 'Update Failed',
            'message': str(e)
        }), 400


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id: str):
    """Delete a user."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    current_user_id = identity.get('user_id')
    
    # Only admins can delete users
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    # Cannot delete self
    if user_id == current_user_id:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Cannot delete your own account'
        }), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User deleted successfully'
    }), 200


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user (admin only)."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can create users
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'viewer')
    
    if not email or not password or not name:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Email, password, and name are required'
        }), 400
    
    # Process role
    try:
        user_role_enum = UserRole(role)
    except ValueError:
        return jsonify({
            'error': 'Validation Error',
            'message': f'Invalid role. Must be one of: {", ".join([r.value for r in UserRole])}'
        }), 400
    
    try:
        user, _, _ = AuthService.register_user(
            email=email,
            password=password,
            name=name,
            role=user_role_enum
        )
        
        return jsonify(user.to_dict()), 201
        
    except ValueError as e:
        return jsonify({
            'error': 'Creation Failed',
            'message': str(e)
        }), 400


@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can view audit logs
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action = request.args.get('action')
    user_id = request.args.get('user_id')
    
    # Validate per_page
    per_page = min(per_page, 100)
    
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@admin_bp.route('/feedback', methods=['GET'])
@jwt_required()
def get_all_feedback():
    """Get all feedback for analysis."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Only admins can view all feedback
    if user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    feedback_type = request.args.get('type')
    
    # Validate per_page
    per_page = min(per_page, 100)
    
    query = QAHistory.query.filter(QAHistory.feedback.isnot(None))
    
    if feedback_type:
        try:
            ft = FeedbackType(feedback_type)
            query = query.filter_by(feedback=ft)
        except ValueError:
            pass
    
    query = query.order_by(QAHistory.feedback_at.desc())
    
    total = query.count()
    records = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'feedback': [{
            'qa_id': r.id,
            'user_id': r.user_id,
            'question': r.question,
            'answer': r.answer[:200] + '...' if len(r.answer) > 200 else r.answer,
            'feedback': r.feedback.value,
            'comment': r.feedback_comment,
            'feedback_at': r.feedback_at.isoformat() if r.feedback_at else None,
            'created_at': r.created_at.isoformat()
        } for r in records],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200
