import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../store/authStore'

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  })

  it('should initialize with default values', () => {
    const state = useAuthStore.getState()
    
    expect(state.user).toBeNull()
    expect(state.accessToken).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should login user correctly', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'viewer' as const,
      is_active: true,
      created_at: new Date().toISOString(),
      last_login: null,
    }
    const accessToken = 'access-token'
    const refreshToken = 'refresh-token'

    useAuthStore.getState().login(mockUser, accessToken, refreshToken)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.accessToken).toBe(accessToken)
    expect(state.refreshToken).toBe(refreshToken)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should logout user correctly', () => {
    // First login
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'viewer' as const,
      is_active: true,
      created_at: new Date().toISOString(),
      last_login: null,
    }
    useAuthStore.getState().login(mockUser, 'token', 'refresh')

    // Then logout
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.accessToken).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should update tokens correctly', () => {
    useAuthStore.getState().setTokens('new-access', 'new-refresh')

    const state = useAuthStore.getState()
    expect(state.accessToken).toBe('new-access')
    expect(state.refreshToken).toBe('new-refresh')
  })
})
