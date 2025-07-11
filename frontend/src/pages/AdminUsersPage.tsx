import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, Search, Shield, ShieldCheck, User, Ban, CheckCircle, AlertCircle, Edit } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { AdminGuard } from '../components/auth/AdminGuard';
import { format } from 'date-fns';

interface UserData {
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
  const { user: currentUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<UserData[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleSuspendUser = async (userId: number) => {
    try {
      setActionLoading(true);
      await api.post(`/admin/users/${userId}/suspend`);
      await fetchUsers();
      setShowEditDialog(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to suspend user');
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivateUser = async (userId: number) => {
    try {
      setActionLoading(true);
      await api.post(`/admin/users/${userId}/activate`);
      await fetchUsers();
      setShowEditDialog(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to activate user');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGrantAdmin = async (userId: number) => {
    try {
      setActionLoading(true);
      await api.post(`/admin/users/${userId}/grant-admin`);
      await fetchUsers();
      setShowEditDialog(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to grant admin privileges');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeAdmin = async (userId: number) => {
    try {
      setActionLoading(true);
      await api.post(`/admin/users/${userId}/revoke-admin`);
      await fetchUsers();
      setShowEditDialog(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revoke admin privileges');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.first_name && user.first_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (user.last_name && user.last_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus = 
      statusFilter === 'all' ||
      (statusFilter === 'active' && user.is_active) ||
      (statusFilter === 'suspended' && !user.is_active) ||
      (statusFilter === 'admin' && (user.is_admin || user.is_superadmin)) ||
      (statusFilter === 'premium' && user.is_premium);

    return matchesSearch && matchesStatus;
  });

  const getUserRole = (user: UserData) => {
    if (user.is_superadmin) return 'superadmin';
    if (user.is_admin) return 'admin';
    return 'user';
  };

  const getRoleBadge = (user: UserData) => {
    const role = getUserRole(user);
    switch (role) {
      case 'superadmin':
        return <Badge variant="destructive"><ShieldCheck className="w-3 h-3 mr-1" />Super Admin</Badge>;
      case 'admin':
        return <Badge variant="secondary"><Shield className="w-3 h-3 mr-1" />Admin</Badge>;
      default:
        return <Badge variant="outline"><User className="w-3 h-3 mr-1" />User</Badge>;
    }
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
            <CardTitle>User Management</CardTitle>
            <CardDescription>View and manage all system users</CardDescription>
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
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                  <SelectItem value="admin">Admins</SelectItem>
                  <SelectItem value="premium">Premium</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Premium</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{user.username}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                          {(user.first_name || user.last_name) && (
                            <div className="text-sm text-muted-foreground">
                              {user.first_name} {user.last_name}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{getRoleBadge(user)}</TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="success"><CheckCircle className="w-3 h-3 mr-1" />Active</Badge>
                        ) : (
                          <Badge variant="destructive"><Ban className="w-3 h-3 mr-1" />Suspended</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.is_premium ? (
                          <Badge variant="default">Premium</Badge>
                        ) : (
                          <Badge variant="outline">Free</Badge>
                        )}
                      </TableCell>
                      <TableCell>{format(new Date(user.created_at), 'MMM d, yyyy')}</TableCell>
                      <TableCell>
                        {user.last_login ? format(new Date(user.last_login), 'MMM d, yyyy') : 'Never'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedUser(user);
                            setShowEditDialog(true);
                          }}
                          disabled={user.id === currentUser?.id}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Manage User</DialogTitle>
              <DialogDescription>
                Update user settings for {selectedUser?.username}
              </DialogDescription>
            </DialogHeader>
            {selectedUser && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Account Status</h4>
                  {selectedUser.is_active ? (
                    <Button
                      variant="destructive"
                      onClick={() => handleSuspendUser(selectedUser.id)}
                      disabled={actionLoading}
                      className="w-full"
                    >
                      {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Ban className="h-4 w-4 mr-2" />}
                      Suspend User
                    </Button>
                  ) : (
                    <Button
                      variant="default"
                      onClick={() => handleActivateUser(selectedUser.id)}
                      disabled={actionLoading}
                      className="w-full"
                    >
                      {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                      Activate User
                    </Button>
                  )}
                </div>

                {currentUser?.is_superadmin && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Admin Privileges</h4>
                    {selectedUser.is_admin || selectedUser.is_superadmin ? (
                      <Button
                        variant="outline"
                        onClick={() => handleRevokeAdmin(selectedUser.id)}
                        disabled={actionLoading || selectedUser.is_superadmin}
                        className="w-full"
                      >
                        {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Shield className="h-4 w-4 mr-2" />}
                        Revoke Admin
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={() => handleGrantAdmin(selectedUser.id)}
                        disabled={actionLoading}
                        className="w-full"
                      >
                        {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Shield className="h-4 w-4 mr-2" />}
                        Grant Admin
                      </Button>
                    )}
                  </div>
                )}
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AdminGuard>
  );
}