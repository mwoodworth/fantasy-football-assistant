import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Filter, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { PlayerService } from '../services/players';
import type { Player } from '../types/player';
import { PlayerCard } from '../components/players/PlayerCard';
import { PlayerFilters } from '../components/players/PlayerFilters';
import { PlayerSearchInput } from '../components/players/PlayerSearchInput';
import { PlayerDetailsModal } from '../components/players/PlayerDetailsModal';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { cn } from '../utils/cn';
import { toast } from '../utils/toast';
import { useESPNStore } from '../store/useESPNStore';

interface PlayerFiltersType {
  position?: string;
  team?: string;
  availability?: 'all' | 'available' | 'owned';
  sortBy?: 'projected' | 'average' | 'trend' | 'ownership';
}

export function PlayersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<PlayerFiltersType>({});
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [selectedPlayerIndex, setSelectedPlayerIndex] = useState<number>(-1);
  const [showTrending, setShowTrending] = useState(false);
  
  const queryClient = useQueryClient();
  const { selectedLeague } = useESPNStore();

  const { data: players, isLoading, error } = useQuery({
    queryKey: ['players', searchQuery, filters],
    queryFn: () => PlayerService.searchPlayers({
      search: searchQuery || undefined,
      position: filters.position,
      limit: 50
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  // Fetch trending players from ESPN
  const { data: trendingData } = useQuery({
    queryKey: ['trending-players', showTrending],
    queryFn: async () => {
      if (!showTrending) return null;
      const [adding, dropping] = await Promise.all([
        PlayerService.getESPNTrendingPlayers('add', 24),
        PlayerService.getESPNTrendingPlayers('drop', 24)
      ]);
      return { adding, dropping };
    },
    enabled: showTrending,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
  
  // Sync league players mutation
  const syncMutation = useMutation({
    mutationFn: (leagueId: number) => PlayerService.syncLeaguePlayers(leagueId, false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['players'] });
      toast.success('Players synced successfully');
    },
    onError: () => {
      toast.error('Failed to sync players');
    }
  });

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilterChange = (newFilters: Partial<PlayerFiltersType>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const clearFilters = () => {
    setFilters({});
    setSearchQuery('');
  };

  const handlePlayerClick = (player: Player) => {
    setSelectedPlayer(player);
    const index = players?.findIndex(p => p.id === player.id) ?? -1;
    setSelectedPlayerIndex(index);
  };

  const handleNextPlayer = () => {
    if (players && selectedPlayerIndex < players.length - 1) {
      const nextIndex = selectedPlayerIndex + 1;
      setSelectedPlayer(players[nextIndex]);
      setSelectedPlayerIndex(nextIndex);
    }
  };

  const handlePreviousPlayer = () => {
    if (players && selectedPlayerIndex > 0) {
      const prevIndex = selectedPlayerIndex - 1;
      setSelectedPlayer(players[prevIndex]);
      setSelectedPlayerIndex(prevIndex);
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load players</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Players</h1>
          <p className="text-gray-600">
            Search and analyze fantasy football players
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {selectedLeague && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncMutation.mutate(selectedLeague.id)}
              disabled={syncMutation.isPending}
            >
              <RefreshCw className={cn("w-4 h-4 mr-2", syncMutation.isPending && "animate-spin")} />
              Sync ESPN
            </Button>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTrending(!showTrending)}
            className={cn(showTrending && 'bg-primary-50 text-primary-700')}
          >
            {showTrending ? <TrendingDown className="w-4 h-4 mr-2" /> : <TrendingUp className="w-4 h-4 mr-2" />}
            Trending
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(showFilters && 'bg-primary-50 text-primary-700')}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          
          <div className="flex border rounded-md">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'px-3 py-2 text-sm',
                viewMode === 'grid'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'px-3 py-2 text-sm border-l',
                viewMode === 'list'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      <PlayerSearchInput
        value={searchQuery}
        onChange={handleSearch}
        placeholder="Search players by name, team, or position..."
      />

      {/* Filters */}
      {showFilters && (
        <PlayerFilters
          filters={filters}
          onChange={handleFilterChange}
          onClear={clearFilters}
        />
      )}

      {/* Trending Players Section */}
      {showTrending && trendingData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-900">Most Added (24h)</h3>
            </div>
            <div className="space-y-2">
              {trendingData.adding.players?.slice(0, 5).map((player: any, idx: number) => (
                <div key={player.id} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{idx + 1}. {player.name}</span>
                  <Badge variant="success" size="sm">+{player.adds_24h}</Badge>
                </div>
              ))}
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingDown className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-gray-900">Most Dropped (24h)</h3>
            </div>
            <div className="space-y-2">
              {trendingData.dropping.players?.slice(0, 5).map((player: any, idx: number) => (
                <div key={player.id} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{idx + 1}. {player.name}</span>
                  <Badge variant="error" size="sm">-{player.drops_24h}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {isLoading ? (
            'Loading players...'
          ) : players ? (
            `${players.length} players found`
          ) : (
            'No players found'
          )}
        </p>
        
        {(searchQuery || Object.keys(filters).length > 0) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
          >
            Clear all filters
          </Button>
        )}
      </div>

      {/* Players Grid/List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-48 bg-gray-100 rounded-lg animate-pulse"
            />
          ))}
        </div>
      ) : players && players.length > 0 ? (
        <div className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
            : 'space-y-2'
        )}>
          {players.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              viewMode={viewMode}
              onPlayerClick={handlePlayerClick}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No players found</h3>
          <p className="text-gray-600 mb-4">
            Try adjusting your search criteria or clearing filters
          </p>
          <Button onClick={clearFilters}>
            Clear Filters
          </Button>
        </div>
      )}

      {/* Player Details Modal */}
      <PlayerDetailsModal
        player={selectedPlayer}
        isOpen={!!selectedPlayer}
        onClose={() => {
          setSelectedPlayer(null);
          setSelectedPlayerIndex(-1);
        }}
        onNext={handleNextPlayer}
        onPrevious={handlePreviousPlayer}
        hasNext={players ? selectedPlayerIndex < players.length - 1 : false}
        hasPrevious={selectedPlayerIndex > 0}
      />
    </div>
  );
}