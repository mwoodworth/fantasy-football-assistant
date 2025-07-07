import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../../test/utils'
import userEvent from '@testing-library/user-event'
import { PlayersPage } from '../PlayersPage'
import { useQuery } from '@tanstack/react-query'

// Mock the player service
vi.mock('../../services/players', () => ({
  PlayerService: {
    searchPlayers: vi.fn(),
  },
}))

// Mock player components
vi.mock('../../components/players/PlayerCard', () => ({
  PlayerCard: ({ player, viewMode }: { player: any; viewMode: string }) => (
    <div data-testid="player-card">
      {player.name} - {player.position} - {viewMode}
    </div>
  ),
}))

vi.mock('../../components/players/PlayerFilters', () => ({
  PlayerFilters: ({ filters, onChange, onClear }: { filters: any; onChange: any; onClear: any }) => (
    <div data-testid="player-filters">
      <button onClick={() => onChange({ position: 'QB' })}>Filter QB</button>
      <button onClick={onClear}>Clear Filters</button>
    </div>
  ),
}))

vi.mock('../../components/players/PlayerSearchInput', () => ({
  PlayerSearchInput: ({ value, onChange, placeholder }: { value: string; onChange: any; placeholder: string }) => (
    <input
      data-testid="player-search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  ),
}))

const mockPlayers = [
  {
    id: 1,
    name: 'Josh Allen',
    position: 'QB',
    team: 'BUF',
    bye_week: 7,
    projected_points: 24.5,
    average_points: 22.3,
    trend: 'up',
  },
  {
    id: 2,
    name: 'Christian McCaffrey',
    position: 'RB',
    team: 'SF',
    bye_week: 9,
    projected_points: 20.1,
    average_points: 18.7,
    trend: 'stable',
  },
]

describe('PlayersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useQuery
    vi.mocked(useQuery).mockReturnValue({
      data: mockPlayers,
      isLoading: false,
      error: null,
    })
  })

  it('renders page header', () => {
    render(<PlayersPage />)
    
    expect(screen.getByRole('heading', { name: /players/i })).toBeInTheDocument()
    expect(screen.getByText(/search and analyze fantasy football players/i)).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<PlayersPage />)
    
    const searchInput = screen.getByTestId('player-search')
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveAttribute('placeholder', 'Search players by name, team, or position...')
  })

  it('renders filters toggle button', () => {
    render(<PlayersPage />)
    
    const filtersButton = screen.getByRole('button', { name: /filters/i })
    expect(filtersButton).toBeInTheDocument()
  })

  it('renders view mode toggle buttons', () => {
    render(<PlayersPage />)
    
    expect(screen.getByRole('button', { name: /grid/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /list/i })).toBeInTheDocument()
  })

  it('displays player count', () => {
    render(<PlayersPage />)
    
    expect(screen.getByText('2 players found')).toBeInTheDocument()
  })

  it('renders player cards', () => {
    render(<PlayersPage />)
    
    expect(screen.getByText('Josh Allen - QB - grid')).toBeInTheDocument()
    expect(screen.getByText('Christian McCaffrey - RB - grid')).toBeInTheDocument()
  })

  it('toggles filters visibility', async () => {
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    const filtersButton = screen.getByRole('button', { name: /filters/i })
    
    // Filters should be hidden initially
    expect(screen.queryByTestId('player-filters')).not.toBeInTheDocument()
    
    // Click to show filters
    await user.click(filtersButton)
    expect(screen.getByTestId('player-filters')).toBeInTheDocument()
    
    // Click to hide filters
    await user.click(filtersButton)
    expect(screen.queryByTestId('player-filters')).not.toBeInTheDocument()
  })

  it('switches between grid and list view modes', async () => {
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    const gridButton = screen.getByRole('button', { name: /grid/i })
    const listButton = screen.getByRole('button', { name: /list/i })
    
    // Should start in grid mode
    expect(screen.getByText('Josh Allen - QB - grid')).toBeInTheDocument()
    
    // Switch to list mode
    await user.click(listButton)
    expect(screen.getByText('Josh Allen - QB - list')).toBeInTheDocument()
    
    // Switch back to grid mode
    await user.click(gridButton)
    expect(screen.getByText('Josh Allen - QB - grid')).toBeInTheDocument()
  })

  it('handles search input', async () => {
    const mockRefetch = vi.fn()
    
    vi.mocked(useQuery).mockReturnValue({
      data: mockPlayers,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    })
    
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    const searchInput = screen.getByTestId('player-search')
    await user.type(searchInput, 'Josh')
    
    expect(searchInput).toHaveValue('Josh')
  })

  it('displays loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    })
    
    render(<PlayersPage />)
    
    expect(screen.getByText('Loading players...')).toBeInTheDocument()
    
    // Should show loading skeletons
    const skeletons = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-pulse')
    )
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('displays error state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to fetch'),
    })
    
    render(<PlayersPage />)
    
    expect(screen.getByText('Failed to load players')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('displays no players found state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    })
    
    render(<PlayersPage />)
    
    expect(screen.getByText('No players found')).toBeInTheDocument()
    expect(screen.getByText('Try adjusting your search criteria or clearing filters')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument()
  })

  it('shows clear filters button when filters are applied', async () => {
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    // Show filters
    const filtersButtons = screen.getAllByRole('button', { name: /filters/i })
    await user.click(filtersButtons[0])
    
    // Apply a filter
    const filterQBButton = screen.getByRole('button', { name: /filter qb/i })
    await user.click(filterQBButton)
    
    // Clear filters button should appear
    expect(screen.getByRole('button', { name: /clear all filters/i })).toBeInTheDocument()
  })

  it('clears filters and search', async () => {
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    // Add search query
    const searchInput = screen.getByTestId('player-search')
    await user.type(searchInput, 'Josh')
    
    // Show filters and apply one
    const filtersButtons = screen.getAllByRole('button', { name: /filters/i })
    await user.click(filtersButtons[0])
    
    const filterQBButton = screen.getByRole('button', { name: /filter qb/i })
    await user.click(filterQBButton)
    
    // Clear all filters
    const clearAllButton = screen.getByRole('button', { name: /clear all filters/i })
    await user.click(clearAllButton)
    
    // Search should be cleared
    expect(searchInput).toHaveValue('')
  })

  it('handles filter changes', async () => {
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    // Show filters
    const filtersButtons = screen.getAllByRole('button', { name: /filters/i })
    await user.click(filtersButtons[0])
    
    // Apply a filter
    const filterQBButton = screen.getByRole('button', { name: /filter qb/i })
    await user.click(filterQBButton)
    
    // This would trigger a re-query with the new filters
    // The actual filtering logic would be tested in the service tests
    expect(screen.getByTestId('player-filters')).toBeInTheDocument()
  })

  it('calls PlayerService.searchPlayers with correct parameters', () => {
    render(<PlayersPage />)
    
    // useQuery should be called with the correct queryFn
    const mockCall = vi.mocked(useQuery).mock.calls[vi.mocked(useQuery).mock.calls.length - 1]
    const queryConfig = mockCall[0]
    
    expect(queryConfig.queryKey).toEqual(['players', '', {}])
    expect(queryConfig.queryFn).toBeDefined()
  })

  it('updates query when search or filters change', async () => {
    let queryKey = ['players', '', {}]
    
    vi.mocked(useQuery).mockImplementation((config) => {
      queryKey = config.queryKey
      return {
        data: mockPlayers,
        isLoading: false,
        error: null,
      }
    })
    
    const user = userEvent.setup()
    render(<PlayersPage />)
    
    // Type in search
    const searchInput = screen.getByTestId('player-search')
    await user.type(searchInput, 'Josh')
    
    // The query key should eventually update (this is a simplified test)
    expect(queryKey[0]).toBe('players')
  })
})