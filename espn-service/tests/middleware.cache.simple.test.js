/**
 * Simplified tests for cache middleware
 */

const request = require('supertest');
const express = require('express');

// Import the cache middleware
const cacheMiddleware = require('../src/middleware/cache');
const { cache } = require('../src/middleware/cache');

describe('Cache Middleware - Simplified', () => {
  let app;

  beforeEach(() => {
    // Clear cache before each test
    cache.clear();
    
    // Create test app
    app = express();
    app.use(express.json());
    app.use(cacheMiddleware);
  });

  describe('cache utility', () => {
    it('should store and retrieve values', () => {
      cache.set('test-key', { data: 'test' });
      const value = cache.get('test-key');
      
      expect(value).toEqual({ data: 'test' });
    });

    it('should return cache statistics', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      
      const stats = cache.getStats();
      
      expect(stats).toMatchObject({
        enabled: true,
        totalEntries: 2
      });
    });

    it('should clear all values', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      cache.clear();
      
      expect(cache.get('key1')).toBeNull();
      expect(cache.get('key2')).toBeNull();
    });
  });

  describe('middleware integration', () => {
    beforeEach(() => {
      app.get('/test', (req, res) => {
        res.json({ message: 'Hello World', timestamp: Date.now() });
      });

      app.get('/cached', (req, res) => {
        // Simulate caching by returning the same data each time
        res.json({ message: 'Cached response', value: 12345 });
      });
    });

    it('should handle GET requests', async () => {
      const response = await request(app)
        .get('/test')
        .expect(200);

      expect(response.body).toMatchObject({
        message: 'Hello World'
      });
      expect(response.headers['x-cache']).toBe('MISS');
    });

    it('should serve cached responses', async () => {
      // First request
      const response1 = await request(app)
        .get('/cached')
        .expect(200);

      expect(response1.headers['x-cache']).toBe('MISS');

      // Second request should be cached
      const response2 = await request(app)
        .get('/cached')
        .expect(200);

      expect(response2.headers['x-cache']).toBe('HIT');
      expect(response2.body).toEqual(response1.body);
    });

    it('should not cache POST requests', async () => {
      app.post('/no-cache', (req, res) => {
        res.json({ message: 'Not cached' });
      });

      const response = await request(app)
        .post('/no-cache')
        .expect(200);

      // POST requests should not have cache headers
      expect(response.headers['x-cache']).toBeUndefined();
    });
  });

  describe('cache key generation', () => {
    it('should generate consistent keys', () => {
      const req1 = { method: 'GET', originalUrl: '/api/test', query: {} };
      const req2 = { method: 'GET', originalUrl: '/api/test', query: {} };
      
      const key1 = cache.generateKey(req1);
      const key2 = cache.generateKey(req2);
      
      expect(key1).toBe(key2);
    });

    it('should generate different keys for different URLs', () => {
      const req1 = { method: 'GET', originalUrl: '/api/test1', query: {} };
      const req2 = { method: 'GET', originalUrl: '/api/test2', query: {} };
      
      const key1 = cache.generateKey(req1);
      const key2 = cache.generateKey(req2);
      
      expect(key1).not.toBe(key2);
    });
  });
});