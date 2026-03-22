# InternalKnowledgeHub API Documentation

This document provides comprehensive documentation for the InternalKnowledgeHub REST API.

## Base URL

```
http://localhost:8000/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Lifecycle
- **Access Token**: Expires in 15 minutes
- **Refresh Token**: Expires in 7 days

---

## Authentication Endpoints

### Register User

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "viewer",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors:**
- `400` - Email already registered
- `422` - Validation error (weak password, invalid email)

---

### Login

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "user": { ... },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Account deactivated

---

### Refresh Token

```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### Logout

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "viewer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-16T08:00:00Z"
}
```

---

## Document Endpoints

### Upload Document

```http
POST /api/documents
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: The document file (PDF, DOCX, MD, TXT)

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "status": "pending",
  "message": "Document uploaded successfully. Processing will begin shortly."
}
```

**Errors:**
- `400` - Unsupported file type
- `413` - File too large (max 50MB)
- `403` - Insufficient permissions

---

### List Documents

```http
GET /api/documents?page=1&per_page=20&status=processed
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page (max 100) |
| status | string | - | Filter by status: pending, processing, processed, failed |

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "document.pdf",
      "original_filename": "My Document.pdf",
      "file_type": "pdf",
      "file_size": 1048576,
      "status": "processed",
      "page_count": 10,
      "chunk_count": 25,
      "uploaded_by": "user-uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:31:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### Get Document

```http
GET /api/documents/{id}
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "original_filename": "My Document.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "status": "processed",
  "error_message": null,
  "page_count": 10,
  "chunk_count": 25,
  "uploaded_by": "user-uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:31:00Z"
}
```

---

### Delete Document

```http
DELETE /api/documents/{id}
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Document deleted successfully"
}
```

**Errors:**
- `403` - Cannot delete documents uploaded by others (unless admin)
- `404` - Document not found

---

### Download Document

```http
GET /api/documents/{id}/download
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="document.pdf"

---

### Reprocess Document

```http
POST /api/documents/{id}/reprocess
Authorization: Bearer <access_token>
```

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "status": "pending",
  "message": "Document queued for reprocessing"
}
```

---

## Ask (RAG) Endpoints

### Ask Question

```http
POST /api/ask
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "question": "What is the vacation policy?",
  "top_k": 5,
  "alpha": 0.7,
  "session_id": "optional-session-uuid"
}
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| question | string | required | The question to ask |
| top_k | int | 5 | Number of documents to retrieve |
| alpha | float | 0.7 | Balance between dense (1.0) and sparse (0.0) retrieval |
| session_id | string | - | Continue an existing conversation |

**Response:** `200 OK`
```json
{
  "answer": "According to the employee handbook, the vacation policy allows...",
  "citations": [
    {
      "document_id": "uuid",
      "document_name": "Employee Handbook.pdf",
      "page_number": 15,
      "paragraph_number": 3,
      "text_snippet": "Employees are entitled to 20 days of paid vacation...",
      "relevance_score": 0.92
    }
  ],
  "session_id": "uuid",
  "qa_id": "uuid",
  "latency_ms": 1250,
  "model_name": "llama3"
}
```

---

### Get Chat History

```http
GET /api/history?session_id=uuid&limit=50
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "id": "uuid",
      "question": "What is the vacation policy?",
      "answer": "According to the employee handbook...",
      "citations": [...],
      "feedback": "up",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10
}
```

---

### Get Chat Sessions

```http
GET /api/sessions
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "title": "Vacation Policy Questions",
      "started_at": "2024-01-15T10:30:00Z",
      "last_activity": "2024-01-15T10:45:00Z",
      "message_count": 5
    }
  ]
}
```

---

## Feedback Endpoints

### Submit Feedback

```http
POST /api/feedback
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "qa_id": "uuid",
  "thumb": "up",
  "comment": "Very helpful answer!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Feedback submitted successfully"
}
```

---

## Admin Endpoints

> **Note:** Admin endpoints require `admin` role.

### Get Statistics

```http
GET /api/admin/stats
Authorization: Bearer <admin_access_token>
```

**Response:** `200 OK`
```json
{
  "total_users": 150,
  "total_documents": 450,
  "total_chunks": 12500,
  "total_questions": 3200,
  "total_feedback": 850,
  "feedback_positive": 720,
  "feedback_negative": 130,
  "documents_by_status": {
    "pending": 5,
    "processing": 2,
    "processed": 440,
    "failed": 3
  },
  "questions_today": 45,
  "questions_this_week": 280
}
```

---

### List Users

```http
GET /api/admin/users?page=1&per_page=20
Authorization: Bearer <admin_access_token>
```

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "viewer",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-16T08:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

---

### Update User

```http
PUT /api/admin/users/{id}
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "name": "New Name",
  "role": "editor",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "New Name",
  "role": "editor",
  "is_active": true,
  ...
}
```

---

### Delete User

```http
DELETE /api/admin/users/{id}
Authorization: Bearer <admin_access_token>
```

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

---

### Get Audit Logs

```http
GET /api/admin/audit-logs?page=1&per_page=50
Authorization: Bearer <admin_access_token>
```

**Response:** `200 OK`
```json
{
  "logs": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "action": "document_upload",
      "resource_type": "document",
      "resource_id": "uuid",
      "details": { "filename": "doc.pdf" },
      "ip_address": "192.168.1.1",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5000
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": { ... }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async processing started) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 413 | Payload Too Large |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable (Ollama offline) |

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Ask endpoint**: 20 requests per minute per user
- **Upload endpoint**: 10 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

---

## Webhooks (Future)

Planned webhook events:
- `document.processed` - Document processing completed
- `document.failed` - Document processing failed
- `user.created` - New user registered

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {access_token}"}

# Ask a question
response = requests.post(
    f"{BASE_URL}/ask",
    headers=headers,
    json={"question": "What is the vacation policy?"}
)
answer = response.json()
print(answer["answer"])
```

### JavaScript

```javascript
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { Authorization: `Bearer ${accessToken}` }
});

// Ask a question
const { data } = await api.post('/ask', {
  question: 'What is the vacation policy?'
});
console.log(data.answer);
```

### cURL

```bash
# Ask a question
curl -X POST http://localhost:8000/api/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
```
