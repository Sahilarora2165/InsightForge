"""
InternalKnowledgeHub - Flask Application Factory
"""
import os
import time
import logging
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_compress import Compress

from app.core.config import settings
from app.core.database import db
from app.core.extensions import jwt, migrate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics storage (in production, use Prometheus/StatsD)
api_metrics = {
    'requests': 0,
    'total_time': 0,
    'endpoints': {}
}


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable gzip compression (70% payload reduction)
    Compress(app)
    app.config['COMPRESS_MIMETYPES'] = ['application/json', 'text/html', 'text/css', 'text/javascript']
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    
    # Load configuration
    app.config.from_object(settings)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.jwt_access_expires
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = settings.jwt_refresh_expires
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_UPLOAD_SIZE
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS
    CORS(app, origins=settings.cors_origins_list, supports_credentials=True)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health endpoints
    register_health_endpoints(app)
    
    # Register request timing middleware
    register_timing_middleware(app)
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    os.makedirs(settings.CHROMA_PATH, exist_ok=True)
    
    return app


def register_timing_middleware(app: Flask) -> None:
    """Register request timing middleware for performance monitoring."""
    
    @app.before_request
    def start_timer():
        g.start_time = time.time()
    
    @app.after_request
    def log_request(response):
        if hasattr(g, 'start_time'):
            elapsed = (time.time() - g.start_time) * 1000  # Convert to ms
            endpoint = request.endpoint or 'unknown'
            method = request.method
            path = request.path
            status = response.status_code
            
            # Update metrics
            api_metrics['requests'] += 1
            api_metrics['total_time'] += elapsed
            
            if endpoint not in api_metrics['endpoints']:
                api_metrics['endpoints'][endpoint] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }
            
            ep_metrics = api_metrics['endpoints'][endpoint]
            ep_metrics['count'] += 1
            ep_metrics['total_time'] += elapsed
            ep_metrics['min_time'] = min(ep_metrics['min_time'], elapsed)
            ep_metrics['max_time'] = max(ep_metrics['max_time'], elapsed)
            
            # Log request details
            logger.info(f"{method} {path} - {status} - {elapsed:.2f}ms")
            
            # Add timing header to response
            response.headers['X-Response-Time'] = f"{elapsed:.2f}ms"
        
        return response


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.api.auth import auth_bp
    from app.api.documents import documents_bp
    from app.api.ask import ask_bp
    from app.api.feedback import feedback_bp
    from app.api.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(ask_bp, url_prefix='/api')
    app.register_blueprint(feedback_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'error': 'File Too Large',
            'message': 'The uploaded file exceeds the maximum allowed size'
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def register_health_endpoints(app: Flask) -> None:
    """Register health check endpoints."""
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'service': 'InternalKnowledgeHub API'
        })
    
    @app.route('/metrics')
    def metrics():
        """API performance metrics endpoint."""
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
            'total_requests': total_requests,
            'avg_response_time_ms': round(avg_time, 2),
            'endpoints': endpoint_stats
        })
    
    @app.route('/ready')
    def ready():
        """Readiness check endpoint."""
        checks = {
            'database': check_database(),
            'ollama': check_ollama(),
            'redis': check_redis()
        }
        
        all_ready = all(checks.values())
        status_code = 200 if all_ready else 503
        
        return jsonify({
            'ready': all_ready,
            'checks': checks
        }), status_code


def check_database() -> bool:
    """Check database connectivity."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


def check_ollama() -> bool:
    """Check Ollama connectivity."""
    import requests
    try:
        response = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except Exception:
        return False


# Create app instance for gunicorn
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=settings.DEBUG)
