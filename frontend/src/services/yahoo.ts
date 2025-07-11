import axios from 'axios';
import type { 
  YahooAuthStatus, 
  YahooLeague, 
  YahooTeam, 
  YahooPlayer, 
  YahooTransaction,
  YahooDraftSession,
  YahooDraftRecommendation,
  YahooDraftStatus
} from './yahooTypes';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Yahoo service object
export const yahooService = {
  // Authentication
  async getAuthUrl(): Promise<{ auth_url: string; state: string }> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/auth/url`);
    return response.data;
  },

  async getAuthStatus(): Promise<YahooAuthStatus> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/auth/status`);
    return response.data;
  },

  async disconnect(): Promise<{ message: string }> {
    const response = await axios.post(`${API_BASE_URL}/yahoo/auth/disconnect`);
    return response.data;
  },

  // Leagues
  async getLeagues(): Promise<YahooLeague[]> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/leagues`);
    return response.data;
  },

  async getLeagueDetails(leagueKey: string): Promise<{
    league: YahooLeague;
    teams: YahooTeam[];
    transactions: YahooTransaction[];
  }> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/leagues/${leagueKey}`);
    return response.data;
  },

  async getLeagueTeams(leagueKey: string): Promise<YahooTeam[]> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/leagues/${leagueKey}/teams`);
    return response.data;
  },

  async syncLeague(leagueKey: string): Promise<{
    success: boolean;
    league_name?: string;
    teams_synced?: number;
    draft_picks_synced?: number;
    error?: string;
  }> {
    const response = await axios.post(`${API_BASE_URL}/yahoo/leagues/${leagueKey}/sync`);
    return response.data;
  },

  // Teams
  async getTeamRoster(teamKey: string): Promise<YahooPlayer[]> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/teams/${teamKey}/roster`);
    return response.data;
  },

  // Players
  async searchPlayers(
    leagueKey: string,
    query: string,
    position?: string
  ): Promise<YahooPlayer[]> {
    const params = new URLSearchParams({ q: query });
    if (position) params.append('position', position);
    
    const response = await axios.get(
      `${API_BASE_URL}/yahoo/leagues/${leagueKey}/players/search?${params}`
    );
    return response.data;
  },

  async getFreeAgents(
    leagueKey: string,
    position?: string
  ): Promise<YahooPlayer[]> {
    const params = new URLSearchParams();
    if (position) params.append('position', position);
    
    const response = await axios.get(
      `${API_BASE_URL}/yahoo/leagues/${leagueKey}/free-agents?${params}`
    );
    return response.data;
  },

  // Transactions
  async getLeagueTransactions(
    leagueKey: string,
    types?: string[]
  ): Promise<YahooTransaction[]> {
    const params = new URLSearchParams();
    if (types?.length) params.append('types', types.join(','));
    
    const response = await axios.get(
      `${API_BASE_URL}/yahoo/leagues/${leagueKey}/transactions?${params}`
    );
    return response.data;
  },

  // Draft
  async getDraftResults(leagueKey: string): Promise<any[]> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/leagues/${leagueKey}/draft`);
    return response.data;
  },

  // Live Draft
  async startDraftSession(
    leagueKey: string, 
    draftPosition: number
  ): Promise<YahooDraftSession> {
    const response = await axios.post(`${API_BASE_URL}/yahoo/draft/start`, {
      league_key: leagueKey,
      draft_position: draftPosition
    });
    return response.data;
  },

  async getDraftSession(sessionId: number): Promise<YahooDraftSession> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/draft/session/${sessionId}`);
    return response.data;
  },

  async getDraftRecommendations(
    sessionId: number,
    forceRefresh: boolean = false
  ): Promise<YahooDraftRecommendation> {
    const params = new URLSearchParams();
    if (forceRefresh) params.append('force_refresh', 'true');
    
    const response = await axios.get(
      `${API_BASE_URL}/yahoo/draft/${sessionId}/recommendations?${params}`
    );
    return response.data;
  },

  async getLiveDraftStatus(sessionId: number): Promise<YahooDraftStatus> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/draft/${sessionId}/live-status`);
    return response.data;
  },

  async toggleDraftSync(sessionId: number, enable: boolean): Promise<{ sync_enabled: boolean; message: string }> {
    const response = await axios.post(`${API_BASE_URL}/yahoo/draft/${sessionId}/toggle-sync`, {
      enable
    });
    return response.data;
  },

  async syncDraft(sessionId: number): Promise<{
    success: boolean;
    current_pick: number;
    current_round: number;
    total_picks: number;
    message: string;
  }> {
    const response = await axios.post(`${API_BASE_URL}/yahoo/draft/${sessionId}/sync`);
    return response.data;
  },

  async getDraftStatus(sessionId: number): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/yahoo/draft/${sessionId}/status`);
    return response.data;
  },

  async endDraftSession(sessionId: number): Promise<{ message: string; session_id: number; total_picks: number }> {
    const response = await axios.delete(`${API_BASE_URL}/yahoo/draft/${sessionId}`);
    return response.data;
  }
};