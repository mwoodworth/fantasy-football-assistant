import { Chart } from './Chart';
import type { ChartDataPoint } from './Chart';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { TrendingUp, Users, Trophy, Target, BarChart3 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface TeamAnalytics {
  weeklyScores: { week: number; points: number; rank: number }[];
  positionBreakdown: { position: string; points: number; percentage: number }[];
  matchupHistory: { week: number; opponent: string; result: 'win' | 'loss'; points: number; opponentPoints: number }[];
  projectedFinish: { position: number; playoffChance: number; championshipChance: number };
  strengthOfSchedule: { remaining: number; overall: number };
}

interface TeamAnalyticsWidgetProps {
  analytics?: TeamAnalytics;
  loading?: boolean;
  teamName: string;
}

export function TeamAnalyticsWidget({ analytics, loading, teamName }: TeamAnalyticsWidgetProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-32"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-60 bg-gray-100 rounded animate-pulse"></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-40 bg-gray-100 rounded animate-pulse"></div>
              <div className="h-40 bg-gray-100 rounded animate-pulse"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Team Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            <BarChart3 className="w-8 h-8 mx-auto mb-2" />
            <p>No analytics data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare weekly scores chart data
  const weeklyScoresData: ChartDataPoint[] = analytics.weeklyScores.map(w => ({
    label: `W${w.week}`,
    value: w.points,
    color: getScoreColor(w.rank),
    metadata: w
  }));

  // Prepare position breakdown chart data
  const positionData: ChartDataPoint[] = analytics.positionBreakdown.map(p => ({
    label: p.position,
    value: p.points,
    color: getPositionColor(p.position),
    metadata: p
  }));

  function getScoreColor(rank: number): string {
    if (rank <= 3) return '#10B981'; // Green for top 3
    if (rank <= 6) return '#3B82F6'; // Blue for middle
    if (rank <= 9) return '#F59E0B'; // Yellow for lower middle
    return '#EF4444'; // Red for bottom
  }

  function getPositionColor(position: string): string {
    const colors: Record<string, string> = {
      'QB': '#3B82F6',
      'RB': '#10B981',
      'WR': '#F59E0B',
      'TE': '#8B5CF6',
      'K': '#6B7280',
      'DEF': '#374151'
    };
    return colors[position] || '#6B7280';
  }

  const currentRecord = analytics.matchupHistory.reduce(
    (acc, match) => {
      acc[match.result]++;
      return acc;
    },
    { win: 0, loss: 0 }
  );

  const avgWeeklyScore = analytics.weeklyScores.reduce((sum, w) => sum + w.points, 0) / analytics.weeklyScores.length;
  const avgRank = analytics.weeklyScores.reduce((sum, w) => sum + w.rank, 0) / analytics.weeklyScores.length;

  return (
    <div className="space-y-6">
      {/* Team Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Trophy className="w-5 h-5 text-yellow-600" />
              <span>{teamName} Analytics</span>
            </div>
            <Badge variant="default" size="sm">
              {currentRecord.win}-{currentRecord.loss}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{avgWeeklyScore.toFixed(1)}</div>
              <div className="text-xs text-gray-600">Avg Points</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{avgRank.toFixed(1)}</div>
              <div className="text-xs text-gray-600">Avg Rank</div>
            </div>
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                analytics.projectedFinish.playoffChance > 60 ? 'text-green-600' :
                analytics.projectedFinish.playoffChance > 30 ? 'text-yellow-600' : 'text-red-600'
              )}>
                {analytics.projectedFinish.playoffChance.toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Playoff Chance</div>
            </div>
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                analytics.strengthOfSchedule.remaining < 0.5 ? 'text-green-600' :
                analytics.strengthOfSchedule.remaining < 0.6 ? 'text-yellow-600' : 'text-red-600'
              )}>
                {(analytics.strengthOfSchedule.remaining * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">SOS Remaining</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4" />
            <span>Weekly Performance</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Chart
            data={weeklyScoresData}
            type="line"
            height={300}
            width={700}
            showGrid={true}
            showLabels={true}
            title=""
            className="border-0 p-0"
          />
          
          {/* Performance insights */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm font-medium text-blue-900">Best Week</span>
              </div>
              <div className="mt-1">
                <span className="text-lg font-bold text-blue-900">
                  {Math.max(...analytics.weeklyScores.map(w => w.points)).toFixed(1)} pts
                </span>
                <span className="text-sm text-blue-700 ml-2">
                  Week {analytics.weeklyScores.find(w => w.points === Math.max(...analytics.weeklyScores.map(w => w.points)))?.week}
                </span>
              </div>
            </div>
            
            <div className="bg-red-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-sm font-medium text-red-900">Worst Week</span>
              </div>
              <div className="mt-1">
                <span className="text-lg font-bold text-red-900">
                  {Math.min(...analytics.weeklyScores.map(w => w.points)).toFixed(1)} pts
                </span>
                <span className="text-sm text-red-700 ml-2">
                  Week {analytics.weeklyScores.find(w => w.points === Math.min(...analytics.weeklyScores.map(w => w.points)))?.week}
                </span>
              </div>
            </div>
            
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-900">Championship</span>
              </div>
              <div className="mt-1">
                <span className="text-lg font-bold text-green-900">
                  {analytics.projectedFinish.championshipChance.toFixed(1)}%
                </span>
                <span className="text-sm text-green-700 ml-2">chance</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Position Breakdown & Recent Matchups */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Points by Position</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Chart
              data={positionData}
              type="pie"
              height={250}
              width={350}
              showLegend={true}
              className="border-0 p-0"
            />
            
            <div className="mt-4 space-y-2">
              {analytics.positionBreakdown
                .sort((a, b) => b.points - a.points)
                .map((pos) => (
                  <div key={pos.position} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: getPositionColor(pos.position) }}
                      />
                      <span className="text-sm font-medium">{pos.position}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold">{pos.points.toFixed(1)} pts</div>
                      <div className="text-xs text-gray-500">{pos.percentage.toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Matchups */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="w-4 h-4" />
              <span>Recent Matchups</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.matchupHistory.slice(-5).reverse().map((match, i) => (
                <div 
                  key={i}
                  className={cn(
                    'p-3 rounded-lg border',
                    match.result === 'win' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Badge 
                        variant={match.result === 'win' ? 'success' : 'error'} 
                        size="sm"
                      >
                        {match.result.toUpperCase()}
                      </Badge>
                      <span className="text-sm font-medium">Week {match.week}</span>
                      <span className="text-sm text-gray-600">vs {match.opponent}</span>
                    </div>
                    <div className="text-right">
                      <div className={cn(
                        'text-sm font-bold',
                        match.result === 'win' ? 'text-green-700' : 'text-red-700'
                      )}>
                        {match.points.toFixed(1)} - {match.opponentPoints.toFixed(1)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4">
              <Button variant="outline" size="sm" className="w-full">
                <Target className="w-4 h-4 mr-2" />
                View Full Schedule
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}