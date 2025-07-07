import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { RegisterPage } from '../RegisterPage'

// Mock the auth store
const mockNavigate = vi.fn()

vi.mock('../../store/useAuthStore', () => ({
  useAuthStore: () => ({
    register: vi.fn(),
    isLoading: false,
    error: null,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
      <a href={to}>{children}</a>
    ),
  }
})

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders registration form', () => {
    render(<RegisterPage />)
    
    expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows link to login page', () => {
    render(<RegisterPage />)
    
    expect(screen.getByText(/already have an account/i)).toBeInTheDocument()
    expect(screen.getByText(/sign in/i)).toBeInTheDocument()
  })

  it('allows typing in form fields', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)
    
    const usernameInput = screen.getByLabelText(/username/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    
    await user.type(usernameInput, 'testuser')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    
    expect(usernameInput).toHaveValue('testuser')
    expect(emailInput).toHaveValue('test@example.com')
    expect(passwordInput).toHaveValue('password123')
  })

  it('can submit the form', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)
    
    const usernameInput = screen.getByLabelText(/username/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /create account/i })
    
    await user.type(usernameInput, 'testuser')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    
    expect(submitButton).toBeInTheDocument()
    expect(submitButton).not.toBeDisabled()
  })

  it('renders app title and description', () => {
    render(<RegisterPage />)
    
    expect(screen.getByText('Fantasy Football Assistant')).toBeInTheDocument()
    expect(screen.getByText('AI-powered insights for winning leagues')).toBeInTheDocument()
  })

  it('renders form description', () => {
    render(<RegisterPage />)
    
    expect(screen.getByText('Get started with AI-powered fantasy football insights')).toBeInTheDocument()
  })
})