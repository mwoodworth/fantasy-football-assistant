import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../../test/utils'
import { AIAssistantPage } from '../AIAssistantPage'

// Mock the ChatInterface component
vi.mock('../../components/ai/ChatInterface', () => ({
  ChatInterface: () => (
    <div data-testid="chat-interface">
      Chat Interface Component
    </div>
  ),
}))

describe('AIAssistantPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the chat interface', () => {
    render(<AIAssistantPage />)
    
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument()
    expect(screen.getByText('Chat Interface Component')).toBeInTheDocument()
  })

  it('applies correct height styling', () => {
    const { container } = render(<AIAssistantPage />)
    
    const pageContainer = container.firstChild as HTMLElement
    expect(pageContainer).toHaveClass('h-[calc(100vh-8rem)]')
  })

  it('renders without crashing', () => {
    expect(() => render(<AIAssistantPage />)).not.toThrow()
  })
})