/**
 * ESPN Fantasy Football API Client
 * 
 * Handles all interactions with ESPN's fantasy football API
 * Manages authentication cookies and request formatting
 */

const axios = require('axios');
const logger = require('./logger');

class ESPNClient {
  constructor(s2Cookie = null, swidCookie = null) {
    this.baseURL = process.env.ESPN_BASE_URL || 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl';
    // Use provided cookies or fall back to environment
    this.s2Cookie = s2Cookie || process.env.ESPN_COOKIE_S2;
    this.swidCookie = swidCookie || process.env.ESPN_COOKIE_SWID;
    
    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; Fantasy-Football-Assistant/1.0)',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        // Add ESPN cookies for private league access
        if (this.s2Cookie && this.swidCookie) {
          config.headers.Cookie = `espn_s2=${this.s2Cookie}; SWID=${this.swidCookie}`;
        }
        
        logger.debug(`ESPN API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          headers: { ...config.headers, Cookie: '[REDACTED]' }
        });
        
        return config;
      },
      (error) => {
        logger.error('ESPN API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response) => {
        logger.debug(`ESPN API Response: ${response.status} ${response.config.url}`, {
          status: response.status,
          dataSize: JSON.stringify(response.data).length
        });
        return response;
      },
      (error) => {
        const { response, request, config } = error;
        
        if (response) {
          // Server responded with error status
          logger.error(`ESPN API Error Response: ${response.status} ${config?.url}`, {
            status: response.status,
            statusText: response.statusText,
            data: response.data
          });
        } else if (request) {
          // Request made but no response received
          logger.error('ESPN API No Response:', {
            url: config?.url,
            timeout: config?.timeout
          });
        } else {
          // Error in request setup
          logger.error('ESPN API Request Setup Error:', error.message);
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * Test ESPN API connectivity
   */
  async testConnection() {
    try {
      // Try to fetch a public league to test connectivity
      const response = await this.client.get('/seasons/2024/segments/0/leagues/1');
      return {
        connected: true,
        status: response.status,
        message: 'ESPN API connection successful'
      };
    } catch (error) {
      return {
        connected: false,
        status: error.response?.status || 0,
        message: error.message || 'ESPN API connection failed'
      };
    }
  }

  /**
   * Get league information
   */
  async getLeague(leagueId, season = 2024) {
    try {
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`);
      return this._formatLeagueData(response.data);
    } catch (error) {
      throw this._handleAPIError(error, 'getLeague');
    }
  }

  /**
   * Get league settings
   */
  async getLeagueSettings(leagueId, season = 2024) {
    try {
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params: { view: 'mSettings' }
      });
      return this._formatLeagueSettings(response.data);
    } catch (error) {
      throw this._handleAPIError(error, 'getLeagueSettings');
    }
  }

  /**
   * Get all teams in a league
   */
  async getLeagueTeams(leagueId, season = 2024) {
    try {
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params: { view: 'mTeam' }
      });
      return this._formatTeamsData(response.data.teams || []);
    } catch (error) {
      throw this._handleAPIError(error, 'getLeagueTeams');
    }
  }

  /**
   * Get team roster
   */
  async getTeamRoster(leagueId, teamId, season = 2024, week = null) {
    try {
      const params = { view: 'mRoster' };
      if (week) {
        params.scoringPeriodId = week;
      }
      
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params
      });
      
      const team = response.data.teams?.find(t => t.id === parseInt(teamId));
      if (!team) {
        throw new Error(`Team ${teamId} not found in league ${leagueId}`);
      }
      
      return this._formatRosterData(team.roster);
    } catch (error) {
      throw this._handleAPIError(error, 'getTeamRoster');
    }
  }

  /**
   * Get free agents
   */
  async getFreeAgents(leagueId, season = 2024, offset = 0, limit = 50) {
    try {
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params: {
          view: 'kona_player_info',
          'players': {
            'filterStatus': 'FREEAGENT',
            'offset': offset,
            'limit': limit,
            'sortPercOwned': {
              'sortAsc': false,
              'sortPriority': 1
            }
          }
        }
      });
      
      return this._formatPlayersData(response.data.players || []);
    } catch (error) {
      throw this._handleAPIError(error, 'getFreeAgents');
    }
  }

  /**
   * Get current week scoreboard
   */
  async getScoreboard(leagueId, season = 2024, week = null) {
    try {
      const params = { view: 'mMatchup' };
      if (week) {
        params.scoringPeriodId = week;
      }
      
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params
      });
      
      return this._formatScoreboardData(response.data.schedule || []);
    } catch (error) {
      throw this._handleAPIError(error, 'getScoreboard');
    }
  }

  /**
   * Get draft information
   */
  async getDraft(leagueId, season = 2024) {
    try {
      const response = await this.client.get(`/seasons/${season}/segments/0/leagues/${leagueId}`, {
        params: { view: 'mDraftDetail' }
      });
      
      return this._formatDraftData(response.data.draftDetail || {});
    } catch (error) {
      throw this._handleAPIError(error, 'getDraft');
    }
  }

  /**
   * Format league data for consistent API response
   */
  _formatLeagueData(data) {
    return {
      id: data.id,
      name: data.settings?.name || 'Unknown League',
      size: data.settings?.size || 0,
      season: data.seasonId,
      currentWeek: data.scoringPeriodId,
      status: data.status,
      isPublic: data.settings?.isPublic || false,
      settings: {
        scoringType: this._getScoringType(data.settings?.scoringSettings),
        rosterSize: data.settings?.rosterSettings?.lineupSlotCounts ? 
          Object.values(data.settings.rosterSettings.lineupSlotCounts).reduce((a, b) => a + b, 0) : 0,
        playoffTeams: data.settings?.scheduleSettings?.playoffTeamCount || 0,
        tradeDeadline: data.settings?.tradeSettings?.deadlineDate || null,
        waiverOrder: data.settings?.acquisitionSettings?.waiverOrderReset || 'UNKNOWN'
      },
      teams: data.teams?.length || 0,
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * Format team data
   */
  _formatTeamsData(teams) {
    return teams.map(team => ({
      id: team.id,
      name: team.name || `Team ${team.id}`,
      abbreviation: team.abbrev || team.name?.substring(0, 3).toUpperCase() || 'TBD',
      logo: team.logo || null,
      owner: {
        firstName: team.primaryOwner?.firstName || '',
        lastName: team.primaryOwner?.lastName || '',
        displayName: team.primaryOwner?.displayName || 'Unknown Owner'
      },
      record: {
        wins: team.record?.overall?.wins || 0,
        losses: team.record?.overall?.losses || 0,
        ties: team.record?.overall?.ties || 0,
        percentage: team.record?.overall?.percentage || 0
      },
      standings: {
        rank: team.playoffSeed || 0,
        pointsFor: team.record?.overall?.pointsFor || 0,
        pointsAgainst: team.record?.overall?.pointsAgainst || 0
      },
      draft: {
        position: team.draftDayProjectedRank || 0
      }
    }));
  }

  /**
   * Format roster data
   */
  _formatRosterData(roster) {
    if (!roster?.entries) {
      return { entries: [] };
    }

    return {
      entries: roster.entries.map(entry => ({
        playerId: entry.playerId,
        player: this._formatPlayerData(entry.playerPoolEntry?.player),
        lineupSlotId: entry.lineupSlotId,
        position: this._getPositionName(entry.lineupSlotId),
        acquisitionDate: entry.acquisitionDate,
        acquisitionType: entry.acquisitionType
      }))
    };
  }

  /**
   * Format player data
   */
  _formatPlayerData(player) {
    if (!player) return null;

    return {
      id: player.id,
      name: player.fullName,
      position: this._getPositionAbbreviation(player.defaultPositionId),
      team: this._getNFLTeamAbbreviation(player.proTeamId),
      injuryStatus: player.injuryStatus || 'ACTIVE',
      percentOwned: player.ownership?.percentOwned || 0,
      stats: player.stats ? this._formatPlayerStats(player.stats) : null
    };
  }

  /**
   * Format players data array
   */
  _formatPlayersData(players) {
    if (!players || !Array.isArray(players)) return [];

    return players.map(playerEntry => {
      // Handle both direct player objects and player entries with nested player data
      const player = playerEntry.player || playerEntry;
      return this._formatPlayerData(player);
    }).filter(player => player !== null);
  }

  /**
   * Format player statistics
   */
  _formatPlayerStats(stats) {
    return stats.map(stat => ({
      season: stat.seasonId,
      week: stat.scoringPeriodId,
      statSourceId: stat.statSourceId,
      stats: stat.stats || {},
      appliedStats: stat.appliedStats || {}
    }));
  }

  /**
   * Get scoring type from settings
   */
  _getScoringType(scoringSettings) {
    if (!scoringSettings) return 'UNKNOWN';
    
    // Check for PPR scoring
    const receptionPoints = scoringSettings['53'] || 0; // Reception stat ID
    if (receptionPoints >= 1) return 'PPR';
    if (receptionPoints > 0 && receptionPoints < 1) return 'HALF_PPR';
    return 'STANDARD';
  }

  /**
   * Get position name from lineup slot ID
   */
  _getPositionName(slotId) {
    const slots = {
      0: 'QB', 1: 'TQB', 2: 'RB', 3: 'RB/WR', 4: 'WR', 5: 'WR/TE',
      6: 'TE', 7: 'OP', 8: 'DT', 9: 'DE', 10: 'LB', 11: 'DL',
      12: 'CB', 13: 'S', 14: 'DB', 15: 'DP', 16: 'D/ST', 17: 'K',
      20: 'BENCH', 21: 'IR', 22: 'UNKNOWN', 23: 'RB/WR/TE'
    };
    return slots[slotId] || 'UNKNOWN';
  }

  /**
   * Get position abbreviation from position ID
   */
  _getPositionAbbreviation(positionId) {
    const positions = {
      1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'
    };
    return positions[positionId] || 'UNKNOWN';
  }

  /**
   * Get NFL team abbreviation from team ID
   */
  _getNFLTeamAbbreviation(teamId) {
    const teams = {
      1: 'ATL', 2: 'BUF', 3: 'CHI', 4: 'CIN', 5: 'CLE', 6: 'DAL',
      7: 'DEN', 8: 'DET', 9: 'GB', 10: 'TEN', 11: 'IND', 12: 'KC',
      13: 'LV', 14: 'LAR', 15: 'MIA', 16: 'MIN', 17: 'NE', 18: 'NO',
      19: 'NYG', 20: 'NYJ', 21: 'PHI', 22: 'ARI', 23: 'PIT', 24: 'LAC',
      25: 'SF', 26: 'SEA', 27: 'TB', 28: 'WAS', 29: 'CAR', 30: 'JAX',
      33: 'BAL', 34: 'HOU'
    };
    return teams[teamId] || 'FA';
  }

  /**
   * Handle API errors consistently
   */
  _handleAPIError(error, method) {
    const { response } = error;
    
    if (response?.status === 401) {
      return new Error('ESPN Authentication failed - check your cookies');
    } else if (response?.status === 403) {
      return new Error('Access denied - league may be private or cookies invalid');
    } else if (response?.status === 404) {
      return new Error('League or resource not found');
    } else if (response?.status === 429) {
      return new Error('Rate limit exceeded - please wait before making more requests');
    } else {
      return new Error(`ESPN API error in ${method}: ${error.message}`);
    }
  }

  /**
   * Format scoreboard data
   */
  _formatScoreboardData(schedule) {
    return schedule.map(matchup => ({
      id: matchup.id,
      week: matchup.matchupPeriodId,
      home: {
        teamId: matchup.home?.teamId,
        totalPoints: matchup.home?.totalPoints || 0,
        rosterForCurrentScoringPeriod: matchup.home?.rosterForCurrentScoringPeriod || {}
      },
      away: {
        teamId: matchup.away?.teamId,
        totalPoints: matchup.away?.totalPoints || 0,
        rosterForCurrentScoringPeriod: matchup.away?.rosterForCurrentScoringPeriod || {}
      },
      winner: matchup.winner || 'UNDECIDED'
    }));
  }

  /**
   * Format draft data
   */
  _formatDraftData(draftDetail) {
    return {
      drafted: draftDetail.drafted || false,
      inProgress: draftDetail.inProgress || false,
      picks: (draftDetail.picks || []).map(pick => ({
        id: pick.id,
        playerId: pick.playerId,
        teamId: pick.teamId,
        roundId: pick.roundId,
        roundPickNumber: pick.roundPickNumber,
        overallPickNumber: pick.overallPickNumber,
        autoDrafted: pick.autoDrafted || false
      }))
    };
  }

  /**
   * Format league settings
   */
  _formatLeagueSettings(data) {
    const settings = data.settings || {};
    
    return {
      name: settings.name,
      size: settings.size,
      isPublic: settings.isPublic,
      scoring: {
        type: this._getScoringType(settings.scoringSettings),
        settings: settings.scoringSettings || {}
      },
      roster: {
        lineupSlotCounts: settings.rosterSettings?.lineupSlotCounts || {},
        positionLimits: settings.rosterSettings?.positionLimits || {}
      },
      schedule: {
        playoffTeamCount: settings.scheduleSettings?.playoffTeamCount || 0,
        regularSeasonMatchupPeriodCount: settings.scheduleSettings?.regularSeasonMatchupPeriodCount || 0
      },
      trade: {
        deadlineDate: settings.tradeSettings?.deadlineDate,
        reviewPeriodHours: settings.tradeSettings?.reviewPeriodHours || 0,
        allowOutOfUniverse: settings.tradeSettings?.allowOutOfUniverse || false
      },
      acquisition: {
        waiverOrderReset: settings.acquisitionSettings?.waiverOrderReset || 'UNKNOWN',
        isWaiverOrderReset: settings.acquisitionSettings?.isWaiverOrderReset || false,
        minimumBid: settings.acquisitionSettings?.minimumBid || 0
      }
    };
  }
}

module.exports = ESPNClient;