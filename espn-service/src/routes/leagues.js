/**
 * League-related routes
 */

const express = require('express');
const Joi = require('joi');
const ESPNClient = require('../utils/espnClient');
const logger = require('../utils/logger');

const router = express.Router();
const espnClient = new ESPNClient();

// Validation schemas
const leagueParamsSchema = Joi.object({
  leagueId: Joi.number().integer().positive().required()
});

const seasonQuerySchema = Joi.object({
  season: Joi.number().integer().min(2020).max(2030).default(2024)
});

const weekQuerySchema = Joi.object({
  week: Joi.number().integer().min(1).max(18).optional(),
  season: Joi.number().integer().min(2020).max(2030).default(2024)
});

/**
 * GET /api/leagues/:leagueId
 * Get basic league information
 */
router.get('/:leagueId', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = seasonQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching league ${params.leagueId} for season ${query.season}`);

    const league = await espnClient.getLeague(params.leagueId, query.season);
    
    res.json({
      success: true,
      data: league,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/leagues/:leagueId/settings
 * Get detailed league settings
 */
router.get('/:leagueId/settings', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = seasonQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching league settings ${params.leagueId} for season ${query.season}`);

    const settings = await espnClient.getLeagueSettings(params.leagueId, query.season);
    
    res.json({
      success: true,
      data: settings,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching league settings ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/leagues/:leagueId/teams
 * Get all teams in the league
 */
router.get('/:leagueId/teams', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = seasonQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching teams for league ${params.leagueId} season ${query.season}`);

    const teams = await espnClient.getLeagueTeams(params.leagueId, query.season);
    
    res.json({
      success: true,
      data: teams,
      count: teams.length,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching teams for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/leagues/:leagueId/scoreboard
 * Get current week scoreboard or specific week
 */
router.get('/:leagueId/scoreboard', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = weekQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching scoreboard for league ${params.leagueId} season ${query.season} week ${query.week || 'current'}`);

    const scoreboard = await espnClient.getScoreboard(params.leagueId, query.season, query.week);
    
    res.json({
      success: true,
      data: scoreboard,
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        week: query.week || 'current',
        matchupCount: scoreboard.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching scoreboard for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/leagues/:leagueId/standings
 * Get league standings (alias for teams with standings focus)
 */
router.get('/:leagueId/standings', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = seasonQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching standings for league ${params.leagueId} season ${query.season}`);

    const teams = await espnClient.getLeagueTeams(params.leagueId, query.season);
    
    // Sort teams by wins, then by points for
    const standings = teams
      .sort((a, b) => {
        if (a.record.wins !== b.record.wins) {
          return b.record.wins - a.record.wins;
        }
        return b.standings.pointsFor - a.standings.pointsFor;
      })
      .map((team, index) => ({
        ...team,
        rank: index + 1
      }));
    
    res.json({
      success: true,
      data: standings,
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        teamCount: standings.length,
        sortedBy: 'wins_then_points_for'
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching standings for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/leagues/:leagueId/free-agents
 * Get available free agents for the league
 */
router.get('/:leagueId/free-agents', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = leagueParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const freeAgentQuerySchema = Joi.object({
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      offset: Joi.number().integer().min(0).default(0),
      limit: Joi.number().integer().min(1).max(100).default(50)
    });

    const { error: queryError, value: query } = freeAgentQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching free agents for league ${params.leagueId} season ${query.season}`);

    const freeAgents = await espnClient.getFreeAgents(
      params.leagueId, 
      query.season, 
      query.offset, 
      query.limit
    );
    
    res.json({
      success: true,
      data: freeAgents,
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        offset: query.offset,
        limit: query.limit,
        count: freeAgents.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching free agents for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

module.exports = router;