/**
 * Draft-related routes
 */

const express = require('express');
const Joi = require('joi');
const ESPNClient = require('../utils/espnClient');
const logger = require('../utils/logger');

const router = express.Router();
const espnClient = new ESPNClient();

// Validation schemas
const draftParamsSchema = Joi.object({
  leagueId: Joi.number().integer().positive().required()
});

const seasonQuerySchema = Joi.object({
  season: Joi.number().integer().min(2020).max(2030).default(2024)
});

/**
 * GET /api/draft/:leagueId
 * Get draft information and results
 */
router.get('/:leagueId', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = draftParamsSchema.validate(req.params);
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

    logger.info(`Fetching draft information for league ${params.leagueId} season ${query.season}`);

    const draftData = await espnClient.getDraft(params.leagueId, query.season);

    // Enhance draft data with additional analysis
    const enhancedDraft = {
      ...draftData,
      analysis: analyzeDraftResults(draftData)
    };

    res.json({
      success: true,
      data: enhancedDraft,
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        totalPicks: draftData.picks?.length || 0,
        isDrafted: draftData.drafted,
        inProgress: draftData.inProgress
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching draft for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/draft/:leagueId/picks
 * Get draft picks with filtering and sorting options
 */
router.get('/:leagueId/picks', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = draftParamsSchema.validate(req.params);
    if (paramError) {
      return res.status(400).json({
        error: 'Invalid parameters',
        details: paramError.details[0].message
      });
    }

    const picksQuerySchema = Joi.object({
      season: Joi.number().integer().min(2020).max(2030).default(2024),
      round: Joi.number().integer().min(1).max(20).optional(),
      teamId: Joi.number().integer().positive().optional(),
      position: Joi.string().valid('QB', 'RB', 'WR', 'TE', 'K', 'D/ST').optional(),
      sortBy: Joi.string().valid('overall', 'round', 'team', 'position').default('overall')
    });

    const { error: queryError, value: query } = picksQuerySchema.validate(req.query);
    if (queryError) {
      return res.status(400).json({
        error: 'Invalid query parameters',
        details: queryError.details[0].message
      });
    }

    logger.info(`Fetching draft picks for league ${params.leagueId}`);

    const draftData = await espnClient.getDraft(params.leagueId, query.season);
    let picks = draftData.picks || [];

    // Apply filters
    if (query.round) {
      picks = picks.filter(pick => pick.roundId === query.round);
    }

    if (query.teamId) {
      picks = picks.filter(pick => pick.teamId === query.teamId);
    }

    // Note: Position filtering would require player data from another API call
    if (query.position) {
      logger.warn('Position filtering not implemented - requires additional player data');
    }

    // Sort picks
    switch (query.sortBy) {
      case 'overall':
        picks.sort((a, b) => a.overallPickNumber - b.overallPickNumber);
        break;
      case 'round':
        picks.sort((a, b) => {
          if (a.roundId !== b.roundId) {
            return a.roundId - b.roundId;
          }
          return a.roundPickNumber - b.roundPickNumber;
        });
        break;
      case 'team':
        picks.sort((a, b) => a.teamId - b.teamId);
        break;
      default:
        // Keep original order
        break;
    }

    // Group picks by round for easier consumption
    const picksByRound = {};
    picks.forEach(pick => {
      if (!picksByRound[pick.roundId]) {
        picksByRound[pick.roundId] = [];
      }
      picksByRound[pick.roundId].push(pick);
    });

    res.json({
      success: true,
      data: {
        picks,
        groupedByRound: picksByRound
      },
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        filters: {
          round: query.round || 'all',
          teamId: query.teamId || 'all',
          position: query.position || 'all'
        },
        sortBy: query.sortBy,
        totalPicks: picks.length,
        rounds: Object.keys(picksByRound).length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error fetching draft picks for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/draft/:leagueId/grades
 * Get draft grades and analysis by team
 */
router.get('/:leagueId/grades', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = draftParamsSchema.validate(req.params);
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

    logger.info(`Generating draft grades for league ${params.leagueId}`);

    const draftData = await espnClient.getDraft(params.leagueId, query.season);
    
    if (!draftData.drafted) {
      return res.status(400).json({
        error: 'Draft not completed',
        message: 'Cannot generate grades for incomplete draft'
      });
    }

    // Get league teams for team names
    const teams = await espnClient.getLeagueTeams(params.leagueId, query.season);
    const teamMap = new Map(teams.map(team => [team.id, team]));

    // Generate draft grades
    const grades = generateDraftGrades(draftData.picks, teamMap);

    res.json({
      success: true,
      data: grades,
      meta: {
        leagueId: params.leagueId,
        season: query.season,
        totalTeams: grades.length,
        avgGrade: calculateAverageGrade(grades)
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error generating draft grades for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * GET /api/draft/:leagueId/summary
 * Get draft summary statistics
 */
router.get('/:leagueId/summary', async (req, res, next) => {
  try {
    // Validate parameters
    const { error: paramError, value: params } = draftParamsSchema.validate(req.params);
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

    logger.info(`Generating draft summary for league ${params.leagueId}`);

    const draftData = await espnClient.getDraft(params.leagueId, query.season);
    const teams = await espnClient.getLeagueTeams(params.leagueId, query.season);

    const summary = generateDraftSummary(draftData, teams);

    res.json({
      success: true,
      data: summary,
      meta: {
        leagueId: params.leagueId,
        season: query.season
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error(`Error generating draft summary for league ${req.params.leagueId}:`, error);
    next(error);
  }
});

/**
 * Analyze draft results
 */
function analyzeDraftResults(draftData) {
  if (!draftData.picks || draftData.picks.length === 0) {
    return {
      totalPicks: 0,
      rounds: 0,
      autoDraftedPicks: 0,
      analysis: 'No draft data available'
    };
  }

  const picks = draftData.picks;
  const totalPicks = picks.length;
  const autoDraftedPicks = picks.filter(pick => pick.autoDrafted).length;
  const rounds = Math.max(...picks.map(pick => pick.roundId));
  
  // Group picks by round
  const picksByRound = {};
  picks.forEach(pick => {
    if (!picksByRound[pick.roundId]) {
      picksByRound[pick.roundId] = 0;
    }
    picksByRound[pick.roundId]++;
  });

  // Group picks by team
  const picksByTeam = {};
  picks.forEach(pick => {
    if (!picksByTeam[pick.teamId]) {
      picksByTeam[pick.teamId] = 0;
    }
    picksByTeam[pick.teamId]++;
  });

  const teamsCount = Object.keys(picksByTeam).length;
  const avgPicksPerTeam = totalPicks / teamsCount;

  return {
    totalPicks,
    rounds,
    teamsCount,
    avgPicksPerTeam: Math.round(avgPicksPerTeam * 10) / 10,
    autoDraftedPicks,
    autoDraftedPercentage: Math.round((autoDraftedPicks / totalPicks) * 100),
    picksByRound,
    picksByTeam
  };
}

/**
 * Generate draft grades for each team
 */
function generateDraftGrades(picks, teamMap) {
  const teamGrades = [];
  
  // Group picks by team
  const picksByTeam = {};
  picks.forEach(pick => {
    if (!picksByTeam[pick.teamId]) {
      picksByTeam[pick.teamId] = [];
    }
    picksByTeam[pick.teamId].push(pick);
  });

  // Generate grades for each team
  Object.entries(picksByTeam).forEach(([teamId, teamPicks]) => {
    const team = teamMap.get(parseInt(teamId));
    const grade = calculateTeamDraftGrade(teamPicks);
    
    teamGrades.push({
      teamId: parseInt(teamId),
      teamName: team?.name || `Team ${teamId}`,
      grade: grade.letter,
      score: grade.score,
      totalPicks: teamPicks.length,
      autoDraftedPicks: teamPicks.filter(pick => pick.autoDrafted).length,
      strengths: grade.strengths,
      weaknesses: grade.weaknesses,
      picks: teamPicks.sort((a, b) => a.overallPickNumber - b.overallPickNumber)
    });
  });

  return teamGrades.sort((a, b) => b.score - a.score);
}

/**
 * Calculate draft grade for a team
 */
function calculateTeamDraftGrade(picks) {
  let score = 75; // Base score
  const strengths = [];
  const weaknesses = [];

  // Penalty for auto-drafted picks
  const autoDraftedCount = picks.filter(pick => pick.autoDrafted).length;
  const autoDraftedPenalty = autoDraftedCount * 5;
  score -= autoDraftedPenalty;
  
  if (autoDraftedCount > picks.length * 0.3) {
    weaknesses.push('High number of auto-drafted picks');
  } else if (autoDraftedCount === 0) {
    strengths.push('No auto-drafted picks');
  }

  // Early round analysis (first 3 rounds)
  const earlyPicks = picks.filter(pick => pick.roundId <= 3);
  if (earlyPicks.length >= 3) {
    strengths.push('Good early round foundation');
    score += 5;
  }

  // Draft position consistency
  const draftPositions = picks.map(pick => pick.roundPickNumber);
  const avgPosition = draftPositions.reduce((a, b) => a + b, 0) / draftPositions.length;
  
  if (avgPosition <= 6) {
    strengths.push('Consistently early picks');
    score += 3;
  } else if (avgPosition >= 10) {
    strengths.push('Value picks from late positions');
    score += 2;
  }

  // Convert score to letter grade
  let letter;
  if (score >= 90) letter = 'A+';
  else if (score >= 87) letter = 'A';
  else if (score >= 83) letter = 'A-';
  else if (score >= 80) letter = 'B+';
  else if (score >= 77) letter = 'B';
  else if (score >= 73) letter = 'B-';
  else if (score >= 70) letter = 'C+';
  else if (score >= 67) letter = 'C';
  else if (score >= 63) letter = 'C-';
  else if (score >= 60) letter = 'D+';
  else if (score >= 57) letter = 'D';
  else if (score >= 53) letter = 'D-';
  else letter = 'F';

  return {
    score: Math.max(0, Math.min(100, score)),
    letter,
    strengths,
    weaknesses
  };
}

/**
 * Generate draft summary statistics
 */
function generateDraftSummary(draftData, teams) {
  const picks = draftData.picks || [];
  
  if (picks.length === 0) {
    return {
      status: 'No draft data available',
      completed: false
    };
  }

  const totalTeams = teams.length;
  const totalPicks = picks.length;
  const rounds = Math.max(...picks.map(pick => pick.roundId));
  const autoDraftedCount = picks.filter(pick => pick.autoDrafted).length;

  // Draft timing analysis
  const pickTimes = [];
  // Note: ESPN API doesn't provide pick timestamps in the basic draft detail
  // This would require additional API endpoints or data structure

  return {
    status: draftData.drafted ? 'Completed' : (draftData.inProgress ? 'In Progress' : 'Not Started'),
    completed: draftData.drafted,
    inProgress: draftData.inProgress,
    stats: {
      totalTeams,
      totalPicks,
      rounds,
      picksPerTeam: Math.round((totalPicks / totalTeams) * 10) / 10,
      autoDraftedCount,
      autoDraftedPercentage: Math.round((autoDraftedCount / totalPicks) * 100),
      manualDraftedCount: totalPicks - autoDraftedCount,
      manualDraftedPercentage: Math.round(((totalPicks - autoDraftedCount) / totalPicks) * 100)
    },
    draftParticipation: {
      fullyManual: teams.filter(team => {
        const teamPicks = picks.filter(pick => pick.teamId === team.id);
        return teamPicks.every(pick => !pick.autoDrafted);
      }).length,
      partialAuto: teams.filter(team => {
        const teamPicks = picks.filter(pick => pick.teamId === team.id);
        return teamPicks.some(pick => pick.autoDrafted) && teamPicks.some(pick => !pick.autoDrafted);
      }).length,
      fullyAuto: teams.filter(team => {
        const teamPicks = picks.filter(pick => pick.teamId === team.id);
        return teamPicks.every(pick => pick.autoDrafted);
      }).length
    }
  };
}

/**
 * Calculate average grade from grades array
 */
function calculateAverageGrade(grades) {
  if (grades.length === 0) return 'N/A';
  
  const avgScore = grades.reduce((sum, grade) => sum + grade.score, 0) / grades.length;
  
  if (avgScore >= 90) return 'A+';
  else if (avgScore >= 87) return 'A';
  else if (avgScore >= 83) return 'A-';
  else if (avgScore >= 80) return 'B+';
  else if (avgScore >= 77) return 'B';
  else if (avgScore >= 73) return 'B-';
  else if (avgScore >= 70) return 'C+';
  else if (avgScore >= 67) return 'C';
  else if (avgScore >= 63) return 'C-';
  else if (avgScore >= 60) return 'D+';
  else if (avgScore >= 57) return 'D';
  else if (avgScore >= 53) return 'D-';
  else return 'F';
}

module.exports = router;