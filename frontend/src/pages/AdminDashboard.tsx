import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Users, 
  UserCheck, 
  Shield, 
  TrendingUp,
  Activity,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  BarChart3
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import api from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { cn } from '../utils/cn';

interface SystemStats {
  total_users: number;
  active_users: number;
  premium_users: number;
  total_admins: number;
  total_superadmins: number;
  users_today: number;
  users_this_week: number;
  users_this_month: number;
}

interface StatCardProps {
  title: string;
  value: number | string;
  description?: string;
  icon: React.ElementType;
  trend?: number;
  color?: string;
}

function StatCard({ title, value, description, icon: Icon, trend, color = "blue" }: StatCardProps) {
  const colorClasses = {
    blue: "bg-blue-600 text-white",
    green: "bg-emerald-600 text-white",
    purple: "bg-purple-600 text-white",
    orange: "bg-orange-600 text-white",
  };

  const bgClasses = {
    blue: "from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900",
    green: "from-emerald-50 to-emerald-100 dark:from-emerald-950 dark:to-emerald-900",
    purple: "from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900",
    orange: "from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900",
  };

  return (
    <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 border-0">
      <CardContent className={cn("p-6 bg-gradient-to-br", bgClasses[color as keyof typeof bgClasses])}>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-gray-600 dark:text-gray-300">{title}</p>
            <div className="flex items-baseline space-x-2">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{value}</h2>
              {trend !== undefined && (
                <span className={cn(
                  "flex items-center text-sm font-semibold",
                  trend > 0 ? "text-emerald-700 dark:text-emerald-400" : "text-red-700 dark:text-red-400"
                )}>
                  {trend > 0 ? (
                    <ArrowUpRight className="h-4 w-4" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4" />
                  )}
                  {Math.abs(trend)}%
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{description}</p>
            )}
          </div>
          <div className={cn("p-3 rounded-lg shadow-lg", colorClasses[color as keyof typeof colorClasses])}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AdminDashboard() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    fetchSystemStats();
  }, []);

  const fetchSystemStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/stats');
      setStats(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch system statistics');
    } finally {
      setLoading(false);
    }
  };

  // Sample data for charts
  const userGrowthData = [
    { name: 'Jan', users: 1200 },
    { name: 'Feb', users: 1350 },
    { name: 'Mar', users: 1480 },
    { name: 'Apr', users: 1620 },
    { name: 'May', users: 1890 },
    { name: 'Jun', users: 2100 },
  ];

  const activityData = [
    { name: 'Mon', active: 420 },
    { name: 'Tue', active: 380 },
    { name: 'Wed', active: 450 },
    { name: 'Thu', active: 470 },
    { name: 'Fri', active: 510 },
    { name: 'Sat', active: 390 },
    { name: 'Sun', active: 480 },
  ];

  const userTypeData = stats ? [
    { name: 'Regular', value: stats.total_users - stats.premium_users - stats.total_admins },
    { name: 'Premium', value: stats.premium_users },
    { name: 'Admin', value: stats.total_admins },
  ] : [];

  const COLORS = ['#4F46E5', '#059669', '#DC2626'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Welcome back, {user?.username}. Here's what's happening in your system.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {stats && (
        <>
          {/* Stats Grid */}
          <div className="grid gap-6 mb-8 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Users"
              value={stats.total_users.toLocaleString()}
              description={`${stats.active_users} active`}
              icon={Users}
              trend={12}
              color="blue"
            />
            <StatCard
              title="Premium Users"
              value={stats.premium_users.toLocaleString()}
              description={`${((stats.premium_users / stats.total_users) * 100).toFixed(1)}% of total`}
              icon={UserCheck}
              trend={8}
              color="green"
            />
            <StatCard
              title="New Today"
              value={stats.users_today}
              description={`${stats.users_this_week} this week`}
              icon={TrendingUp}
              trend={stats.users_today > 0 ? 15 : -5}
              color="purple"
            />
            <StatCard
              title="Admin Users"
              value={stats.total_admins}
              description={`${stats.total_superadmins} superadmins`}
              icon={Shield}
              color="orange"
            />
          </div>

          {/* Charts Grid */}
          <div className="grid gap-6 mb-8 md:grid-cols-2 lg:grid-cols-3">
            {/* User Growth Chart */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>User Growth</CardTitle>
                <CardDescription>Monthly user registration trend</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={userGrowthData}>
                    <defs>
                      <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.9}/>
                        <stop offset="95%" stopColor="#4F46E5" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#6B7280" style={{ fontSize: '12px', fontWeight: 500 }} />
                    <YAxis stroke="#6B7280" style={{ fontSize: '12px', fontWeight: 500 }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                      }} 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="users" 
                      stroke="#4F46E5" 
                      fillOpacity={1} 
                      fill="url(#colorUsers)" 
                      strokeWidth={3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* User Types Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>User Distribution</CardTitle>
                <CardDescription>By user type</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={userTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {userTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Activity Chart */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Weekly Activity</CardTitle>
              <CardDescription>Active users per day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={activityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="name" stroke="#6B7280" style={{ fontSize: '12px', fontWeight: 500 }} />
                  <YAxis stroke="#6B7280" style={{ fontSize: '12px', fontWeight: 500 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Bar dataKey="active" fill="#059669" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => window.location.href = '/admin/users'}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">Manage Users</h3>
                    <p className="text-sm text-muted-foreground mt-1">View and manage all users</p>
                  </div>
                  <Users className="h-8 w-8 text-gray-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => window.location.href = '/admin/activity'}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">Activity Logs</h3>
                    <p className="text-sm text-muted-foreground mt-1">View recent admin actions</p>
                  </div>
                  <Activity className="h-8 w-8 text-gray-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </CardContent>
            </Card>

            {user?.is_superadmin && (
              <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => window.location.href = '/admin/settings'}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">System Settings</h3>
                      <p className="text-sm text-muted-foreground mt-1">Configure system settings</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-gray-400 group-hover:text-blue-600 transition-colors" />
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </>
      )}
    </div>
  );
}