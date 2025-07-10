import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Search, Filter, TrendingUp, TrendingDown, RefreshCw, 
  BarChart3, Users, Trophy, AlertCircle, ChevronLeft, 
  ChevronRight, Grid3X3, List, Scale
} from 'lucide-react';
import { PlayerService } from '../services/players';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { PlayerCardEnhanced } from '../components/players/PlayerCardEnhanced';
import { cn } from '../utils/cn';
import { toast } from '../utils/toast';
import { useESPNStore } from '../store/useESPNStore';

interface ESPNPlayer {
  id: number;
  full_name: string;
  position: string;
  team: string;
  ownership_percentage: number;
  is_droppable: boolean;
  eligible_slots?: number[];
  average_draft_position?: number;
  ownership_change?: number;
}

interface PlayerFilters {
  position?: string;
  minOwnership?: number;
  maxOwnership?: number;
  searchName?: string;
  teamId?: number;
  availableOnly?: boolean;
}

export function PlayersPageEnhanced() {
  const [filters, setFilters] = useState<PlayerFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const [showTrending, setShowTrending] = useState(false);
  const [trendType, setTrendType] = useState<'most_owned' | 'rising' | 'falling'>('most_owned');
  
  const queryClient = useQueryClient();
  const { selectedLeague } = useESPNStore();
  const pageSize = 50;

  // Fetch players using cached ESPN data
  const { data: playersData, isLoading, error } = useQuery({
    queryKey: ['espn-players', filters, currentPage],
    queryFn: async () => {
      if (filters.searchName || Object.keys(filters).length > 0) {
        // Use search endpoint if filters are applied
        return PlayerService.searchESPNPlayersEnhanced(filters);
      } else {
        // Use paginated all players endpoint
        return PlayerService.getAllESPNPlayers(pageSize, currentPage * pageSize);
      }
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Fetch trending players
  const { data: trendingData } = useQuery({
    queryKey: ['trending-players', trendType, filters.position],
    queryFn: () => PlayerService.getESPNTrendingEnhanced(trendType, filters.position, 20),
    enabled: showTrending,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
  });

  // Fetch player distribution stats
  const { data: statsData } = useQuery({
    queryKey: ['player-stats-distribution'],
    queryFn: () => PlayerService.getPlayerDistributionStats(),
    staleTime: 30 * 60 * 1000, // Cache for 30 minutes
  });

  // Sync players mutation
  const syncMutation = useMutation({
    mutationFn: () => {
      if (!selectedLeague) throw new Error('No league selected');
      return PlayerService.syncLeaguePlayers(selectedLeague.id, true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-players'] });
      queryClient.invalidateQueries({ queryKey: ['player-stats-distribution'] });
      toast.success('Players synced successfully');
    },
    onError: () => {
      toast.error('Failed to sync players');
    }
  });

  const handleFilterChange = (newFilters: Partial<PlayerFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(0); // Reset to first page when filters change
  };

  const handleSearch = (searchTerm: string) => {
    handleFilterChange({ searchName: searchTerm || undefined });
  };

  const clearFilters = () => {
    setFilters({});
    setCurrentPage(0);
  };

  const totalPlayers = playersData?.total_count || 0;
  const players = playersData?.players || [];
  const totalPages = Math.ceil(totalPlayers / pageSize);

  const positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST', 'FLEX'];
  const nflTeams = [
    { id: 1, name: 'ATL' }, { id: 2, name: 'BUF' }, { id: 3, name: 'CHI' },
    { id: 4, name: 'CIN' }, { id: 5, name: 'CLE' }, { id: 6, name: 'DAL' },
    { id: 7, name: 'DEN' }, { id: 8, name: 'DET' }, { id: 9, name: 'GB' },
    { id: 10, name: 'TEN' }, { id: 11, name: 'IND' }, { id: 12, name: 'KC' },
    { id: 13, name: 'LV' }, { id: 14, name: 'LAR' }, { id: 15, name: 'MIA' },
    { id: 16, name: 'MIN' }, { id: 17, name: 'NE' }, { id: 18, name: 'NO' },
    { id: 19, name: 'NYG' }, { id: 20, name: 'NYJ' }, { id: 21, name: 'PHI' },
    { id: 22, name: 'ARI' }, { id: 23, name: 'PIT' }, { id: 24, name: 'LAC' },
    { id: 25, name: 'SF' }, { id: 26, name: 'SEA' }, { id: 27, name: 'TB' },
    { id: 28, name: 'WSH' }, { id: 29, name: 'CAR' }, { id: 30, name: 'JAX' },
    { id: 33, name: 'BAL' }, { id: 34, name: 'HOU' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">NFL Players Database</h1>
          <p className="text-gray-600">
            Browse {totalPlayers.toLocaleString()} players with real-time ESPN ownership data
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {selectedLeague && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
            >
              <RefreshCw className={cn("w-4 h-4 mr-2", syncMutation.isPending && "animate-spin")} />
              Sync Players
            </Button>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTrending(!showTrending)}
            className={cn(showTrending && 'bg-primary-50 text-primary-700')}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
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
              <Grid3X3 className="w-4 h-4" />
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
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-primary-600" />
              <div>
                <p className="text-sm text-gray-600">Total Players</p>
                <p className="text-2xl font-bold">{statsData.total_players.toLocaleString()}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <Trophy className="w-8 h-8 text-yellow-600" />
              <div>
                <p className="text-sm text-gray-600">90%+ Owned</p>
                <p className="text-2xl font-bold">{statsData.ownership_distribution['90-100%']}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Available (0-10%)</p>
                <p className="text-2xl font-bold">{statsData.ownership_distribution['0-10%']}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Last Updated</p>
                <p className="text-sm font-medium">
                  {playersData?.cache_updated 
                    ? new Date(playersData.cache_updated).toLocaleTimeString()
                    : 'Never'}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search players by name..."
          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          value={filters.searchName || ''}
          onChange={(e) => handleSearch(e.target.value)}
        />
      </div>

      {/* Filters */}
      {showFilters && (
        <Card className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Position
              </label>
              <select
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={filters.position || ''}
                onChange={(e) => handleFilterChange({ position: e.target.value || undefined })}
              >
                <option value="">All Positions</option>
                {positions.map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Team
              </label>
              <select
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={filters.teamId || ''}
                onChange={(e) => handleFilterChange({ teamId: e.target.value ? parseInt(e.target.value) : undefined })}
              >
                <option value="">All Teams</option>
                {nflTeams.map(team => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Ownership %
              </label>
              <input
                type="number"
                min="0"
                max="100"
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={filters.minOwnership || ''}
                onChange={(e) => handleFilterChange({ minOwnership: e.target.value ? parseFloat(e.target.value) : undefined })}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Ownership %
              </label>
              <input
                type="number"
                min="0"
                max="100"
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={filters.maxOwnership || ''}
                onChange={(e) => handleFilterChange({ maxOwnership: e.target.value ? parseFloat(e.target.value) : undefined })}
              />
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={filters.availableOnly || false}
                onChange={(e) => handleFilterChange({ availableOnly: e.target.checked })}
              />
              <span className="text-sm text-gray-700">Available players only</span>
            </label>
            
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </Card>
      )}

      {/* Trending Section */}
      {showTrending && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Trending Players</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setTrendType('most_owned')}
                className={cn(
                  'px-3 py-1 text-sm rounded',
                  trendType === 'most_owned' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                Most Owned
              </button>
              <button
                onClick={() => setTrendType('rising')}
                className={cn(
                  'px-3 py-1 text-sm rounded',
                  trendType === 'rising' 
                    ? 'bg-green-100 text-green-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                Rising
              </button>
              <button
                onClick={() => setTrendType('falling')}
                className={cn(
                  'px-3 py-1 text-sm rounded',
                  trendType === 'falling' 
                    ? 'bg-red-100 text-red-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                Falling
              </button>
            </div>
          </div>
          
          {trendingData && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {trendingData.players.slice(0, 8).map((player: any, idx: number) => (
                <div key={player.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{player.full_name}</p>
                    <p className="text-xs text-gray-600">{player.position} - {player.team}</p>
                  </div>
                  <div className="text-right ml-2">
                    <p className="text-sm font-semibold">{player.ownership_percentage.toFixed(1)}%</p>
                    {player.ownership_change !== undefined && (
                      <p className={cn(
                        "text-xs",
                        player.ownership_change > 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {player.ownership_change > 0 ? '+' : ''}{player.ownership_change.toFixed(1)}%
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {isLoading ? (
            'Loading players...'
          ) : (
            <>
              Showing {players.length} of {totalPlayers.toLocaleString()} players
              {Object.keys(filters).length > 0 && ' (filtered)'}
            </>
          )}
        </p>
        
        {!isLoading && totalPages > 1 && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
              disabled={currentPage === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-gray-600">
              Page {currentPage + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
              disabled={currentPage >= totalPages - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Players Grid/List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load players</h3>
          <p className="text-gray-600 mb-4">There was an error loading the player data.</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['espn-players'] })}>
            Try Again
          </Button>
        </Card>
      ) : players.length === 0 ? (
        <Card className="p-8 text-center">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No players found</h3>
          <p className="text-gray-600 mb-4">Try adjusting your search criteria or filters.</p>
          <Button onClick={clearFilters}>Clear Filters</Button>
        </Card>
      ) : (
        <div className={cn(
          viewMode === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            : "space-y-2"
        )}>
          {players.map((player: ESPNPlayer) => (
            <PlayerCardEnhanced
              key={player.id}
              player={player}
              viewMode={viewMode}
              onClick={() => {
                // TODO: Open player detail modal or navigate to player page
                console.log('Player clicked:', player);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}