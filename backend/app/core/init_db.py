"""
Database Initialization
"""
import os
from app.core.database import db
from app.core.security import hash_password
from app.models import User, UserRole


def init_db():
    """Initialize the database with tables."""
    db.create_all()
    print("Database tables created.")


def seed_db():
    """Seed the database with initial data."""
    # Check if admin user exists
    admin = User.query.filter_by(email="admin@internal.local").first()
    
    if not admin:
        admin = User(
            email="admin@internal.local",
            name="Admin User",
            hashed_password=hash_password("changeme123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@internal.local / changeme123")
    else:
        print("Admin user already exists.")
    
    # Create demo users if they don't exist
    demo_users = [
        {"email": "editor@internal.local", "name": "Editor User", "role": UserRole.EDITOR},
        {"email": "viewer@internal.local", "name": "Viewer User", "role": UserRole.VIEWER},
    ]
    
    for demo_user in demo_users:
        existing = User.query.filter_by(email=demo_user["email"]).first()
        if not existing:
            user = User(
                email=demo_user["email"],
                name=demo_user["name"],
                hashed_password=hash_password("demo123456"),
                role=demo_user["role"],
                is_active=True
            )
            db.session.add(user)
            print(f"Demo user created: {demo_user['email']} / demo123456")
    
    db.session.commit()
    print("Database seeding complete.")


def reset_db():
    """Reset the database (drop all tables and recreate)."""
    db.drop_all()
    db.create_all()
    print("Database reset complete.")
