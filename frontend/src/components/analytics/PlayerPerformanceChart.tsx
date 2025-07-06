import { Chart } from './Chart';
import type { ChartDataPoint } from './Chart';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface PlayerPerformance {
  week: number;
  points: number;
  projected: number;
  opponent: string;
  gameResult: 'win' | 'loss' | 'tie';
}

interface PlayerPerformanceChartProps {
  playerName: string;
  position: string;
  team: string;
  performances: PlayerPerformance[];
  loading?: boolean;
}

export function PlayerPerformanceChart({
  playerName,
  position,
  team,
  performances,
  loading
}: PlayerPerformanceChartProps) {
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
          <div className="h-80 bg-gray-100 rounded animate-pulse"></div>
        </CardContent>
      </Card>
    );
  }

  if (!performances || performances.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div>
              <span>{playerName}</span>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant="secondary" size="sm">{position}</Badge>
                <span className="text-sm text-gray-500">{team}</span>
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            <Activity className="w-8 h-8 mx-auto mb-2" />
            <p>No performance data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const actualData: ChartDataPoint[] = performances.map(p => ({
    label: `W${p.week}`,
    value: p.points,
    color: '#3B82F6',
    metadata: p
  }));

  const projectedData: ChartDataPoint[] = performances.map(p => ({
    label: `W${p.week}`,
    value: p.projected,
    color: '#94A3B8',
    metadata: p
  }));

  // Calculate stats
  const totalPoints = performances.reduce((sum, p) => sum + p.points, 0);
  const totalProjected = performances.reduce((sum, p) => sum + p.projected, 0);
  const avgPoints = totalPoints / performances.length;
  const avgProjected = totalProjected / performances.length;
  const consistencyScore = calculateConsistency(performances);
  const trend = calculateTrend(performances);

  function calculateConsistency(perfs: PlayerPerformance[]): number {
    if (perfs.length < 2) return 0;
    const avg = perfs.reduce((sum, p) => sum + p.points, 0) / perfs.length;
    const variance = perfs.reduce((sum, p) => sum + Math.pow(p.points - avg, 2), 0) / perfs.length;
    const stdDev = Math.sqrt(variance);
    return Math.max(0, 100 - (stdDev / avg) * 100);
  }

  function calculateTrend(perfs: PlayerPerformance[]): 'up' | 'down' | 'stable' {
    if (perfs.length < 3) return 'stable';
    const recent = perfs.slice(-3);
    const earlier = perfs.slice(-6, -3);
    if (earlier.length === 0) return 'stable';
    
    const recentAvg = recent.reduce((sum, p) => sum + p.points, 0) / recent.length;
    const earlierAvg = earlier.reduce((sum, p) => sum + p.points, 0) / earlier.length;
    
    const difference = (recentAvg - earlierAvg) / earlierAvg;
    if (difference > 0.1) return 'up';
    if (difference < -0.1) return 'down';
    return 'stable';
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div>
            <span>{playerName}</span>
            <div className="flex items-center space-x-2 mt-1">
              <Badge variant="secondary" size="sm">{position}</Badge>
              <span className="text-sm text-gray-500">{team}</span>
              <div className="flex items-center space-x-1">
                {getTrendIcon()}
                <span className={cn('text-sm font-medium', getTrendColor())}>
                  {trend === 'up' ? 'Trending Up' : trend === 'down' ? 'Trending Down' : 'Stable'}
                </span>
              </div>
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{avgPoints.toFixed(1)}</div>
            <div className="text-xs text-gray-600">Avg Points</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{avgProjected.toFixed(1)}</div>
            <div className="text-xs text-gray-600">Avg Projected</div>
          </div>
          <div className="text-center">
            <div className={cn(
              'text-2xl font-bold',
              totalPoints > totalProjected ? 'text-green-600' : 'text-red-600'
            )}>
              {totalPoints > totalProjected ? '+' : ''}{(totalPoints - totalProjected).toFixed(1)}
            </div>
            <div className="text-xs text-gray-600">vs Projected</div>
          </div>
          <div className="text-center">
            <div className={cn(
              'text-2xl font-bold',
              consistencyScore > 70 ? 'text-green-600' : 
              consistencyScore > 50 ? 'text-yellow-600' : 'text-red-600'
            )}>
              {consistencyScore.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600">Consistency</div>
          </div>
        </div>

        {/* Performance Chart */}
        <div className="relative">
          <Chart
            data={actualData}
            type="line"
            height={300}
            width={600}
            showGrid={true}
            showLabels={true}
            colors={['#3B82F6', '#94A3B8']}
            className="border-0 p-0"
          />
          
          {/* Overlay projected line */}
          <div className="absolute top-0 left-0 pointer-events-none">
            <Chart
              data={projectedData}
              type="line"
              height={300}
              width={600}
              showGrid={false}
              showLabels={false}
              colors={['#94A3B8']}
              className="border-0 p-0 bg-transparent"
            />
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center space-x-6 mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span className="text-sm text-gray-600">Actual Points</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-400 rounded"></div>
            <span className="text-sm text-gray-600">Projected Points</span>
          </div>
        </div>

        {/* Recent Games */}
        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-3">Recent Games</h4>
          <div className="space-y-2">
            {performances.slice(-5).reverse().map((perf, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium">Week {perf.week}</span>
                  <span className="text-sm text-gray-600">vs {perf.opponent}</span>
                  <Badge 
                    variant={perf.gameResult === 'win' ? 'success' : 'error'} 
                    size="sm"
                  >
                    {perf.gameResult.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">{perf.projected} proj</span>
                  <span className={cn(
                    'text-sm font-medium',
                    perf.points > perf.projected ? 'text-green-600' : 'text-red-600'
                  )}>
                    {perf.points.toFixed(1)} pts
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}