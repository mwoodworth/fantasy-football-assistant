/**
 * In-memory caching middleware for ESPN service
 * Reduces API calls to ESPN by caching responses
 */

const logger = require('../utils/logger');

class MemoryCache {
  constructor() {
    this.cache = new Map();
    this.ttl = parseInt(process.env.CACHE_TTL_MINUTES) * 60 * 1000 || 15 * 60 * 1000; // 15 minutes default
    this.enabled = process.env.ENABLE_CACHING !== 'false';
    
    // Clean up expired entries every 5 minutes
    if (this.enabled) {
      setInterval(() => this.cleanup(), 5 * 60 * 1000);
    }
  }

  generateKey(req) {
    const { method, originalUrl, query } = req;
    return `${method}:${originalUrl}:${JSON.stringify(query || {})}`;
  }

  get(key) {
    if (!this.enabled) return null;
    
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    logger.debug('Cache hit', { key, size: this.cache.size });
    return item.data;
  }

  set(key, data) {
    if (!this.enabled) return;
    
    this.cache.set(key, {
      data,
      expiry: Date.now() + this.ttl,
      createdAt: Date.now()
    });
    
    logger.debug('Cache set', { key, size: this.cache.size, ttl: this.ttl });
  }

  delete(key) {
    const deleted = this.cache.delete(key);
    if (deleted) {
      logger.debug('Cache entry deleted', { key });
    }
    return deleted;
  }

  clear() {
    const size = this.cache.size;
    this.cache.clear();
    logger.info('Cache cleared', { previousSize: size });
  }

  cleanup() {
    const now = Date.now();
    let cleaned = 0;
    
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key);
        cleaned++;
      }
    }
    
    if (cleaned > 0) {
      logger.debug('Cache cleanup completed', { 
        entriesRemoved: cleaned, 
        remainingEntries: this.cache.size 
      });
    }
  }

  getStats() {
    const now = Date.now();
    let validEntries = 0;
    let expiredEntries = 0;
    let totalDataSize = 0;

    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        expiredEntries++;
      } else {
        validEntries++;
      }
      totalDataSize += JSON.stringify(item.data).length;
    }

    return {
      enabled: this.enabled,
      totalEntries: this.cache.size,
      validEntries,
      expiredEntries,
      ttlMinutes: this.ttl / (60 * 1000),
      estimatedSizeBytes: totalDataSize
    };
  }
}

// Create global cache instance
const cache = new MemoryCache();

/**
 * Cache middleware
 */
const cacheMiddleware = (req, res, next) => {
  // Only cache GET requests
  if (req.method !== 'GET') {
    return next();
  }

  const key = cache.generateKey(req);
  const cachedData = cache.get(key);

  if (cachedData) {
    // Return cached response
    res.set('X-Cache', 'HIT');
    res.set('X-Cache-Key', key);
    return res.json(cachedData);
  }

  // No cache hit, continue to route handler
  res.set('X-Cache', 'MISS');
  res.set('X-Cache-Key', key);

  // Override res.json to cache the response
  const originalJson = res.json;
  res.json = function(data) {
    // Only cache successful responses
    if (res.statusCode >= 200 && res.statusCode < 300) {
      cache.set(key, data);
    }
    
    // Call original json method
    return originalJson.call(this, data);
  };

  next();
};

// Export middleware and cache instance for management
module.exports = cacheMiddleware;
module.exports.cache = cache;