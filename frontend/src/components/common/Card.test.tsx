import { describe, it, expect } from 'vitest'
import { render, screen } from '../../test/utils'
import { Card } from './Card'

describe('Card Component', () => {
  it('renders card with children', () => {
    render(
      <Card>
        <div>Card content</div>
      </Card>
    )
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(
      <Card className="custom-class" data-testid="card">
        <div>Content</div>
      </Card>
    )
    const card = screen.getByTestId('card')
    expect(card).toHaveClass('custom-class')
  })

  it('applies default classes', () => {
    render(
      <Card data-testid="card">
        <div>Content</div>
      </Card>
    )
    const card = screen.getByTestId('card')
    expect(card).toHaveClass('bg-white', 'rounded-lg', 'border')
  })
})