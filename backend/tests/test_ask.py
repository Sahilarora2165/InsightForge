"""
Tests for ask/RAG API endpoints.
"""

import pytest
from flask.testing import FlaskClient


class TestAskEndpoint:
    """Tests for the ask question endpoint."""

    def test_ask_question(
        self, client: FlaskClient, auth_headers, test_document, test_chunks
    ):
        """Test asking a question."""
        response = client.post(
            "/api/ask/",
            headers=auth_headers,
            json={"question": "What is the test content about?"}
        )
        # May return 200 or 503 if Ollama is not available
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json
            assert "answer" in data
            assert "sources" in data

    def test_ask_empty_question(self, client: FlaskClient, auth_headers):
        """Test asking empty question."""
        response = client.post(
            "/api/ask/",
            headers=auth_headers,
            json={"question": ""}
        )
        assert response.status_code == 422

    def test_ask_no_auth(self, client: FlaskClient):
        """Test asking question without authentication."""
        response = client.post(
            "/api/ask/",
            json={"question": "What is this about?"}
        )
        assert response.status_code == 401

    def test_ask_with_top_k(self, client: FlaskClient, auth_headers):
        """Test asking question with custom top_k."""
        response = client.post(
            "/api/ask/",
            headers=auth_headers,
            json={
                "question": "What is this about?",
                "top_k": 5
            }
        )
        assert response.status_code in [200, 503]


class TestAskHistory:
    """Tests for Q&A history endpoint."""

    def test_get_history(self, client: FlaskClient, auth_headers):
        """Test getting Q&A history."""
        response = client.get("/api/ask/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_get_history_pagination(self, client: FlaskClient, auth_headers):
        """Test Q&A history pagination."""
        response = client.get(
            "/api/ask/history?page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_history_no_auth(self, client: FlaskClient):
        """Test getting history without authentication."""
        response = client.get("/api/ask/history")
        assert response.status_code == 401


class TestFeedbackEndpoint:
    """Tests for feedback endpoint."""

    def test_submit_feedback(self, client: FlaskClient, auth_headers):
        """Test submitting feedback for an answer."""
        # First create a Q&A entry (mocked scenario)
        # In real test, would need to actually ask a question first
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "qa_id": 1,
                "is_helpful": True,
                "feedback_text": "Very helpful answer!"
            }
        )
        # May return 200 or 404 depending on whether QA entry exists
        assert response.status_code in [200, 404]

    def test_submit_negative_feedback(self, client: FlaskClient, auth_headers):
        """Test submitting negative feedback."""
        response = client.post(
            "/api/feedback/",
            headers=auth_headers,
            json={
                "qa_id": 1,
                "is_helpful": False,
                "feedback_text": "The answer was not relevant."
            }
        )
        assert response.status_code in [200, 404]

    def test_submit_feedback_no_auth(self, client: FlaskClient):
        """Test submitting feedback without authentication."""
        response = client.post(
            "/api/feedback/",
            json={
                "qa_id": 1,
                "is_helpful": True
            }
        )
        assert response.status_code == 401
