// Jest setup file for ESPN Service tests
process.env.NODE_ENV = 'test'
process.env.PORT = 3001
process.env.CACHE_TTL = 60
process.env.LOG_LEVEL = 'error'

// Mock console.log in tests to reduce noise
global.console = {
  ...console,
  log: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
}