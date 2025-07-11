import { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  Key, 
  Shield,
  Smartphone,
  Monitor
} from 'lucide-react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';

interface PasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export function UserSecuritySettings() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [passwords, setPasswords] = useState<PasswordForm>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    // Client-side validation
    if (passwords.new_password !== passwords.confirm_password) {
      setError('New passwords do not match');
      setLoading(false);
      return;
    }

    if (passwords.new_password.length < 8) {
      setError('New password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    try {
      await api.put('/user/security/password', passwords);
      setSuccess('Password changed successfully. Please log in again.');
      
      // Clear form
      setPasswords({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      
      // Log out user after password change
      setTimeout(() => {
        logout();
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSessions = async () => {
    if (!confirm('This will log you out of all devices. Continue?')) return;

    setLoading(true);
    setError(null);

    try {
      await api.post('/user/security/sessions/clear');
      setSuccess('All sessions cleared. Logging out...');
      
      setTimeout(() => {
        logout();
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear sessions');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Security Settings</h2>
        <p className="mt-1 text-sm text-gray-600">
          Manage your account security and authentication
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

      {/* Change Password Section */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Key className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Change Password</h3>
        </div>
        
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords.current ? 'text' : 'password'}
                value={passwords.current_password}
                onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })}
                required
                disabled={loading}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
              >
                {showPasswords.current ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords.new ? 'text' : 'password'}
                value={passwords.new_password}
                onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}
                required
                minLength={8}
                disabled={loading}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
              >
                {showPasswords.new ? 'Hide' : 'Show'}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Must be at least 8 characters long
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm New Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords.confirm ? 'text' : 'password'}
                value={passwords.confirm_password}
                onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })}
                required
                disabled={loading}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
              >
                {showPasswords.confirm ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Changing Password...
              </>
            ) : (
              'Change Password'
            )}
          </Button>
        </form>
      </div>

      {/* Two-Factor Authentication Section */}
      <div className="mb-8 pb-8 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Smartphone className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h3>
          </div>
          <span className="text-sm text-gray-500">Coming Soon</span>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Add an extra layer of security to your account by enabling two-factor authentication.
        </p>
        <Button variant="outline" disabled>
          Enable 2FA
        </Button>
      </div>

      {/* Active Sessions Section */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Monitor className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Active Sessions</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Manage your active sessions across all devices. If you notice any suspicious activity,
          you can sign out of all devices.
        </p>
        <Button 
          variant="outline" 
          onClick={handleClearSessions}
          disabled={loading}
          className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300"
        >
          Sign Out All Devices
        </Button>
      </div>

      {/* Security Tips */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-start">
          <Shield className="h-5 w-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">Security Tips</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Use a unique password that you don't use on other sites</li>
              <li>• Enable two-factor authentication when available</li>
              <li>• Regularly review your active sessions</li>
              <li>• Never share your password with anyone</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}