"""
Feedback API Routes
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.core.database import db
from app.models import QAHistory, FeedbackType
from app.schemas import FeedbackRequest
from app.core.security import get_current_user_info

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit feedback for a QA response."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    try:
        data = FeedbackRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': e.errors()
        }), 400
    
    # Get QA history record
    qa_record = QAHistory.query.get(data.qa_id)
    
    if not qa_record:
        return jsonify({
            'error': 'Not Found',
            'message': 'QA record not found'
        }), 404
    
    # Verify user owns this QA record
    if qa_record.user_id != user_id:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You can only provide feedback for your own questions'
        }), 403
    
    # Update feedback
    qa_record.feedback = FeedbackType(data.thumb.value)
    qa_record.feedback_comment = data.comment
    qa_record.feedback_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Feedback submitted successfully'
    }), 200


@feedback_bp.route('/feedback/<qa_id>', methods=['GET'])
@jwt_required()
def get_feedback(qa_id: str):
    """Get feedback for a specific QA record."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    qa_record = QAHistory.query.get(qa_id)
    
    if not qa_record:
        return jsonify({
            'error': 'Not Found',
            'message': 'QA record not found'
        }), 404
    
    # Verify user owns this QA record
    if qa_record.user_id != user_id:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied'
        }), 403
    
    return jsonify({
        'qa_id': qa_record.id,
        'feedback': qa_record.feedback.value if qa_record.feedback else None,
        'comment': qa_record.feedback_comment,
        'feedback_at': qa_record.feedback_at.isoformat() if qa_record.feedback_at else None
    }), 200


@feedback_bp.route('/feedback/<qa_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(qa_id: str):
    """Delete feedback for a specific QA record."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    qa_record = QAHistory.query.get(qa_id)
    
    if not qa_record:
        return jsonify({
            'error': 'Not Found',
            'message': 'QA record not found'
        }), 404
    
    # Verify user owns this QA record
    if qa_record.user_id != user_id:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied'
        }), 403
    
    # Clear feedback
    qa_record.feedback = None
    qa_record.feedback_comment = None
    qa_record.feedback_at = None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Feedback deleted successfully'
    }), 200
