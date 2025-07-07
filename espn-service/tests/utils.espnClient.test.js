/**
 * Tests for ESPN Client utility
 */

const axios = require('axios');
const ESPNClient = require('../src/utils/espnClient');

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock logger
jest.mock('../src/utils/logger', () => ({
  debug: jest.fn(),
  error: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
}));

describe('ESPNClient', () => {
  let client;
  let mockAxiosInstance;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock axios.create to return a mock instance
    mockAxiosInstance = {
      get: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    };
    
    mockedAxios.create.mockReturnValue(mockAxiosInstance);
    
    // Create client instance
    client = new ESPNClient();
  });

  describe('Constructor', () => {
    it('should create client with default configuration', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl',
        timeout: 30000,
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; Fantasy-Football-Assistant/1.0)',
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
    });

    it('should use provided cookies', () => {
      const testClient = new ESPNClient('test_s2', 'test_swid');
      expect(testClient.s2Cookie).toBe('test_s2');
      expect(testClient.swidCookie).toBe('test_swid');
    });

    it('should fall back to environment variables for cookies', () => {
      process.env.ESPN_COOKIE_S2 = 'env_s2';
      process.env.ESPN_COOKIE_SWID = 'env_swid';
      
      const testClient = new ESPNClient();
      expect(testClient.s2Cookie).toBe('env_s2');
      expect(testClient.swidCookie).toBe('env_swid');
    });
  });

  describe('testConnection', () => {
    it('should return success when connection works', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        status: 200,
        data: { id: 1 }
      });

      const result = await client.testConnection();

      expect(result).toEqual({
        connected: true,
        status: 200,
        message: 'ESPN API connection successful'
      });
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/1');
    });

    it('should return failure when connection fails', async () => {
      const error = new Error('Network error');
      error.response = { status: 500 };
      mockAxiosInstance.get.mockRejectedValue(error);

      const result = await client.testConnection();

      expect(result).toEqual({
        connected: false,
        status: 500,
        message: 'Network error'
      });
    });

    it('should handle connection without response', async () => {
      const error = new Error('Timeout');
      mockAxiosInstance.get.mockRejectedValue(error);

      const result = await client.testConnection();

      expect(result).toEqual({
        connected: false,
        status: 0,
        message: 'Timeout'
      });
    });
  });

  describe('getLeague', () => {
    const mockLeagueData = {
      id: 12345,
      seasonId: 2024,
      scoringPeriodId: 5,
      status: 'ACTIVE',
      settings: {
        name: 'Test League',
        size: 10,
        isPublic: false,
        scoringSettings: { '53': 1 }, // PPR
        rosterSettings: {
          lineupSlotCounts: { '0': 1, '2': 2, '4': 2 } // QB, RB, WR
        },
        scheduleSettings: {
          playoffTeamCount: 4
        }
      },
      teams: [{ id: 1 }, { id: 2 }]
    };

    it('should fetch and format league data', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockLeagueData
      });

      const result = await client.getLeague(12345);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345');
      expect(result).toMatchObject({
        id: 12345,
        name: 'Test League',
        size: 10,
        season: 2024,
        currentWeek: 5,
        status: 'ACTIVE',
        isPublic: false,
        settings: {
          scoringType: 'PPR',
          rosterSize: 5,
          playoffTeams: 4
        },
        teams: 2
      });
    });

    it('should handle different seasons', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockLeagueData
      });

      await client.getLeague(12345, 2023);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2023/segments/0/leagues/12345');
    });

    it('should handle API errors', async () => {
      const error = new Error('Not found');
      error.response = { status: 404 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('League or resource not found');
    });
  });

  describe('getLeagueTeams', () => {
    const mockTeamsData = {
      teams: [
        {
          id: 1,
          name: 'Team Alpha',
          abbrev: 'ALP',
          primaryOwner: {
            firstName: 'John',
            lastName: 'Doe',
            displayName: 'JohnD'
          },
          record: {
            overall: {
              wins: 5,
              losses: 3,
              ties: 0,
              percentage: 0.625,
              pointsFor: 1250.5,
              pointsAgainst: 1100.2
            }
          },
          playoffSeed: 2
        }
      ]
    };

    it('should fetch and format teams data', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockTeamsData
      });

      const result = await client.getLeagueTeams(12345);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345', {
        params: { view: 'mTeam' }
      });

      expect(result).toEqual([{
        id: 1,
        name: 'Team Alpha',
        abbreviation: 'ALP',
        logo: null,
        owner: {
          firstName: 'John',
          lastName: 'Doe',
          displayName: 'JohnD'
        },
        record: {
          wins: 5,
          losses: 3,
          ties: 0,
          percentage: 0.625
        },
        standings: {
          rank: 2,
          pointsFor: 1250.5,
          pointsAgainst: 1100.2
        },
        draft: {
          position: 0
        }
      }]);
    });

    it('should handle empty teams array', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { teams: [] }
      });

      const result = await client.getLeagueTeams(12345);
      expect(result).toEqual([]);
    });
  });

  describe('getTeamRoster', () => {
    const mockRosterData = {
      teams: [
        {
          id: 1,
          roster: {
            entries: [
              {
                playerId: 123,
                lineupSlotId: 0, // QB
                acquisitionDate: 1625097600000,
                acquisitionType: 'DRAFT',
                playerPoolEntry: {
                  player: {
                    id: 123,
                    fullName: 'Josh Allen',
                    defaultPositionId: 1,
                    proTeamId: 2,
                    injuryStatus: 'ACTIVE',
                    ownership: {
                      percentOwned: 99.5
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    };

    it('should fetch and format roster data', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockRosterData
      });

      const result = await client.getTeamRoster(12345, 1);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345', {
        params: { view: 'mRoster' }
      });

      expect(result.entries).toHaveLength(1);
      expect(result.entries[0]).toMatchObject({
        playerId: 123,
        lineupSlotId: 0,
        position: 'QB',
        player: {
          id: 123,
          name: 'Josh Allen',
          position: 'QB',
          team: 'BUF',
          injuryStatus: 'ACTIVE',
          percentOwned: 99.5
        }
      });
    });

    it('should include week parameter when provided', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockRosterData
      });

      await client.getTeamRoster(12345, 1, 2024, 5);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345', {
        params: { view: 'mRoster', scoringPeriodId: 5 }
      });
    });

    it('should throw error when team not found', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { teams: [] }
      });

      await expect(client.getTeamRoster(12345, 999)).rejects.toThrow('Team 999 not found in league 12345');
    });
  });

  describe('getFreeAgents', () => {
    const mockPlayersData = {
      players: [
        {
          id: 456,
          player: {
            id: 456,
            fullName: 'Christian McCaffrey',
            defaultPositionId: 2,
            proTeamId: 25,
            injuryStatus: 'ACTIVE',
            ownership: {
              percentOwned: 15.2
            }
          }
        }
      ]
    };

    it('should fetch and format free agents', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockPlayersData
      });

      const result = await client.getFreeAgents(12345);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345', {
        params: {
          view: 'kona_player_info',
          'players': {
            'filterStatus': 'FREEAGENT',
            'offset': 0,
            'limit': 50,
            'sortPercOwned': {
              'sortAsc': false,
              'sortPriority': 1
            }
          }
        }
      });

      expect(result).toHaveLength(1);
      expect(result[0]).toMatchObject({
        id: 456,
        name: 'Christian McCaffrey',
        position: 'RB',
        team: 'SF',
        injuryStatus: 'ACTIVE',
        percentOwned: 15.2
      });
    });

    it('should handle pagination parameters', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { players: [] }
      });

      await client.getFreeAgents(12345, 2024, 25, 100);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/seasons/2024/segments/0/leagues/12345', {
        params: {
          view: 'kona_player_info',
          'players': {
            'filterStatus': 'FREEAGENT',
            'offset': 25,
            'limit': 100,
            'sortPercOwned': {
              'sortAsc': false,
              'sortPriority': 1
            }
          }
        }
      });
    });
  });

  describe('Error handling', () => {
    it('should handle 401 authentication errors', async () => {
      const error = new Error('Unauthorized');
      error.response = { status: 401 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('ESPN Authentication failed - check your cookies');
    });

    it('should handle 403 access denied errors', async () => {
      const error = new Error('Forbidden');
      error.response = { status: 403 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('Access denied - league may be private or cookies invalid');
    });

    it('should handle 404 not found errors', async () => {
      const error = new Error('Not Found');
      error.response = { status: 404 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('League or resource not found');
    });

    it('should handle 429 rate limit errors', async () => {
      const error = new Error('Too Many Requests');
      error.response = { status: 429 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('Rate limit exceeded - please wait before making more requests');
    });

    it('should handle generic errors', async () => {
      const error = new Error('Internal server error');
      error.response = { status: 500 };
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getLeague(12345)).rejects.toThrow('ESPN API error in getLeague: Internal server error');
    });
  });

  describe('Position and team mappings', () => {
    it('should correctly map position IDs to abbreviations', () => {
      expect(client._getPositionAbbreviation(1)).toBe('QB');
      expect(client._getPositionAbbreviation(2)).toBe('RB');
      expect(client._getPositionAbbreviation(3)).toBe('WR');
      expect(client._getPositionAbbreviation(4)).toBe('TE');
      expect(client._getPositionAbbreviation(5)).toBe('K');
      expect(client._getPositionAbbreviation(16)).toBe('D/ST');
      expect(client._getPositionAbbreviation(999)).toBe('UNKNOWN');
    });

    it('should correctly map lineup slot IDs to position names', () => {
      expect(client._getPositionName(0)).toBe('QB');
      expect(client._getPositionName(2)).toBe('RB');
      expect(client._getPositionName(4)).toBe('WR');
      expect(client._getPositionName(6)).toBe('TE');
      expect(client._getPositionName(20)).toBe('BENCH');
      expect(client._getPositionName(999)).toBe('UNKNOWN');
    });

    it('should correctly map NFL team IDs to abbreviations', () => {
      expect(client._getNFLTeamAbbreviation(1)).toBe('ATL');
      expect(client._getNFLTeamAbbreviation(2)).toBe('BUF');
      expect(client._getNFLTeamAbbreviation(12)).toBe('KC');
      expect(client._getNFLTeamAbbreviation(25)).toBe('SF');
      expect(client._getNFLTeamAbbreviation(999)).toBe('FA');
    });

    it('should correctly determine scoring type', () => {
      expect(client._getScoringType({ '53': 1 })).toBe('PPR');
      expect(client._getScoringType({ '53': 0.5 })).toBe('HALF_PPR');
      expect(client._getScoringType({ '53': 0 })).toBe('STANDARD');
      expect(client._getScoringType({})).toBe('STANDARD');
      expect(client._getScoringType()).toBe('UNKNOWN');
    });
  });
});