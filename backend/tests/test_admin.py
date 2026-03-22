"""
Tests for admin API endpoints.
"""

import pytest
from flask.testing import FlaskClient


class TestAdminStats:
    """Tests for admin statistics endpoint."""

    def test_get_stats_as_admin(self, client: FlaskClient, admin_auth_headers):
        """Test getting stats as admin user."""
        response = client.get("/api/admin/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json
        assert "total_documents" in data
        assert "total_users" in data
        assert "total_queries" in data

    def test_get_stats_as_regular_user(self, client: FlaskClient, auth_headers):
        """Test getting stats as regular user (should fail)."""
        response = client.get("/api/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    def test_get_stats_no_auth(self, client: FlaskClient):
        """Test getting stats without authentication."""
        response = client.get("/api/admin/stats")
        assert response.status_code == 401


class TestAdminUsers:
    """Tests for admin user management endpoints."""

    def test_list_users_as_admin(self, client: FlaskClient, admin_auth_headers):
        """Test listing users as admin."""
        response = client.get("/api/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_list_users_as_regular_user(self, client: FlaskClient, auth_headers):
        """Test listing users as regular user (should fail)."""
        response = client.get("/api/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_update_user_role(self, client: FlaskClient, admin_auth_headers, test_user):
        """Test updating user role as admin."""
        response = client.patch(
            f"/api/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"role": "admin"}
        )
        assert response.status_code == 200

    def test_deactivate_user(self, client: FlaskClient, admin_auth_headers, test_user):
        """Test deactivating user as admin."""
        response = client.patch(
            f"/api/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"is_active": False}
        )
        assert response.status_code == 200


class TestAdminDocuments:
    """Tests for admin document management endpoints."""

    def test_list_all_documents_as_admin(
        self, client: FlaskClient, admin_auth_headers, test_document
    ):
        """Test listing all documents as admin."""
        response = client.get("/api/admin/documents", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json
        assert "documents" in data

    def test_reprocess_document(
        self, client: FlaskClient, admin_auth_headers, test_document
    ):
        """Test reprocessing a document as admin."""
        response = client.post(
            f"/api/admin/documents/{test_document.id}/reprocess",
            headers=admin_auth_headers
        )
        assert response.status_code in [200, 202]


class TestAdminSystem:
    """Tests for admin system endpoints."""

    def test_get_system_info(self, client: FlaskClient, admin_auth_headers):
        """Test getting system information as admin."""
        response = client.get("/api/admin/system", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_get_system_info_no_auth(self, client: FlaskClient):
        """Test getting system info without authentication."""
        response = client.get("/api/admin/system")
        assert response.status_code == 401
