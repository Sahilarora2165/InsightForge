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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_metrics = {
    'requests': 0,
    'total_time': 0,
    'endpoints': {}
}


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    Compress(app)
    app.config['COMPRESS_MIMETYPES'] = ['application/json', 'text/html', 'text/css', 'text/javascript']
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500

    app.config.from_object(settings)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.jwt_access_expires
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = settings.jwt_refresh_expires
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_UPLOAD_SIZE

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    CORS(app, origins=settings.cors_origins_list, supports_credentials=True)

    register_blueprints(app)
    register_error_handlers(app)
    register_health_endpoints(app)
    register_timing_middleware(app)

    os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    os.makedirs(settings.CHROMA_PATH, exist_ok=True)

    return app


def register_timing_middleware(app: Flask) -> None:
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        if hasattr(g, 'start_time'):
            elapsed = (time.time() - g.start_time) * 1000
            endpoint = request.endpoint or 'unknown'
            method = request.method
            path = request.path
            status = response.status_code

            api_metrics['requests'] += 1
            api_metrics['total_time'] += elapsed

            if endpoint not in api_metrics['endpoints']:
                api_metrics['endpoints'][endpoint] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }

            ep = api_metrics['endpoints'][endpoint]
            ep['count'] += 1
            ep['total_time'] += elapsed
            ep['min_time'] = min(ep['min_time'], elapsed)
            ep['max_time'] = max(ep['max_time'], elapsed)

            logger.info(f"{method} {path} - {status} - {elapsed:.2f}ms")
            response.headers['X-Response-Time'] = f"{elapsed:.2f}ms"

        return response


def register_blueprints(app: Flask) -> None:
    from app.api.auth import auth_bp
    from app.api.documents import documents_bp
    from app.api.ask import ask_bp
    from app.api.feedback import feedback_bp
    from app.api.admin import admin_bp
    from app.api.collections import collections_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(ask_bp, url_prefix='/api')
    app.register_blueprint(feedback_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(collections_bp, url_prefix='/api/collections')


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error.description)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File Too Large', 'message': 'The uploaded file exceeds the maximum allowed size'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500


def register_health_endpoints(app: Flask) -> None:
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'InternalKnowledgeHub API'})

    @app.route('/metrics')
    def metrics():
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
        checks = {
            'database': check_database(),
            'ollama': check_ollama(),
            'redis': check_redis()
        }
        all_ready = all(checks.values())
        return jsonify({'ready': all_ready, 'checks': checks}), 200 if all_ready else 503


def check_database() -> bool:
    try:
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


def check_ollama() -> bool:
    import requests
    try:
        response = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_redis() -> bool:
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except Exception:
        return False


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=settings.DEBUG)