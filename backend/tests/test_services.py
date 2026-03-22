"""
Unit tests for service modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAuthService:
    """Tests for authentication service."""

    def test_password_hash_verification(self):
        """Test password hashing and verification."""
        from app.core.security import get_password_hash, verify_password
        
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        from app.core.security import get_password_hash
        
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Bcrypt should produce different hashes due to random salt
        assert hash1 != hash2


class TestIngestService:
    """Tests for document ingestion service."""

    @pytest.mark.unit
    def test_chunk_text(self):
        """Test text chunking functionality."""
        from app.services.ingest import IngestService
        
        service = IngestService()
        
        # Create a long text
        text = "This is a test sentence. " * 100
        
        chunks = service._chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk["content"]) <= 150 for chunk in chunks)  # Allow some overflow

    @pytest.mark.unit
    def test_extract_text_from_txt(self):
        """Test text extraction from TXT files."""
        import tempfile
        import os
        from app.services.ingest import IngestService
        
        service = IngestService()
        
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content for extraction.")
            temp_path = f.name
        
        try:
            content = service._extract_text(temp_path, "text/plain")
            assert "test content" in content
        finally:
            os.unlink(temp_path)

    @pytest.mark.unit
    def test_supported_file_types(self):
        """Test that supported file types are correctly identified."""
        from app.services.ingest import IngestService
        
        service = IngestService()
        
        supported = [".pdf", ".docx", ".txt", ".md"]
        unsupported = [".exe", ".jpg", ".zip"]
        
        for ext in supported:
            assert service._is_supported_type(f"file{ext}")
        
        for ext in unsupported:
            assert not service._is_supported_type(f"file{ext}")


class TestRAGService:
    """Tests for RAG service."""

    @pytest.mark.unit
    def test_normalize_scores(self):
        """Test score normalization."""
        from app.services.rag import RAGService
        
        scores = [0.5, 0.8, 0.3, 1.0, 0.1]
        normalized = RAGService._normalize_scores(scores)
        
        assert min(normalized) >= 0
        assert max(normalized) <= 1

    @pytest.mark.unit
    def test_reciprocal_rank_fusion(self):
        """Test RRF score calculation."""
        from app.services.rag import RAGService
        
        # Mock ranked lists
        dense_results = [("chunk1", 0.9), ("chunk2", 0.7), ("chunk3", 0.5)]
        sparse_results = [("chunk2", 0.8), ("chunk1", 0.6), ("chunk4", 0.4)]
        
        fused = RAGService._reciprocal_rank_fusion(
            dense_results, sparse_results, k=60
        )
        
        # chunk1 and chunk2 should have highest scores (appear in both)
        assert len(fused) >= 2

    @pytest.mark.unit
    @patch('app.services.rag.requests.post')
    def test_generate_embedding_mock(self, mock_post):
        """Test embedding generation with mocked Ollama."""
        from app.services.rag import RAGService
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 384}
        mock_post.return_value = mock_response
        
        service = RAGService()
        embedding = service._generate_embedding("test text")
        
        assert embedding is not None
        assert len(embedding) == 384


class TestConfigSettings:
    """Tests for configuration settings."""

    def test_settings_from_env(self):
        """Test settings loading from environment."""
        import os
        os.environ["SECRET_KEY"] = "test-secret-key"
        os.environ["DATABASE_URL"] = "sqlite:///test.db"
        
        from app.core.config import Settings
        settings = Settings()
        
        assert settings.SECRET_KEY == "test-secret-key"

    def test_default_settings(self):
        """Test default settings values."""
        from app.core.config import Settings
        
        settings = Settings()
        
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert settings.MAX_FILE_SIZE_MB > 0
