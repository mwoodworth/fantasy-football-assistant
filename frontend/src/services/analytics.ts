import { api } from './api';

export interface TeamAnalytics {
  teamName: string;
  weeklyScores: number[];
  totalPoints: number;
  averagePoints: number;
  leagueRank: number;
  playoffChance: number;
  winLossRecord: { wins: number; losses: number };
  projectedFinish: number;
  strengthOfSchedule: number;
  consistencyRating: number;
}

export interface PlayerPerformance {
  playerId: number;
  playerName: string;
  position: string;
  team: string;
  performances: {
    week: number;
    points: number;
    projectedPoints: number;
    actualVsProjected: number;
  }[];
  seasonStats: {
    totalPoints: number;
    averagePoints: number;
    consistencyScore: number;
    boom: number;
    bust: number;
  };
}

export interface LeagueComparison {
  standings: {
    rank: number;
    teamName: string;
    wins: number;
    losses: number;
    totalPoints: number;
    averagePoints: number;
  }[];
  positionAnalysis: {
    position: string;
    leagueAverage: number;
    yourAverage: number;
    rank: number;
    percentile: number;
  }[];
  strengthsWeaknesses: {
    strengths: string[];
    weaknesses: string[];
  };
}

export interface ProjectionData {
  remainingGames: {
    week: number;
    opponent: string;
    projectedPoints: number;
    winProbability: number;
  }[];
  seasonProjections: {
    finalRecord: { wins: number; losses: number };
    playoffChance: number;
    championshipChance: number;
    expectedFinish: number;
  };
}

export class AnalyticsService {
  static async getTeamAnalytics(timeRange: string = 'season'): Promise<TeamAnalytics> {
    try {
      const response = await api.get(`/analytics/team?timeRange=${timeRange}`);
      return response.data;
    } catch (error) {
      return this.getMockTeamAnalytics();
    }
  }

  static async getPlayerPerformance(playerId: number, timeRange: string = 'season'): Promise<PlayerPerformance> {
    try {
      const response = await api.get(`/analytics/player/${playerId}?timeRange=${timeRange}`);
      return response.data;
    } catch (error) {
      return this.getMockPlayerPerformance();
    }
  }

  static async getLeagueComparison(): Promise<LeagueComparison> {
    try {
      const response = await api.get('/analytics/league-comparison');
      return response.data;
    } catch (error) {
      return this.getMockLeagueComparison();
    }
  }

  static async getProjections(): Promise<ProjectionData> {
    try {
      const response = await api.get('/analytics/projections');
      return response.data;
    } catch (error) {
      return this.getMockProjections();
    }
  }

  // Mock data methods
  private static getMockTeamAnalytics(): TeamAnalytics {
    return {
      teamName: 'Your Team',
      weeklyScores: [124.5, 118.2, 142.8, 97.3, 156.7, 112.4, 134.9, 128.6],
      totalPoints: 1024.2,
      averagePoints: 128.0,
      leagueRank: 3,
      playoffChance: 75.4,
      winLossRecord: { wins: 5, losses: 3 },
      projectedFinish: 3,
      strengthOfSchedule: 0.52,
      consistencyRating: 8.2,
    };
  }

  private static getMockPlayerPerformance(): PlayerPerformance {
    return {
      playerId: 1,
      playerName: 'Josh Allen',
      position: 'QB',
      team: 'BUF',
      performances: [
        { week: 1, points: 24.8, projectedPoints: 22.1, actualVsProjected: 2.7 },
        { week: 2, points: 18.4, projectedPoints: 23.5, actualVsProjected: -5.1 },
        { week: 3, points: 31.2, projectedPoints: 24.8, actualVsProjected: 6.4 },
        { week: 4, points: 19.7, projectedPoints: 22.3, actualVsProjected: -2.6 },
        { week: 5, points: 28.9, projectedPoints: 25.1, actualVsProjected: 3.8 },
        { week: 6, points: 22.1, projectedPoints: 21.9, actualVsProjected: 0.2 },
        { week: 7, points: 26.3, projectedPoints: 23.7, actualVsProjected: 2.6 },
        { week: 8, points: 33.1, projectedPoints: 24.2, actualVsProjected: 8.9 },
      ],
      seasonStats: {
        totalPoints: 204.5,
        averagePoints: 25.6,
        consistencyScore: 7.8,
        boom: 3,
        bust: 1,
      },
    };
  }

  private static getMockLeagueComparison(): LeagueComparison {
    return {
      standings: [
        { rank: 1, teamName: 'Team Alpha', wins: 7, losses: 1, totalPoints: 1184.3, averagePoints: 148.0 },
        { rank: 2, teamName: 'Team Beta', wins: 6, losses: 2, totalPoints: 1152.7, averagePoints: 144.1 },
        { rank: 3, teamName: 'Your Team', wins: 5, losses: 3, totalPoints: 1024.2, averagePoints: 128.0 },
        { rank: 4, teamName: 'Team Delta', wins: 5, losses: 3, totalPoints: 1018.9, averagePoints: 127.4 },
      ],
      positionAnalysis: [
        { position: 'QB', leagueAverage: 18.7, yourAverage: 25.6, rank: 2, percentile: 91.7 },
        { position: 'RB', leagueAverage: 12.4, yourAverage: 11.8, rank: 7, percentile: 41.7 },
        { position: 'WR', leagueAverage: 14.2, yourAverage: 16.9, rank: 3, percentile: 75.0 },
        { position: 'TE', leagueAverage: 8.9, yourAverage: 7.2, rank: 9, percentile: 25.0 },
      ],
      strengthsWeaknesses: {
        strengths: [
          'Elite QB production (25.6 ppg, #2 in league)',
          'Strong WR depth (16.9 ppg average)',
          'Consistent lineup decisions',
        ],
        weaknesses: [
          'Below-average TE production (7.2 ppg, #9 in league)',
          'Inconsistent RB2 performance',
          'Weak bench depth at skill positions',
        ],
      },
    };
  }

  private static getMockProjections(): ProjectionData {
    return {
      remainingGames: [
        { week: 9, opponent: 'Team Epsilon', projectedPoints: 124.7, winProbability: 0.68 },
        { week: 10, opponent: 'Team Zeta', projectedPoints: 118.3, winProbability: 0.45 },
        { week: 11, opponent: 'Team Eta', projectedPoints: 132.1, winProbability: 0.72 },
        { week: 12, opponent: 'Team Theta', projectedPoints: 126.8, winProbability: 0.61 },
        { week: 13, opponent: 'Team Iota', projectedPoints: 129.4, winProbability: 0.58 },
      ],
      seasonProjections: {
        finalRecord: { wins: 8, losses: 5 },
        playoffChance: 75.4,
        championshipChance: 12.8,
        expectedFinish: 3.2,
      },
    };
  }
}