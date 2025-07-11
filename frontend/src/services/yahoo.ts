import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Types for Yahoo Fantasy data
export interface YahooAuthStatus {
  authenticated: boolean;
  user_id: number;
}

export interface YahooLeague {
  league_key: string;
  league_id: string;
  name: string;
  season: number;
  num_teams: number;
  scoring_type: string;
  draft_status: string;
  current_week: number;
  user_team?: YahooTeam;
  teams?: YahooTeam[];
}

export interface YahooTeam {
  team_key: string;
  team_id: number;
  name: string;
  manager_name?: string;
  logo_url?: string;
  rank?: number;
  points_for?: number;
  points_against?: number;
  wins?: number;
  losses?: number;
  ties?: number;
  is_owned_by_current_login?: boolean;
}

export interface YahooPlayer {
  player_id: string;
  name: string;
  first_name: string;
  last_name: string;
  position: string;
  team: string;
  bye_week: number;
  status: string;
  injury_status?: string;
  ownership: {
    percentage_owned: number;
    change: number;
  };
  points: {
    total: number;
    average: number;
  };
  projections: {
    season: number;
    week: number;
  };
  source: 'yahoo';
}

export interface YahooTransaction {
  transaction_key: string;
  type: string;
  status: string;
  timestamp: number;
  players?: YahooPlayer[];
}

// Yahoo Fantasy API service
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
  }
};