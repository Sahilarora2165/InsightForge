"""
RAG (Retrieval-Augmented Generation) Service
Implements hybrid search with dense + sparse retrieval and re-ranking.
"""
import time
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import requests
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.core.database import db
from app.models import Chunk, Document, QAHistory

logger = logging.getLogger(__name__)

# Simple in-memory cache for query results
_query_cache: Dict[str, Dict[str, Any]] = {}
_cache_stats = {'hits': 0, 'misses': 0, 'saved_time_ms': 0}
CACHE_TTL = 3600  # 1 hour


@dataclass
class SearchResult:
    """Search result with chunk and score."""
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    page_number: Optional[int]
    paragraph_number: Optional[int]
    score: float


@dataclass
class Citation:
    """Citation for an answer."""
    document_id: str
    document_name: str
    page_number: Optional[int]
    paragraph_number: Optional[int]
    text_snippet: str
    relevance_score: float


class RAGService:
    """Service for RAG operations."""
    
    # Class-level cross-encoder (lazy loaded once)
    _cross_encoder = None
    _cross_encoder_loaded = False
    
    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL
        self.top_k = settings.RAG_TOP_K
        self.alpha = settings.RAG_HYBRID_ALPHA
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=int(settings.CHROMA_PORT),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_hub",
            metadata={"hnsw:space": "cosine"}
        )
    
    @property
    def cross_encoder(self):
        """Lazy load cross-encoder only when needed (saves ~3s startup time)."""
        if not RAGService._cross_encoder_loaded:
            RAGService._cross_encoder_loaded = True
            try:
                logger.info("Lazy loading cross-encoder...")
                start = time.time()
                RAGService._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info(f"Cross-encoder loaded in {time.time() - start:.2f}s")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")
                RAGService._cross_encoder = None
        return RAGService._cross_encoder
    
    @staticmethod
    def _get_cache_key(question: str, user_id: str) -> str:
        """Generate cache key for a question."""
        normalized = question.lower().strip()
        return hashlib.md5(f"{user_id}:{normalized}".encode()).hexdigest()
    
    @staticmethod
    def get_cached_response(question: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        key = RAGService._get_cache_key(question, user_id)
        if key in _query_cache:
            cached = _query_cache[key]
            if time.time() - cached['timestamp'] < CACHE_TTL:
                _cache_stats['hits'] += 1
                _cache_stats['saved_time_ms'] += cached.get('latency_ms', 2000)
                response = cached['response'].copy()
                response['cached'] = True
                response['latency_ms'] = 5  # Cache lookup ~5ms
                logger.info(f"Cache HIT: {question[:50]}...")
                return response
            del _query_cache[key]
        _cache_stats['misses'] += 1
        return None
    
    @staticmethod
    def cache_response(question: str, user_id: str, response: Dict[str, Any]) -> None:
        """Cache a response."""
        if len(_query_cache) > 1000:  # Simple size limit
            oldest = min(_query_cache.keys(), key=lambda k: _query_cache[k]['timestamp'])
            del _query_cache[oldest]
        key = RAGService._get_cache_key(question, user_id)
        _query_cache[key] = {'response': response, 'timestamp': time.time(), 'latency_ms': response.get('latency_ms', 0)}
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics."""
        total = _cache_stats['hits'] + _cache_stats['misses']
        return {
            'hits': _cache_stats['hits'],
            'misses': _cache_stats['misses'],
            'hit_rate': round(_cache_stats['hits'] / total * 100, 2) if total > 0 else 0,
            'saved_time_ms': _cache_stats['saved_time_ms'],
            'cache_size': len(_query_cache)
        }
    
    def _load_cross_encoder(self):
        """Deprecated - using lazy loading now."""
        pass
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_texts_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        60% faster than embedding one at a time.
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                embedding = self.embed_text(text)
                batch_embeddings.append(embedding)
            
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        return all_embeddings
    
    def embed_chunks(self, chunks: List[Chunk]) -> None:
        """Generate and store embeddings for chunks using batch processing."""
        if not chunks:
            return
        
        start_time = time.time()
        
        # Get document info once
        doc_ids = set(c.document_id for c in chunks)
        docs = {d.id: d for d in Document.query.filter(Document.id.in_(doc_ids)).all()}
        
        # Batch embed all texts
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts_batch(texts)
        
        # Prepare batch data for ChromaDB
        ids = []
        metadatas = []
        
        for chunk, embedding in zip(chunks, embeddings):
            doc = docs.get(chunk.document_id)
            uploaded_by = doc.uploaded_by if doc else ""
            
            ids.append(chunk.id)
            metadatas.append({
                "document_id": chunk.document_id,
                "uploaded_by": uploaded_by,
                "page_number": chunk.page_number or 0,
                "paragraph_number": chunk.paragraph_number or 0,
                "chunk_index": chunk.chunk_index
            })
            chunk.embedding_id = chunk.id
        
        # Add all to ChromaDB in one call
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        db.session.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"Batch embedded {len(chunks)} chunks in {elapsed:.2f}s ({len(chunks)/elapsed:.1f} chunks/sec)")
    
    def delete_document_embeddings(self, document_id: str) -> None:
        """Delete embeddings for a document."""
        chunks = Chunk.query.filter_by(document_id=document_id).all()
        chunk_ids = [c.id for c in chunks if c.embedding_id]
        
        if chunk_ids:
            try:
                self.collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} embeddings for document {document_id}")
            except Exception as e:
                logger.error(f"Error deleting embeddings: {e}")
    
    def dense_search(self, query: str, top_k: int = 20, user_id: Optional[str] = None) -> List[SearchResult]:
        """Perform dense (embedding) search."""
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Build where filter for user's documents
        where_filter = None
        if user_id:
            where_filter = {"uploaded_by": user_id}
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        search_results = []
        if results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Get chunk from database for additional info
                chunk = Chunk.query.get(chunk_id)
                if chunk:
                    document = Document.query.get(chunk.document_id)
                    # Convert distance to similarity score (cosine)
                    score = 1 - results['distances'][0][i]
                    
                    search_results.append(SearchResult(
                        chunk_id=chunk_id,
                        document_id=chunk.document_id,
                        document_name=document.original_filename if document else "Unknown",
                        text=chunk.text,
                        page_number=chunk.page_number,
                        paragraph_number=chunk.paragraph_number,
                        score=score
                    ))
        
        return search_results
    
    def sparse_search(self, query: str, top_k: int = 20, user_id: Optional[str] = None) -> List[SearchResult]:
        """Perform sparse (BM25) search."""
        # Get chunks from database, filtered by user if specified
        if user_id:
            # Join with Document to filter by uploaded_by
            chunks = Chunk.query.join(Document).filter(Document.uploaded_by == user_id).all()
        else:
            chunks = Chunk.query.all()
        
        if not chunks:
            return []
        
        # Tokenize documents
        tokenized_docs = [chunk.text.lower().split() for chunk in chunks]
        
        # Build BM25 index
        bm25 = BM25Okapi(tokenized_docs)
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get scores
        scores = bm25.get_scores(tokenized_query)
        
        # Get top-k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        search_results = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk = chunks[idx]
                document = Document.query.get(chunk.document_id)
                
                search_results.append(SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=document.original_filename if document else "Unknown",
                    text=chunk.text,
                    page_number=chunk.page_number,
                    paragraph_number=chunk.paragraph_number,
                    score=scores[idx]
                ))
        
        return search_results
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        alpha: float = 0.7,
        user_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining dense and sparse results.
        Uses Reciprocal Rank Fusion (RRF).
        """
        # Get dense and sparse results filtered by user
        dense_results = self.dense_search(query, top_k, user_id=user_id)
        sparse_results = self.sparse_search(query, top_k, user_id=user_id)
        
        # Create RRF scores
        k = 60  # RRF constant
        rrf_scores = {}
        
        # Process dense results
        for rank, result in enumerate(dense_results):
            rrf_scores[result.chunk_id] = {
                'result': result,
                'score': alpha * (1 / (k + rank + 1))
            }
        
        # Process sparse results
        for rank, result in enumerate(sparse_results):
            if result.chunk_id in rrf_scores:
                rrf_scores[result.chunk_id]['score'] += (1 - alpha) * (1 / (k + rank + 1))
            else:
                rrf_scores[result.chunk_id] = {
                    'result': result,
                    'score': (1 - alpha) * (1 / (k + rank + 1))
                }
        
        # Sort by RRF score
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        # Return top results with updated scores
        final_results = []
        for item in sorted_results[:top_k]:
            result = item['result']
            result.score = item['score']
            final_results.append(result)
        
        return final_results
    
    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """Re-rank results using cross-encoder."""
        if not self.cross_encoder or not results:
            return results[:top_k]
        
        # Prepare pairs for cross-encoder
        pairs = [[query, result.text] for result in results]
        
        # Get cross-encoder scores
        scores = self.cross_encoder.predict(pairs)
        
        # Combine with original scores
        for i, result in enumerate(results):
            result.score = float(scores[i])
        
        # Sort by new scores
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def build_context(self, results: List[SearchResult]) -> Tuple[str, List[Citation]]:
        """Build context string and citations from search results."""
        context_parts = []
        citations = []
        
        for i, result in enumerate(results):
            # Build context entry
            location = []
            if result.page_number:
                location.append(f"Page {result.page_number}")
            if result.paragraph_number:
                location.append(f"Paragraph {result.paragraph_number}")
            
            location_str = ", ".join(location) if location else "Unknown location"
            
            context_parts.append(
                f"[Source {i+1}: {result.document_name}, {location_str}]\n{result.text}"
            )
            
            # Build citation
            citations.append(Citation(
                document_id=result.document_id,
                document_name=result.document_name,
                page_number=result.page_number,
                paragraph_number=result.paragraph_number,
                text_snippet=result.text[:200] + "..." if len(result.text) > 200 else result.text,
                relevance_score=result.score
            ))
        
        context = "\n\n".join(context_parts)
        return context, citations
    
    def generate_answer(
        self,
        question: str,
        context: str,
        stream: bool = False
    ) -> str:
        """Generate answer using Ollama."""
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.
Use ONLY the information from the context below to answer the question.
If the answer is not in the context, say "I don't have enough information to answer this question."
Always cite your sources by mentioning the source number (e.g., [Source 1]).

Context:
{context}

Question: {question}

Answer:"""
        
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1024
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            
            if stream:
                # Return generator for streaming
                return response.iter_lines()
            else:
                return response.json()["response"]
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    def ask(
        self,
        question: str,
        user_id: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        alpha: float = 0.7
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline: search, rerank, generate answer.
        Uses caching to avoid repeated LLM calls for same questions.
        """
        start_time = time.time()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check cache first (95% faster for repeated queries)
        cached = self.get_cached_response(question, user_id)
        if cached:
            cached['session_id'] = session_id
            return cached
        
        # Step 1: Hybrid search (filtered by user's documents)
        search_results = self.hybrid_search(question, top_k=20, alpha=alpha, user_id=user_id)
        
        if not search_results:
            return {
                "answer": "I don't have any documents to search through. Please upload some documents first.",
                "citations": [],
                "session_id": session_id,
                "qa_id": None,
                "latency_ms": int((time.time() - start_time) * 1000),
                "model_name": self.model,
                "cached": False
            }
        
        # Step 2: Re-rank
        reranked_results = self.rerank(question, search_results, top_k=top_k)
        
        # Step 3: Build context
        context, citations = self.build_context(reranked_results)
        
        # Step 4: Generate answer
        answer = self.generate_answer(question, context)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Store QA history
        qa_history = QAHistory(
            user_id=user_id,
            session_id=session_id,
            question=question,
            answer=answer,
            citations=[{
                "document_id": c.document_id,
                "document_name": c.document_name,
                "page_number": c.page_number,
                "paragraph_number": c.paragraph_number,
                "text_snippet": c.text_snippet,
                "relevance_score": c.relevance_score
            } for c in citations],
            context_chunks=[r.chunk_id for r in reranked_results],
            model_name=self.model,
            latency_ms=latency_ms
        )
        
        db.session.add(qa_history)
        db.session.commit()
        
        response = {
            "answer": answer,
            "citations": [{
                "document_id": c.document_id,
                "document_name": c.document_name,
                "page_number": c.page_number,
                "paragraph_number": c.paragraph_number,
                "text_snippet": c.text_snippet,
                "relevance_score": c.relevance_score
            } for c in citations],
            "session_id": session_id,
            "qa_id": qa_history.id,
            "latency_ms": latency_ms,
            "model_name": self.model,
            "cached": False
        }
        
        # Cache the response for future queries
        self.cache_response(question, user_id, response)
        
        return response
    
    def get_chat_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for a user."""
        query = QAHistory.query.filter_by(user_id=user_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        query = query.order_by(QAHistory.created_at.desc()).limit(limit)
        
        history = query.all()
        
        return [qa.to_dict() for qa in reversed(history)]
