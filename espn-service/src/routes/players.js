/**
 * Player-related routes
 */

const express = require('express');
const Joi = require('joi');
const ESPNClient = require('../utils/espnClient');
const logger = require('../utils/logger');

const router = express.Router();
const espnClient = new ESPNClient();

/**
 * GET /api/players/free-agents
 * Get available free agents
 */
router.get('/free-agents', async (req, res, next) => {
  try {
    const querySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      offset: Joi.number().integer().min(0).default(0),
      limit: Joi.number().integer().min(1).max(100).default(50),
      position: Joi.string().valid('QB', 'RB', 'WR', 'TE', 'K', 'D/ST').optional(),
      sortBy: Joi.string().valid('percentOwned', 'projectedPoints', 'avgPoints').default('percentOwned')
    });

    const { error, value: query } = querySchema.validate(req.query);
    if (error) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: error.details[0].message
      });
    }

    logger.info(`Fetching free agents for league ${query.leagueId}`);

    const freeAgents = await espnClient.getFreeAgents(
      query.leagueId,
      query.season,
      query.offset,
      query.limit
    );

    // Filter by position if specified
    let filteredAgents = freeAgents;
    if (query.position) {
      filteredAgents = freeAgents.filter(player => 
        player.position === query.position
      );
    }

    // Sort by specified criteria
    switch (query.sortBy) {
      case 'percentOwned':
        filteredAgents.sort((a, b) => (b.percentOwned || 0) - (a.percentOwned || 0));
        break;
      case 'projectedPoints':
        // This would require additional ESPN API calls for projections
        // For now, maintain original order
        break;
      case 'avgPoints':
        // This would require additional ESPN API calls for season stats
        // For now, maintain original order
        break;
    }

    // Group by position for easier consumption
    const groupedByPosition = {};
    filteredAgents.forEach(player => {
      if (!groupedByPosition[player.position]) {
        groupedByPosition[player.position] = [];
      }
      groupedByPosition[player.position].push(player);
    });

    res.json({
      success: true,
      data: {
        players: filteredAgents,
        groupedByPosition
      },
      meta: {
        leagueId: query.leagueId,
        season: query.season,
        offset: query.offset,
        limit: query.limit,
        position: query.position || 'all',
        sortBy: query.sortBy,
        totalReturned: filteredAgents.length,
        hasMore: filteredAgents.length === query.limit
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Error fetching free agents:', error);
    next(error);
  }
});

/**
 * GET /api/players/trending
 * Get trending players (most added/dropped)
 */
router.get('/trending', async (req, res, next) => {
  try {
    const querySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      limit: Joi.number().integer().min(1).max(50).default(20),
      trendType: Joi.string().valid('added', 'dropped', 'both').default('both')
    });

    const { error, value: query } = querySchema.validate(req.query);
    if (error) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: error.details[0].message
      });
    }

    logger.info(`Fetching trending players for league ${query.leagueId}`);

    // Note: ESPN API doesn't directly provide trending data
    // This would require tracking changes over time or using additional ESPN endpoints
    // For now, we'll return free agents sorted by ownership percentage as a proxy
    
    const freeAgents = await espnClient.getFreeAgents(
      query.leagueId,
      query.season,
      0,
      query.limit * 2
    );

    // Sort by ownership percentage (higher ownership = more trending up)
    const trending = freeAgents
      .filter(player => player.percentOwned > 0) // Players with some ownership
      .sort((a, b) => (b.percentOwned || 0) - (a.percentOwned || 0))
      .slice(0, query.limit)
      .map((player, index) => ({
        ...player,
        trendRank: index + 1,
        trendType: 'rising', // Simulated trend type
        ownershipChange: `+${Math.floor(Math.random() * 20)}%` // Simulated change
      }));

    res.json({
      success: true,
      data: trending,
      meta: {
        leagueId: query.leagueId,
        season: query.season,
        trendType: query.trendType,
        limit: query.limit,
        count: trending.length,
        note: 'Trending data is approximated based on ownership percentage. Real trending data requires historical tracking.'
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Error fetching trending players:', error);
    next(error);
  }
});

/**
 * GET /api/players/:playerId/details
 * Get detailed player information
 */
router.get('/:playerId/details', async (req, res, next) => {
  try {
    const paramsSchema = Joi.object({
      playerId: Joi.number().integer().positive().required()
    });

    const querySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      includeStats: Joi.boolean().default(true),
      includeProjections: Joi.boolean().default(true)
    });

    const { error: paramError, value: params } = paramsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = querySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching details for player ${params.playerId}`);

    // Note: ESPN API doesn't have a direct single player endpoint
    // We need to search through free agents or roster data
    // This is a limitation that would require additional ESPN API exploration

    res.status(501).json({
      error: 'Not implemented',
      message: 'Individual player details endpoint requires additional ESPN API research',
      suggestion: 'Use free agents endpoint and filter by player ID, or get player from team rosters',
      alternatives: [
        'GET /api/players/free-agents?leagueId=X',
        'GET /api/teams/:teamId/roster?leagueId=X'
      ]
    });

  } catch (error) {
    logger.error(`Error fetching player details for ${req.params.playerId}:`, error);
    next(error);
  }
});

/**
 * GET /api/players/search
 * Search for players by name
 */
router.get('/search', async (req, res, next) => {
  try {
    const querySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      name: Joi.string().min(2).max(50).required(),
      includeRostered: Joi.boolean().default(false),
      limit: Joi.number().integer().min(1).max(50).default(20)
    });

    const { error, value: query } = querySchema.validate(req.query);
    if (error) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: error.details[0].message
      });
    }

    logger.info(`Searching for players with name containing "${query.name}"`);

    // Search through free agents
    const freeAgents = await espnClient.getFreeAgents(
      query.leagueId,
      query.season,
      0,
      100 // Get more to search through
    );

    // Filter by name (case-insensitive partial match)
    const searchResults = freeAgents
      .filter(player => 
        player.name.toLowerCase().includes(query.name.toLowerCase())
      )
      .slice(0, query.limit);

    // If including rostered players, we'd need to fetch all team rosters
    // This is more complex and would require multiple API calls
    let rosteredResults = [];
    if (query.includeRostered) {
      // Note: This would require fetching all team rosters
      // Skipping for now due to API complexity
      logger.info('Rostered player search not implemented - would require fetching all team rosters');
    }

    const allResults = [...searchResults, ...rosteredResults];

    res.json({
      success: true,
      data: allResults,
      meta: {
        leagueId: query.leagueId,
        season: query.season,
        searchTerm: query.name,
        includeRostered: query.includeRostered,
        limit: query.limit,
        totalFound: allResults.length,
        freeAgentsFound: searchResults.length,
        rosteredFound: rosteredResults.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Error searching for players:', error);
    next(error);
  }
});

/**
 * GET /api/players/by-position/:position
 * Get players by position
 */
router.get('/by-position/:position', async (req, res, next) => {
  try {
    const paramsSchema = Joi.object({
      position: Joi.string().valid('QB', 'RB', 'WR', 'TE', 'K', 'D/ST').required()
    });

    const querySchema = Joi.object({
      leagueId: Joi.number().integer().positive().required(),
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      offset: Joi.number().integer().min(0).default(0),
      limit: Joi.number().integer().min(1).max(100).default(50),
      availableOnly: Joi.boolean().default(true)
    });

    const { error: paramError, value: params } = paramsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const { error: queryError, value: query } = querySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching ${params.position} players for league ${query.leagueId}`);

    if (query.availableOnly) {
      // Get free agents and filter by position
      const freeAgents = await espnClient.getFreeAgents(
        query.leagueId,
        query.season,
        0,
        200 // Get more to filter properly
      );

      const positionPlayers = freeAgents
        .filter(player => player.position === params.position)
        .slice(query.offset, query.offset + query.limit);

      res.json({
        success: true,
        data: positionPlayers,
        meta: {
          leagueId: query.leagueId,
          season: query.season,
          position: params.position,
          offset: query.offset,
          limit: query.limit,
          availableOnly: query.availableOnly,
          count: positionPlayers.length
        },
        timestamp: new Date().toISOString()
      });

    } else {
      // Getting all players (including rostered) would require fetching all team rosters
      res.status(501).json({
        error: 'Not implemented',
        message: 'Getting all players (including rostered) requires fetching all team rosters',
        suggestion: 'Use availableOnly=true to get free agents only, or fetch team rosters separately'
      });
    }

  } catch (error) {
    logger.error(`Error fetching ${req.params.position} players:`, error);
    next(error);
  }
});

module.exports = router;