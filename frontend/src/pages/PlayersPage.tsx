import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Filter } from 'lucide-react';
import { PlayerService } from '../services/players';
import { PlayerCard } from '../components/players/PlayerCard';
import { PlayerFilters } from '../components/players/PlayerFilters';
import { PlayerSearchInput } from '../components/players/PlayerSearchInput';
import { Button } from '../components/common/Button';
import { cn } from '../utils/cn';

export interface Player {
  id: number;
  name: string;
  position: string;
  team: string;
  bye_week: number;
  injury_status?: string;
  projected_points?: number;
  average_points?: number;
  trend?: 'up' | 'down' | 'stable';
  ownership_percentage?: number;
  trade_value?: number;
}

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

  const { data: players, isLoading, error } = useQuery({
    queryKey: ['players', searchQuery, filters],
    queryFn: () => PlayerService.searchPlayers({
      search: searchQuery || undefined,
      position: filters.position,
      limit: 50
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
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
    </div>
  );
}