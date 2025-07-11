import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Loader2, 
  Save, 
  AlertCircle, 
  RefreshCw,
  Database,
  Activity,
  Shield,
  Settings,
  Check
} from 'lucide-react';
import api from '../services/api';
import { AdminGuard } from '../components/auth/AdminGuard';

interface SystemSettings {
  draft_monitor_interval: number;
  live_monitor_interval: number;
  disable_espn_sync_logs: boolean;
  log_level: string;
  cache_expire_time: number;
  rate_limit_default: number;
  rate_limit_espn: number;
  rate_limit_ai: number;
}

export function AdminSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [activeTab, setActiveTab] = useState('general');
  const [maintenanceAction, setMaintenanceAction] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/settings');
      setSettings(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch system settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;
    
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      await api.put('/admin/settings', settings);
      setSuccess('Settings saved successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSettingChange = (key: keyof SystemSettings, value: any) => {
    if (settings) {
      setSettings({
        ...settings,
        [key]: value
      });
    }
  };

  const performMaintenanceAction = async (action: string) => {
    try {
      setMaintenanceAction(action);
      setError(null);
      setSuccess(null);
      
      const response = await api.post(`/admin/maintenance/${action}`);
      setSuccess(response.data.message || `${action} completed successfully`);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to perform ${action}`);
    } finally {
      setMaintenanceAction(null);
    }
  };

  if (loading) {
    return (
      <AdminGuard requireSuperAdmin>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard requireSuperAdmin>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Settings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Configure system-wide settings and perform maintenance tasks
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-6 bg-emerald-50 border-emerald-200 dark:bg-emerald-950 dark:border-emerald-800">
            <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <AlertDescription className="text-emerald-800 dark:text-emerald-200">{success}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            <TabsTrigger 
              value="general" 
              className="text-gray-700 dark:text-gray-300 font-medium data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-white"
            >
              General
            </TabsTrigger>
            <TabsTrigger 
              value="monitoring" 
              className="text-gray-700 dark:text-gray-300 font-medium data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-white"
            >
              Monitoring
            </TabsTrigger>
            <TabsTrigger 
              value="rate-limits" 
              className="text-gray-700 dark:text-gray-300 font-medium data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-white"
            >
              Rate Limits
            </TabsTrigger>
            <TabsTrigger 
              value="maintenance" 
              className="text-gray-700 dark:text-gray-300 font-medium data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-white"
            >
              Maintenance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">General Settings</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">Configure general system settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">Log Level</label>
                  <Select 
                    value={settings?.log_level || 'INFO'} 
                    onValueChange={(value) => handleSettingChange('log_level', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DEBUG">DEBUG</SelectItem>
                      <SelectItem value="INFO">INFO</SelectItem>
                      <SelectItem value="WARNING">WARNING</SelectItem>
                      <SelectItem value="ERROR">ERROR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    Cache Expire Time (seconds)
                  </label>
                  <Input
                    type="number"
                    value={settings?.cache_expire_time || 3600}
                    onChange={(e) => handleSettingChange('cache_expire_time', parseInt(e.target.value))}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    How long to cache data before refreshing
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monitoring" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">Monitoring Settings</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">Configure data monitoring intervals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    Draft Monitor Interval (seconds)
                  </label>
                  <Input
                    type="number"
                    value={settings?.draft_monitor_interval || 60}
                    onChange={(e) => handleSettingChange('draft_monitor_interval', parseInt(e.target.value))}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    How often to check for draft updates
                  </p>
                </div>

                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    Live Monitor Interval (seconds)
                  </label>
                  <Input
                    type="number"
                    value={settings?.live_monitor_interval || 300}
                    onChange={(e) => handleSettingChange('live_monitor_interval', parseInt(e.target.value))}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    How often to check for live game updates
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="disable-espn-logs"
                    checked={settings?.disable_espn_sync_logs || false}
                    onChange={(e) => handleSettingChange('disable_espn_sync_logs', e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <label htmlFor="disable-espn-logs" className="text-sm font-semibold text-gray-900 dark:text-white">
                    Disable ESPN Sync Logs
                  </label>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rate-limits" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">Rate Limiting</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">Configure API rate limits</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    Default Rate Limit (requests/minute)
                  </label>
                  <Input
                    type="number"
                    value={settings?.rate_limit_default || 60}
                    onChange={(e) => handleSettingChange('rate_limit_default', parseInt(e.target.value))}
                  />
                </div>

                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    ESPN API Rate Limit (requests/minute)
                  </label>
                  <Input
                    type="number"
                    value={settings?.rate_limit_espn || 10}
                    onChange={(e) => handleSettingChange('rate_limit_espn', parseInt(e.target.value))}
                  />
                </div>

                <div>
                  <label className="text-sm font-semibold text-gray-900 dark:text-white mb-2 block">
                    AI API Rate Limit (requests/hour)
                  </label>
                  <Input
                    type="number"
                    value={settings?.rate_limit_ai || 20}
                    onChange={(e) => handleSettingChange('rate_limit_ai', parseInt(e.target.value))}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="maintenance" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">Maintenance Tasks</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">Perform system maintenance operations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800 mb-4">
                  <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                    These maintenance tasks help keep your system running smoothly. Each task runs in the background without affecting users.
                  </p>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <Button 
                    onClick={() => performMaintenanceAction('clear-cache')}
                    disabled={maintenanceAction === 'clear-cache'}
                    variant="outline"
                    className="border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-white font-medium"
                  >
                    {maintenanceAction === 'clear-cache' ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Clear Cache
                  </Button>

                  <Button 
                    onClick={() => performMaintenanceAction('optimize-database')}
                    disabled={maintenanceAction === 'optimize-database'}
                    variant="outline"
                    className="border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-white font-medium"
                  >
                    {maintenanceAction === 'optimize-database' ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Database className="mr-2 h-4 w-4" />
                    )}
                    Optimize Database
                  </Button>

                  <Button 
                    onClick={() => performMaintenanceAction('clean-logs')}
                    disabled={maintenanceAction === 'clean-logs'}
                    variant="outline"
                    className="border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-white font-medium"
                  >
                    {maintenanceAction === 'clean-logs' ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Activity className="mr-2 h-4 w-4" />
                    )}
                    Clean Old Logs
                  </Button>

                  <Button 
                    onClick={() => performMaintenanceAction('reset-rate-limits')}
                    disabled={maintenanceAction === 'reset-rate-limits'}
                    variant="outline"
                    className="border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-white font-medium"
                  >
                    {maintenanceAction === 'reset-rate-limits' ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Shield className="mr-2 h-4 w-4" />
                    )}
                    Reset Rate Limits
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">System Information</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">Current system status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400 font-medium">Environment:</span>
                    <Badge className="bg-blue-100 text-blue-900 border border-blue-200 dark:bg-blue-950 dark:text-blue-100 dark:border-blue-800 font-semibold">Production</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400 font-medium">Database:</span>
                    <Badge className="bg-purple-100 text-purple-900 border border-purple-200 dark:bg-purple-950 dark:text-purple-100 dark:border-purple-800 font-semibold">SQLite</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400 font-medium">API Version:</span>
                    <Badge className="bg-emerald-100 text-emerald-900 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-100 dark:border-emerald-800 font-semibold">1.0.0</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="mt-8 flex justify-end">
          <Button 
            onClick={saveSettings} 
            disabled={saving || !settings}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6"
          >
            {saving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save Settings
          </Button>
        </div>
      </div>
    </AdminGuard>
  );
}