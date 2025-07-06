import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useAuthStore } from './store/useAuthStore';

// Pages
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { PlayersPage } from './pages/PlayersPage';
import { PlayerDetailPage } from './pages/PlayerDetailPage';
import { TeamsPage } from './pages/TeamsPage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

// Components
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

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
            <Route path="players" element={<PlayersPage />} />
            <Route path="players/:playerId" element={<PlayerDetailPage />} />
            <Route path="teams" element={<TeamsPage />} />
            <Route path="ai-assistant" element={<AIAssistantPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;