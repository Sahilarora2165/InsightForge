import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from '../pages/LoginPage'

// Mock the auth store
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    login: vi.fn(),
    isAuthenticated: false,
    user: null,
  })),
}))

// Mock the API
vi.mock('../api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
  },
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form by default', () => {
    renderWithProviders(<LoginPage />)
    
    expect(screen.getByText('Welcome Back')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })

  it('switches to register form when clicking create account', () => {
    renderWithProviders(<LoginPage />)
    
    const switchButton = screen.getByText(/Don't have an account/i)
    fireEvent.click(switchButton)
    
    expect(screen.getByText('Create Account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your name')).toBeInTheDocument()
  })

  it('shows password when clicking eye icon', () => {
    renderWithProviders(<LoginPage />)
    
    const passwordInput = screen.getByPlaceholderText('••••••••')
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    // Find and click the eye button
    const eyeButton = passwordInput.parentElement?.querySelector('button')
    if (eyeButton) {
      fireEvent.click(eyeButton)
    }
    
    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('validates email format', async () => {
    renderWithProviders(<LoginPage />)
    
    const emailInput = screen.getByPlaceholderText('you@example.com')
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    
    const submitButton = screen.getByRole('button', { name: /Sign In/i })
    fireEvent.click(submitButton)
    
    // HTML5 validation should prevent submission
    expect(emailInput).toBeInvalid()
  })

  it('displays demo credentials', () => {
    renderWithProviders(<LoginPage />)
    
    expect(screen.getByText(/Demo Credentials/i)).toBeInTheDocument()
    expect(screen.getByText(/admin@internal.local/i)).toBeInTheDocument()
  })
})
