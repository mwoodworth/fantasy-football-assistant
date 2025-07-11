import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  Settings, 
  Shield,
  ChevronRight,
  Home,
  LogOut
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';

const navigation = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'Activity', href: '/admin/activity', icon: Activity },
  { name: 'Settings', href: '/admin/settings', icon: Settings, superadminOnly: true },
];

export function AdminLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 dark:bg-black shadow-xl">
        <div className="flex h-full flex-col">
          {/* Logo/Header */}
          <div className="flex h-16 items-center px-6 bg-gradient-to-r from-indigo-600 to-purple-600">
            <Shield className="h-8 w-8 text-white" />
            <span className="ml-3 text-xl font-bold text-white">Admin Panel</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    isActive
                      ? 'bg-indigo-700 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                    'group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200'
                  )}
                >
                  <item.icon
                    className={cn(
                      isActive
                        ? 'text-white'
                        : 'text-gray-400 group-hover:text-white',
                      'mr-3 h-5 w-5 flex-shrink-0 transition-colors'
                    )}
                  />
                  {item.name}
                  {isActive && (
                    <ChevronRight className="ml-auto h-4 w-4" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Bottom section */}
          <div className="border-t border-gray-800 p-4">
            <Link
              to="/dashboard"
              className="flex items-center px-3 py-2.5 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
            >
              <Home className="mr-3 h-5 w-5 text-gray-400" />
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}