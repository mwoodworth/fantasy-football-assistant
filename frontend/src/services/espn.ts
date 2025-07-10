/**
 * ESPN Integration Service
 * Handles all ESPN-related API calls for league management and draft assistance
 */

import { api } from './api';

// Types
export interface ESPNLeague {
  id: number;
  espn_league_id: number;
  season: number;
  league_name: string;
  is_active: boolean;
  is_archived: boolean;
  team_count: number;
  scoring_type: string;
  draft_date?: string;
  draft_completed: boolean;
  user_draft_position?: number;
  sync_status: string;
  last_sync?: string;
  user_team_name?: string;
  league_type_description: string;
  espn_s2?: string;
  swid?: string;
}

export interface LeagueConnection {
  espn_league_id: number;
  season: number;
  league_name?: string;
  espn_s2?: string;
  swid?: string;
  user_team_id?: number;
}

export interface DraftSession {
  id: number;
  session_token: string;
  league_id: number;
  current_pick: number;
  current_round: number;
  user_pick_position: number;
  is_active: boolean;
  is_live_synced: boolean;
  next_user_pick: number;
  picks_until_user_turn: number;
  total_picks: number;
  drafted_players?: any[];
  user_roster?: any[];
  started_at: string;
  league?: ESPNLeague;
}

export interface DraftSessionStart {
  league_id: number;
  draft_position: number;
  live_sync: boolean;
}

export interface PlayerRecommendation {
  player_id: number;
  name: string;
  position: string;
  team: string;
  projected_points?: number;
  vor?: number;
  score: number;
  tier?: number;
  adp?: number;
  reasoning: string;
}

export interface DraftRecommendation {
  id: number;
  pick_number: number;
  round_number: number;
  recommended_players: PlayerRecommendation[];
  primary_recommendation: PlayerRecommendation;
  strategy_reasoning: string;
  confidence_score: number;
  recommendation_type: string;
  ai_insights: string[];
  next_pick_strategy: string;
  available_player_count: number;
  generated_at: string;
}

export interface DraftPick {
  player_id: number;
  player_name: string;
  position: string;
  team: string;
  pick_number: number;
  drafted_by_user: boolean;
}

export interface AdminSettings {
  max_leagues_per_user: number;
  allow_historical_access: boolean;
  historical_years_limit: number;
  auto_archive_old_seasons: boolean;
  require_league_verification: boolean;
}

// ESPN API Service
class ESPNService {
  
  // League Management
  async getMyLeagues(includeArchived = false, season?: number): Promise<ESPNLeague[]> {
    const params = new URLSearchParams();
    if (includeArchived) params.append('include_archived', 'true');
    if (season) params.append('season', season.toString());
    
    const response = await api.get(`/espn/my-leagues?${params.toString()}`);
    return response.data;
  }

  async connectLeague(connection: LeagueConnection): Promise<{ message: string; league_id: number; league_name: string; scoring_type: string }> {
    const response = await api.post('/espn/connect-league', connection);
    return response.data;
  }

  async disconnectLeague(leagueId: number): Promise<{ message: string }> {
    const response = await api.delete(`/espn/leagues/${leagueId}`);
    return response.data;
  }

  async permanentlyDeleteLeague(leagueId: number): Promise<{ message: string }> {
    const response = await api.delete(`/espn/leagues/${leagueId}/permanent`);
    return response.data;
  }

  async unarchiveLeague(leagueId: number): Promise<{ message: string; league_id: number; league_name: string }> {
    const response = await api.put(`/espn/leagues/${leagueId}/unarchive`);
    return response.data;
  }

  async updateESPNCookies(leagueId: number, espnS2: string, swid: string): Promise<{ message: string; league_id: number; validation_status: string }> {
    const response = await api.put(`/espn/leagues/${leagueId}/update-cookies`, {
      espn_s2: espnS2,
      swid: swid
    });
    return response.data;
  }

  // Admin Settings
  async getAdminSettings(): Promise<AdminSettings> {
    const response = await api.get('/espn/admin/settings');
    return response.data;
  }

  async updateAdminSettings(settings: Partial<AdminSettings>): Promise<{ message: string }> {
    const response = await api.post('/espn/admin/settings', settings);
    return response.data;
  }

  // Draft Session Management
  async startDraftSession(draftData: DraftSessionStart): Promise<DraftSession> {
    const response = await api.post('/espn/draft/start', draftData);
    return response.data;
  }

  async getDraftRecommendations(sessionId: number): Promise<DraftRecommendation> {
    const response = await api.get(`/espn/draft/${sessionId}/recommendations`);
    return response.data;
  }

  async recordDraftPick(sessionId: number, pick: DraftPick): Promise<{ message: string; draft_complete: boolean }> {
    const response = await api.post(`/espn/draft/${sessionId}/pick`, pick);
    return response.data;
  }

  // Helper methods
  validateLeagueId(leagueId: string): boolean {
    return /^\d+$/.test(leagueId) && parseInt(leagueId) > 0;
  }

  validateSeason(season: number): boolean {
    const currentYear = new Date().getFullYear();
    return season >= 2020 && season <= currentYear + 1;
  }

  formatScoreType(scoringType: string): string {
    const types: Record<string, string> = {
      'standard': 'Standard',
      'ppr': 'PPR',
      'half_ppr': 'Half PPR',
      'superflex': 'Superflex',
      'dynasty': 'Dynasty'
    };
    return types[scoringType] || scoringType;
  }

  formatSyncStatus(status: string): { text: string; color: 'success' | 'warning' | 'error' | 'secondary' | 'default' } {
    const statuses: Record<string, { text: string; color: 'success' | 'warning' | 'error' | 'secondary' | 'default' }> = {
      'active': { text: 'Active', color: 'success' },
      'syncing': { text: 'Syncing...', color: 'warning' },
      'error': { text: 'Sync Error', color: 'error' },
      'paused': { text: 'Paused', color: 'secondary' },
      'disabled': { text: 'Disabled', color: 'secondary' }
    };
    return statuses[status] || { text: status, color: 'secondary' };
  }
}

export const espnService = new ESPNService();