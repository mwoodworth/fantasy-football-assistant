import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { ESPNLeaguesPage } from '../ESPNLeaguesPage'
import { useQuery, useMutation } from '@tanstack/react-query'

// Mock the ESPN service
vi.mock('../../services/espn', () => ({
  espnService: {
    getMyLeagues: vi.fn(),
    disconnectLeague: vi.fn(),
    formatSyncStatus: vi.fn(() => ({ text: 'Active', color: 'success' })),
    formatScoreType: vi.fn(() => 'Standard Scoring'),
  },
}))


// Mock ESPN components
vi.mock('../../components/espn/ConnectLeagueForm', () => ({
  ConnectLeagueForm: ({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) => (
    <div data-testid="connect-league-form">
      <button onClick={onSuccess}>Connect</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}))

vi.mock('../../components/espn/DraftSessionModal', () => ({
  DraftSessionModal: ({ isOpen, onClose, league }: { isOpen: boolean; onClose: () => void; league: any }) => (
    isOpen ? (
      <div data-testid="draft-session-modal">
        Draft modal for {league.league_name}
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
  ),
}))

vi.mock('../../components/espn/LeagueSettingsModal', () => ({
  LeagueSettingsModal: ({ isOpen, onClose, league }: { isOpen: boolean; onClose: () => void; league: any }) => (
    isOpen ? (
      <div data-testid="league-settings-modal">
        Settings modal for {league.league_name}
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
  ),
}))

// Mock Modal component
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
}))

// Mock confirm dialog
Object.defineProperty(window, 'confirm', {
  value: vi.fn(),
  writable: true,
})

const mockLeagues = [
  {
    id: 1,
    league_name: 'Test League 1',
    season: 2024,
    team_count: 12,
    sync_status: 'active',
    is_archived: false,
    draft_date: '2024-09-01',
    user_team_name: 'My Team',
    scoring_type: 'standard',
    draft_completed: false,
    is_active: true,
  },
  {
    id: 2,
    league_name: 'Test League 2',
    season: 2023,
    team_count: 10,
    sync_status: 'inactive',
    is_archived: true,
    draft_date: '2023-08-15',
    user_team_name: 'Another Team',
    scoring_type: 'ppr',
    draft_completed: true,
    is_active: false,
  },
]

describe('ESPNLeaguesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useQuery
    vi.mocked(useQuery).mockReturnValue({
      data: mockLeagues,
      isLoading: false,
      error: null,
    })
  })

  it('renders page header', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByRole('heading', { name: /espn leagues/i })).toBeInTheDocument()
    expect(screen.getByText(/connect and manage your espn fantasy football leagues/i)).toBeInTheDocument()
  })

  it('renders connect league button', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByRole('button', { name: /connect league/i })).toBeInTheDocument()
  })

  it('renders include archived checkbox', () => {
    render(<ESPNLeaguesPage />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeInTheDocument()
    expect(screen.getByText('Include archived leagues')).toBeInTheDocument()
  })

  it('displays league cards', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('Test League 1')).toBeInTheDocument()
    expect(screen.getByText('2024 Season • 12 Teams')).toBeInTheDocument()
    expect(screen.getByText('Test League 2')).toBeInTheDocument()
    expect(screen.getByText('2023 Season • 10 Teams')).toBeInTheDocument()
  })

  it('displays league information', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('Your Team: My Team')).toBeInTheDocument()
    expect(screen.getByText('Your Team: Another Team')).toBeInTheDocument()
    expect(screen.getAllByText('Standard Scoring')).toHaveLength(2)
  })

  it('shows draft button for active leagues with incomplete draft', () => {
    render(<ESPNLeaguesPage />)
    
    const draftButtons = screen.getAllByRole('button', { name: /draft/i })
    expect(draftButtons).toHaveLength(1) // Only for the active league
  })

  it('shows settings buttons for all leagues', () => {
    render(<ESPNLeaguesPage />)
    
    const settingsButtons = screen.getAllByRole('button', { name: /settings/i })
    expect(settingsButtons).toHaveLength(2)
  })

  it('shows disconnect button only for non-archived leagues', () => {
    render(<ESPNLeaguesPage />)
    
    const disconnectButtons = screen.getAllByRole('button', { name: /disconnect/i })
    expect(disconnectButtons).toHaveLength(1) // Only for the non-archived league
  })

  it('displays archived badge for archived leagues', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('Archived')).toBeInTheDocument()
  })

  it('opens connect league modal', async () => {
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const connectButton = screen.getByRole('button', { name: /connect league/i })
    await user.click(connectButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
      expect(screen.getByTestId('modal-title')).toHaveTextContent('Connect ESPN League')
      expect(screen.getByTestId('connect-league-form')).toBeInTheDocument()
    })
  })

  it('opens draft session modal', async () => {
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const draftButton = screen.getByRole('button', { name: /draft/i })
    await user.click(draftButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('draft-session-modal')).toBeInTheDocument()
      expect(screen.getByText('Draft modal for Test League 1')).toBeInTheDocument()
    })
  })

  it('opens league settings modal', async () => {
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const settingsButtons = screen.getAllByRole('button', { name: /settings/i })
    await user.click(settingsButtons[0])
    
    await waitFor(() => {
      expect(screen.getByTestId('league-settings-modal')).toBeInTheDocument()
      expect(screen.getByText('Settings modal for Test League 1')).toBeInTheDocument()
    })
  })

  it('toggles include archived checkbox', async () => {
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).not.toBeChecked()
    
    await user.click(checkbox)
    expect(checkbox).toBeChecked()
    
    await user.click(checkbox)
    expect(checkbox).not.toBeChecked()
  })

  it('confirms before disconnecting league', async () => {
    const mockConfirm = vi.mocked(window.confirm)
    mockConfirm.mockReturnValue(true)
    const mockMutate = vi.fn()
    
    vi.mocked(useMutation).mockReturnValue({
      mutate: mockMutate,
      mutateAsync: vi.fn(),
      isPending: false,
      isLoading: false,
      error: null,
    })
    
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const disconnectButton = screen.getByRole('button', { name: /disconnect/i })
    await user.click(disconnectButton)
    
    expect(mockConfirm).toHaveBeenCalledWith(
      'Are you sure you want to disconnect this league? This will archive the league but preserve historical data.'
    )
    expect(mockMutate).toHaveBeenCalledWith(1)
  })

  it('does not disconnect if user cancels', async () => {
    const mockConfirm = vi.mocked(window.confirm)
    mockConfirm.mockReturnValue(false)
    
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    const disconnectButton = screen.getByRole('button', { name: /disconnect/i })
    await user.click(disconnectButton)
    
    expect(mockConfirm).toHaveBeenCalled()
  })

  it('displays loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [],
      isLoading: true,
      error: null,
    })
    
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('Loading your ESPN leagues...')).toBeInTheDocument()
  })

  it('displays error state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [],
      isLoading: false,
      error: new Error('Failed to fetch'),
    })
    
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('Error loading leagues. Please try again.')).toBeInTheDocument()
  })

  it('displays empty state when no leagues', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    })
    
    render(<ESPNLeaguesPage />)
    
    expect(screen.getByText('No ESPN leagues connected')).toBeInTheDocument()
    expect(screen.getByText('Connect your first ESPN league to get started with draft assistance and insights.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /connect your first league/i })).toBeInTheDocument()
  })

  it('formats draft date correctly', () => {
    render(<ESPNLeaguesPage />)
    
    expect(screen.getAllByText(/Draft/)).toHaveLength(2)
    expect(screen.getByText(/2024/)).toBeInTheDocument()
    expect(screen.getByText(/2023/)).toBeInTheDocument()
  })

  it('closes modals when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<ESPNLeaguesPage />)
    
    // Open connect modal
    const connectButton = screen.getByRole('button', { name: /connect league/i })
    await user.click(connectButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('modal')).toBeInTheDocument()
    })
    
    const closeButton = screen.getByTestId('close-modal')
    await user.click(closeButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
    })
  })

  it('calls ESPN service with correct parameters', () => {
    render(<ESPNLeaguesPage />)
    
    const lastCall = vi.mocked(useQuery).mock.calls[vi.mocked(useQuery).mock.calls.length - 1]
    const queryConfig = lastCall[0]
    
    expect(queryConfig.queryKey).toEqual(['espn-leagues', false])
    expect(queryConfig.queryFn).toBeDefined()
  })
})