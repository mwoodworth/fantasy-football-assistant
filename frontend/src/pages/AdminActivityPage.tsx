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
  'USER_CREATED': <User className="h-4 w-4 text-green-600" />,
  'USER_UPDATED': <Edit className="h-4 w-4 text-blue-600" />,
  'USER_SUSPENDED': <Ban className="h-4 w-4 text-red-600" />,
  'USER_ACTIVATED': <CheckCircle className="h-4 w-4 text-green-600" />,
  'USER_DELETED': <Trash className="h-4 w-4 text-red-600" />,
  'ADMIN_GRANTED': <Shield className="h-4 w-4 text-purple-600" />,
  'ADMIN_REVOKED': <Shield className="h-4 w-4 text-orange-600" />,
  'ADMIN_LOGIN': <User className="h-4 w-4 text-blue-600" />,
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
    const icon = ACTION_ICONS[action] || <Activity className="h-4 w-4" />;
    const label = ACTION_LABELS[action] || action;
    
    return (
      <Badge variant="outline" className="flex items-center gap-1">
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
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Admin Activity Log</CardTitle>
            <CardDescription>View all administrative actions performed in the system</CardDescription>
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

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Admin</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredActivities.map((activity) => (
                    <TableRow key={activity.id}>
                      <TableCell className="whitespace-nowrap">
                        {format(new Date(activity.created_at), 'MMM d, yyyy HH:mm:ss')}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{activity.admin_username}</div>
                      </TableCell>
                      <TableCell>{getActionBadge(activity.action)}</TableCell>
                      <TableCell>
                        {activity.target_type && activity.target_id && (
                          <span className="text-sm text-muted-foreground">
                            {activity.target_type} #{activity.target_id}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-md">
                        {activity.details && (
                          <span className="text-sm text-muted-foreground truncate block">
                            {activity.details}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {activity.ip_address && (
                          <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
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
              <div className="text-center py-8 text-muted-foreground">
                No activity logs found matching your filters.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminGuard>
  );
}