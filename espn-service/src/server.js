/**
 * ESPN Fantasy Football Service
 * 
 * Node.js service for handling ESPN Fantasy Football API integration
 * Provides endpoints for accessing private league data that requires ESPN cookies
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const logger = require('./utils/logger');
const errorHandler = require('./middleware/errorHandler');
const authMiddleware = require('./middleware/auth');
const cacheMiddleware = require('./middleware/cache');

// Route imports
const healthRoutes = require('./routes/health');
const authRoutes = require('./routes/auth');
const leagueRoutes = require('./routes/leagues');
const playerRoutes = require('./routes/players');
const teamRoutes = require('./routes/teams');
const draftRoutes = require('./routes/draft');

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());
app.use(compression());

// CORS configuration
app.use(cors({
  origin: [
    'http://localhost:6001',  // Python FastAPI service
    'http://localhost:8000',  // Landing page
    'http://localhost:3000',  // React dev server (if added later)
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: Math.ceil((parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 900000) / 1000)
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.originalUrl}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    timestamp: new Date().toISOString()
  });
  next();
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'ESPN Fantasy Football Service',
    version: '1.0.0',
    status: 'active',
    description: 'Node.js service for ESPN Fantasy Football API integration',
    endpoints: {
      health: '/health',
      auth: '/auth',
      leagues: '/api/leagues',
      players: '/api/players', 
      teams: '/api/teams',
      draft: '/api/draft'
    },
    documentation: '/api/docs'
  });
});

// Health check routes (no auth required)
app.use('/health', healthRoutes);

// Auth routes (no auth required for login)
app.use('/auth', authRoutes);

// API routes (require authentication)
app.use('/api/leagues', authMiddleware, cacheMiddleware, leagueRoutes);
app.use('/api/players', authMiddleware, cacheMiddleware, playerRoutes);
app.use('/api/teams', authMiddleware, cacheMiddleware, teamRoutes);
app.use('/api/draft', authMiddleware, cacheMiddleware, draftRoutes);

// API documentation endpoint
app.get('/api/docs', (req, res) => {
  res.json({
    title: 'ESPN Fantasy Football Service API',
    version: '1.0.0',
    description: 'RESTful API for ESPN Fantasy Football data integration',
    baseUrl: `http://localhost:${PORT}`,
    authentication: {
      type: 'API Key',
      header: 'X-API-Key',
      description: 'Include your API key in the X-API-Key header'
    },
    endpoints: {
      'GET /health': 'Service health check',
      'GET /health/espn': 'ESPN API connectivity check',
      'POST /auth/login': 'ESPN login to get cookies',
      'POST /auth/validate-cookies': 'Validate ESPN cookies',
      'GET /auth/cookie-status': 'Check current cookie status',
      'GET /api/leagues/:leagueId': 'Get league information',
      'GET /api/leagues/:leagueId/teams': 'Get all teams in league',
      'GET /api/leagues/:leagueId/settings': 'Get league settings',
      'GET /api/leagues/:leagueId/scoreboard': 'Get current week scoreboard',
      'GET /api/teams/:teamId': 'Get team details',
      'GET /api/teams/:teamId/roster': 'Get team roster',
      'GET /api/players/free-agents': 'Get available free agents',
      'GET /api/draft/:leagueId': 'Get draft information'
    },
    rateLimit: {
      windowMs: process.env.RATE_LIMIT_WINDOW_MS || 900000,
      maxRequests: process.env.RATE_LIMIT_MAX_REQUESTS || 100
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: `Cannot ${req.method} ${req.originalUrl}`,
    availableEndpoints: [
      'GET /',
      'GET /health',
      'GET /api/docs',
      'GET /api/leagues/:leagueId',
      'GET /api/teams/:teamId',
      'GET /api/players/free-agents'
    ]
  });
});

// Global error handler
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Start server (skip in test environment)
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    logger.info(`ESPN Fantasy Football Service started on port ${PORT}`, {
      environment: process.env.NODE_ENV,
      port: PORT,
      timestamp: new Date().toISOString()
    });
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`
🏈 ESPN Fantasy Football Service
================================
🚀 Server: http://localhost:${PORT}
📚 API Docs: http://localhost:${PORT}/api/docs
❤️  Health: http://localhost:${PORT}/health
🔧 Environment: ${process.env.NODE_ENV}
      `);
    }
  });
}

module.exports = app;