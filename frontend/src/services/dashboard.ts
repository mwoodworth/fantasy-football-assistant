import { api } from './api';

export interface DashboardData {
  teamRank: string;
  leagueSize: number;
  rankTrend: 'up' | 'down' | 'stable';
  weeklyPoints: string;
  pointsProjected: number;
  pointsTrend: 'up' | 'down' | 'stable';
  activePlayers: string;
  benchPlayers: number;
  injuryAlerts: number;
  recentActivity: Activity[];
  injuries: InjuryAlert[];
}

export interface Activity {
  type: 'recommendation' | 'injury' | 'trade' | 'waiver' | 'lineup';
  title: string;
  description: string;
  timestamp: string;
  priority?: 'high' | 'medium' | 'low';
  actionUrl?: string;
}

export interface InjuryAlert {
  player: {
    id: number;
    name: string;
    position: string;
    team: string;
  };
  status: 'Questionable' | 'Doubtful' | 'Out' | 'IR';
  severity: 'low' | 'medium' | 'high';
  description: string;
  expectedReturn?: string;
  recommendation: string;
}

export interface LiveScore {
  gameId: string;
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  quarter: string;
  timeRemaining: string;
  isComplete: boolean;
  gameTime: string;
}

export interface TopPerformer {
  player: {
    id: number;
    name: string;
    position: string;
    team: string;
  };
  points: number;
  projectedPoints: number;
  percentageOfProjected: number;
  trend: 'up' | 'down' | 'stable';
}

export interface TrendingPlayer {
  player: {
    id: number;
    name: string;
    position: string;
    team: string;
  };
  trendDirection: 'up' | 'down';
  trendPercentage: number;
  reason: string;
  ownershipChange: number;
  addDropRatio: number;
}

export interface WaiverTarget {
  player: {
    id: number;
    name: string;
    position: string;
    team: string;
  };
  ownershipPercentage: number;
  projectedPoints: number;
  upcomingMatchup: string;
  matchupDifficulty: 'easy' | 'medium' | 'hard';
  recommendation: string;
  priority: 'high' | 'medium' | 'low';
}

export class DashboardService {
  static async getDashboardData(): Promise<DashboardData> {
    try {
      const response = await api.get('/dashboard');
      return response.data;
    } catch (error) {
      // Return mock data if API fails
      return this.getMockDashboardData();
    }
  }

  static async getLiveScores(): Promise<LiveScore[]> {
    try {
      const response = await api.get('/dashboard/live-scores');
      return response.data;
    } catch (error) {
      return this.getMockLiveScores();
    }
  }

  static async getTopPerformers(week?: number): Promise<TopPerformer[]> {
    try {
      const params = week ? `?week=${week}` : '';
      const response = await api.get(`/dashboard/top-performers${params}`);
      return response.data;
    } catch (error) {
      return this.getMockTopPerformers();
    }
  }

  static async getTrendingPlayers(): Promise<TrendingPlayer[]> {
    try {
      const response = await api.get('/dashboard/trending-players');
      return response.data;
    } catch (error) {
      return this.getMockTrendingPlayers();
    }
  }

  static async getWaiverTargets(): Promise<WaiverTarget[]> {
    try {
      const response = await api.get('/dashboard/waiver-targets');
      return response.data;
    } catch (error) {
      return this.getMockWaiverTargets();
    }
  }

  static async getInjuryReport(): Promise<InjuryAlert[]> {
    try {
      const response = await api.get('/dashboard/injury-report');
      return response.data;
    } catch (error) {
      return this.getMockInjuryReport();
    }
  }

  // Mock data methods for development/fallback
  private static getMockDashboardData(): DashboardData {
    return {
      teamRank: '3rd',
      leagueSize: 12,
      rankTrend: 'up',
      weeklyPoints: '127.4',
      pointsProjected: 142.3,
      pointsTrend: 'up',
      activePlayers: '15',
      benchPlayers: 2,
      injuryAlerts: 2,
      recentActivity: [
        {
          type: 'recommendation',
          title: 'AI Recommendation',
          description: 'Consider starting Josh Allen over Lamar Jackson this week based on matchup analysis',
          timestamp: '2 hours ago',
          priority: 'high'
        },
        {
          type: 'injury',
          title: 'Injury Update',
          description: 'Christian McCaffrey listed as questionable for Sunday\'s game',
          timestamp: '5 hours ago',
          priority: 'medium'
        },
        {
          type: 'trade',
          title: 'Trade Proposal',
          description: 'New trade offer: Your Stefon Diggs for their Travis Kelce',
          timestamp: '1 day ago',
          priority: 'medium'
        }
      ],
      injuries: [
        {
          player: { id: 1, name: 'Christian McCaffrey', position: 'RB', team: 'SF' },
          status: 'Questionable',
          severity: 'medium',
          description: 'Knee injury, limited in practice',
          expectedReturn: 'This week',
          recommendation: 'Monitor practice reports, have backup ready'
        },
        {
          player: { id: 2, name: 'Cooper Kupp', position: 'WR', team: 'LAR' },
          status: 'Doubtful',
          severity: 'high',
          description: 'Ankle injury, did not practice',
          expectedReturn: 'Next week',
          recommendation: 'Consider dropping or finding replacement'
        }
      ]
    };
  }

  private static getMockLiveScores(): LiveScore[] {
    return [
      {
        gameId: '1',
        homeTeam: 'KC',
        awayTeam: 'BUF',
        homeScore: 21,
        awayScore: 14,
        quarter: '3rd',
        timeRemaining: '8:45',
        isComplete: false,
        gameTime: '1:00 PM ET'
      },
      {
        gameId: '2',
        homeTeam: 'SF',
        awayTeam: 'DAL',
        homeScore: 28,
        awayScore: 31,
        quarter: 'Final',
        timeRemaining: '',
        isComplete: true,
        gameTime: '4:25 PM ET'
      }
    ];
  }

  private static getMockTopPerformers(): TopPerformer[] {
    return [
      {
        player: { id: 1, name: 'Josh Allen', position: 'QB', team: 'BUF' },
        points: 32.4,
        projectedPoints: 24.8,
        percentageOfProjected: 130.6,
        trend: 'up'
      },
      {
        player: { id: 2, name: 'Christian McCaffrey', position: 'RB', team: 'SF' },
        points: 28.7,
        projectedPoints: 22.1,
        percentageOfProjected: 129.9,
        trend: 'up'
      },
      {
        player: { id: 3, name: 'Tyreek Hill', position: 'WR', team: 'MIA' },
        points: 24.3,
        projectedPoints: 18.9,
        percentageOfProjected: 128.6,
        trend: 'stable'
      }
    ];
  }

  private static getMockTrendingPlayers(): TrendingPlayer[] {
    return [
      {
        player: { id: 1, name: 'Puka Nacua', position: 'WR', team: 'LAR' },
        trendDirection: 'up',
        trendPercentage: 85.2,
        reason: 'Breakout rookie performance',
        ownershipChange: 15.3,
        addDropRatio: 12.4
      },
      {
        player: { id: 2, name: 'De\'Von Achane', position: 'RB', team: 'MIA' },
        trendDirection: 'up',
        trendPercentage: 78.9,
        reason: 'Multiple explosive games',
        ownershipChange: 22.1,
        addDropRatio: 18.7
      }
    ];
  }

  private static getMockWaiverTargets(): WaiverTarget[] {
    return [
      {
        player: { id: 1, name: 'Tyler Boyd', position: 'WR', team: 'CIN' },
        ownershipPercentage: 34.2,
        projectedPoints: 12.4,
        upcomingMatchup: 'vs JAX',
        matchupDifficulty: 'easy',
        recommendation: 'Strong add for WR depth',
        priority: 'high'
      },
      {
        player: { id: 2, name: 'Ezekiel Elliott', position: 'RB', team: 'NE' },
        ownershipPercentage: 28.7,
        projectedPoints: 10.8,
        upcomingMatchup: 'vs NYG',
        matchupDifficulty: 'medium',
        recommendation: 'Desperation play only',
        priority: 'low'
      }
    ];
  }

  private static getMockInjuryReport(): InjuryAlert[] {
    return [
      {
        player: { id: 1, name: 'Christian McCaffrey', position: 'RB', team: 'SF' },
        status: 'Questionable',
        severity: 'medium',
        description: 'Knee injury, limited in practice',
        expectedReturn: 'This week',
        recommendation: 'Monitor practice reports, have backup ready'
      },
      {
        player: { id: 2, name: 'Cooper Kupp', position: 'WR', team: 'LAR' },
        status: 'Doubtful',
        severity: 'high',
        description: 'Ankle injury, did not practice',
        expectedReturn: 'Next week',
        recommendation: 'Consider dropping or finding replacement'
      }
    ];
  }
}