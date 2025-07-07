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

// Teams API Service
class TeamsService {
  
  async getUserTeams(includeESPN = true, includeManual = true, season?: number): Promise<Team[]> {
    const params = new URLSearchParams();
    params.append('include_espn', includeESPN.toString());
    params.append('include_manual', includeManual.toString());
    if (season) params.append('season', season.toString());
    
    const response = await api.get(`/teams?${params.toString()}`);
    return response.data;
  }

  async getTeamDetail(teamId: string): Promise<TeamDetail> {
    try {
      const response = await api.get(`/teams/${teamId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching team detail:', error);
      throw error;
    }
  }

  async syncTeam(teamId: string): Promise<{ message: string; last_sync?: string }> {
    const response = await api.post(`/teams/${teamId}/sync`);
    return response.data;
  }

  async getTeamDraftInfo(teamId: string): Promise<{
    league_id: number;
    league_name: string;
    draft_completed: boolean;
    draft_date?: string;
    can_start_draft: boolean;
  }> {
    const response = await api.get(`/teams/${teamId}/draft`);
    return response.data;
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