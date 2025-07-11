import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useAuthStore } from './store/useAuthStore';
import { queryErrorHandler, setupGlobalErrorHandlers, shouldRetryRequest } from './utils/errorHandler';

// Pages
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { PlayersPageEnhanced } from './pages/PlayersPageEnhanced';
import { PlayerDetailPage } from './pages/PlayerDetailPage';
import { TeamsPage } from './pages/TeamsPage';
import { ESPNLeaguesPage } from './pages/ESPNLeaguesPage';
import { YahooLeaguesPage } from './pages/YahooLeaguesPage';
import { YahooDraftRoomPage } from './pages/YahooDraftRoomPage';
import { DraftRoomPage } from './pages/DraftRoomPage';
import { DraftTest } from './pages/DraftTest';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AdminDashboard } from './pages/AdminDashboard';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AdminActivityPage } from './pages/AdminActivityPage';
import { AdminSettingsPage } from './pages/AdminSettingsPage';

// Components
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AdminLayout } from './components/admin/AdminLayout';
import { AdminGuard } from './components/auth/AdminGuard';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: shouldRetryRequest,
      onError: queryErrorHandler,
    },
    mutations: {
      onError: queryErrorHandler,
    },
  },
});

// Setup global error handlers
setupGlobalErrorHandlers();

function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="players" element={<PlayersPageEnhanced />} />
            <Route path="players/:playerId" element={<PlayerDetailPage />} />
            <Route path="teams" element={<TeamsPage />} />
            <Route path="espn/leagues" element={<ESPNLeaguesPage />} />
            <Route path="yahoo/leagues" element={<YahooLeaguesPage />} />
            <Route path="yahoo/draft/:leagueKey" element={<YahooDraftRoomPage />} />
            <Route path="espn/draft/:sessionId" element={<DraftRoomPage />} />
            <Route path="draft-test" element={<DraftTest />} />
            <Route path="ai-assistant" element={<AIAssistantPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
          </Route>

          {/* Admin routes with separate layout */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminGuard>
                  <AdminLayout />
                </AdminGuard>
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminDashboard />} />
            <Route path="users" element={<AdminUsersPage />} />
            <Route path="activity" element={<AdminActivityPage />} />
            <Route path="settings" element={<AdminSettingsPage />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;