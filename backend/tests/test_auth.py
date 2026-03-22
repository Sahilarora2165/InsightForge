"""
Tests for authentication API endpoints.
"""

import pytest
from flask.testing import FlaskClient


class TestAuthRegister:
    """Tests for user registration endpoint."""

    def test_register_success(self, client: FlaskClient):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data

    def test_register_duplicate_email(self, client: FlaskClient, test_user):
        """Test registration with existing email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "anotherpassword123",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json["detail"].lower()

    def test_register_invalid_email(self, client: FlaskClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "password": "securepassword123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422

    def test_register_weak_password(self, client: FlaskClient):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client: FlaskClient, test_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: FlaskClient, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: FlaskClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123"
            }
        )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for current user endpoint."""

    def test_get_current_user(self, client: FlaskClient, auth_headers, test_user):
        """Test getting current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    def test_get_current_user_no_auth(self, client: FlaskClient):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token(self, client: FlaskClient, test_user):
        """Test refreshing access token."""
        # First login to get refresh token
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json


class TestAuthLogout:
    """Tests for logout endpoint."""

    def test_logout(self, client: FlaskClient, auth_headers):
        """Test user logout."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "logged out" in response.json["message"].lower()

    def test_logout_no_auth(self, client: FlaskClient):
        """Test logout without authentication."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401
