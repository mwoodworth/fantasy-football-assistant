/**
 * Global error handling middleware
 */

const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  // Log the error
  logger.error('Unhandled error:', {
    error: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // Don't expose stack traces in production
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Determine error type and response
  let status = 500;
  let message = 'Internal server error';
  let details = null;

  if (err.name === 'ValidationError') {
    status = 400;
    message = 'Validation error';
    details = err.details || err.message;
  } else if (err.name === 'UnauthorizedError') {
    status = 401;
    message = 'Unauthorized';
  } else if (err.message.includes('ESPN Authentication failed')) {
    status = 401;
    message = 'ESPN authentication failed';
    details = 'Check your ESPN cookies configuration';
  } else if (err.message.includes('not found')) {
    status = 404;
    message = 'Resource not found';
  } else if (err.message.includes('Rate limit exceeded')) {
    status = 429;
    message = 'Rate limit exceeded';
    details = 'Please wait before making more requests';
  } else if (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT') {
    status = 503;
    message = 'Service temporarily unavailable';
    details = 'ESPN API is not responding';
  }

  // Build error response
  const errorResponse = {
    error: message,
    status,
    timestamp: new Date().toISOString(),
    path: req.originalUrl,
    method: req.method
  };

  // Add details if available
  if (details) {
    errorResponse.details = details;
  }

  // Add stack trace in development
  if (isDevelopment) {
    errorResponse.stack = err.stack;
  }

  // Add request ID if available
  if (req.id) {
    errorResponse.requestId = req.id;
  }

  res.status(status).json(errorResponse);
};

module.exports = errorHandler;