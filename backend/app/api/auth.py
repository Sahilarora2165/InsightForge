"""
Authentication API Routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from pydantic import ValidationError

from app.services.auth import AuthService
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse
)
from app.core.config import settings
from app.core.security import get_current_user_info

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = UserRegisterRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': e.errors()
        }), 400
    
    try:
        user, access_token, refresh_token = AuthService.register_user(
            email=data.email,
            password=data.password,
            name=data.name
        )
        
        return jsonify({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_EXPIRES * 60
        }), 201
        
    except ValueError as e:
        return jsonify({
            'error': 'Registration Failed',
            'message': str(e)
        }), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return tokens."""
    try:
        data = UserLoginRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': e.errors()
        }), 400
    
    try:
        user, access_token, refresh_token = AuthService.login(
            email=data.email,
            password=data.password
        )
        
        return jsonify({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_EXPIRES * 60
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Authentication Failed',
            'message': str(e)
        }), 401


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    try:
        claims = get_jwt()
        user_id = claims.get('user_id', get_jwt_identity())
        role = claims.get('role', 'viewer')
        
        access_token, refresh_token = AuthService.refresh_tokens(user_id, role)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_EXPIRES * 60
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Token Refresh Failed',
            'message': str(e)
        }), 401


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user by revoking their token."""
    jwt_data = get_jwt()
    jti = jwt_data.get('jti')
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    # Calculate expiry time
    exp = jwt_data.get('exp')
    expires_at = datetime.fromtimestamp(exp)
    
    AuthService.logout(jti, user_id, expires_at)
    
    return jsonify({
        'message': 'Successfully logged out'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user information."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    data = request.get_json()
    
    # Only allow updating name
    allowed_fields = {'name'}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    try:
        user = AuthService.update_user(user_id, **update_data)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({
            'error': 'Update Failed',
            'message': str(e)
        }), 400


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Both old_password and new_password are required'
        }), 400
    
    try:
        AuthService.change_password(user_id, old_password, new_password)
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
    except ValueError as e:
        return jsonify({
            'error': 'Password Change Failed',
            'message': str(e)
        }), 400
