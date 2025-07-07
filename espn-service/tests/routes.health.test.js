/**
 * Tests for health.js routes
 */

const request = require('supertest');
const express = require('express');

// Mock dependencies
jest.mock('../src/utils/espnClient');
jest.mock('../src/middleware/cache', () => ({
  cache: {
    getStats: jest.fn(() => ({
      enabled: true,
      totalEntries: 10,
      hitRate: 0.85,
      size: '2.5MB'
    })),
    clear: jest.fn()
  }
}));

jest.mock('../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  warn: jest.fn()
}));

const ESPNClient = require('../src/utils/espnClient');
const healthRoutes = require('../src/routes/health');

// Create test app
const app = express();
app.use(express.json());
app.use('/health', healthRoutes);

describe('Health Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Set up environment variables for tests
    process.env.NODE_ENV = 'test';
    process.env.ESPN_BASE_URL = 'https://test.espn.com';
  });

  describe('GET /health', () => {
    it('should return basic health check', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'ESPN Fantasy Football Service',
        status: 'healthy',
        timestamp: expect.any(String),
        uptime: expect.any(Number),
        environment: 'test',
        version: '1.0.0',
        memory: {
          used: expect.any(Number),
          total: expect.any(Number),
          external: expect.any(Number)
        },
        cache: expect.any(Object)
      });
    });
  });

  describe('GET /health/detailed', () => {
    beforeEach(() => {
      // Mock ESPN client
      ESPNClient.mockImplementation(() => ({
        testConnection: jest.fn()
      }));
    });

    it('should return detailed health check when all services are healthy', async () => {
      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockResolvedValue({
        connected: true,
        status: 200,
        message: 'ESPN API connection successful'
      });

      const response = await request(app)
        .get('/health/detailed')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'ESPN Fantasy Football Service',
        status: 'healthy',
        timestamp: expect.any(String),
        uptime: expect.any(Number),
        checks: {
          service: { status: 'healthy' },
          espn: {
            status: 'healthy',
            connected: true,
            message: 'ESPN API connection successful'
          },
          cache: {
            status: 'healthy',
            enabled: true
          },
          environment: {
            status: 'healthy',
            variables: expect.any(Object)
          }
        }
      });
    });

    it('should return unhealthy status when ESPN is down', async () => {
      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockResolvedValue({
        connected: false,
        status: 0,
        message: 'Connection failed'
      });

      const response = await request(app)
        .get('/health/detailed')
        .expect(503);

      expect(response.body.status).toBe('unhealthy');
      expect(response.body.checks.espn.status).toBe('unhealthy');
    });

    it('should return warnings when ESPN cookies are not configured', async () => {
      delete process.env.ESPN_COOKIE_S2;
      delete process.env.ESPN_COOKIE_SWID;

      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockResolvedValue({
        connected: true,
        status: 200,
        message: 'ESPN API connection successful'
      });

      const response = await request(app)
        .get('/health/detailed')
        .expect(200);

      expect(response.body.checks.environment.warnings).toContain(
        'ESPN cookies not configured - private leagues will not be accessible'
      );
    });
  });

  describe('GET /health/espn', () => {
    beforeEach(() => {
      ESPNClient.mockImplementation(() => ({
        testConnection: jest.fn()
      }));
    });

    it('should return ESPN health check when connection is successful', async () => {
      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockResolvedValue({
        connected: true,
        status: 200,
        message: 'ESPN API connection successful'
      });

      const response = await request(app)
        .get('/health/espn')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'ESPN API',
        status: 'healthy',
        timestamp: expect.any(String),
        responseTime: expect.any(Number),
        details: {
          connected: true,
          message: 'ESPN API connection successful',
          baseUrl: 'https://test.espn.com',
          hasCredentials: false
        }
      });
    });

    it('should return unhealthy status when ESPN connection fails', async () => {
      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockResolvedValue({
        connected: false,
        status: 0,
        message: 'Connection timeout'
      });

      const response = await request(app)
        .get('/health/espn')
        .expect(503);

      expect(response.body).toMatchObject({
        service: 'ESPN API',
        status: 'unhealthy',
        details: {
          connected: false
        }
      });
    });

    it('should handle ESPN client errors', async () => {
      const mockESPNClient = new ESPNClient();
      mockESPNClient.testConnection.mockRejectedValue(new Error('Network error'));

      const response = await request(app)
        .get('/health/espn')
        .expect(503);

      expect(response.body).toMatchObject({
        service: 'ESPN API',
        status: 'unhealthy',
        error: 'Network error',
        details: {
          connected: false
        }
      });
    });
  });

  describe('GET /health/cache', () => {
    it('should return cache health status', async () => {
      const response = await request(app)
        .get('/health/cache')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'Cache',
        status: 'healthy',
        timestamp: expect.any(String),
        stats: {
          enabled: true,
          totalEntries: 10,
          hitRate: 0.85,
          size: '2.5MB'
        }
      });
    });

    it('should handle cache errors', async () => {
      const { cache } = require('../src/middleware/cache');
      cache.getStats.mockImplementation(() => {
        throw new Error('Cache error');
      });

      const response = await request(app)
        .get('/health/cache')
        .expect(500);

      expect(response.body).toMatchObject({
        service: 'Cache',
        status: 'unhealthy',
        error: 'Cache error'
      });
    });
  });

  describe('DELETE /health/cache', () => {
    it('should clear cache successfully', async () => {
      const { cache } = require('../src/middleware/cache');
      const statsBefore = {
        enabled: true,
        totalEntries: 10,
        hitRate: 0.85
      };
      const statsAfter = {
        enabled: true,
        totalEntries: 0,
        hitRate: 0
      };

      cache.getStats
        .mockReturnValueOnce(statsBefore)
        .mockReturnValueOnce(statsAfter);

      const response = await request(app)
        .delete('/health/cache')
        .expect(200);

      expect(response.body).toMatchObject({
        message: 'Cache cleared successfully',
        before: statsBefore,
        after: statsAfter
      });

      expect(cache.clear).toHaveBeenCalled();
    });

    it('should handle cache clear errors', async () => {
      const { cache } = require('../src/middleware/cache');
      cache.clear.mockImplementation(() => {
        throw new Error('Clear failed');
      });

      const response = await request(app)
        .delete('/health/cache')
        .expect(500);

      expect(response.body).toMatchObject({
        error: 'Failed to clear cache',
        message: 'Clear failed'
      });
    });
  });
});