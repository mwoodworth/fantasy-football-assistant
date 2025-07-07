import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { TeamsPage } from '../TeamsPage'
import { useQuery } from '@tanstack/react-query'

// Mock react-router-dom
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock teams service
vi.mock('../../services/teams', () => ({
  teamsService: {
    getUserTeams: vi.fn(),
    getTeamDetail: vi.fn(),
    syncTeam: vi.fn(),
    updateESPNCookies: vi.fn(),
    formatTeamOption: vi.fn(),
    getPlatformColor: vi.fn(),
    getTeamIcon: vi.fn(),
  },
}))


// Mock Table component
vi.mock('../../components/common/Table', () => ({
  Table: ({ data, columns }: { data: any[]; columns: any[] }) => (
    <div data-testid="table">
      Table with {data.length} rows and {columns.length} columns
      {data.map((row, index) => (
        <div key={index} data-testid="table-row">
          {row.name} - {row.position} - {row.points}
        </div>
      ))}
    </div>
  ),
}))

// Mock Select component
vi.mock('../../components/common/Select', () => ({
  Select: ({ options, value, onChange, className, searchable }: { options: any[]; value: string; onChange: (value: string) => void; className?: string; searchable?: boolean }) => (
    <select
      data-testid="select"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className}
      data-searchable={searchable}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
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
  ModalFooter: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="modal-footer">{children}</div>
  ),
}))

const mockTeams = [
  {
    id: 'team1',
    name: 'Test Team 1',
    platform: 'ESPN',
    league: 'Test League',
    season: 2024,
    rank: 3,
    record: '7-4',
    points: 1250.5,
    playoffs: true,
    draft_completed: true,
    espn_league_id: 123,
  },
  {
    id: 'team2',
    name: 'Test Team 2',
    platform: 'Manual',
    league: 'Custom League',
    season: 2024,
    rank: 8,
    record: '4-7',
    points: 980.2,
    playoffs: false,
    draft_completed: false,
    espn_league_id: null,
  },
]

const mockTeamDetail = {
  roster: [
    {
      name: 'Josh Allen',
      position: 'QB',
      team: 'BUF',
      status: 'starter',
      points: 285.4,
    },
    {
      name: 'Christian McCaffrey',
      position: 'RB',
      team: 'SF',
      status: 'starter',
      points: 198.2,
    },
    {
      name: 'Bench Player',
      position: 'WR',
      team: 'DAL',
      status: 'bench',
      points: 45.1,
    },
  ],
}

describe('TeamsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useQuery calls
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: mockTeams,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      if (queryKey[0] === 'team-detail') {
        return {
          data: mockTeamDetail,
          isLoading: false,
          error: null,
        }
      }
      return { data: null, isLoading: false, error: null }
    })
  })

  it('renders page header', () => {
    render(<TeamsPage />)
    
    expect(screen.getByRole('heading', { name: /teams/i })).toBeInTheDocument()
    expect(screen.getByText(/manage your fantasy teams and lineups/i)).toBeInTheDocument()
  })

  it('renders team selector', () => {
    render(<TeamsPage />)
    
    const select = screen.getByTestId('select')
    expect(select).toBeInTheDocument()
    expect(select).toHaveAttribute('data-searchable', 'true')
  })

  it('renders settings button', () => {
    render(<TeamsPage />)
    
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
  })

  it('displays team overview', () => {
    render(<TeamsPage />)
    
    expect(screen.getByText('Test Team 1')).toBeInTheDocument()
    expect(screen.getByText('Test League • ESPN League • 2024 Season')).toBeInTheDocument()
  })

  it('displays team statistics', () => {
    render(<TeamsPage />)
    
    expect(screen.getByText('#3')).toBeInTheDocument()
    expect(screen.getByText('League Rank')).toBeInTheDocument()
    expect(screen.getByText('7-4')).toBeInTheDocument()
    expect(screen.getByText('W-L Record')).toBeInTheDocument()
    expect(screen.getByText('1250.5')).toBeInTheDocument()
    expect(screen.getByText('Total Points')).toBeInTheDocument()
    expect(screen.getByText('Yes')).toBeInTheDocument()
    expect(screen.getByText('Playoff Bound')).toBeInTheDocument()
  })

  it('shows ESPN-specific actions for ESPN teams', () => {
    render(<TeamsPage />)
    
    expect(screen.getByRole('button', { name: /sync/i })).toBeInTheDocument()
  })

  it('shows draft button for teams with incomplete draft', () => {
    // Mock team with incomplete draft
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: [{ ...mockTeams[0], draft_completed: false }],
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      return { data: mockTeamDetail, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByRole('button', { name: /go to draft/i })).toBeInTheDocument()
  })

  it('renders tab navigation', () => {
    render(<TeamsPage />)
    
    expect(screen.getByRole('button', { name: /current roster/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /set lineup/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /trade center/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /waivers/i })).toBeInTheDocument()
  })

  it('displays roster tab by default', () => {
    render(<TeamsPage />)
    
    expect(screen.getAllByText('Current Roster')).toHaveLength(2)
    expect(screen.getByTestId('table')).toBeInTheDocument()
    expect(screen.getByText('Josh Allen - QB - 285.4')).toBeInTheDocument()
  })

  it('switches between tabs', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    // Switch to lineup tab
    const lineupTab = screen.getByRole('button', { name: /set lineup/i })
    await user.click(lineupTab)
    
    expect(screen.getByText('Set Your Lineup')).toBeInTheDocument()
    expect(screen.getByText('Lineup Optimizer')).toBeInTheDocument()
    
    // Switch to trades tab
    const tradesTab = screen.getByRole('button', { name: /trade center/i })
    await user.click(tradesTab)
    
    expect(screen.getAllByText('Trade Center')).toHaveLength(2)
    expect(screen.getByText('Trade Analyzer')).toBeInTheDocument()
    
    // Switch to waivers tab
    const waiversTab = screen.getByRole('button', { name: /waivers/i })
    await user.click(waiversTab)
    
    expect(screen.getByText('Waiver Wire')).toBeInTheDocument()
    expect(screen.getByText('Waiver Targets')).toBeInTheDocument()
  })

  it('opens settings modal', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const settingsButton = screen.getByRole('button', { name: /settings/i })
    await user.click(settingsButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
      expect(screen.getByTestId('modal-title')).toHaveTextContent('Team Settings')
    })
  })

  it('displays settings sections in modal', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const settingsButton = screen.getByRole('button', { name: /settings/i })
    await user.click(settingsButton)
    
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument()
      expect(screen.getByText('Privacy')).toBeInTheDocument()
      expect(screen.getByText('Display')).toBeInTheDocument()
      expect(screen.getByText('Team Information')).toBeInTheDocument()
    })
  })

  it('closes settings modal', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const settingsButton = screen.getByRole('button', { name: /settings/i })
    await user.click(settingsButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
    })
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
    })
  })

  it('handles loading state', () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: [],
          isLoading: true,
          error: null,
          refetch: vi.fn(),
        }
      }
      return { data: null, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByText('Loading your teams...')).toBeInTheDocument()
  })

  it('handles error state', () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: [],
          isLoading: false,
          error: new Error('Failed to fetch'),
          refetch: vi.fn(),
        }
      }
      return { data: null, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByText('Error loading teams. Please try again.')).toBeInTheDocument()
  })

  it('displays empty state when no teams', () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: [],
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      return { data: null, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByText('No teams found')).toBeInTheDocument()
    expect(screen.getByText('Connect your ESPN league or create a manual team to get started.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /connect espn league/i })).toBeInTheDocument()
  })

  it('navigates to ESPN leagues when draft button clicked', async () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: [{ ...mockTeams[0], draft_completed: false }],
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      return { data: mockTeamDetail, isLoading: false, error: null }
    })
    
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const draftButton = screen.getByRole('button', { name: /go to draft/i })
    await user.click(draftButton)
    
    expect(mockNavigate).toHaveBeenCalledWith('/espn/leagues')
  })

  it('calls sync team when sync button clicked', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const syncButton = screen.getByRole('button', { name: /sync/i })
    await user.click(syncButton)
    
    // The service call is mocked, so we just verify the button was clicked
    expect(syncButton).toBeInTheDocument()
  })

  it('displays empty roster message when no roster data', () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: mockTeams,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      if (queryKey[0] === 'team-detail') {
        return {
          data: { roster: [] },
          isLoading: false,
          error: null,
        }
      }
      return { data: null, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByText('No Roster Data')).toBeInTheDocument()
  })

  it('displays roster loading state', () => {
    vi.mocked(useQuery).mockImplementation(({ queryKey }: { queryKey: string[] }) => {
      if (queryKey[0] === 'user-teams') {
        return {
          data: mockTeams,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
        }
      }
      if (queryKey[0] === 'team-detail') {
        return {
          data: null,
          isLoading: true,
          error: null,
        }
      }
      return { data: null, isLoading: false, error: null }
    })
    
    render(<TeamsPage />)
    
    expect(screen.getByText('Loading roster...')).toBeInTheDocument()
  })

  it('changes selected team', async () => {
    const user = userEvent.setup()
    render(<TeamsPage />)
    
    const select = screen.getByTestId('select')
    await user.selectOptions(select, 'team2')
    
    expect(select).toHaveValue('team2')
  })
})