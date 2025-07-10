import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus, Users, Lock, CheckCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { cn } from '../../utils/cn';

interface PlayerCardEnhancedProps {
  player: {
    id: number;
    full_name: string;
    position: string;
    team: string;
    ownership_percentage: number;
    is_droppable: boolean;
    average_draft_position?: number;
    ownership_change?: number;
  };
  viewMode: 'grid' | 'list';
  onClick?: () => void;
  isSelected?: boolean;
}

export const PlayerCardEnhanced = memo(function PlayerCardEnhanced({
  player,
  viewMode,
  onClick,
  isSelected = false
}: PlayerCardEnhancedProps) {
  // Determine ownership badge color
  const getOwnershipBadgeVariant = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 50) return 'warning';
    if (percentage >= 10) return 'default';
    return 'success';
  };

  // Get ownership trend icon
  const getTrendIcon = (change?: number) => {
    if (!change || Math.abs(change) < 0.1) {
      return <Minus className="w-3 h-3 text-gray-400" />;
    }
    if (change > 0) {
      return <TrendingUp className="w-3 h-3 text-green-600" />;
    }
    return <TrendingDown className="w-3 h-3 text-red-600" />;
  };

  // Position colors
  const positionColors: Record<string, string> = {
    'QB': 'bg-red-100 text-red-800',
    'RB': 'bg-blue-100 text-blue-800',
    'WR': 'bg-green-100 text-green-800',
    'TE': 'bg-purple-100 text-purple-800',
    'K': 'bg-yellow-100 text-yellow-800',
    'D/ST': 'bg-orange-100 text-orange-800',
    'DEF': 'bg-orange-100 text-orange-800',
  };

  if (viewMode === 'list') {
    return (
      <Card 
        className={cn(
          "p-4 hover:shadow-md transition-all cursor-pointer",
          isSelected && "ring-2 ring-primary-500"
        )}
        onClick={onClick}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="flex-shrink-0">
              <span className={cn(
                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                positionColors[player.position] || 'bg-gray-100 text-gray-800'
              )}>
                {player.position}
              </span>
            </div>
            
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-gray-900 truncate">{player.full_name}</h3>
              <p className="text-sm text-gray-600">{player.team}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="text-xs text-gray-500">Ownership</p>
              <div className="flex items-center gap-1">
                <p className="font-semibold">{player.ownership_percentage.toFixed(1)}%</p>
                {getTrendIcon(player.ownership_change)}
              </div>
            </div>
            
            {player.average_draft_position && (
              <div className="text-center">
                <p className="text-xs text-gray-500">ADP</p>
                <p className="font-semibold">{player.average_draft_position.toFixed(1)}</p>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              {player.is_droppable ? (
                <Badge variant="success" size="sm">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Available
                </Badge>
              ) : (
                <Badge variant="default" size="sm">
                  <Lock className="w-3 h-3 mr-1" />
                  Rostered
                </Badge>
              )}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Grid view
  return (
    <Card 
      className={cn(
        "p-4 hover:shadow-lg transition-all cursor-pointer h-full",
        isSelected && "ring-2 ring-primary-500"
      )}
      onClick={onClick}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <span className={cn(
            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
            positionColors[player.position] || 'bg-gray-100 text-gray-800'
          )}>
            {player.position}
          </span>
          
          <Badge 
            variant={getOwnershipBadgeVariant(player.ownership_percentage)}
            size="sm"
          >
            <Users className="w-3 h-3 mr-1" />
            {player.ownership_percentage.toFixed(1)}%
          </Badge>
        </div>
        
        {/* Player Info */}
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 truncate mb-1">
            {player.full_name}
          </h3>
          <p className="text-sm text-gray-600 mb-3">{player.team}</p>
        </div>
        
        {/* Stats */}
        <div className="space-y-2 pt-3 border-t">
          {player.average_draft_position && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">ADP</span>
              <span className="font-medium">{player.average_draft_position.toFixed(1)}</span>
            </div>
          )}
          
          {player.ownership_change !== undefined && Math.abs(player.ownership_change) >= 0.1 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Trend</span>
              <div className="flex items-center gap-1">
                {getTrendIcon(player.ownership_change)}
                <span className={cn(
                  "font-medium",
                  player.ownership_change > 0 ? "text-green-600" : "text-red-600"
                )}>
                  {player.ownership_change > 0 ? '+' : ''}{player.ownership_change.toFixed(1)}%
                </span>
              </div>
            </div>
          )}
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Status</span>
            {player.is_droppable ? (
              <span className="text-green-600 font-medium">Available</span>
            ) : (
              <span className="text-gray-600 font-medium">Rostered</span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
});