// API Types for InternalKnowledgeHub

// User Types
export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'editor' | 'viewer'
  is_active: boolean
  created_at: string
  last_login: string | null
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// Document Types
export interface Document {
  id: string
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: 'pending' | 'processing' | 'processed' | 'failed'
  error_message: string | null
  page_count: number | null
  chunk_count: number
  uploaded_by: string
  created_at: string
  processed_at: string | null
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface DocumentUploadResponse {
  id: string
  filename: string
  status: string
  message: string
}

// Citation Types
export interface Citation {
  document_id: string
  document_name: string
  page_number: number | null
  paragraph_number: number | null
  text_snippet: string
  relevance_score: number
}

// Ask Types
export interface AskRequest {
  question: string
  top_k?: number
  alpha?: number
  session_id?: string
}

export interface AskResponse {
  answer: string
  citations: Citation[]
  session_id: string
  qa_id: string
  latency_ms: number
  model_name: string
}

// Chat Types
export interface ChatMessage {
  id: string
  question: string
  answer: string
  citations: Citation[]
  feedback: 'up' | 'down' | null
  created_at: string
  isLoading?: boolean
}

export interface ChatSession {
  session_id: string
  started_at: string
  last_activity: string
  message_count: number
  title: string
}

// Feedback Types
export interface FeedbackRequest {
  qa_id: string
  thumb: 'up' | 'down'
  comment?: string
}

// Admin Types
export interface StatsResponse {
  total_users: number
  total_documents: number
  total_chunks: number
  total_questions: number
  total_feedback: number
  feedback_positive: number
  feedback_negative: number
  documents_by_status: Record<string, number>
  questions_today: number
  questions_this_week: number
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Error Types
export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>
}

// QA History Types
export interface QAHistoryItem {
  id: string
  question: string
  answer: string
  citations: Citation[]
  feedback: 'up' | 'down' | null
  feedback_comment: string | null
  model_name: string
  latency_ms: number | null
  session_id: string
  created_at: string
}

export interface QAHistoryResponse {
  history: QAHistoryItem[]
  total: number
  page: number
  per_page: number
  pages: number
}
