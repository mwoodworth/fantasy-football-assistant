import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, TrendingUp, TrendingDown, Activity, Users, AlertCircle, Zap, Target, LineChart } from 'lucide-react';
import type { Player } from '../../types/player';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Sparkline } from '../common/Sparkline';
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
            {player.average_points_last_3 && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.average_points_last_3.toFixed(1)}</div>
                <div>L3 Avg</div>
              </div>
            )}
            {player.ownership_percentage && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.ownership_percentage}%</div>
                <div>Owned</div>
              </div>
            )}
            {player.consistency_rating && (
              <div className="text-center">
                <div className="font-medium text-gray-900">{player.consistency_rating}%</div>
                <div>Consistency</div>
              </div>
            )}
          </div>

          {/* Trend with Sparkline */}
          <div className="flex items-center space-x-2">
            {player.points_last_3_weeks && player.points_last_3_weeks.length > 0 && (
              <Sparkline data={player.points_last_3_weeks} width={50} height={16} />
            )}
            {getTrendIcon()}
          </div>

          {/* News Alert */}
          {player.latest_news && (
            <div className="max-w-xs">
              <p className="text-xs text-gray-600 truncate">{player.latest_news.headline}</p>
            </div>
          )}

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
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
    >
      {/* Ownership Badge */}
      {player.ownership_percentage && (
        <div className="absolute top-2 right-2">
          <Badge 
            variant="secondary" 
            className={cn(
              "text-xs",
              player.ownership_percentage > 80 ? "bg-red-100 text-red-700" :
              player.ownership_percentage > 50 ? "bg-yellow-100 text-yellow-700" :
              "bg-green-100 text-green-700"
            )}
          >
            {player.ownership_percentage}%
          </Badge>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 pr-8">
          <h3 className="font-medium text-gray-900 truncate" title={player.name}>
            {player.name}
          </h3>
          <div className="flex items-center space-x-2 mt-1">
            <Badge className={POSITION_COLORS[player.position as keyof typeof POSITION_COLORS] || 'bg-gray-100 text-gray-800'}>
              {player.position}
            </Badge>
            <span className="text-sm text-gray-600">{player.team}</span>
            {player.bye_week && (
              <span className="text-xs text-gray-500">BYE: {player.bye_week}</span>
            )}
          </div>
        </div>
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
      <div className="space-y-3 mb-4">
        {/* Points Section */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-sm font-medium text-gray-700">Fantasy Points</span>
            </div>
            {player.trend && getTrendIcon()}
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-sm">
            {player.projected_points && (
              <div>
                <span className="text-gray-500">Projected:</span>
                <span className="font-semibold ml-1">{player.projected_points.toFixed(1)}</span>
              </div>
            )}
            {player.average_points_last_3 && (
              <div>
                <span className="text-gray-500">L3 Avg:</span>
                <span className="font-semibold ml-1">{player.average_points_last_3.toFixed(1)}</span>
              </div>
            )}
          </div>
          
          {/* Performance Sparkline */}
          {player.points_last_3_weeks && player.points_last_3_weeks.length > 0 && (
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-500">Last 3 weeks:</span>
              <Sparkline data={player.points_last_3_weeks} />
            </div>
          )}
        </div>

        {/* Additional Stats */}
        {player.consistency_rating && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Consistency</span>
            <div className="flex items-center gap-1">
              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${player.consistency_rating}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">{player.consistency_rating}%</span>
            </div>
          </div>
        )}

        {player.matchup_rating && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Matchup</span>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-2 h-2 rounded-full",
                    i < Math.ceil(player.matchup_rating / 2)
                      ? player.matchup_rating >= 8 ? "bg-green-500" 
                        : player.matchup_rating >= 5 ? "bg-yellow-500" 
                        : "bg-red-500"
                      : "bg-gray-300"
                  )}
                />
              ))}
              <span className="text-xs text-gray-500 ml-1">{player.matchup_rating}/10</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="space-y-2">
        {/* Latest News */}
        {player.latest_news && (
          <div className="bg-blue-50 rounded-lg p-2">
            <div className="flex items-start gap-2">
              <LineChart className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-blue-900 truncate">
                  {player.latest_news.headline}
                </p>
                <p className="text-xs text-blue-700 mt-0.5">
                  {new Date(player.latest_news.date).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {player.boom_bust_rating && (
              <Badge variant="outline" className="text-xs">
                {player.boom_bust_rating}
              </Badge>
            )}
          </div>
          
          {showActions && (
            <div className="flex items-center gap-2">
              <button
                onClick={toggleFavorite}
                className={cn(
                  'p-1.5 rounded-md transition-colors',
                  isFavorite 
                    ? 'text-yellow-600 bg-yellow-50 hover:bg-yellow-100' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                )}
              >
                <Star className={cn('w-3 h-3', isFavorite && 'fill-current')} />
              </button>
              <Button size="sm" variant="outline">
                Details
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}