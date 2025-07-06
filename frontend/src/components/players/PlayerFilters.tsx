import { useState } from 'react';
import { X, ChevronDown } from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { cn } from '../../utils/cn';

interface PlayerFiltersProps {
  filters: {
    position?: string;
    team?: string;
    availability?: 'all' | 'available' | 'owned';
    sortBy?: 'projected' | 'average' | 'trend' | 'ownership';
  };
  onChange: (filters: any) => void;
  onClear: () => void;
}

const POSITIONS = [
  { value: 'QB', label: 'Quarterback' },
  { value: 'RB', label: 'Running Back' },
  { value: 'WR', label: 'Wide Receiver' },
  { value: 'TE', label: 'Tight End' },
  { value: 'K', label: 'Kicker' },
  { value: 'DEF', label: 'Defense' },
];

const TEAMS = [
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
  'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
  'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
  'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
];

const AVAILABILITY_OPTIONS = [
  { value: 'all', label: 'All Players' },
  { value: 'available', label: 'Available' },
  { value: 'owned', label: 'Owned' },
];

const SORT_OPTIONS = [
  { value: 'projected', label: 'Projected Points' },
  { value: 'average', label: 'Average Points' },
  { value: 'trend', label: 'Trending' },
  { value: 'ownership', label: 'Ownership %' },
];

export function PlayerFilters({ filters, onChange, onClear }: PlayerFiltersProps) {
  const [showTeamDropdown, setShowTeamDropdown] = useState(false);

  const handleFilterChange = (key: string, value: string | undefined) => {
    onChange({ [key]: value });
  };

  const removeFilter = (key: string) => {
    onChange({ [key]: undefined });
  };

  const getActiveFiltersCount = () => {
    return Object.values(filters).filter(Boolean).length;
  };

  const getTeamLabel = (team: string) => {
    return team;
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
      {/* Filter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Position Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Position
          </label>
          <select
            value={filters.position || ''}
            onChange={(e) => handleFilterChange('position', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Positions</option>
            {POSITIONS.map((position) => (
              <option key={position.value} value={position.value}>
                {position.label}
              </option>
            ))}
          </select>
        </div>

        {/* Team Filter */}
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Team
          </label>
          <div className="relative">
            <button
              onClick={() => setShowTeamDropdown(!showTeamDropdown)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-left bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 flex items-center justify-between"
            >
              <span className={cn(filters.team ? 'text-gray-900' : 'text-gray-500')}>
                {filters.team ? getTeamLabel(filters.team) : 'All Teams'}
              </span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>
            
            {showTeamDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
                <button
                  onClick={() => {
                    handleFilterChange('team', undefined);
                    setShowTeamDropdown(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 text-gray-500"
                >
                  All Teams
                </button>
                {TEAMS.map((team) => (
                  <button
                    key={team}
                    onClick={() => {
                      handleFilterChange('team', team);
                      setShowTeamDropdown(false);
                    }}
                    className={cn(
                      'w-full px-3 py-2 text-left text-sm hover:bg-gray-50',
                      filters.team === team ? 'bg-primary-50 text-primary-700' : 'text-gray-900'
                    )}
                  >
                    {team}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Availability Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Availability
          </label>
          <select
            value={filters.availability || 'all'}
            onChange={(e) => handleFilterChange('availability', e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {AVAILABILITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Sort By Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sort By
          </label>
          <select
            value={filters.sortBy || ''}
            onChange={(e) => handleFilterChange('sortBy', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">Default</option>
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {filters.position && (
            <Badge className="bg-primary-100 text-primary-800 flex items-center gap-1">
              Position: {filters.position}
              <button
                onClick={() => removeFilter('position')}
                className="ml-1 hover:text-primary-900"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          )}
          
          {filters.team && (
            <Badge className="bg-primary-100 text-primary-800 flex items-center gap-1">
              Team: {filters.team}
              <button
                onClick={() => removeFilter('team')}
                className="ml-1 hover:text-primary-900"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          )}
          
          {filters.availability && filters.availability !== 'all' && (
            <Badge className="bg-primary-100 text-primary-800 flex items-center gap-1">
              {AVAILABILITY_OPTIONS.find(opt => opt.value === filters.availability)?.label}
              <button
                onClick={() => removeFilter('availability')}
                className="ml-1 hover:text-primary-900"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          )}
          
          {filters.sortBy && (
            <Badge className="bg-primary-100 text-primary-800 flex items-center gap-1">
              Sort: {SORT_OPTIONS.find(opt => opt.value === filters.sortBy)?.label}
              <button
                onClick={() => removeFilter('sortBy')}
                className="ml-1 hover:text-primary-900"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          )}
        </div>

        {getActiveFiltersCount() > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="text-gray-600 hover:text-gray-900"
          >
            Clear All ({getActiveFiltersCount()})
          </Button>
        )}
      </div>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm font-medium text-gray-700">Quick filters:</span>
        <button
          onClick={() => onChange({ position: 'QB' })}
          className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
        >
          QBs
        </button>
        <button
          onClick={() => onChange({ position: 'RB' })}
          className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
        >
          RBs
        </button>
        <button
          onClick={() => onChange({ position: 'WR' })}
          className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
        >
          WRs
        </button>
        <button
          onClick={() => onChange({ position: 'TE' })}
          className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
        >
          TEs
        </button>
        <button
          onClick={() => onChange({ availability: 'available' })}
          className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
        >
          Available
        </button>
      </div>

      {/* Click outside to close team dropdown */}
      {showTeamDropdown && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setShowTeamDropdown(false)}
        />
      )}
    </div>
  );
}