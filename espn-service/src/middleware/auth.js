/**
 * Authentication middleware for ESPN service
 */

const logger = require('../utils/logger');

/**
 * Middleware to validate API key
 */
const authMiddleware = (req, res, next) => {
  const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
  const expectedApiKey = process.env.API_KEY;

  // Skip auth in development if no API key is configured or if it's the default value
  if (process.env.NODE_ENV === 'development' && (!expectedApiKey || expectedApiKey === 'your_secure_api_key_here')) {
    logger.warn('No API key configured or using default, skipping authentication in development mode');
    return next();
  }

  if (!expectedApiKey || expectedApiKey === 'your_secure_api_key_here') {
    logger.error('API_KEY not properly configured in environment variables');
    return res.status(500).json({
      error: 'Server configuration error',
      message: 'Authentication not properly configured'
    });
  }

  if (!apiKey) {
    logger.warn('Request made without API key', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      path: req.path
    });
    
    return res.status(401).json({
      error: 'Authentication required',
      message: 'API key must be provided in X-API-Key header or Authorization header',
      example: {
        'X-API-Key': 'your-api-key-here'
      }
    });
  }

  if (apiKey !== expectedApiKey) {
    logger.warn('Request made with invalid API key', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      path: req.path,
      providedKey: apiKey.substring(0, 8) + '...' // Log partial key for debugging
    });
    
    return res.status(401).json({
      error: 'Invalid authentication',
      message: 'The provided API key is not valid'
    });
  }

  // API key is valid, proceed
  logger.debug('API key validated successfully', {
    ip: req.ip,
    path: req.path
  });
  
  next();
};

module.exports = authMiddleware;