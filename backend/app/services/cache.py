"""
Semantic caching for RAG queries.

Uses embedding similarity to find cached answers for similar questions,
reducing LLM calls and improving response time.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import redis

from app.core.config import settings


class SemanticCache:
    """
    Semantic cache for RAG query results.
    
    Uses Redis for storage with embedding-based similarity search.
    Falls back to exact hash matching if embeddings unavailable.
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        similarity_threshold: float = 0.92,
        ttl_hours: int = 24,
        max_cache_size: int = 10000
    ):
        self.redis = redis_client or redis.from_url(settings.REDIS_URL)
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)
        self.max_cache_size = max_cache_size
        self.cache_prefix = "semantic_cache:"
        self.embedding_prefix = "cache_embedding:"
        self.index_key = "cache_index"
    
    def _compute_hash(self, question: str) -> str:
        """Compute hash of normalized question for exact matching."""
        normalized = question.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
    
    def get(
        self,
        question: str,
        embedding: Optional[list[float]] = None
    ) -> Optional[dict]:
        """
        Retrieve cached answer for a question.
        
        Args:
            question: The question to look up
            embedding: Optional embedding of the question for semantic matching
            
        Returns:
            Cached result dict with 'answer' and 'sources' if found, None otherwise
        """
        # Try exact hash match first (fast path)
        question_hash = self._compute_hash(question)
        exact_key = f"{self.cache_prefix}{question_hash}"
        
        cached = self.redis.get(exact_key)
        if cached:
            result = json.loads(cached)
            result["cache_hit"] = "exact"
            return result
        
        # Try semantic similarity if embedding provided
        if embedding:
            return self._semantic_lookup(embedding)
        
        return None
    
    def _semantic_lookup(self, query_embedding: list[float]) -> Optional[dict]:
        """Find semantically similar cached question."""
        # Get all cached embeddings
        index_data = self.redis.hgetall(self.index_key)
        if not index_data:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for cache_key, embedding_json in index_data.items():
            try:
                stored_embedding = json.loads(embedding_json)
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = cache_key.decode() if isinstance(cache_key, bytes) else cache_key
            except (json.JSONDecodeError, ValueError):
                continue
        
        if best_match:
            cached = self.redis.get(best_match)
            if cached:
                result = json.loads(cached)
                result["cache_hit"] = "semantic"
                result["similarity"] = best_similarity
                return result
        
        return None
    
    def set(
        self,
        question: str,
        answer: str,
        sources: list[dict],
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Cache a question-answer pair.
        
        Args:
            question: The question
            answer: The generated answer
            sources: List of source documents/chunks
            embedding: Optional question embedding for semantic matching
            metadata: Optional additional metadata
        """
        question_hash = self._compute_hash(question)
        cache_key = f"{self.cache_prefix}{question_hash}"
        
        cache_data = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "cached_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store the cache entry
        self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(cache_data)
        )
        
        # Store embedding for semantic matching
        if embedding:
            self.redis.hset(
                self.index_key,
                cache_key,
                json.dumps(embedding)
            )
        
        # Prune if needed
        self._prune_if_needed()
    
    def _prune_if_needed(self) -> None:
        """Remove old entries if cache exceeds max size."""
        cache_size = self.redis.hlen(self.index_key)
        if cache_size > self.max_cache_size:
            # Remove oldest 10% of entries
            to_remove = int(cache_size * 0.1)
            keys = list(self.redis.hkeys(self.index_key))[:to_remove]
            
            if keys:
                pipe = self.redis.pipeline()
                for key in keys:
                    pipe.delete(key)
                    pipe.hdel(self.index_key, key)
                pipe.execute()
    
    def invalidate(self, question: str) -> bool:
        """
        Invalidate a cached entry.
        
        Args:
            question: The question to invalidate
            
        Returns:
            True if entry was found and removed
        """
        question_hash = self._compute_hash(question)
        cache_key = f"{self.cache_prefix}{question_hash}"
        
        deleted = self.redis.delete(cache_key)
        self.redis.hdel(self.index_key, cache_key)
        
        return deleted > 0
    
    def invalidate_all(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            Number of entries removed
        """
        # Get all cache keys
        keys = list(self.redis.scan_iter(f"{self.cache_prefix}*"))
        
        if keys:
            count = self.redis.delete(*keys)
            self.redis.delete(self.index_key)
            return count
        
        return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "total_entries": self.redis.hlen(self.index_key),
            "similarity_threshold": self.similarity_threshold,
            "ttl_hours": self.ttl.total_seconds() / 3600,
            "max_size": self.max_cache_size
        }


# Singleton instance
_cache_instance: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Get or create semantic cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance
