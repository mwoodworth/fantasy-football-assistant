import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/common/Card';
import { TrendingUp, Users, Trophy, AlertCircle } from 'lucide-react';

export function DashboardPage() {
  const stats = [
    {
      title: 'Team Rank',
      value: '3rd',
      description: 'Out of 12 teams',
      icon: Trophy,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      title: 'Win Streak',
      value: '4',
      description: 'Games in a row',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Active Players',
      value: '15',
      description: '2 on bench',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Injury Alerts',
      value: '2',
      description: 'Players at risk',
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Here's your team overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-gray-600">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest team updates and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">AI Recommendation</p>
                <p className="text-sm text-gray-600">
                  Consider starting Josh Allen over Lamar Jackson this week based on matchup analysis
                </p>
                <p className="text-xs text-gray-500 mt-1">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-yellow-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Injury Update</p>
                <p className="text-sm text-gray-600">
                  Christian McCaffrey listed as questionable for Sunday's game
                </p>
                <p className="text-xs text-gray-500 mt-1">5 hours ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-2 h-2 mt-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Trade Proposal</p>
                <p className="text-sm text-gray-600">
                  New trade offer: Your Stefon Diggs for their Travis Kelce
                </p>
                <p className="text-xs text-gray-500 mt-1">1 day ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}