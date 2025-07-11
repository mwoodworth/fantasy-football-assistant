import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  User, 
  Shield, 
  Link2, 
  Lock,
  Settings,
  ChevronLeft
} from 'lucide-react';
import { cn } from '../../utils/cn';

const navigation = [
  { name: 'Profile', href: '/settings/profile', icon: User },
  { name: 'Preferences', href: '/settings/preferences', icon: Settings },
  { name: 'Security', href: '/settings/security', icon: Shield },
  { name: 'Connected Accounts', href: '/settings/accounts', icon: Link2 },
  { name: 'Privacy', href: '/settings/privacy', icon: Lock },
];

export function SettingsLayout() {
  const location = useLocation();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link 
          to="/dashboard" 
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Account Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Sidebar */}
        <div className="col-span-12 md:col-span-3">
          <nav className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    isActive
                      ? 'bg-primary-50 text-primary-700 border-primary-500'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-transparent',
                    'group flex items-center px-3 py-2 text-sm font-medium border-l-4 transition-colors'
                  )}
                >
                  <item.icon
                    className={cn(
                      isActive
                        ? 'text-primary-600'
                        : 'text-gray-400 group-hover:text-gray-500',
                      'mr-3 h-5 w-5 flex-shrink-0'
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Main content */}
        <div className="col-span-12 md:col-span-9">
          <div className="bg-white shadow rounded-lg">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}