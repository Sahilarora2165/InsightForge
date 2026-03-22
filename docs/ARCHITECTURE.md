# Architecture Overview

This document describes the architecture of InternalKnowledgeHub, a production-grade internal document Q&A system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React + Vite + TypeScript                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│   │
│  │  │  Login   │  │   Chat   │  │  Upload  │  │      Admin       ││   │
│  │  │   Page   │  │   Page   │  │   Page   │  │    Dashboard     ││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│   │
│  │  ┌────────────────────────────────────────────────────────────┐│   │
│  │  │              Zustand (State) + React Query (Server)         ││   │
│  │  └────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Nginx (Reverse Proxy)                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Flask Application                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │  Auth API    │  │ Documents API│  │       Ask API        │  │   │
│  │  │  /auth/*     │  │  /documents/*│  │       /ask/*         │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │                      Services Layer                        │  │   │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │  │   │
│  │  │  │AuthService │  │IngestService│  │    RAG Service     │ │  │   │
│  │  │  └────────────┘  └────────────┘  └────────────────────┘ │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          │                    │                          │
│                          ▼                    ▼                          │
│  ┌──────────────────────────────┐  ┌───────────────────────────────┐  │
│  │         PostgreSQL           │  │           Redis               │  │
│  │  ┌────────┐  ┌────────────┐ │  │  ┌─────────┐  ┌────────────┐ │  │
│  │  │ Users  │  │  Documents │ │  │  │ Session │  │   Cache    │ │  │
│  │  │ QAHist │  │   Chunks   │ │  │  │  Store  │  │  (Semantic)│ │  │
│  │  └────────┘  └────────────┘ │  │  └─────────┘  └────────────┘ │  │
│  └──────────────────────────────┘  └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           WORKER LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        Celery Workers                             │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────────────┐ │   │
│  │  │   Task Queue     │  │          Document Pipeline           │ │   │
│  │  │   (Redis)        │  │  Parse → Chunk → Embed → Store      │ │   │
│  │  └──────────────────┘  └──────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AI/ML LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                           Ollama                                  │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────────────┐ │   │
│  │  │   Llama 3        │  │      nomic-embed-text                │ │   │
│  │  │   (Generation)   │  │         (Embeddings)                 │ │   │
│  │  └──────────────────┘  └──────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         ChromaDB                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │              Vector Index (Dense Retrieval)               │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI Framework | React 18 | Component-based UI |
| Build Tool | Vite | Fast development and builds |
| Type System | TypeScript | Type safety |
| Styling | Tailwind CSS | Utility-first CSS |
| State (Client) | Zustand | Lightweight state management |
| State (Server) | React Query | Server state and caching |
| Routing | React Router v6 | Client-side routing |
| Icons | Lucide React | Consistent iconography |

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | Flask 3.0 | REST API |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema migrations |
| Validation | Pydantic v2 | Request/Response validation |
| Auth | Flask-JWT-Extended | JWT authentication |
| Task Queue | Celery | Async task processing |
| Caching | Redis | Session & semantic cache |

### AI/ML Pipeline

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM | Ollama + Llama 3 | Answer generation |
| Embeddings | nomic-embed-text | Text → vectors |
| Vector DB | ChromaDB | Similarity search |
| Sparse Search | BM25 (rank-bm25) | Keyword matching |
| Re-ranking | Cross-encoder | Result refinement |

## Data Flow

### Document Ingestion

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   Upload   │────▶│   Parse    │────▶│   Chunk    │────▶│   Embed    │
│   (API)    │     │ (PyMuPDF)  │     │ (RecursiveCharacterTextSplitter) │     │ (Ollama)   │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
                                                                │
                                                                ▼
                                              ┌────────────────────────────┐
                                              │         Store             │
                                              │  PostgreSQL + ChromaDB    │
                                              └────────────────────────────┘
```

1. **Upload**: User uploads document via API
2. **Queue**: Document added to Celery queue
3. **Parse**: Extract text from PDF/DOCX/MD/TXT
4. **Chunk**: Split into overlapping chunks (512 tokens, 128 overlap)
5. **Embed**: Generate embeddings via Ollama
6. **Store**: Save metadata to PostgreSQL, vectors to ChromaDB

### Query Processing (RAG)

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│  Question  │────▶│   Embed    │────▶│  Retrieve  │────▶│  Re-rank   │
│   (User)   │     │  (Query)   │     │(Dense+BM25)│     │(CrossEnc.) │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
                                                                │
                   ┌────────────┐     ┌────────────┐            │
                   │   Answer   │◀────│  Generate  │◀───────────┘
                   │ (User)     │     │  (Llama3)  │
                   └────────────┘     └────────────┘
```

1. **Embed Query**: Convert question to vector
2. **Dense Retrieval**: Find similar chunks via ChromaDB
3. **Sparse Retrieval**: BM25 keyword search
4. **Fusion**: Reciprocal Rank Fusion (RRF) to combine results
5. **Re-rank**: Cross-encoder scores for top candidates
6. **Generate**: LLM generates answer with citations

## Hybrid RAG Pipeline

The hybrid retrieval combines multiple strategies:

```python
# Dense retrieval (semantic similarity)
dense_results = chroma.query(embedding, k=20)

# Sparse retrieval (keyword matching)  
sparse_results = bm25.search(query, k=20)

# Reciprocal Rank Fusion
def rrf_score(rank, k=60):
    return 1 / (k + rank)

# Combine scores
for doc_id in union(dense_results, sparse_results):
    score = α * rrf(dense_rank) + (1-α) * rrf(sparse_rank)

# Re-rank top candidates
top_k = sorted(combined, key=lambda x: x.score)[:20]
reranked = cross_encoder.predict(query, top_k)

# Return top 5 for context
context = reranked[:5]
```

## Security Architecture

### Authentication Flow

```
┌────────┐                    ┌────────┐                    ┌────────┐
│ Client │                    │  API   │                    │   DB   │
└───┬────┘                    └───┬────┘                    └───┬────┘
    │                             │                             │
    │ POST /auth/login           │                             │
    │ {email, password}          │                             │
    │───────────────────────────▶│                             │
    │                             │ Verify credentials         │
    │                             │────────────────────────────▶│
    │                             │◀────────────────────────────│
    │                             │                             │
    │ {access_token, refresh_token}                            │
    │◀───────────────────────────│                             │
    │                             │                             │
    │ GET /api/documents         │                             │
    │ Authorization: Bearer xxx   │                             │
    │───────────────────────────▶│                             │
    │                             │ Validate JWT               │
    │                             │ Check permissions          │
    │                             │────────────────────────────▶│
    │                             │◀────────────────────────────│
    │ {documents: [...]}         │                             │
    │◀───────────────────────────│                             │
```

### Security Measures

| Layer | Measure | Implementation |
|-------|---------|----------------|
| Transport | HTTPS | TLS 1.3 (nginx) |
| Auth | JWT | RS256, short expiry |
| Passwords | Hashing | bcrypt, cost 12 |
| Input | Validation | Pydantic schemas |
| Output | Sanitization | DOMPurify |
| CORS | Restricted | Allowlist origins |
| Rate Limit | Per-user | Redis sliding window |

## Deployment Options

### Development

```bash
# Start all services
docker-compose up -d

# Or run individually
cd backend && flask run
cd frontend && npm run dev
celery -A worker.tasks worker -l info
```

### Production (Docker Swarm)

```yaml
# docker-stack.yml
version: '3.8'
services:
  frontend:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 256M
  
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
  
  worker:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
```

### Production (Kubernetes)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    spec:
      containers:
      - name: backend
        image: internal-knowledge-hub-backend:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Performance Considerations

### Caching Strategy

| Cache | Purpose | TTL |
|-------|---------|-----|
| Session | User sessions | 7 days |
| Semantic | Similar query results | 1 hour |
| Document List | Frequently accessed | 5 min |
| Stats | Admin dashboard | 1 min |

### Optimization Tips

1. **Embedding Batch Processing**: Process multiple chunks together
2. **Connection Pooling**: SQLAlchemy pool size = workers * 2
3. **Async Workers**: Celery concurrency = CPU cores
4. **Vector Index**: ChromaDB HNSW for fast ANN search
5. **Response Streaming**: SSE for long LLM responses

## Monitoring

### Health Checks

```bash
# API health
GET /health → {"status": "healthy", "db": "ok", "redis": "ok"}

# Worker health
celery -A worker.tasks inspect ping

# Ollama health
curl http://ollama:11434/api/tags
```

### Metrics to Track

- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Document processing time
- RAG query latency
- LLM token usage
- Cache hit rate
