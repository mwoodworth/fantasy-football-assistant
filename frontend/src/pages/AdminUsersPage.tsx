import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Search, 
  Filter,
  MoreVertical,
  UserCheck,
  UserX,
  Shield,
  ShieldOff,
  Mail,
  Calendar,
  AlertCircle,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react';
import api from '../services/api';
import { format } from 'date-fns';
import { cn } from '../utils/cn';

interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_premium: boolean;
  is_admin: boolean;
  is_superadmin: boolean;
  created_at: string;
  last_login?: string;
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const usersPerPage = 10;

  useEffect(() => {
    fetchUsers();
  }, [search, statusFilter, roleFilter, currentPage]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params: any = {
        skip: (currentPage - 1) * usersPerPage,
        limit: usersPerPage,
      };
      
      if (search) params.search = search;
      if (statusFilter !== 'all') params.is_active = statusFilter === 'active';
      if (roleFilter === 'admin') params.is_admin = true;
      
      const response = await api.get('/admin/users', { params });
      setUsers(response.data);
      
      // Calculate total pages (would come from API in real implementation)
      setTotalPages(Math.ceil(response.data.length / usersPerPage));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId: number, action: string) => {
    try {
      setError(null);
      setSuccess(null);
      
      if (action === 'suspend') {
        await api.post(`/admin/users/${userId}/suspend`, { reason: 'Admin action' });
        setSuccess('User suspended successfully');
      } else if (action === 'activate') {
        await api.post(`/admin/users/${userId}/activate`);
        setSuccess('User activated successfully');
      } else if (action === 'grant-admin') {
        await api.post(`/admin/grant-admin/${userId}`);
        setSuccess('Admin privileges granted successfully');
      } else if (action === 'revoke-admin') {
        await api.post(`/admin/revoke-admin/${userId}`);
        setSuccess('Admin privileges revoked successfully');
      }
      
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${action} user`);
    }
  };

  const getRoleBadge = (user: User) => {
    if (user.is_superadmin) {
      return <Badge className="bg-purple-600 text-white font-semibold">Superadmin</Badge>;
    }
    if (user.is_admin) {
      return <Badge className="bg-blue-600 text-white font-semibold">Admin</Badge>;
    }
    if (user.is_premium) {
      return <Badge className="bg-emerald-600 text-white font-semibold">Premium</Badge>;
    }
    return <Badge className="bg-gray-500 text-white font-semibold">Regular</Badge>;
  };

  const getStatusBadge = (user: User) => {
    return user.is_active ? (
      <Badge className="bg-emerald-100 text-emerald-900 border border-emerald-200 font-semibold">
        <CheckCircle className="h-3 w-3 mr-1" />
        Active
      </Badge>
    ) : (
      <Badge className="bg-red-100 text-red-900 border border-red-200 font-semibold">
        <XCircle className="h-3 w-3 mr-1" />
        Suspended
      </Badge>
    );
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Management</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Manage user accounts, roles, and permissions
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Users</CardTitle>
              <CardDescription>View and manage user accounts</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                Export CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search by name, email, or username..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={(value) => {
              setStatusFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active Only</SelectItem>
                <SelectItem value="suspended">Suspended Only</SelectItem>
              </SelectContent>
            </Select>
            <Select value={roleFilter} onValueChange={(value) => {
              setRoleFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-[180px]">
                <Shield className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admins Only</SelectItem>
                <SelectItem value="premium">Premium Only</SelectItem>
                <SelectItem value="regular">Regular Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Active
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                              {user.username.charAt(0).toUpperCase()}
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {user.first_name && user.last_name
                                ? `${user.first_name} ${user.last_name}`
                                : user.username}
                            </div>
                            <div className="text-sm text-gray-500 flex items-center">
                              <Mail className="h-3 w-3 mr-1" />
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(user)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getRoleBadge(user)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          {format(new Date(user.created_at), 'MMM d, yyyy')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.last_login
                          ? format(new Date(user.last_login), 'MMM d, yyyy')
                          : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          {user.is_active ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleUserAction(user.id, 'suspend')}
                              className="border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300"
                            >
                              <UserX className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleUserAction(user.id, 'activate')}
                              className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:border-emerald-300"
                            >
                              <UserCheck className="h-4 w-4" />
                            </Button>
                          )}
                          
                          {!user.is_superadmin && (
                            <>
                              {user.is_admin ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleUserAction(user.id, 'revoke-admin')}
                                  className="border-orange-200 text-orange-700 hover:bg-orange-50 hover:border-orange-300"
                                >
                                  <ShieldOff className="h-4 w-4" />
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleUserAction(user.id, 'grant-admin')}
                                  className="border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300"
                                >
                                  <Shield className="h-4 w-4" />
                                </Button>
                              )}
                            </>
                          )}
                          
                          <Button size="sm" variant="ghost">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 px-2">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}