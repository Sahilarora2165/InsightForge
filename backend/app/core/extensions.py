"""
Flask Extensions
"""
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

jwt = JWTManager()
migrate = Migrate()
