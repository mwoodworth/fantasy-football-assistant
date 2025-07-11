import { useState, useEffect } from 'react';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  Link2,
  Unlink,
  RefreshCw,
  Calendar
} from 'lucide-react';
import api from '../../services/api';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';

interface ConnectedAccount {
  provider: string;
  connected_at: string;
  account_email?: string;
  account_username?: string;
  last_sync?: string;
}

export function UserConnectedAccounts() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  useEffect(() => {
    fetchConnectedAccounts();
  }, []);

  const fetchConnectedAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/user/connected-accounts');
      setAccounts(response.data);
    } catch (err: any) {
      setError('Failed to load connected accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`Are you sure you want to disconnect your ${provider} account?`)) return;

    setDisconnecting(provider);
    setError(null);
    setSuccess(null);

    try {
      await api.delete(`/user/connected-accounts/${provider}`);
      setSuccess(`${provider} account disconnected successfully`);
      
      // Remove from local state
      setAccounts(accounts.filter(acc => acc.provider !== provider));
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to disconnect ${provider} account`);
    } finally {
      setDisconnecting(null);
    }
  };

  const handleConnect = (provider: string) => {
    if (provider === 'ESPN') {
      navigate('/espn/leagues');
    } else if (provider === 'Yahoo') {
      navigate('/yahoo/leagues');
    }
  };

  const getProviderIcon = (provider: string) => {
    // In a real app, you'd have provider-specific icons
    return (
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold
        ${provider === 'ESPN' ? 'bg-red-600' : 'bg-purple-600'}`}>
        {provider.charAt(0)}
      </div>
    );
  };

  const isConnected = (provider: string) => {
    return accounts.some(acc => acc.provider === provider);
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Connected Accounts</h2>
        <p className="mt-1 text-sm text-gray-600">
          Manage your connections to fantasy football platforms
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

      <div className="space-y-4">
        {/* ESPN Account */}
        <div className="border rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              {getProviderIcon('ESPN')}
              <div>
                <h3 className="text-lg font-medium text-gray-900">ESPN Fantasy</h3>
                {isConnected('ESPN') ? (
                  <>
                    <p className="text-sm text-gray-600 mt-1">
                      Connected leagues: {accounts.find(a => a.provider === 'ESPN')?.account_username}
                    </p>
                    {accounts.find(a => a.provider === 'ESPN')?.last_sync && (
                      <p className="text-xs text-gray-500 mt-1 flex items-center">
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Last synced: {format(new Date(accounts.find(a => a.provider === 'ESPN')!.last_sync!), 'MMM d, yyyy h:mm a')}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-gray-600 mt-1">
                    Connect your ESPN account to import leagues and track your teams
                  </p>
                )}
              </div>
            </div>
            
            <div>
              {isConnected('ESPN') ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDisconnect('ESPN')}
                  disabled={disconnecting === 'ESPN'}
                  className="text-red-600 hover:text-red-700"
                >
                  {disconnecting === 'ESPN' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Unlink className="h-4 w-4 mr-2" />
                      Disconnect
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => handleConnect('ESPN')}
                >
                  <Link2 className="h-4 w-4 mr-2" />
                  Connect
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Yahoo Account */}
        <div className="border rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              {getProviderIcon('Yahoo')}
              <div>
                <h3 className="text-lg font-medium text-gray-900">Yahoo Fantasy</h3>
                {isConnected('Yahoo') ? (
                  <>
                    <p className="text-sm text-gray-600 mt-1">
                      Account connected
                    </p>
                    {accounts.find(a => a.provider === 'Yahoo')?.connected_at && (
                      <p className="text-xs text-gray-500 mt-1 flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        Connected: {format(new Date(accounts.find(a => a.provider === 'Yahoo')!.connected_at), 'MMM d, yyyy')}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-gray-600 mt-1">
                    Connect your Yahoo account to import leagues and participate in drafts
                  </p>
                )}
              </div>
            </div>
            
            <div>
              {isConnected('Yahoo') ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDisconnect('Yahoo')}
                  disabled={disconnecting === 'Yahoo'}
                  className="text-red-600 hover:text-red-700"
                >
                  {disconnecting === 'Yahoo' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Unlink className="h-4 w-4 mr-2" />
                      Disconnect
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => handleConnect('Yahoo')}
                >
                  <Link2 className="h-4 w-4 mr-2" />
                  Connect
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Future Platforms */}
        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Coming Soon</h3>
          <div className="space-y-3">
            <div className="border border-gray-200 rounded-lg p-4 opacity-50">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">Sleeper</h4>
                  <p className="text-sm text-gray-600">Import leagues from Sleeper</p>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Coming Soon</span>
              </div>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4 opacity-50">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">NFL.com</h4>
                  <p className="text-sm text-gray-600">Connect your NFL Fantasy account</p>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Coming Soon</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">About Connected Accounts</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• We only access league and roster information</li>
              <li>• Your login credentials are never stored</li>
              <li>• You can disconnect accounts at any time</li>
              <li>• All data is synced securely and encrypted</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}