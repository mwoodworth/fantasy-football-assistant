import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';
import { Loader2 } from 'lucide-react';

interface AdminGuardProps {
  children: React.ReactNode;
  requireSuperAdmin?: boolean;
}

export function AdminGuard({ children, requireSuperAdmin = false }: AdminGuardProps) {
  const { user, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Not logged in
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check for superadmin requirement
  if (requireSuperAdmin && !user.is_superadmin) {
    return <Navigate to="/dashboard" replace />;
  }

  // Check for admin access
  if (!user.is_admin && !user.is_superadmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}