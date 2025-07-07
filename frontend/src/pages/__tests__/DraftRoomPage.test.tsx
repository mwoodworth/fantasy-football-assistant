import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { DraftRoomPage } from '../DraftRoomPage'
import { useQuery } from '@tanstack/react-query'

// Mock react-router-dom
const mockNavigate = vi.fn()
const mockParams = { sessionId: '123' }
const mockLocation = {
  state: {
    session: {
      id: 123,
      current_pick: 5,
      current_round: 1,
      next_user_pick: 8,
      picks_until_user_turn: 3,
      user_pick_position: 8,
      is_live_synced: true,
      user_roster: [
        { player_name: 'Josh Allen', position: 'QB' },
        { player_name: 'Christian McCaffrey', position: 'RB' },
      ],
    },
    league: {
      id: 1,
      league_name: 'Test League',
      season: 2024,
    },
  },
}

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => mockParams,
    useLocation: () => mockLocation,
    Navigate: ({ to, replace }: { to: string; replace?: boolean }) => (
      <div data-testid="navigate" data-to={to} data-replace={replace}>
        Navigate to {to}
      </div>
    ),
  }
})

// Mock ESPN service
vi.mock('../../services/espn', () => ({
  espnService: {
    getDraftRecommendations: vi.fn(),
    recordDraftPick: vi.fn(),
  },
}))


// Mock ESPN components
vi.mock('../../components/espn/DraftRecommendations', () => ({
  DraftRecommendations: ({ recommendations, isUserTurn, onSelectPlayer }: { recommendations: any; isUserTurn: boolean; onSelectPlayer: () => void }) => (
    <div data-testid="draft-recommendations">
      Recommendations - {recommendations.length} players - User turn: {isUserTurn.toString()}
      <button onClick={onSelectPlayer}>Select Player</button>
    </div>
  ),
}))

vi.mock('../../components/espn/DraftBoard', () => ({
  DraftBoard: ({ session }: { session: any }) => (
    <div data-testid="draft-board">
      Draft Board - Current pick: {session.current_pick}
    </div>
  ),
}))

vi.mock('../../components/espn/ManualPickEntry', () => ({
  ManualPickEntry: ({ session, onSubmit, onCancel, isSubmitting }: { session: any; onSubmit: (pick: any) => void; onCancel: () => void; isSubmitting: boolean }) => (
    <div data-testid="manual-pick-entry">
      Manual Pick Entry - Session {session.id} - Submitting: {isSubmitting.toString()}
      <button onClick={() => onSubmit({ player: 'Test Player' })}>Submit Pick</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}))

const mockRecommendations = [
  { player_name: 'Recommended Player 1', position: 'RB', ranking: 1 },
  { player_name: 'Recommended Player 2', position: 'WR', ranking: 2 },
]

describe('DraftRoomPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useQuery
    vi.mocked(useQuery).mockReturnValue({
      data: mockRecommendations,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  it('redirects when no session ID', () => {
    mockParams.sessionId = ''
    
    render(<DraftRoomPage />)
    
    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/espn/leagues')
  })

  it('shows loading when no session data', () => {
    mockLocation.state = null
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Loading draft session...')).toBeInTheDocument()
  })

  it('renders draft room header', () => {
    mockParams.sessionId = '123'
    mockLocation.state = {
      session: {
        id: 123,
        current_pick: 5,
        current_round: 1,
        next_user_pick: 8,
        picks_until_user_turn: 3,
        user_pick_position: 8,
        is_live_synced: true,
        user_roster: [],
      },
      league: {
        id: 1,
        league_name: 'Test League',
        season: 2024,
      },
    }
    
    render(<DraftRoomPage />)
    
    expect(screen.getByRole('heading', { name: /test league/i })).toBeInTheDocument()
    expect(screen.getByText('Draft Room • 2024 Season')).toBeInTheDocument()
  })

  it('displays live sync badge when live synced', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Live Sync')).toBeInTheDocument()
  })

  it('displays manual mode badge when not live synced', () => {
    mockLocation.state.session.is_live_synced = false
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Manual Mode')).toBeInTheDocument()
  })

  it('displays draft status information', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Current Pick')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('Round')).toBeInTheDocument()
    expect(screen.getByText('1 of 16')).toBeInTheDocument()
    expect(screen.getByText('Your Position')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('3 picks away')).toBeInTheDocument()
  })

  it('shows turn indicator when it is user turn', () => {
    mockLocation.state.session.current_pick = 8
    mockLocation.state.session.next_user_pick = 8
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText("It's your turn to pick!")).toBeInTheDocument()
    expect(screen.getByText('Pick #8 • Round 1')).toBeInTheDocument()
  })

  it('shows enter pick button when manual mode and user turn', () => {
    mockLocation.state.session.current_pick = 8
    mockLocation.state.session.next_user_pick = 8
    mockLocation.state.session.is_live_synced = false
    
    render(<DraftRoomPage />)
    
    expect(screen.getByRole('button', { name: /enter pick/i })).toBeInTheDocument()
  })

  it('renders refresh button', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
  })

  it('renders draft recommendations', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Draft Recommendations')).toBeInTheDocument()
    expect(screen.getByTestId('draft-recommendations')).toBeInTheDocument()
  })

  it('renders draft board', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByTestId('draft-board')).toBeInTheDocument()
    expect(screen.getByText('Draft Board - Current pick: 5')).toBeInTheDocument()
  })

  it('displays user roster', () => {
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Your Roster')).toBeInTheDocument()
    expect(screen.getByText('Josh Allen')).toBeInTheDocument()
    expect(screen.getByText('Christian McCaffrey')).toBeInTheDocument()
  })

  it('displays empty roster message when no picks', () => {
    mockLocation.state.session.user_roster = []
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('No picks yet')).toBeInTheDocument()
  })

  it('opens manual pick entry modal', async () => {
    mockLocation.state.session.current_pick = 8
    mockLocation.state.session.next_user_pick = 8
    mockLocation.state.session.is_live_synced = false
    
    const user = userEvent.setup()
    render(<DraftRoomPage />)
    
    const enterPickButton = screen.getByRole('button', { name: /enter pick/i })
    await user.click(enterPickButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('manual-pick-entry')).toBeInTheDocument()
    })
  })

  it('closes manual pick entry modal when cancelled', async () => {
    mockLocation.state.session.current_pick = 8
    mockLocation.state.session.next_user_pick = 8
    mockLocation.state.session.is_live_synced = false
    
    const user = userEvent.setup()
    render(<DraftRoomPage />)
    
    const enterPickButton = screen.getByRole('button', { name: /enter pick/i })
    await user.click(enterPickButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('manual-pick-entry')).toBeInTheDocument()
    })
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('manual-pick-entry')).not.toBeInTheDocument()
    })
  })

  it('handles recommendation loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    })
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('handles recommendation error state', () => {
    const mockRefetch = vi.fn()
    vi.mocked(useQuery).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to fetch'),
      refetch: mockRefetch,
    })
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('Failed to load recommendations')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('shows no recommendations message when empty', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
    
    render(<DraftRoomPage />)
    
    expect(screen.getByText('No recommendations available')).toBeInTheDocument()
  })

  it('calls refresh recommendations when refresh button clicked', async () => {
    const mockRefetch = vi.fn()
    vi.mocked(useQuery).mockReturnValue({
      data: mockRecommendations,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    })
    
    const user = userEvent.setup()
    render(<DraftRoomPage />)
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshButton)
    
    expect(mockRefetch).toHaveBeenCalled()
  })

  it('submits pick through manual entry', async () => {
    const mockMutate = vi.fn()
    const { useMutation } = require('@tanstack/react-query')
    useMutation.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    })
    
    mockLocation.state.session.current_pick = 8
    mockLocation.state.session.next_user_pick = 8
    mockLocation.state.session.is_live_synced = false
    
    const user = userEvent.setup()
    render(<DraftRoomPage />)
    
    const enterPickButton = screen.getByRole('button', { name: /enter pick/i })
    await user.click(enterPickButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('manual-pick-entry')).toBeInTheDocument()
    })
    
    const submitButton = screen.getByRole('button', { name: /submit pick/i })
    await user.click(submitButton)
    
    expect(mockMutate).toHaveBeenCalledWith({ pick: { player: 'Test Player' } })
  })
})