import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, TrendingUp, TrendingDown, Activity, Users, AlertCircle } from 'lucide-react';
import type { Player } from '../../pages/PlayersPage';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { cn } from '../../utils/cn';

interface PlayerCardProps {
  player: Player;
  viewMode: 'grid' | 'list';
  onPlayerClick?: (player: Player) => void;
  showActions?: boolean;
}

const POSITION_COLORS = {
  QB: 'bg-red-100 text-red-800',
  RB: 'bg-green-100 text-green-800',
  WR: 'bg-blue-100 text-blue-800',
  TE: 'bg-yellow-100 text-yellow-800',
  K: 'bg-purple-100 text-purple-800',
  DEF: 'bg-gray-100 text-gray-800',
};

const INJURY_STATUS_COLORS = {
  'Healthy': 'bg-green-100 text-green-800',
  'Questionable': 'bg-yellow-100 text-yellow-800',
  'Doubtful': 'bg-orange-100 text-orange-800',
  'Out': 'bg-red-100 text-red-800',
  'IR': 'bg-red-100 text-red-800',
};

export function PlayerCard({ 
  player, 
  viewMode, 
  onPlayerClick, 
  showActions = true 
}: PlayerCardProps) {
  const [isFavorite, setIsFavorite] = useState(false);
  const navigate = useNavigate();

  const handleCardClick = () => {
    if (onPlayerClick) {
      onPlayerClick(player);
    } else {
      navigate(`/players/${player.id}`);
    }
  };

  const toggleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorite(!isFavorite);
  };

  const getTrendIcon = () => {
    if (!player.trend) return null;
    
    switch (player.trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  if (viewMode === 'list') {
    return (
      <div 
        onClick={handleCardClick}
        className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all cursor-pointer"
      >
        <div className="flex items-center space-x-4 flex-1">
          {/* Player Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-gray-900 truncate">{player.name}</h3>
              <Badge className={POSITION_COLORS[player.position as keyof typeof POSITION_COLORS] || 'bg-gray-100 text-gray-800'}>
                {player.position}
              </Badge>
              <span className="text-sm text-gray-600">{player.team}</span>
              {player.injury_status && player.injury_status !== 'Healthy' && (
                <Badge className={INJURY_STATUS_COLORS[player.injury_status as keyof typeof INJURY_STATUS_COLORS] || 'bg-gray-100 text-gray-800'}>
                  {player.injury_status}
                </Badge>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center space-x-6 text-sm text-gray-600">
            {player.projected_points && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.projected_points.toFixed(1)}</div>
                <div>Projected</div>
              </div>
            )}
            {player.average_points && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.average_points.toFixed(1)}</div>
                <div>Average</div>
              </div>
            )}
            {player.ownership_percentage && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.ownership_percentage}%</div>
                <div>Owned</div>
              </div>
            )}
          </div>

          {/* Trend */}
          <div className="flex items-center space-x-2">
            {getTrendIcon()}
          </div>

          {/* Actions */}
          {showActions && (
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleFavorite}
                className={cn(
                  'p-2 rounded-md transition-colors',
                  isFavorite 
                    ? 'text-yellow-600 bg-yellow-50 hover:bg-yellow-100' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                )}
              >
                <Star className={cn('w-4 h-4', isFavorite && 'fill-current')} />
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Grid view
  return (
    <div 
      onClick={handleCardClick}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:shadow-md transition-all cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate" title={player.name}>
            {player.name}
          </h3>
          <div className="flex items-center space-x-2 mt-1">
            <Badge className={POSITION_COLORS[player.position as keyof typeof POSITION_COLORS] || 'bg-gray-100 text-gray-800'}>
              {player.position}
            </Badge>
            <span className="text-sm text-gray-600">{player.team}</span>
          </div>
        </div>
        
        {showActions && (
          <button
            onClick={toggleFavorite}
            className={cn(
              'p-1 rounded-md transition-colors',
              isFavorite 
                ? 'text-yellow-600 bg-yellow-50 hover:bg-yellow-100' 
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
            )}
          >
            <Star className={cn('w-4 h-4', isFavorite && 'fill-current')} />
          </button>
        )}
      </div>

      {/* Injury Status */}
      {player.injury_status && player.injury_status !== 'Healthy' && (
        <div className="mb-3">
          <Badge className={INJURY_STATUS_COLORS[player.injury_status as keyof typeof INJURY_STATUS_COLORS] || 'bg-gray-100 text-gray-800'}>
            <AlertCircle className="w-3 h-3 mr-1" />
            {player.injury_status}
          </Badge>
        </div>
      )}

      {/* Stats */}
      <div className="space-y-2 mb-4">
        {player.projected_points && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Projected</span>
            <span className="font-medium">{player.projected_points.toFixed(1)} pts</span>
          </div>
        )}
        {player.average_points && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Average</span>
            <span className="font-medium">{player.average_points.toFixed(1)} pts</span>
          </div>
        )}
        {player.ownership_percentage && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Ownership</span>
            <div className="flex items-center space-x-1">
              <Users className="w-3 h-3 text-gray-400" />
              <span className="font-medium">{player.ownership_percentage}%</span>
            </div>
          </div>
        )}
        {player.bye_week && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Bye Week</span>
            <span className="font-medium">Week {player.bye_week}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          {getTrendIcon()}
          {player.trend && (
            <span className="text-xs text-gray-600 capitalize">{player.trend}</span>
          )}
        </div>
        
        {showActions && (
          <Button size="sm" variant="outline">
            View Details
          </Button>
        )}
      </div>
    </div>
  );
}