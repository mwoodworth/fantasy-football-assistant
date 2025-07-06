import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/common/Card';
import { TrendingUp, Users, Trophy, AlertCircle, RefreshCw, Clock, TrendingDown, Star } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { PlayerService } from '../services/players';
import { DashboardService } from '../services/dashboard';
import { LiveScoreTicker } from '../components/dashboard/LiveScoreTicker';
import { TopPerformersWidget } from '../components/dashboard/TopPerformersWidget';
import { InjuryReportWidget } from '../components/dashboard/InjuryReportWidget';
import { TrendingPlayersWidget } from '../components/dashboard/TrendingPlayersWidget';
import { WaiverWireWidget } from '../components/dashboard/WaiverWireWidget';

export function DashboardPage() {
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch dashboard data
  const { data: dashboardData, isLoading, refetch, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => DashboardService.getDashboardData(),
    refetchInterval: autoRefresh ? 30000 : false, // Auto-refresh every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });

  const { data: topPerformers } = useQuery({
    queryKey: ['topPerformers'],
    queryFn: () => PlayerService.getTopPerformers(),
    refetchInterval: autoRefresh ? 60000 : false,
  });

  const { data: trendingPlayers } = useQuery({
    queryKey: ['trendingPlayers'],
    queryFn: () => PlayerService.getTrendingPlayers('up'),
    refetchInterval: autoRefresh ? 120000 : false,
  });

  const { data: waiverTargets } = useQuery({
    queryKey: ['waiverTargets'],
    queryFn: () => PlayerService.getWaiverTargets(),
    refetchInterval: autoRefresh ? 300000 : false,
  });

  // Update timestamp when data refreshes
  useEffect(() => {
    setLastUpdated(new Date());
  }, [dashboardData]);

  const handleManualRefresh = () => {
    refetch();
    setLastUpdated(new Date());
  };

  const stats = [
    {
      title: 'Team Rank',
      value: dashboardData?.teamRank || '---',
      description: `Out of ${dashboardData?.leagueSize || 12} teams`,
      icon: Trophy,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      trend: dashboardData?.rankTrend,
    },
    {
      title: 'Points This Week',
      value: dashboardData?.weeklyPoints || '---',
      description: `${dashboardData?.pointsProjected || 0} projected`,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      trend: dashboardData?.pointsTrend,
    },
    {
      title: 'Active Players',
      value: dashboardData?.activePlayers || '---',
      description: `${dashboardData?.benchPlayers || 0} on bench`,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Injury Alerts',
      value: dashboardData?.injuryAlerts || '0',
      description: 'Players at risk',
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      urgent: (dashboardData?.injuryAlerts || 0) > 0,
    },
  ];

  const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-red-500" />;
      default:
        return null;
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load dashboard</h3>
          <p className="text-gray-600 mb-4">There was an error loading your dashboard data.</p>
          <Button onClick={handleManualRefresh}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here's your team overview.</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock className="w-4 h-4" />
            <span>Updated {lastUpdated.toLocaleTimeString()}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span>Auto-refresh</span>
            </label>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Live Score Ticker */}
      <LiveScoreTicker />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title} className={stat.urgent ? 'border-red-200 bg-red-50' : undefined}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className="flex items-center space-x-1">
                {getTrendIcon(stat.trend)}
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-gray-600">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Top Performers */}
          <TopPerformersWidget 
            players={topPerformers} 
            loading={isLoading}
          />
          
          {/* Trending Players */}
          <TrendingPlayersWidget 
            players={trendingPlayers}
            loading={isLoading}
          />
        </div>

        {/* Middle Column */}
        <div className="space-y-6">
          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Recent Activity
                <Badge variant="secondary" size="sm">
                  Live
                </Badge>
              </CardTitle>
              <CardDescription>Your latest team updates and recommendations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboardData?.recentActivity?.map((activity, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className={`flex-shrink-0 w-2 h-2 mt-2 rounded-full ${
                      activity.type === 'recommendation' ? 'bg-green-500' :
                      activity.type === 'injury' ? 'bg-yellow-500' :
                      activity.type === 'trade' ? 'bg-blue-500' : 'bg-gray-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-sm text-gray-600">{activity.description}</p>
                      <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                    </div>
                  </div>
                )) || (
                  <div className="text-center py-4 text-gray-500">
                    No recent activity
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Injury Report */}
          <InjuryReportWidget 
            injuries={dashboardData?.injuries} 
            loading={isLoading}
          />
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Waiver Wire Targets */}
          <WaiverWireWidget 
            players={waiverTargets}
            loading={isLoading}
          />
          
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" variant="outline">
                <Star className="w-4 h-4 mr-2" />
                Set Lineup
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <TrendingUp className="w-4 h-4 mr-2" />
                View Trade Analyzer
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <AlertCircle className="w-4 h-4 mr-2" />
                Check Waivers
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Users className="w-4 h-4 mr-2" />
                Compare Players
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}