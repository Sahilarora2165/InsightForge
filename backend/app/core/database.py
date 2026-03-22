"""
Database Configuration
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()

# Alias Base for compatibility with Alembic migrations
# Flask-SQLAlchemy uses db.Model as the base class
Base = db.Model

def get_session():
    """Get a database session from Flask-SQLAlchemy."""
    return db.session

# Alias for compatibility with services that expect SessionLocal pattern
SessionLocal = lambda: db.session
