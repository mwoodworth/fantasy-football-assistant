/**
 * Teams Service
 * Handles all team-related API calls across platforms
 */

import { api } from './api';

// Types
export interface Team {
  id: string;
  name: string;
  league: string;
  platform: string;
  season?: number;
  record: string;
  points: number;
  rank: string;
  playoffs: boolean;
  active: boolean;
  espn_league_id?: number;
  user_team_id?: number;
  draft_completed?: boolean;
  scoring_type?: string;
}

export interface TeamDetail {
  id: string;
  name: string;
  league: string;
  platform: string;
  roster: Player[];
  recent_activity: Activity[];
  settings: TeamSettings;
}

export interface Player {
  id: number;
  name: string;
  position: string;
  team: string;
  status?: string;
  points?: number;
  projected_points?: number;
  injury_status?: string;
}

export interface Activity {
  type: string;
  description: string;
  timestamp?: string;
}

export interface TeamSettings {
  scoring_type?: string;
  team_count?: number;
  roster_positions?: Record<string, number>;
  season?: number;
  draft_completed?: boolean;
  wins?: number;
  losses?: number;
  points_for?: number;
  points_against?: number;
}

export interface WaiverTarget {
  player_id: number;
  name: string;
  position: string;
  team: string;
  ownership_percentage: number;
  recommendation_score: number;
  pickup_priority: string;
  suggested_faab_bid: number;
  analysis: string;
  trending_direction: 'up' | 'down' | 'stable';
  recent_performance: Record<string, number>;
  matchup_analysis: string;
  injury_status: string;
}

export interface TrendingPlayer {
  player_id: number;
  name: string;
  position: string;
  team: string;
  trend_type: 'most_added' | 'most_dropped';
  percentage_rostered: number;
  weekly_change: number;
  points_last_week: number;
  season_points: number;
}

export interface WaiverClaimRequest {
  team_id: string;
  player_to_add_id: number;
  player_to_drop_id?: number;
  faab_bid: number;
  waiver_priority: number;
  notes?: string;
}

export interface TradeProposal {
  team1_id: string;
  team1_players: Player[];
  team2_id: string;
  team2_players: Player[];
}

export interface TradeEvaluation {
  fairness_score: number;
  grade: string;
  team1_impact: {
    value_change: number;
    needs_improvement: Record<string, number>;
    recommendation: string;
  };
  team2_impact: {
    value_change: number;
    needs_improvement: Record<string, number>;
    recommendation: string;
  };
  analysis: string;
  verdict: 'accept' | 'reject' | 'consider';
}

export interface TradeTarget {
  player: Player;
  team_id: string;
  team_name: string;
  trade_value: number;
  likelihood: 'high' | 'medium' | 'low';
  suggested_offer: Player[];
  rationale: string;
}

// Teams API Service
class TeamsService {
  
  async getUserTeams(includeESPN = true, includeManual = true, season?: number): Promise<Team[]> {
    const params = new URLSearchParams();
    params.append('include_espn', includeESPN.toString());
    params.append('include_manual', includeManual.toString());
    if (season) params.append('season', season.toString());
    
    const response = await api.get(`/teams/?${params.toString()}`);
    return response.data;
  }

  async getTeamDetail(teamId: string): Promise<TeamDetail> {
    try {
      console.log('Requesting team detail for:', teamId);
      const response = await api.get(`/teams/${teamId}/`);
      console.log('Team detail response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching team detail:', error);
      throw error;
    }
  }

  async syncTeam(teamId: string): Promise<{ message: string; last_sync?: string }> {
    const response = await api.post(`/teams/${teamId}/sync/`);
    return response.data;
  }

  async getTeamDraftInfo(teamId: string): Promise<{
    league_id: number;
    league_name: string;
    draft_completed: boolean;
    draft_date?: string;
    can_start_draft: boolean;
  }> {
    const response = await api.get(`/teams/${teamId}/draft/`);
    return response.data;
  }

  async updateESPNCookies(leagueId: number, espnS2: string, swid: string): Promise<{
    message: string;
    league_id: number;
    validation_status: string;
  }> {
    const response = await api.put(`/espn/leagues/${leagueId}/update-cookies`, {
      espn_s2: espnS2,
      swid: swid
    });
    return response.data;
  }

  async getWaiverRecommendations(teamId: string): Promise<WaiverTarget[]> {
    const response = await api.post(`/teams/${teamId}/waiver-recommendations`);
    console.log('Waiver recommendations response:', response.data);
    return response.data.recommendations || [];
  }

  async getTrendingPlayers(leagueId: number): Promise<TrendingPlayer[]> {
    const response = await api.get(`/fantasy/waivers/${leagueId}/trending`);
    return response.data.players || [];
  }

  async submitWaiverClaim(claim: WaiverClaimRequest): Promise<{
    message: string;
    claim_id: number;
  }> {
    const response = await api.post('/fantasy/waivers/claims', claim);
    return response.data;
  }

  async evaluateTrade(proposal: TradeProposal): Promise<TradeEvaluation> {
    const response = await api.post('/fantasy/trades/evaluate', {
      team1_id: parseInt(proposal.team1_id.replace('espn_', '')),
      team1_sends: proposal.team1_players.map(p => p.id),
      team1_receives: proposal.team2_players.map(p => p.id),
      team2_id: parseInt(proposal.team2_id.replace('espn_', '')),
      team2_sends: proposal.team2_players.map(p => p.id),
      team2_receives: proposal.team1_players.map(p => p.id)
    });
    return response.data;
  }

  async getTradeTargets(teamId: string): Promise<TradeTarget[]> {
    const response = await api.post(`/teams/${teamId}/trade-targets`);
    console.log('Trade targets response:', response.data);
    return response.data.targets || [];
  }

  async refreshTradeTargets(teamId: string): Promise<{
    targets: TradeTarget[];
    refreshInfo: {
      refreshed: boolean;
      teams_synced: number;
      generated_at: string;
      expires_in_days: number;
    };
  }> {
    const response = await api.post(`/teams/${teamId}/trade-targets/refresh`);
    console.log('Refresh trade targets response:', response.data);
    return {
      targets: response.data.targets || [],
      refreshInfo: response.data.refresh_info || {}
    };
  }

  // Mock data for development/fallback
  private getMockTeams(): Team[] {
    return [
      {
        id: '1',
        name: 'Thunder Bolts',
        league: 'Championship League',
        platform: 'Manual',
        record: '8-5',
        points: 1247.8,
        rank: '2',
        playoffs: true,
        active: true
      },
      {
        id: '2',
        name: 'Fantasy Kings',
        league: 'Friends League',
        platform: 'Manual',
        record: '6-7',
        points: 1189.3,
        rank: '7',
        playoffs: false,
        active: true
      }
    ];
  }

  // Helper methods
  formatTeamOption(team: Team): { value: string; label: string; description?: string } {
    const platformBadge = team.platform === 'ESPN' ? ' [ESPN]' : '';
    const seasonText = team.season ? ` (${team.season})` : '';
    
    return {
      value: team.id,
      label: `${team.name}${platformBadge}`,
      description: `${team.league}${seasonText} • ${team.record}`
    };
  }

  getTeamIcon(platform: string): string {
    const icons: Record<string, string> = {
      'ESPN': '🏈',
      'Yahoo': '⚡',
      'Manual': '📝',
      'Sleeper': '😴'
    };
    return icons[platform] || '🏆';
  }

  getPlatformColor(platform: string): string {
    const colors: Record<string, string> = {
      'ESPN': 'text-red-600',
      'Yahoo': 'text-purple-600',
      'Manual': 'text-blue-600',
      'Sleeper': 'text-green-600'
    };
    return colors[platform] || 'text-gray-600';
  }
}

export const teamsService = new TeamsService();