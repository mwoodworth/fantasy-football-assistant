/**
 * Health check routes
 */

const express = require('express');
const ESPNClient = require('../utils/espnClient');
const { cache } = require('../middleware/cache');
const logger = require('../utils/logger');

const router = express.Router();
const espnClient = new ESPNClient();

/**
 * Basic health check
 */
router.get('/', (req, res) => {
  const healthCheck = {
    service: 'ESPN Fantasy Football Service',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV,
    version: '1.0.0',
    memory: {
      used: Math.round((process.memoryUsage().heapUsed / 1024 / 1024) * 100) / 100,
      total: Math.round((process.memoryUsage().heapTotal / 1024 / 1024) * 100) / 100,
      external: Math.round((process.memoryUsage().external / 1024 / 1024) * 100) / 100
    },
    cache: cache.getStats()
  };

  res.json(healthCheck);
});

/**
 * Detailed health check with dependencies
 */
router.get('/detailed', async (req, res) => {
  const startTime = Date.now();
  const checks = {
    service: { status: 'healthy' },
    espn: { status: 'unknown' },
    cache: { status: 'unknown' },
    environment: { status: 'unknown' }
  };

  // Check ESPN API connectivity
  try {
    const espnStatus = await espnClient.testConnection();
    checks.espn = {
      status: espnStatus.connected ? 'healthy' : 'unhealthy',
      connected: espnStatus.connected,
      message: espnStatus.message,
      responseTime: Date.now() - startTime
    };
  } catch (error) {
    checks.espn = {
      status: 'unhealthy',
      connected: false,
      error: error.message
    };
  }

  // Check cache
  try {
    const cacheStats = cache.getStats();
    checks.cache = {
      status: cacheStats.enabled ? 'healthy' : 'disabled',
      ...cacheStats
    };
  } catch (error) {
    checks.cache = {
      status: 'unhealthy',
      error: error.message
    };
  }

  // Check environment variables
  const requiredEnvVars = ['ESPN_BASE_URL'];
  const optionalEnvVars = ['ESPN_COOKIE_S2', 'ESPN_COOKIE_SWID', 'API_KEY'];
  
  const envStatus = {
    required: {},
    optional: {}
  };

  requiredEnvVars.forEach(envVar => {
    envStatus.required[envVar] = !!process.env[envVar];
  });

  optionalEnvVars.forEach(envVar => {
    envStatus.optional[envVar] = !!process.env[envVar];
  });

  const allRequiredPresent = Object.values(envStatus.required).every(Boolean);
  
  checks.environment = {
    status: allRequiredPresent ? 'healthy' : 'unhealthy',
    variables: envStatus,
    warnings: []
  };

  if (!process.env.ESPN_COOKIE_S2 || !process.env.ESPN_COOKIE_SWID) {
    checks.environment.warnings.push('ESPN cookies not configured - private leagues will not be accessible');
  }

  if (!process.env.API_KEY && process.env.NODE_ENV !== 'development') {
    checks.environment.warnings.push('API_KEY not configured - authentication disabled');
  }

  // Overall health status
  const overallStatus = Object.values(checks).every(check => 
    check.status === 'healthy' || check.status === 'disabled'
  ) ? 'healthy' : 'unhealthy';

  const healthCheck = {
    service: 'ESPN Fantasy Football Service',
    status: overallStatus,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV,
    version: '1.0.0',
    checks,
    responseTime: Date.now() - startTime
  };

  const statusCode = overallStatus === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthCheck);
});

/**
 * ESPN-specific health check
 */
router.get('/espn', async (req, res) => {
  try {
    const startTime = Date.now();
    const espnStatus = await espnClient.testConnection();
    const responseTime = Date.now() - startTime;

    const result = {
      service: 'ESPN API',
      status: espnStatus.connected ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      responseTime,
      details: {
        connected: espnStatus.connected,
        message: espnStatus.message,
        baseUrl: process.env.ESPN_BASE_URL,
        hasCredentials: !!(process.env.ESPN_COOKIE_S2 && process.env.ESPN_COOKIE_SWID)
      }
    };

    const statusCode = espnStatus.connected ? 200 : 503;
    res.status(statusCode).json(result);
    
  } catch (error) {
    logger.error('ESPN health check failed:', error);
    
    res.status(503).json({
      service: 'ESPN API',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message,
      details: {
        connected: false,
        baseUrl: process.env.ESPN_BASE_URL,
        hasCredentials: !!(process.env.ESPN_COOKIE_S2 && process.env.ESPN_COOKIE_SWID)
      }
    });
  }
});

/**
 * Cache health and management
 */
router.get('/cache', (req, res) => {
  try {
    const stats = cache.getStats();
    
    res.json({
      service: 'Cache',
      status: stats.enabled ? 'healthy' : 'disabled',
      timestamp: new Date().toISOString(),
      stats
    });
  } catch (error) {
    res.status(500).json({
      service: 'Cache',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * Clear cache (useful for debugging)
 */
router.delete('/cache', (req, res) => {
  try {
    const statsBeforeClear = cache.getStats();
    cache.clear();
    const statsAfterClear = cache.getStats();
    
    logger.info('Cache cleared via health endpoint', {
      entriesCleared: statsBeforeClear.totalEntries,
      ip: req.ip
    });
    
    res.json({
      message: 'Cache cleared successfully',
      timestamp: new Date().toISOString(),
      before: statsBeforeClear,
      after: statsAfterClear
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to clear cache',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;