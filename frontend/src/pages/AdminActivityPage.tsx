import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, Search, AlertCircle, Activity, User, Shield, Ban, CheckCircle, Edit, Trash } from 'lucide-react';
import api from '../services/api';
import { AdminGuard } from '../components/auth/AdminGuard';
import { format } from 'date-fns';

interface ActivityLog {
  id: number;
  admin_id: number;
  admin_username: string;
  action: string;
  target_type?: string;
  target_id?: number;
  details?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  'USER_CREATED': <User className="h-4 w-4 text-emerald-700" />,
  'USER_UPDATED': <Edit className="h-4 w-4 text-blue-700" />,
  'USER_SUSPENDED': <Ban className="h-4 w-4 text-red-700" />,
  'USER_ACTIVATED': <CheckCircle className="h-4 w-4 text-emerald-700" />,
  'USER_DELETED': <Trash className="h-4 w-4 text-red-700" />,
  'ADMIN_GRANTED': <Shield className="h-4 w-4 text-purple-700" />,
  'ADMIN_REVOKED': <Shield className="h-4 w-4 text-orange-700" />,
  'ADMIN_LOGIN': <User className="h-4 w-4 text-blue-700" />,
};

const ACTION_LABELS: Record<string, string> = {
  'USER_CREATED': 'User Created',
  'USER_UPDATED': 'User Updated',
  'USER_SUSPENDED': 'User Suspended',
  'USER_ACTIVATED': 'User Activated',
  'USER_DELETED': 'User Deleted',
  'ADMIN_GRANTED': 'Admin Granted',
  'ADMIN_REVOKED': 'Admin Revoked',
  'ADMIN_LOGIN': 'Admin Login',
};

export function AdminActivityPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [adminFilter, setAdminFilter] = useState<string>('all');
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    fetchActivityLogs();
  }, [limit]);

  const fetchActivityLogs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/activity', {
        params: { limit }
      });
      setActivities(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch activity logs');
    } finally {
      setLoading(false);
    }
  };

  const filteredActivities = activities.filter(activity => {
    const matchesSearch = 
      activity.admin_username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (activity.details && activity.details.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesAction = 
      actionFilter === 'all' || activity.action === actionFilter;

    const matchesAdmin = 
      adminFilter === 'all' || activity.admin_username === adminFilter;

    return matchesSearch && matchesAction && matchesAdmin;
  });

  const uniqueAdmins = Array.from(new Set(activities.map(a => a.admin_username)));
  const uniqueActions = Array.from(new Set(activities.map(a => a.action)));

  const getActionBadge = (action: string) => {
    const icon = ACTION_ICONS[action] || <Activity className="h-4 w-4 text-gray-700" />;
    const label = ACTION_LABELS[action] || action;
    
    const badgeColors: Record<string, string> = {
      'USER_CREATED': 'bg-emerald-100 text-emerald-900 border-emerald-200',
      'USER_UPDATED': 'bg-blue-100 text-blue-900 border-blue-200',
      'USER_SUSPENDED': 'bg-red-100 text-red-900 border-red-200',
      'USER_ACTIVATED': 'bg-emerald-100 text-emerald-900 border-emerald-200',
      'USER_DELETED': 'bg-red-100 text-red-900 border-red-200',
      'ADMIN_GRANTED': 'bg-purple-100 text-purple-900 border-purple-200',
      'ADMIN_REVOKED': 'bg-orange-100 text-orange-900 border-orange-200',
      'ADMIN_LOGIN': 'bg-blue-100 text-blue-900 border-blue-200',
    };
    
    return (
      <Badge className={`flex items-center gap-1 font-semibold border ${badgeColors[action] || 'bg-gray-100 text-gray-900 border-gray-200'}`}>
        {icon}
        {label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <AdminGuard>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Activity Logs</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            View all administrative actions performed in the system
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">Recent Activity</CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">Track all changes made by administrators</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search activities..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  {uniqueActions.map(action => (
                    <SelectItem key={action} value={action}>
                      {ACTION_LABELS[action] || action}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={adminFilter} onValueChange={setAdminFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by admin" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Admins</SelectItem>
                  {uniqueAdmins.map(admin => (
                    <SelectItem key={admin} value={admin}>{admin}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="50">Last 50</SelectItem>
                  <SelectItem value="100">Last 100</SelectItem>
                  <SelectItem value="200">Last 200</SelectItem>
                  <SelectItem value="500">Last 500</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-800">
                  <TableRow className="border-b border-gray-200 dark:border-gray-700">
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</TableHead>
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</TableHead>
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">Action</TableHead>
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">Target</TableHead>
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">Details</TableHead>
                    <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredActivities.map((activity) => (
                    <TableRow key={activity.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      <TableCell className="whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {format(new Date(activity.created_at), 'MMM d, yyyy HH:mm:ss')}
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold text-gray-900 dark:text-white">{activity.admin_username}</div>
                      </TableCell>
                      <TableCell>{getActionBadge(activity.action)}</TableCell>
                      <TableCell>
                        {activity.target_type && activity.target_id && (
                          <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                            {activity.target_type} #{activity.target_id}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-md">
                        {activity.details && (
                          <span className="text-sm text-gray-600 dark:text-gray-400 truncate block">
                            {activity.details}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {activity.ip_address && (
                          <code className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-2 py-1 rounded font-mono">
                            {activity.ip_address}
                          </code>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {filteredActivities.length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                <p className="font-medium">No activity logs found matching your filters</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminGuard>
  );
}