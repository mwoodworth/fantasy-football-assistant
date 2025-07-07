/**
 * Tests for server.js - Express app configuration and middleware
 */

const request = require('supertest');

// Mock the modules before requiring the app
jest.mock('../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  warn: jest.fn()
}));

jest.mock('../src/middleware/errorHandler', () => (err, req, res, next) => {
  res.status(500).json({ error: 'Internal server error' });
});

jest.mock('../src/middleware/auth', () => (req, res, next) => {
  next();
});

jest.mock('../src/middleware/cache', () => (req, res, next) => {
  next();
});

// Mock all route modules
jest.mock('../src/routes/health', () => {
  const express = require('express');
  const router = express.Router();
  router.get('/', (req, res) => res.json({ status: 'healthy' }));
  return router;
});

jest.mock('../src/routes/auth', () => {
  const express = require('express');
  const router = express.Router();
  router.post('/login', (req, res) => res.json({ success: true }));
  return router;
});

jest.mock('../src/routes/leagues', () => {
  const express = require('express');
  const router = express.Router();
  router.get('/:leagueId', (req, res) => res.json({ leagueId: req.params.leagueId }));
  return router;
});

jest.mock('../src/routes/players', () => {
  const express = require('express');
  const router = express.Router();
  router.get('/free-agents', (req, res) => res.json({ players: [] }));
  return router;
});

jest.mock('../src/routes/teams', () => {
  const express = require('express');
  const router = express.Router();
  router.get('/:teamId', (req, res) => res.json({ teamId: req.params.teamId }));
  return router;
});

jest.mock('../src/routes/draft', () => {
  const express = require('express');
  const router = express.Router();
  router.get('/:leagueId', (req, res) => res.json({ leagueId: req.params.leagueId }));
  return router;
});

// Prevent server from starting during tests
process.env.NODE_ENV = 'test';

const app = require('../src/server');

describe('ESPN Service Server', () => {
  describe('Root endpoint', () => {
    it('should return service information', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'ESPN Fantasy Football Service',
        version: '1.0.0',
        status: 'active',
        description: 'Node.js service for ESPN Fantasy Football API integration',
        endpoints: expect.any(Object)
      });
    });
  });

  describe('API Documentation', () => {
    it('should return API documentation', async () => {
      const response = await request(app)
        .get('/api/docs')
        .expect(200);

      expect(response.body).toMatchObject({
        title: 'ESPN Fantasy Football Service API',
        version: '1.0.0',
        description: expect.any(String),
        baseUrl: expect.stringContaining('localhost'),
        authentication: expect.any(Object),
        endpoints: expect.any(Object)
      });
    });
  });

  describe('Health routes', () => {
    it('should handle health check requests', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toEqual({ status: 'healthy' });
    });
  });

  describe('Auth routes', () => {
    it('should handle auth login requests', async () => {
      const response = await request(app)
        .post('/auth/login')
        .send({ username: 'test', password: 'test' })
        .expect(200);

      expect(response.body).toEqual({ success: true });
    });
  });

  describe('API routes', () => {
    it('should handle league requests', async () => {
      const response = await request(app)
        .get('/api/leagues/12345')
        .expect(200);

      expect(response.body).toEqual({ leagueId: '12345' });
    });

    it('should handle player requests', async () => {
      const response = await request(app)
        .get('/api/players/free-agents')
        .expect(200);

      expect(response.body).toEqual({ players: [] });
    });

    it('should handle team requests', async () => {
      const response = await request(app)
        .get('/api/teams/1')
        .expect(200);

      expect(response.body).toEqual({ teamId: '1' });
    });

    it('should handle draft requests', async () => {
      const response = await request(app)
        .get('/api/draft/12345')
        .expect(200);

      expect(response.body).toEqual({ leagueId: '12345' });
    });
  });

  describe('404 handler', () => {
    it('should return 404 for unknown endpoints', async () => {
      const response = await request(app)
        .get('/unknown/endpoint')
        .expect(404);

      expect(response.body).toMatchObject({
        error: 'Endpoint not found',
        message: expect.stringContaining('Cannot GET /unknown/endpoint'),
        availableEndpoints: expect.any(Array)
      });
    });
  });

  describe('CORS', () => {
    it('should include CORS headers', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.headers).toHaveProperty('access-control-allow-origin');
    });
  });

  describe('Security headers', () => {
    it('should include security headers from helmet', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      // Helmet adds various security headers
      expect(response.headers).toHaveProperty('x-content-type-options');
    });
  });

  describe('Request body parsing', () => {
    it('should parse JSON request bodies', async () => {
      const response = await request(app)
        .post('/auth/login')
        .send({ test: 'data' })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.body).toEqual({ success: true });
    });
  });
});