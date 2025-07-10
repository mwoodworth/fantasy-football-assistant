import { api } from './api';
import { generateMockPlayers } from '../utils/mockPlayerData';
import type { Player, PlayersFilterOptions, PlayersResponse } from '../types/player';

export type { Player, PlayersFilterOptions, PlayersResponse };

export interface PlayerSearchParams {
  search?: string;
  position?: string;
  team?: string;
  limit?: number;
}

export interface PlayerStats {
  id: number;
  player_id: number;
  week: number;
  season: number;
  points: number;
  passing_yards?: number;
  passing_tds?: number;
  rushing_yards?: number;
  rushing_tds?: number;
  receiving_yards?: number;
  receiving_tds?: number;
  receptions?: number;
  targets?: number;
  fumbles?: number;
  interceptions?: number;
}

export interface ComparisonResult {
  player1: Player;
  player2: Player;
  winner: 'player1' | 'player2' | 'tie';
  categories: {
    projected_points: { player1: number; player2: number; winner: string };
    consistency: { player1: number; player2: number; winner: string };
    upside: { player1: number; player2: number; winner: string };
    matchup: { player1: string; player2: string; winner: string };
  };
  recommendation: string;
}

// Generate mock players once when the service loads
const mockPlayers = generateMockPlayers();

export class PlayerService {
  static async getPlayers(params: PlayerSearchParams = {}): Promise<Player[]> {
    try {
      const searchParams = new URLSearchParams();
      
      if (params.search) searchParams.append('search', params.search);
      if (params.position) searchParams.append('position', params.position);
      if (params.team) searchParams.append('team', params.team);
      if (params.limit) searchParams.append('limit', params.limit.toString());
      
      const response = await api.get(`/players?${searchParams.toString()}`);
      return response.data;
    } catch (error) {
      // Fallback to mock data if API fails
      console.log('Using mock player data');
      let filteredPlayers = [...mockPlayers];
      
      // Apply filters to mock data
      if (params.search) {
        const searchLower = params.search.toLowerCase();
        filteredPlayers = filteredPlayers.filter(player => 
          player.name.toLowerCase().includes(searchLower) ||
          player.team.toLowerCase().includes(searchLower) ||
          player.position.toLowerCase().includes(searchLower)
        );
      }
      
      if (params.position) {
        filteredPlayers = filteredPlayers.filter(player => 
          player.position === params.position
        );
      }
      
      if (params.team) {
        filteredPlayers = filteredPlayers.filter(player => 
          player.team === params.team
        );
      }
      
      // Apply limit
      if (params.limit) {
        filteredPlayers = filteredPlayers.slice(0, params.limit);
      }
      
      return filteredPlayers;
    }
  }

  static async searchPlayers(params: PlayerSearchParams): Promise<Player[]> {
    return this.getPlayers(params);
  }

  static async getPlayer(playerId: number): Promise<Player> {
    try {
      const response = await api.get(`/players/${playerId}`);
      return response.data;
    } catch (error) {
      // Fallback to mock data
      const player = mockPlayers.find(p => p.id === playerId);
      if (!player) {
        throw new Error('Player not found');
      }
      return player;
    }
  }

  static async getPlayerStats(playerId: number, week?: number): Promise<PlayerStats[]> {
    const params = new URLSearchParams();
    if (week) params.append('week', week.toString());
    
    const response = await api.get(`/players/${playerId}/stats?${params.toString()}`);
    return response.data;
  }

  static async getPlayerProjections(playerId: number, week?: number): Promise<any> {
    const params = new URLSearchParams();
    if (week) params.append('week', week.toString());
    
    const response = await api.get(`/players/${playerId}/projections?${params.toString()}`);
    return response.data;
  }

  static async comparePlayers(player1Id: number, player2Id: number): Promise<ComparisonResult> {
    const response = await api.post('/players/compare', {
      player1_id: player1Id,
      player2_id: player2Id
    });
    return response.data;
  }

  static async getTopPerformers(position?: string, week?: number): Promise<Player[]> {
    const params = new URLSearchParams();
    if (position) params.append('position', position);
    if (week) params.append('week', week.toString());
    
    const response = await api.get(`/players/top-performers?${params.toString()}`);
    return response.data;
  }

  static async getTrendingPlayers(direction: 'up' | 'down' = 'up'): Promise<Player[]> {
    const response = await api.get(`/players/trending?direction=${direction}`);
    return response.data;
  }

  static async getWaiverTargets(position?: string): Promise<Player[]> {
    const params = new URLSearchParams();
    if (position) params.append('position', position);
    
    const response = await api.get(`/players/waiver-targets?${params.toString()}`);
    return response.data;
  }

  static async getMatchupAnalysis(playerId: number, week?: number): Promise<any> {
    const params = new URLSearchParams();
    if (week) params.append('week', week.toString());
    
    const response = await api.get(`/players/${playerId}/matchup?${params.toString()}`);
    return response.data;
  }
}