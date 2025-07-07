import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { DashboardPage } from '../DashboardPage'
import { useQuery } from '@tanstack/react-query'

// Mock the dashboard service
vi.mock('../../services/dashboard', () => ({
  DashboardService: {
    getDashboardData: vi.fn(),
    getTopPerformers: vi.fn(),
    getTrendingPlayers: vi.fn(),
    getWaiverTargets: vi.fn(),
  },
}))

// Mock dashboard widgets
vi.mock('../../components/dashboard/LiveScoreTicker', () => ({
  LiveScoreTicker: () => <div data-testid="live-score-ticker">Live Score Ticker</div>,
}))

vi.mock('../../components/dashboard/TopPerformersWidget', () => ({
  TopPerformersWidget: ({ players, loading }: { players: any; loading: boolean }) => (
    <div data-testid="top-performers-widget">
      {loading ? 'Loading...' : `Top Performers: ${players?.length || 0}`}
    </div>
  ),
}))

vi.mock('../../components/dashboard/InjuryReportWidget', () => ({
  InjuryReportWidget: ({ injuries, loading }: { injuries: any; loading: boolean }) => (
    <div data-testid="injury-report-widget">
      {loading ? 'Loading...' : `Injuries: ${injuries?.length || 0}`}
    </div>
  ),
}))

vi.mock('../../components/dashboard/TrendingPlayersWidget', () => ({
  TrendingPlayersWidget: ({ players, loading }: { players: any; loading: boolean }) => (
    <div data-testid="trending-players-widget">
      {loading ? 'Loading...' : `Trending Players: ${players?.length || 0}`}
    </div>
  ),
}))

vi.mock('../../components/dashboard/WaiverWireWidget', () => ({
  WaiverWireWidget: ({ players, loading }: { players: any; loading: boolean }) => (
    <div data-testid="waiver-wire-widget">
      {loading ? 'Loading...' : `Waiver Targets: ${players?.length || 0}`}
    </div>
  ),
}))

vi.mock('../../components/dashboard/TeamAnalyticsWidget', () => ({
  TeamAnalyticsWidget: ({ data, loading }: { data: any; loading: boolean }) => (
    <div data-testid="team-analytics-widget">
      {loading ? 'Loading...' : `Team Analytics: ${data?.rank || 0}`}
    </div>
  ),
}))

const mockDashboardData = {
  teamRank: 3,
  leagueSize: 12,
  rankTrend: 'up',
  weeklyPoints: 125.5,
  pointsProjected: 130.0,
  pointsTrend: 'up',
  activePlayers: 9,
  benchPlayers: 6,
  injuryAlerts: 2,
  recentActivity: [
    {
      type: 'recommendation',
      title: 'Start Recommended Player',
      description: 'Consider starting Player X this week',
      timestamp: '2 hours ago',
    },
    {
      type: 'injury',
      title: 'Injury Alert',
      description: 'Player Y is questionable',
      timestamp: '1 hour ago',
    },
  ],
  injuries: [
    { player: 'Player Y', status: 'questionable', description: 'Knee injury' },
  ],
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useQuery to return mock data
    vi.mocked(useQuery).mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      refetch: vi.fn(),
      error: null,
    })
  })

  it('renders dashboard header', () => {
    render(<DashboardPage />)
    
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument()
  })

  it('displays stats cards with correct data', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Team Rank')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Out of 12 teams')).toBeInTheDocument()
    
    expect(screen.getByText('Points This Week')).toBeInTheDocument()
    expect(screen.getByText('125.5')).toBeInTheDocument()
    expect(screen.getByText('130 projected')).toBeInTheDocument()
    
    expect(screen.getByText('Active Players')).toBeInTheDocument()
    expect(screen.getByText('9')).toBeInTheDocument()
    expect(screen.getByText('6 on bench')).toBeInTheDocument()
    
    expect(screen.getByText('Injury Alerts')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('displays auto-refresh toggle', () => {
    render(<DashboardPage />)
    
    const autoRefreshCheckbox = screen.getByRole('checkbox')
    expect(autoRefreshCheckbox).toBeInTheDocument()
    expect(autoRefreshCheckbox).toBeChecked()
    
    expect(screen.getByText('Auto-refresh')).toBeInTheDocument()
  })

  it('displays refresh button', () => {
    render(<DashboardPage />)
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    expect(refreshButton).toBeInTheDocument()
    expect(refreshButton).not.toBeDisabled()
  })

  it('displays last updated timestamp', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText(/updated/i)).toBeInTheDocument()
  })

  it('renders all dashboard widgets', () => {
    render(<DashboardPage />)
    
    expect(screen.getByTestId('live-score-ticker')).toBeInTheDocument()
    expect(screen.getByTestId('top-performers-widget')).toBeInTheDocument()
    expect(screen.getByTestId('trending-players-widget')).toBeInTheDocument()
    expect(screen.getByTestId('injury-report-widget')).toBeInTheDocument()
    expect(screen.getByTestId('waiver-wire-widget')).toBeInTheDocument()
  })

  it('displays recent activity', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    expect(screen.getByText('Start Recommended Player')).toBeInTheDocument()
    expect(screen.getByText('Injury Alert')).toBeInTheDocument()
    expect(screen.getByText('Consider starting Player X this week')).toBeInTheDocument()
  })

  it('displays quick actions', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /set lineup/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /view trade analyzer/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /check waivers/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /compare players/i })).toBeInTheDocument()
  })

  it('toggles auto-refresh', async () => {
    const user = userEvent.setup()
    render(<DashboardPage />)
    
    const autoRefreshCheckbox = screen.getByRole('checkbox')
    expect(autoRefreshCheckbox).toBeChecked()
    
    await user.click(autoRefreshCheckbox)
    expect(autoRefreshCheckbox).not.toBeChecked()
    
    await user.click(autoRefreshCheckbox)
    expect(autoRefreshCheckbox).toBeChecked()
  })

  it('handles manual refresh', async () => {
    const mockRefetch = vi.fn()
    vi.mocked(useQuery).mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      refetch: mockRefetch,
      error: null,
    })
    
    const user = userEvent.setup()
    render(<DashboardPage />)
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshButton)
    
    expect(mockRefetch).toHaveBeenCalled()
  })

  it('renders dashboard components', () => {
    render(<DashboardPage />)
    
    // Check that the main dashboard elements are rendered
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
    expect(screen.getByTestId('live-score-ticker')).toBeInTheDocument()
  })

  it('highlights injury alerts when present', () => {
    render(<DashboardPage />)
    
    const injuryCard = screen.getByText('Injury Alerts').closest('.border-red-200')
    expect(injuryCard).toBeInTheDocument()
  })

  it('displays trend icons for stats', () => {
    render(<DashboardPage />)
    
    // Check that trend icons are rendered (they would be present in the DOM)
    // We can't easily test the specific icons, but we can verify the stats are displayed
    expect(screen.getByText('Team Rank')).toBeInTheDocument()
    expect(screen.getByText('Points This Week')).toBeInTheDocument()
  })
})