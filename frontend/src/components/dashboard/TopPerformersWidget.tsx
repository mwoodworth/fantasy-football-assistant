import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import type { TopPerformer } from '../../services/dashboard';
import { cn } from '../../utils/cn';

interface TopPerformersWidgetProps {
  players?: TopPerformer[];
  loading?: boolean;
}

export function TopPerformersWidget({ players, loading }: TopPerformersWidgetProps) {
  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-red-500" />;
      default:
        return <Activity className="w-3 h-3 text-gray-500" />;
    }
  };

  const getPerformanceColor = (percentage: number) => {
    if (percentage >= 120) return 'text-green-600';
    if (percentage >= 100) return 'text-blue-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceBadge = (percentage: number) => {
    if (percentage >= 120) return { variant: 'success' as const, label: 'Excellent' };
    if (percentage >= 100) return { variant: 'default' as const, label: 'Good' };
    if (percentage >= 80) return { variant: 'warning' as const, label: 'Fair' };
    return { variant: 'error' as const, label: 'Poor' };
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Top Performers
          <Badge variant="success" size="sm">This Week</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                    <div className="space-y-1">
                      <div className="w-24 h-4 bg-gray-200 rounded"></div>
                      <div className="w-16 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                  <div className="w-12 h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : players && players.length > 0 ? (
          <div className="space-y-4">
            {players.slice(0, 5).map((performer, index) => {
              const badge = getPerformanceBadge(performer.percentageOfProjected);
              
              return (
                <div
                  key={performer.player.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {/* Rank */}
                    <div className={cn(
                      'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                      index === 0 ? 'bg-yellow-100 text-yellow-800' :
                      index === 1 ? 'bg-gray-100 text-gray-800' :
                      index === 2 ? 'bg-orange-100 text-orange-800' :
                      'bg-blue-100 text-blue-800'
                    )}>
                      {index + 1}
                    </div>

                    {/* Player Info */}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">{performer.player.name}</span>
                        <Badge className="bg-gray-100 text-gray-700" size="sm">
                          {performer.player.position}
                        </Badge>
                        <span className="text-xs text-gray-500">{performer.player.team}</span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs text-gray-600">
                          {performer.points} pts ({performer.projectedPoints} proj)
                        </span>
                        {getTrendIcon(performer.trend)}
                      </div>
                    </div>
                  </div>

                  {/* Performance */}
                  <div className="text-right">
                    <div className={cn(
                      'font-bold text-lg',
                      getPerformanceColor(performer.percentageOfProjected)
                    )}>
                      {performer.percentageOfProjected.toFixed(0)}%
                    </div>
                    <Badge variant={badge.variant} size="sm">
                      {badge.label}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No performance data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}