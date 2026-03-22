import api from './client'
import type {
  AuthResponse,
  User,
  Document,
  DocumentListResponse,
  DocumentUploadResponse,
  AskRequest,
  AskResponse,
  ChatSession,
  ChatMessage,
  FeedbackRequest,
  StatsResponse,
  UserListResponse,
} from '../types'

// ====================
// Auth API
// ====================

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/login', { email, password })
    return response.data
  },

  register: async (email: string, password: string, name: string): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/register', { email, password, name })
    return response.data
  },

  refresh: async (): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/refresh')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/api/auth/logout')
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  updateMe: async (data: { name?: string }): Promise<User> => {
    const response = await api.put('/api/auth/me', data)
    return response.data
  },

  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await api.post('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },
}

// ====================
// Documents API
// ====================

export const documentsApi = {
  list: async (page = 1, perPage = 20, status?: string): Promise<DocumentListResponse> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (status) params.append('status', status)
    const response = await api.get(`/api/documents?${params}`)
    return response.data
  },

  get: async (id: string): Promise<Document> => {
    const response = await api.get(`/api/documents/${id}`)
    return response.data
  },

  upload: async (file: File, onProgress?: (progress: number) => void): Promise<DocumentUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/documents/${id}`)
  },

  download: async (id: string): Promise<Blob> => {
    const response = await api.get(`/api/documents/${id}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  reprocess: async (id: string): Promise<DocumentUploadResponse> => {
    const response = await api.post(`/api/documents/${id}/reprocess`)
    return response.data
  },
}

// ====================
// Ask API
// ====================

export const askApi = {
  ask: async (request: AskRequest): Promise<AskResponse> => {
    const response = await api.post('/api/ask', request)
    return response.data
  },

  getHistory: async (sessionId?: string, limit = 50): Promise<{ messages: ChatMessage[]; total: number }> => {
    const params = new URLSearchParams({ limit: String(limit) })
    if (sessionId) params.append('session_id', sessionId)
    const response = await api.get(`/api/history?${params}`)
    return response.data
  },

  getSessions: async (): Promise<{ sessions: ChatSession[] }> => {
    const response = await api.get('/api/sessions')
    return response.data
  },
}

// ====================
// Feedback API
// ====================

export const feedbackApi = {
  submit: async (request: FeedbackRequest): Promise<void> => {
    await api.post('/api/feedback', request)
  },

  get: async (qaId: string): Promise<{ feedback: 'up' | 'down' | null; comment: string | null }> => {
    const response = await api.get(`/api/feedback/${qaId}`)
    return response.data
  },

  delete: async (qaId: string): Promise<void> => {
    await api.delete(`/api/feedback/${qaId}`)
  },
}

// ====================
// Admin API
// ====================

export const adminApi = {
  getStats: async (): Promise<StatsResponse> => {
    const response = await api.get('/api/admin/stats')
    return response.data
  },

  getUsers: async (page = 1, perPage = 20): Promise<UserListResponse> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    const response = await api.get(`/api/admin/users?${params}`)
    return response.data
  },

  getUser: async (id: string): Promise<User> => {
    const response = await api.get(`/api/admin/users/${id}`)
    return response.data
  },

  createUser: async (data: { email: string; password: string; name: string; role: string }): Promise<User> => {
    const response = await api.post('/api/admin/users', data)
    return response.data
  },

  updateUser: async (id: string, data: { name?: string; role?: string; is_active?: boolean }): Promise<User> => {
    const response = await api.put(`/api/admin/users/${id}`, data)
    return response.data
  },

  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/api/admin/users/${id}`)
  },

  getAuditLogs: async (page = 1, perPage = 50): Promise<{ logs: unknown[]; total: number }> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    const response = await api.get(`/api/admin/audit-logs?${params}`)
    return response.data
  },

  getAllFeedback: async (page = 1, perPage = 50, type?: string): Promise<{ feedback: unknown[]; total: number }> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (type) params.append('type', type)
    const response = await api.get(`/api/admin/feedback?${params}`)
    return response.data
  },
}
