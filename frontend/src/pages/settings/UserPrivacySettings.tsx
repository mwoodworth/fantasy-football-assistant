import { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  Eye,
  EyeOff,
  Users,
  FileText,
  Download,
  Trash2
} from 'lucide-react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';

interface PrivacySettings {
  profile_visibility: 'public' | 'friends' | 'private';
  show_email: boolean;
  show_leagues: boolean;
  show_trade_history: boolean;
  allow_friend_requests: boolean;
  data_sharing: boolean;
}

export function UserPrivacySettings() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [settings, setSettings] = useState<PrivacySettings>({
    profile_visibility: 'friends',
    show_email: false,
    show_leagues: true,
    show_trade_history: true,
    allow_friend_requests: true,
    data_sharing: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await api.put('/user/privacy', settings);
      setSuccess('Privacy settings updated successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update privacy settings');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/user/data-export', { responseType: 'blob' });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fantasy-football-data-${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Data exported successfully');
    } catch (err: any) {
      setError('Failed to export data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmText = prompt(
      'This action cannot be undone. Type "DELETE" to permanently delete your account:'
    );
    
    if (confirmText !== 'DELETE') return;

    setDeletingAccount(true);
    setError(null);

    try {
      await api.delete('/user/account');
      logout();
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete account');
      setDeletingAccount(false);
    }
  };

  return (
    <div className="p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Privacy Settings</h2>
        <p className="mt-1 text-sm text-gray-600">
          Control your privacy and data sharing preferences
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

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Profile Visibility */}
        <div>
          <div className="flex items-center mb-4">
            <Eye className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Profile Visibility</h3>
          </div>
          <div className="space-y-3 ml-7">
            <label className="flex items-start">
              <input
                type="radio"
                name="visibility"
                className="mt-1 text-primary-600 focus:ring-primary-500"
                checked={settings.profile_visibility === 'public'}
                onChange={() => setSettings({ ...settings, profile_visibility: 'public' })}
              />
              <div className="ml-3">
                <span className="block text-sm font-medium text-gray-700">Public</span>
                <span className="block text-sm text-gray-500">Anyone can view your profile</span>
              </div>
            </label>
            <label className="flex items-start">
              <input
                type="radio"
                name="visibility"
                className="mt-1 text-primary-600 focus:ring-primary-500"
                checked={settings.profile_visibility === 'friends'}
                onChange={() => setSettings({ ...settings, profile_visibility: 'friends' })}
              />
              <div className="ml-3">
                <span className="block text-sm font-medium text-gray-700">Friends Only</span>
                <span className="block text-sm text-gray-500">Only friends can view your profile</span>
              </div>
            </label>
            <label className="flex items-start">
              <input
                type="radio"
                name="visibility"
                className="mt-1 text-primary-600 focus:ring-primary-500"
                checked={settings.profile_visibility === 'private'}
                onChange={() => setSettings({ ...settings, profile_visibility: 'private' })}
              />
              <div className="ml-3">
                <span className="block text-sm font-medium text-gray-700">Private</span>
                <span className="block text-sm text-gray-500">No one can view your profile</span>
              </div>
            </label>
          </div>
        </div>

        {/* Information Sharing */}
        <div className="border-t pt-6">
          <div className="flex items-center mb-4">
            <Users className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Information Sharing</h3>
          </div>
          <div className="space-y-3 ml-7">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.show_email}
                onChange={(e) => setSettings({ ...settings, show_email: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">
                Show email address on profile
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.show_leagues}
                onChange={(e) => setSettings({ ...settings, show_leagues: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">
                Show leagues I'm participating in
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.show_trade_history}
                onChange={(e) => setSettings({ ...settings, show_trade_history: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">
                Show trade history
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.allow_friend_requests}
                onChange={(e) => setSettings({ ...settings, allow_friend_requests: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">
                Allow friend requests
              </span>
            </label>
          </div>
        </div>

        {/* Data Usage */}
        <div className="border-t pt-6">
          <div className="flex items-center mb-4">
            <FileText className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Data Usage</h3>
          </div>
          <div className="space-y-3 ml-7">
            <label className="flex items-start">
              <input
                type="checkbox"
                className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.data_sharing}
                onChange={(e) => setSettings({ ...settings, data_sharing: e.target.checked })}
              />
              <div className="ml-3">
                <span className="block text-sm font-medium text-gray-700">
                  Share usage data for improvement
                </span>
                <span className="block text-sm text-gray-500">
                  Help us improve the app by sharing anonymous usage statistics
                </span>
              </div>
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Privacy Settings'
            )}
          </Button>
        </div>
      </form>

      {/* Data Management */}
      <div className="mt-8 pt-8 border-t">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Data Management</h3>
        
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Export Your Data</h4>
              <p className="text-sm text-gray-600 mt-1">
                Download a copy of all your data in JSON format
              </p>
            </div>
            <Button 
              variant="outline" 
              onClick={handleExportData}
              disabled={loading}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
          </div>

          <div className="flex items-start justify-between pt-4 border-t">
            <div>
              <h4 className="text-sm font-medium text-red-600">Delete Account</h4>
              <p className="text-sm text-gray-600 mt-1">
                Permanently delete your account and all associated data
              </p>
            </div>
            <Button 
              variant="outline" 
              onClick={handleDeleteAccount}
              disabled={deletingAccount}
              className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300"
            >
              {deletingAccount ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Account
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="mt-8 bg-gray-50 rounded-lg p-4">
        <div className="flex items-start">
          <EyeOff className="h-5 w-5 text-gray-600 mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-1">Privacy Notice</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• We never sell your personal data to third parties</li>
              <li>• Your data is encrypted in transit and at rest</li>
              <li>• You can export or delete your data at any time</li>
              <li>• Changes may take up to 24 hours to take effect</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}