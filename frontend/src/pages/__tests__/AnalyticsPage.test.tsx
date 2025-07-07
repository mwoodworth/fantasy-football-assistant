import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { AnalyticsPage } from '../AnalyticsPage'

// Mock analytics components
vi.mock('../../components/analytics/Chart', () => ({
  Chart: ({ data, type, height, width, title }: { data: any; type: string; height: number; width: number; title: string }) => (
    <div data-testid="chart">
      {type} chart - {height}x{width} - {data.length} data points - {title}
    </div>
  ),
}))

vi.mock('../../components/analytics/PlayerPerformanceChart', () => ({
  PlayerPerformanceChart: ({ playerName, position, team, performances }: { playerName: string; position: string; team: string; performances: any[] }) => (
    <div data-testid="player-performance-chart">
      Performance chart for {playerName} ({position} - {team}) - {performances.length} performances
    </div>
  ),
}))

vi.mock('../../components/analytics/TeamAnalyticsWidget', () => ({
  TeamAnalyticsWidget: ({ analytics, teamName }: { analytics: any; teamName: string }) => (
    <div data-testid="team-analytics-widget">
      Team analytics for {teamName} - {analytics.weeklyScores.length} weeks
    </div>
  ),
}))

// Mock Select component
vi.mock('../../components/common/Select', () => ({
  Select: ({ options, value, onChange, className }: { options: any[]; value: string; onChange: (value: string) => void; className?: string }) => (
    <select
      data-testid="select"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
}))

describe('AnalyticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders page header', () => {
    render(<AnalyticsPage />)
    
    expect(screen.getByRole('heading', { name: /analytics/i })).toBeInTheDocument()
    expect(screen.getByText(/deep dive into your team's performance/i)).toBeInTheDocument()
  })

  it('renders view and time range selects', () => {
    render(<AnalyticsPage />)
    
    const selects = screen.getAllByTestId('select')
    expect(selects).toHaveLength(2)
    
    // Check that the selects have the correct default values
    expect(selects[0]).toHaveValue('overview')
    expect(selects[1]).toHaveValue('season')
  })

  it('displays overview tab by default', () => {
    render(<AnalyticsPage />)
    
    expect(screen.getByText('1,024.2')).toBeInTheDocument()
    expect(screen.getByText('Total Points')).toBeInTheDocument()
    expect(screen.getByText('3rd')).toBeInTheDocument()
    expect(screen.getByText('League Rank')).toBeInTheDocument()
    expect(screen.getByText('75.4%')).toBeInTheDocument()
    expect(screen.getByText('Playoff Chance')).toBeInTheDocument()
    expect(screen.getByText('5-3')).toBeInTheDocument()
    expect(screen.getByText('W-L Record')).toBeInTheDocument()
  })

  it('renders team analytics widget in overview', () => {
    render(<AnalyticsPage />)
    
    expect(screen.getByTestId('team-analytics-widget')).toBeInTheDocument()
    expect(screen.getByText('Team analytics for Your Team - 8 weeks')).toBeInTheDocument()
  })

  it('switches to player analysis view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'players')
    
    await waitFor(() => {
      expect(screen.getByTestId('player-performance-chart')).toBeInTheDocument()
      expect(screen.getByText('Performance chart for Josh Allen (QB - BUF) - 8 performances')).toBeInTheDocument()
    })
  })

  it('renders player selector in player analysis view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'players')
    
    await waitFor(() => {
      const selects = screen.getAllByTestId('select')
      expect(selects).toHaveLength(3) // view, time range, and player select
    })
  })

  it('switches to league comparison view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'league')
    
    await waitFor(() => {
      expect(screen.getByText('League Standings')).toBeInTheDocument()
      expect(screen.getByTestId('chart')).toBeInTheDocument()
      expect(screen.getByText('Position vs League Average')).toBeInTheDocument()
      expect(screen.getByText('Strengths & Weaknesses')).toBeInTheDocument()
    })
  })

  it('displays position comparison in league view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'league')
    
    await waitFor(() => {
      expect(screen.getByText('#3 in league')).toBeInTheDocument()
      expect(screen.getByText('#2 in league')).toBeInTheDocument()
      expect(screen.getByText('#6 in league')).toBeInTheDocument()
      expect(screen.getByText('#8 in league')).toBeInTheDocument()
    })
  })

  it('displays strengths and weaknesses in league view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'league')
    
    await waitFor(() => {
      expect(screen.getByText('🔥 Strengths')).toBeInTheDocument()
      expect(screen.getByText('⚠️ Areas to Improve')).toBeInTheDocument()
      expect(screen.getByText('Elite QB production (19.5 ppg, #3 in league)')).toBeInTheDocument()
      expect(screen.getByText('WR production below league average')).toBeInTheDocument()
    })
  })

  it('switches to projections view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'projections')
    
    await waitFor(() => {
      expect(screen.getByText('Season Projection')).toBeInTheDocument()
      expect(screen.getByText('11-6')).toBeInTheDocument()
      expect(screen.getByText('Projected Final Record')).toBeInTheDocument()
      expect(screen.getByText('Remaining Schedule')).toBeInTheDocument()
    })
  })

  it('displays projection details in projections view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'projections')
    
    await waitFor(() => {
      expect(screen.getByText('75.4%')).toBeInTheDocument()
      expect(screen.getByText('12.8%')).toBeInTheDocument()
      expect(screen.getByText('Championship')).toBeInTheDocument()
      expect(screen.getByText('Most Likely Outcomes:')).toBeInTheDocument()
    })
  })

  it('displays remaining schedule in projections view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'projections')
    
    await waitFor(() => {
      expect(screen.getByText('Week 9')).toBeInTheDocument()
      expect(screen.getByText('Team Kappa')).toBeInTheDocument()
      expect(screen.getByText('78% win')).toBeInTheDocument()
      expect(screen.getByText('Easy')).toBeInTheDocument()
    })
  })

  it('changes time range', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const timeRangeSelect = screen.getAllByTestId('select')[1]
    await user.selectOptions(timeRangeSelect, 'last-4')
    
    expect(timeRangeSelect).toHaveValue('last-4')
  })

  it('shows time range badge in player analysis view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'players')
    
    await waitFor(() => {
      expect(screen.getByText('Full Season')).toBeInTheDocument()
    })
    
    const timeRangeSelect = screen.getAllByTestId('select')[1]
    await user.selectOptions(timeRangeSelect, 'last-4')
    
    await waitFor(() => {
      expect(screen.getByText('Last 4 Weeks')).toBeInTheDocument()
    })
  })

  it('displays quick stats with icons', () => {
    render(<AnalyticsPage />)
    
    // Check that all the quick stats are displayed
    const statCards = screen.getAllByRole('generic').filter(el => 
      el.textContent?.includes('Total Points') ||
      el.textContent?.includes('League Rank') ||
      el.textContent?.includes('Playoff Chance') ||
      el.textContent?.includes('W-L Record')
    )
    
    expect(statCards.length).toBeGreaterThan(0)
  })

  it('changes player selection in player analysis view', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'players')
    
    await waitFor(() => {
      const selects = screen.getAllByTestId('select')
      const playerSelect = selects[2] // Third select should be player select
      
      expect(playerSelect).toHaveValue('josh-allen')
    })
  })

  it('displays correct position performance data', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'league')
    
    await waitFor(() => {
      expect(screen.getByText('19.5 vs 17.8')).toBeInTheDocument()
      expect(screen.getByText('24.2 vs 22.1')).toBeInTheDocument()
      expect(screen.getByText('18.7 vs 19.3')).toBeInTheDocument()
      expect(screen.getByText('9.8 vs 11.2')).toBeInTheDocument()
    })
  })

  it('displays playoff and championship percentages', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'projections')
    
    await waitFor(() => {
      expect(screen.getByText('3rd place finish (32.1% chance)')).toBeInTheDocument()
      expect(screen.getByText('2nd place finish (24.7% chance)')).toBeInTheDocument()
      expect(screen.getByText('4th place finish (18.6% chance)')).toBeInTheDocument()
    })
  })

  it('displays schedule difficulty badges', async () => {
    const user = userEvent.setup()
    render(<AnalyticsPage />)
    
    const viewSelect = screen.getAllByTestId('select')[0]
    await user.selectOptions(viewSelect, 'projections')
    
    await waitFor(() => {
      expect(screen.getByText('Easy')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
      expect(screen.getByText('Hard')).toBeInTheDocument()
    })
  })
})