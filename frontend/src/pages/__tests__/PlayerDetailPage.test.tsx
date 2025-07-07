import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { PlayerDetailPage } from '../PlayerDetailPage'

// Mock react-router-dom
const mockNavigate = vi.fn()
const mockParams = { playerId: '1' }

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => mockParams,
    useNavigate: () => mockNavigate,
  }
})

// Mock chart components
vi.mock('../../components/analytics/PlayerPerformanceChart', () => ({
  PlayerPerformanceChart: ({ playerName, position, team }: { playerName: string; position: string; team: string }) => (
    <div data-testid="player-performance-chart">
      Performance chart for {playerName} ({position} - {team})
    </div>
  ),
}))

vi.mock('../../components/analytics/Chart', () => ({
  Chart: ({ data, type, height, width }: { data: any; type: string; height: number; width: number }) => (
    <div data-testid="chart">
      {type} chart - {height}x{width} - {data.length} data points
    </div>
  ),
}))

// Mock Modal components
vi.mock('../../components/common/Modal', () => ({
  Modal: ({ isOpen, onClose, title, children }: { isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode }) => (
    isOpen ? (
      <div data-testid="modal">
        <div data-testid="modal-title">{title}</div>
        <button onClick={onClose} data-testid="close-modal">Close</button>
        {children}
      </div>
    ) : null
  ),
  ModalBody: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="modal-body">{children}</div>
  ),
}))

describe('PlayerDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders player header with basic info', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByRole('heading', { name: /josh allen/i })).toBeInTheDocument()
    expect(screen.getByText('#17')).toBeInTheDocument()
    expect(screen.getByText('QB')).toBeInTheDocument()
    expect(screen.getByText('BUF')).toBeInTheDocument()
    expect(screen.getByText('Healthy')).toBeInTheDocument()
  })

  it('displays player physical stats', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Age: 27')).toBeInTheDocument()
    expect(screen.getByText('Height: 6\'5"')).toBeInTheDocument()
    expect(screen.getByText('Weight: 237 lbs')).toBeInTheDocument()
    expect(screen.getByText('Experience: 6 years')).toBeInTheDocument()
  })

  it('displays player additional info', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Wyoming')).toBeInTheDocument()
    expect(screen.getByText('$43.0M')).toBeInTheDocument()
    expect(screen.getByText('98.2% owned')).toBeInTheDocument()
  })

  it('displays next game information', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Next Game: vs MIA')).toBeInTheDocument()
    expect(screen.getByText('Sunday 1:00 PM ET')).toBeInTheDocument()
    expect(screen.getByText('22.1 pts')).toBeInTheDocument()
    expect(screen.getByText('projected')).toBeInTheDocument()
  })

  it('renders back button', () => {
    render(<PlayerDetailPage />)
    
    const backButton = screen.getByRole('button', { name: /back to players/i })
    expect(backButton).toBeInTheDocument()
  })

  it('navigates back to players page when back button is clicked', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const backButton = screen.getByRole('button', { name: /back to players/i })
    await user.click(backButton)
    
    expect(mockNavigate).toHaveBeenCalledWith('/players')
  })

  it('renders action buttons', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByRole('button', { name: /add to watchlist/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /add to team/i })).toBeInTheDocument()
  })

  it('toggles watchlist status', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const watchlistButton = screen.getByRole('button', { name: /add to watchlist/i })
    expect(watchlistButton).toBeInTheDocument()
    
    await user.click(watchlistButton)
    expect(screen.getByRole('button', { name: /watchlisted/i })).toBeInTheDocument()
    
    await user.click(watchlistButton)
    expect(screen.getByRole('button', { name: /add to watchlist/i })).toBeInTheDocument()
  })

  it('renders all tab buttons', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /performance/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /matchups/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /news/i })).toBeInTheDocument()
  })

  it('shows overview tab by default', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Season Stats')).toBeInTheDocument()
    expect(screen.getByText('Projections')).toBeInTheDocument()
    expect(screen.getByText('Similar Players')).toBeInTheDocument()
  })

  it('displays season stats in overview tab', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Passing Yards')).toBeInTheDocument()
    expect(screen.getByText('2,876')).toBeInTheDocument()
    expect(screen.getByText('Passing TDs')).toBeInTheDocument()
    expect(screen.getByText('21')).toBeInTheDocument()
    expect(screen.getByText('Interceptions')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('displays projections in overview tab', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('312.4')).toBeInTheDocument()
    expect(screen.getByText('#3')).toBeInTheDocument()
    expect(screen.getByText('22.1')).toBeInTheDocument()
    expect(screen.getByText('16.8')).toBeInTheDocument()
    expect(screen.getByText('28.7')).toBeInTheDocument()
  })

  it('displays similar players in overview tab', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('Lamar Jackson')).toBeInTheDocument()
    expect(screen.getByText('87% similar')).toBeInTheDocument()
    expect(screen.getByText('Kyler Murray')).toBeInTheDocument()
    expect(screen.getByText('82% similar')).toBeInTheDocument()
  })

  it('switches to performance tab', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const performanceTab = screen.getByRole('button', { name: /performance/i })
    await user.click(performanceTab)
    
    expect(screen.getByTestId('player-performance-chart')).toBeInTheDocument()
    expect(screen.getByText('Performance chart for Josh Allen (QB - BUF)')).toBeInTheDocument()
  })

  it('switches to matchups tab', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const matchupsTab = screen.getByRole('button', { name: /matchups/i })
    await user.click(matchupsTab)
    
    expect(screen.getByText('Matchup Performance')).toBeInTheDocument()
    expect(screen.getByTestId('chart')).toBeInTheDocument()
  })

  it('switches to news tab', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const newsTab = screen.getByRole('button', { name: /news/i })
    await user.click(newsTab)
    
    expect(screen.getByText('Recent News')).toBeInTheDocument()
    expect(screen.getByText('Allen throws for 4 TDs in win over Dolphins')).toBeInTheDocument()
    expect(screen.getByText('ESPN')).toBeInTheDocument()
    expect(screen.getByText('2 hours ago')).toBeInTheDocument()
  })

  it('opens compare modal', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const compareButton = screen.getByRole('button', { name: /compare/i })
    await user.click(compareButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
      expect(screen.getByTestId('modal-title')).toHaveTextContent('Compare Players')
      expect(screen.getByText('Player comparison feature coming soon...')).toBeInTheDocument()
    })
  })

  it('closes compare modal', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const compareButton = screen.getByRole('button', { name: /compare/i })
    await user.click(compareButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
    })
    
    const closeButton = screen.getByTestId('close-modal')
    await user.click(closeButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
    })
  })

  it('displays injury status with correct styling', () => {
    render(<PlayerDetailPage />)
    
    const healthyBadge = screen.getByText('Healthy')
    expect(healthyBadge).toHaveClass('bg-green-100', 'text-green-800')
  })

  it('displays news articles with impact badges', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const newsTab = screen.getByRole('button', { name: /news/i })
    await user.click(newsTab)
    
    expect(screen.getByText('positive')).toBeInTheDocument()
    expect(screen.getByText('neutral')).toBeInTheDocument()
  })

  it('shows tab active state correctly', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const overviewTab = screen.getByRole('button', { name: /overview/i })
    const performanceTab = screen.getByRole('button', { name: /performance/i })
    
    // Overview should be active by default
    expect(overviewTab).toHaveClass('border-blue-500', 'text-blue-600')
    
    // Switch to performance tab
    await user.click(performanceTab)
    expect(performanceTab).toHaveClass('border-blue-500', 'text-blue-600')
  })

  it('formats salary correctly', () => {
    render(<PlayerDetailPage />)
    
    expect(screen.getByText('$43.0M')).toBeInTheDocument()
  })

  it('displays all news article information', async () => {
    const user = userEvent.setup()
    render(<PlayerDetailPage />)
    
    const newsTab = screen.getByRole('button', { name: /news/i })
    await user.click(newsTab)
    
    expect(screen.getByText('Allen throws for 4 TDs in win over Dolphins')).toBeInTheDocument()
    expect(screen.getByText('Bills offense clicking on all cylinders')).toBeInTheDocument()
    expect(screen.getByText('Weather concerns for Sunday\'s game')).toBeInTheDocument()
  })
})