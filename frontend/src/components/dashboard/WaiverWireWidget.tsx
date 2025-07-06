import { Target, Users, TrendingUp, Calendar, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import type { WaiverTarget } from '../../services/dashboard';
import { cn } from '../../utils/cn';

interface WaiverWireWidgetProps {
  players?: WaiverTarget[];
  loading?: boolean;
}

export function WaiverWireWidget({ players, loading }: WaiverWireWidgetProps) {
  const getPriorityColor = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const getPriorityIcon = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high':
        return '🔥';
      case 'medium':
        return '⚡';
      default:
        return '💡';
    }
  };


  const getMatchupBadge = (difficulty: 'easy' | 'medium' | 'hard') => {
    switch (difficulty) {
      case 'easy':
        return { variant: 'success' as const, label: '👍 Good' };
      case 'medium':
        return { variant: 'warning' as const, label: '👌 Fair' };
      default:
        return { variant: 'error' as const, label: '👎 Tough' };
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Target className="w-4 h-4 text-blue-500" />
            Waiver Wire
          </div>
          <Badge variant="default" size="sm">
            Targets
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between p-3 bg-gray-100 rounded-lg">
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
            {players.slice(0, 4).map((target) => {
              const matchupBadge = getMatchupBadge(target.matchupDifficulty);
              
              return (
                <div
                  key={target.player.id}
                  className={cn(
                    'p-3 rounded-lg border transition-colors hover:shadow-sm',
                    target.priority === 'high' ? 'border-red-200 bg-red-50' :
                    target.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                    'border-green-200 bg-green-50'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      {/* Priority Indicator */}
                      <div className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-lg',
                        target.priority === 'high' ? 'bg-red-100' :
                        target.priority === 'medium' ? 'bg-yellow-100' :
                        'bg-green-100'
                      )}>
                        {getPriorityIcon(target.priority)}
                      </div>

                      <div className="flex-1">
                        {/* Player Info */}
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium text-sm">{target.player.name}</span>
                          <Badge className="bg-gray-100 text-gray-700" size="sm">
                            {target.player.position}
                          </Badge>
                          <span className="text-xs text-gray-500">{target.player.team}</span>
                          <Badge className={getPriorityColor(target.priority)} size="sm">
                            {target.priority.toUpperCase()}
                          </Badge>
                        </div>

                        {/* Stats */}
                        <div className="flex items-center space-x-4 mb-2">
                          <div className="flex items-center space-x-1">
                            <Users className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-600">
                              {target.ownershipPercentage.toFixed(1)}% owned
                            </span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <TrendingUp className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-600">
                              {target.projectedPoints.toFixed(1)} pts proj
                            </span>
                          </div>
                        </div>

                        {/* Matchup */}
                        <div className="flex items-center space-x-2 mb-2">
                          <Calendar className="w-3 h-3 text-gray-400" />
                          <span className="text-xs text-gray-600">
                            Next: {target.upcomingMatchup}
                          </span>
                          <Badge variant={matchupBadge.variant} size="sm">
                            {matchupBadge.label}
                          </Badge>
                        </div>

                        {/* Recommendation */}
                        <p className="text-xs text-gray-700 font-medium">
                          💡 {target.recommendation}
                        </p>
                      </div>
                    </div>

                    {/* Add Button */}
                    <div className="ml-2">
                      <Button size="sm" variant="outline" className="text-xs">
                        <Plus className="w-3 h-3 mr-1" />
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* View All Button */}
            <div className="pt-2 border-t">
              <Button variant="outline" size="sm" className="w-full">
                <Target className="w-4 h-4 mr-2" />
                View All Waiver Targets
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Target className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No waiver targets</p>
            <p className="text-xs text-gray-400 mt-1">Check back for recommendations</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}