/**
 * Team-related routes
 */

const express = require('express');
const Joi = require('joi');
const ESPNClient = require('../utils/espnClient');
const logger = require('../utils/logger');

const router = express.Router();

// Helper function to create ESPN client with request-specific cookies
function getESPNClient(req) {
  const s2Cookie = req.headers['x-espn-s2'];
  const swidCookie = req.headers['x-espn-swid'];
  return new ESPNClient(s2Cookie, swidCookie);
}

// Validation schemas
const teamParamsSchema = Joi.object({
  teamId: Joi.number().integer().positive().required()
});

const rosterQuerySchema = Joi.object({
  leagueId: Joi.number().integer().positive().required(),
  season: Joi.number().integer().min(2020).max(2030).default(2024),
  week: Joi.number().integer().min(1).max(18).optional()
});

/**
 * GET /api/teams/:teamId/roster
 * Get team roster for a specific week
 */
router.get('/:teamId/roster', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = teamParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = rosterQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching roster for team ${params.teamId} in league ${query.leagueId}`);

    // Create ESPN client with request-specific cookies
    const espnClient = getESPNClient(req);
    const roster = await espnClient.getTeamRoster(
      query.leagueId,
      params.teamId,
      query.season,
      query.week
    );

    // Group roster entries by position for easier consumption
    const groupedRoster = {
      starters: [],
      bench: [],
      ir: [],
      all: roster.entries
    };

    roster.entries.forEach(entry => {
      const position = entry.position;
      
      if (position === 'BENCH') {
        groupedRoster.bench.push(entry);
      } else if (position === 'IR') {
        groupedRoster.ir.push(entry);
      } else {
        groupedRoster.starters.push(entry);
      }
    });

    res.json({
      success: true,
      data: {
        ...roster,
        grouped: groupedRoster
      },
      meta: {
        teamId: params.teamId,
        leagueId: query.leagueId,
        season: query.season,
        week: query.week || 'current',
        totalPlayers: roster.entries.length,
        starters: groupedRoster.starters.length,
        bench: groupedRoster.bench.length,
        ir: groupedRoster.ir.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching roster for team ${req.params.teamId}:`, error);
    next(error);
  }
});

/**
 * GET /api/teams/:teamId/stats
 * Get team statistics (points, record, etc.)
 */
router.get('/:teamId/stats', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = teamParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const statsQuerySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024)
    });

    const { error: queryError, value: query } = statsQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching stats for team ${params.teamId} in league ${query.leagueId}`);

    // Get all teams to find the specific team
    const espnClient = getESPNClient(req);
    const teams = await espnClient.getLeagueTeams(query.leagueId, query.season);
    const team = teams.find(t => t.id === parseInt(params.teamId));

    if (!team) {
      return res.status(404).json({
        error: 'Team not found',
        message: `Team ${params.teamId} not found in league ${query.leagueId}`
      });
    }

    // Calculate additional stats
    const totalGames = team.record.wins + team.record.losses + team.record.ties;
    const winPercentage = totalGames > 0 ? (team.record.wins / totalGames) : 0;
    const avgPointsFor = totalGames > 0 ? (team.standings.pointsFor / totalGames) : 0;
    const avgPointsAgainst = totalGames > 0 ? (team.standings.pointsAgainst / totalGames) : 0;
    const pointsDifferential = team.standings.pointsFor - team.standings.pointsAgainst;

    const enhancedStats = {
      ...team,
      calculatedStats: {
        totalGames,
        winPercentage: Math.round(winPercentage * 1000) / 1000,
        avgPointsFor: Math.round(avgPointsFor * 100) / 100,
        avgPointsAgainst: Math.round(avgPointsAgainst * 100) / 100,
        pointsDifferential: Math.round(pointsDifferential * 100) / 100
      }
    };

    res.json({
      success: true,
      data: enhancedStats,
      meta: {
        teamId: params.teamId,
        leagueId: query.leagueId,
        season: query.season
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching stats for team ${req.params.teamId}:`, error);
    next(error);
  }
});

/**
 * GET /api/teams/:teamId/matchups
 * Get team's schedule/matchups
 */
router.get('/:teamId/matchups', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = teamParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const matchupQuerySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      week: Joi.number().integer().min(1).max(18).optional()
    });

    const { error: queryError, value: query } = matchupQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching matchups for team ${params.teamId} in league ${query.leagueId}`);

    const espnClient = getESPNClient(req);
    const scoreboard = await espnClient.getScoreboard(query.leagueId, query.season, query.week);
    
    // Filter matchups for this team
    const teamMatchups = scoreboard.filter(matchup => 
      matchup.home.teamId === parseInt(params.teamId) || 
      matchup.away.teamId === parseInt(params.teamId)
    );

    // Enhance matchup data with team perspective
    const enhancedMatchups = teamMatchups.map(matchup => {
      const isHome = matchup.home.teamId === parseInt(params.teamId);
      const teamScore = isHome ? matchup.home.totalPoints : matchup.away.totalPoints;
      const opponentScore = isHome ? matchup.away.totalPoints : matchup.home.totalPoints;
      const opponentTeamId = isHome ? matchup.away.teamId : matchup.home.teamId;

      let result = 'TBD';
      if (matchup.winner !== 'UNDECIDED') {
        if (
          (isHome && matchup.winner === 'HOME') || 
          (!isHome && matchup.winner === 'AWAY')
        ) {
          result = 'WIN';
        } else if (matchup.winner === 'TIE') {
          result = 'TIE';
        } else {
          result = 'LOSS';
        }
      }

      return {
        ...matchup,
        teamPerspective: {
          teamId: parseInt(params.teamId),
          isHome,
          teamScore,
          opponentTeamId,
          opponentScore,
          result,
          pointsDifferential: teamScore - opponentScore
        }
      };
    });

    res.json({
      success: true,
      data: enhancedMatchups,
      meta: {
        teamId: params.teamId,
        leagueId: query.leagueId,
        season: query.season,
        week: query.week || 'all',
        matchupCount: enhancedMatchups.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching matchups for team ${req.params.teamId}:`, error);
    next(error);
  }
});

/**
 * GET /api/teams/compare
 * Compare two teams head-to-head
 */
router.get('/compare', async (req, res, next) => {
  try {
    const compareQuerySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      team1Id: Joi.number().integer().positive().required(),
      team2Id: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024)
    });

    const { error: queryError, value: query } = compareQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Comparing teams ${query.team1Id} vs ${query.team2Id} in league ${query.leagueId}`);

    // Get all teams to find the specific teams
    const espnClient = getESPNClient(req);
    const teams = await espnClient.getLeagueTeams(query.leagueId, query.season);
    const team1 = teams.find(t => t.id === parseInt(query.team1Id));
    const team2 = teams.find(t => t.id === parseInt(query.team2Id));

    if (!team1 || !team2) {
      return res.status(404).json({
        error: 'Team not found',
        message: `One or both teams not found in league ${query.leagueId}`
      });
    }

    // Get head-to-head matchups
    const scoreboard = await espnClient.getScoreboard(query.leagueId, query.season);
    const headToHeadMatchups = scoreboard.filter(matchup => 
      (matchup.home.teamId === parseInt(query.team1Id) && matchup.away.teamId === parseInt(query.team2Id)) ||
      (matchup.home.teamId === parseInt(query.team2Id) && matchup.away.teamId === parseInt(query.team1Id))
    );

    // Calculate head-to-head record
    let team1Wins = 0;
    let team2Wins = 0;
    let ties = 0;

    headToHeadMatchups.forEach(matchup => {
      if (matchup.winner === 'TIE') {
        ties++;
      } else if (
        (matchup.home.teamId === parseInt(query.team1Id) && matchup.winner === 'HOME') ||
        (matchup.away.teamId === parseInt(query.team1Id) && matchup.winner === 'AWAY')
      ) {
        team1Wins++;
      } else if (matchup.winner !== 'UNDECIDED') {
        team2Wins++;
      }
    });

    const comparison = {
      team1: {
        ...team1,
        headToHeadRecord: { wins: team1Wins, losses: team2Wins, ties }
      },
      team2: {
        ...team2,
        headToHeadRecord: { wins: team2Wins, losses: team1Wins, ties }
      },
      headToHeadMatchups,
      summary: {
        totalMeetings: headToHeadMatchups.length,
        team1Advantages: [],
        team2Advantages: [],
        ties: []
      }
    };

    // Determine advantages
    if (team1.record.wins > team2.record.wins) {
      comparison.summary.team1Advantages.push('Better overall record');
    } else if (team2.record.wins > team1.record.wins) {
      comparison.summary.team2Advantages.push('Better overall record');
    } else {
      comparison.summary.ties.push('Equal overall record');
    }

    if (team1.standings.pointsFor > team2.standings.pointsFor) {
      comparison.summary.team1Advantages.push('Higher points scored');
    } else if (team2.standings.pointsFor > team1.standings.pointsFor) {
      comparison.summary.team2Advantages.push('Higher points scored');
    } else {
      comparison.summary.ties.push('Equal points scored');
    }

    if (team1.standings.pointsAgainst < team2.standings.pointsAgainst) {
      comparison.summary.team1Advantages.push('Fewer points allowed');
    } else if (team2.standings.pointsAgainst < team1.standings.pointsAgainst) {
      comparison.summary.team2Advantages.push('Fewer points allowed');
    } else {
      comparison.summary.ties.push('Equal points allowed');
    }

    if (team1Wins > team2Wins) {
      comparison.summary.team1Advantages.push('Better head-to-head record');
    } else if (team2Wins > team1Wins) {
      comparison.summary.team2Advantages.push('Better head-to-head record');
    } else {
      comparison.summary.ties.push('Equal head-to-head record');
    }

    res.json({
      success: true,
      data: comparison,
      meta: {
        leagueId: query.leagueId,
        season: query.season,
        comparedTeams: [query.team1Id, query.team2Id]
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error comparing teams:`, error);
    next(error);
  }
});

module.exports = router;