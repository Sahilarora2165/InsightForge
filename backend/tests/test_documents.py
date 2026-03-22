"""
Tests for document API endpoints.
"""

import pytest
import io
from flask.testing import FlaskClient


class TestDocumentUpload:
    """Tests for document upload endpoint."""

    def test_upload_pdf(self, client: FlaskClient, auth_headers):
        """Test uploading a PDF document."""
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 test content"), "test.pdf")
        }
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            data=data,
            content_type="multipart/form-data"
        )
        assert response.status_code == 202
        assert "document_id" in response.json

    def test_upload_txt(self, client: FlaskClient, auth_headers):
        """Test uploading a text document."""
        data = {
            "file": (io.BytesIO(b"This is test content for the document."), "test.txt")
        }
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            data=data,
            content_type="multipart/form-data"
        )
        assert response.status_code == 202

    def test_upload_no_auth(self, client: FlaskClient):
        """Test upload without authentication."""
        data = {
            "file": (io.BytesIO(b"test content"), "test.txt")
        }
        response = client.post(
            "/api/documents/upload",
            data=data,
            content_type="multipart/form-data"
        )
        assert response.status_code == 401

    def test_upload_unsupported_type(self, client: FlaskClient, auth_headers):
        """Test uploading unsupported file type."""
        data = {
            "file": (io.BytesIO(b"test content"), "test.exe")
        }
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            data=data,
            content_type="multipart/form-data"
        )
        assert response.status_code == 400


class TestDocumentList:
    """Tests for document listing endpoint."""

    def test_list_documents(self, client: FlaskClient, auth_headers, test_document):
        """Test listing documents."""
        response = client.get("/api/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert "documents" in data
        assert len(data["documents"]) >= 1

    def test_list_documents_pagination(self, client: FlaskClient, auth_headers):
        """Test document listing pagination."""
        response = client.get(
            "/api/documents/?page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "total" in response.json
        assert "page" in response.json

    def test_list_documents_no_auth(self, client: FlaskClient):
        """Test listing documents without authentication."""
        response = client.get("/api/documents/")
        assert response.status_code == 401


class TestDocumentDetail:
    """Tests for document detail endpoint."""

    def test_get_document(self, client: FlaskClient, auth_headers, test_document):
        """Test getting document details."""
        response = client.get(
            f"/api/documents/{test_document.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json
        assert data["id"] == test_document.id
        assert data["filename"] == test_document.filename

    def test_get_nonexistent_document(self, client: FlaskClient, auth_headers):
        """Test getting non-existent document."""
        response = client.get(
            "/api/documents/99999",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestDocumentDelete:
    """Tests for document deletion endpoint."""

    def test_delete_document(self, client: FlaskClient, auth_headers, test_document):
        """Test deleting a document."""
        response = client.delete(
            f"/api/documents/{test_document.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_delete_nonexistent_document(self, client: FlaskClient, auth_headers):
        """Test deleting non-existent document."""
        response = client.delete(
            "/api/documents/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_document_no_auth(self, client: FlaskClient, test_document):
        """Test deleting document without authentication."""
        response = client.delete(f"/api/documents/{test_document.id}")
        assert response.status_code == 401


class TestDocumentStatus:
    """Tests for document status endpoint."""

    def test_get_document_status(self, client: FlaskClient, auth_headers, test_document):
        """Test getting document processing status."""
        response = client.get(
            f"/api/documents/{test_document.id}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json
        assert "status" in data
        assert data["status"] == "completed"
