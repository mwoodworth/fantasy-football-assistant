import { TrendingUp, TrendingDown, Users, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import type { TrendingPlayer } from '../../services/dashboard';
import { cn } from '../../utils/cn';

interface TrendingPlayersWidgetProps {
  players?: TrendingPlayer[];
  loading?: boolean;
}

export function TrendingPlayersWidget({ players, loading }: TrendingPlayersWidgetProps) {
  const getTrendIcon = (direction: 'up' | 'down') => {
    return direction === 'up' ? (
      <TrendingUp className="w-4 h-4 text-green-500" />
    ) : (
      <TrendingDown className="w-4 h-4 text-red-500" />
    );
  };

  const getTrendColor = (direction: 'up' | 'down') => {
    return direction === 'up' ? 'text-green-600' : 'text-red-600';
  };

  const getTrendBadge = (direction: 'up' | 'down', percentage: number) => {
    const isHot = percentage > 70;
    
    if (direction === 'up') {
      return (
        <Badge 
          variant={isHot ? 'success' : 'default'} 
          size="sm"
          className={isHot ? 'animate-pulse' : ''}
        >
          🔥 Hot
        </Badge>
      );
    } else {
      return (
        <Badge variant="error" size="sm">
          📉 Cooling
        </Badge>
      );
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Trending Players
          <Badge variant="default" size="sm">
            <TrendingUp className="w-3 h-3 mr-1" />
            Rising
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                    <div className="space-y-1">
                      <div className="w-24 h-4 bg-gray-200 rounded"></div>
                      <div className="w-16 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                  <div className="w-16 h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : players && players.length > 0 ? (
          <div className="space-y-4">
            {players.slice(0, 4).map((player) => (
              <div
                key={player.player.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {/* Trend Icon */}
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center',
                    player.trendDirection === 'up' ? 'bg-green-100' : 'bg-red-100'
                  )}>
                    {getTrendIcon(player.trendDirection)}
                  </div>

                  {/* Player Info */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-sm">{player.player.name}</span>
                      <Badge className="bg-gray-100 text-gray-700" size="sm">
                        {player.player.position}
                      </Badge>
                      <span className="text-xs text-gray-500">{player.player.team}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-gray-600">{player.reason}</span>
                    </div>
                    
                    <div className="flex items-center space-x-3 mt-1">
                      <div className="flex items-center space-x-1 text-xs text-gray-500">
                        <Users className="w-3 h-3" />
                        <span>+{player.ownershipChange.toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center space-x-1 text-xs text-gray-500">
                        <Plus className="w-3 h-3" />
                        <span>{player.addDropRatio.toFixed(1)}:1</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trend Percentage & Badge */}
                <div className="text-right space-y-1">
                  <div className={cn(
                    'font-bold text-lg',
                    getTrendColor(player.trendDirection)
                  )}>
                    {player.trendDirection === 'up' ? '+' : ''}{player.trendPercentage.toFixed(0)}%
                  </div>
                  {getTrendBadge(player.trendDirection, player.trendPercentage)}
                </div>
              </div>
            ))}

            {/* View More Button */}
            <div className="pt-2">
              <Button variant="outline" size="sm" className="w-full">
                View All Trending Players
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No trending data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}