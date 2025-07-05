/**
 * Authentication routes for ESPN login
 */

const express = require('express');
const axios = require('axios');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * ESPN Login endpoint
 * Authenticates with ESPN and returns the required cookies
 */
router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({
      error: 'Missing credentials',
      message: 'Email and password are required',
      example: {
        email: 'your-email@example.com',
        password: 'your-password'
      }
    });
  }

  try {
    logger.info('Attempting ESPN login', { email: email.replace(/(.{3}).*(@.*)/, '$1***$2') });

    // Step 1: Get initial login page to get CSRF token
    const loginPageResponse = await axios.get('https://registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest/login', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
    });

    // Step 2: Perform login
    const loginData = {
      loginValue: email,
      password: password
    };

    const loginResponse = await axios.post('https://ha.registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest/login', loginData, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
      },
      maxRedirects: 0,
      validateStatus: (status) => status < 400 || status === 302
    });

    // Step 3: Follow redirects to get fantasy cookies
    let cookies = [];
    if (loginResponse.headers['set-cookie']) {
      cookies = loginResponse.headers['set-cookie'];
    }

    // Step 4: Access fantasy page to get the required cookies
    const cookieString = cookies.join('; ');
    const fantasyResponse = await axios.get('https://fantasy.espn.com/basketball/', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cookie': cookieString
      },
      maxRedirects: 5,
      validateStatus: (status) => status < 400
    });

    // Extract ESPN_S2 and SWID cookies
    const allCookies = [...cookies];
    if (fantasyResponse.headers['set-cookie']) {
      allCookies.push(...fantasyResponse.headers['set-cookie']);
    }

    let espnS2 = null;
    let swid = null;

    allCookies.forEach(cookie => {
      if (cookie.includes('espn_s2=')) {
        espnS2 = cookie.split('espn_s2=')[1].split(';')[0];
      }
      if (cookie.includes('SWID=')) {
        swid = cookie.split('SWID=')[1].split(';')[0];
      }
    });

    if (!espnS2 || !swid) {
      logger.warn('ESPN login succeeded but cookies not found');
      return res.status(500).json({
        error: 'Login successful but cookies not found',
        message: 'ESPN login succeeded but required cookies (espn_s2, SWID) were not returned',
        debug: {
          foundCookies: allCookies.map(c => c.split('=')[0]).filter(name => name.length > 0)
        }
      });
    }

    logger.info('ESPN login successful', { 
      email: email.replace(/(.{3}).*(@.*)/, '$1***$2'),
      hasEspnS2: !!espnS2,
      hasSwid: !!swid
    });

    // Return the cookies
    res.json({
      success: true,
      message: 'ESPN login successful',
      cookies: {
        espn_s2: espnS2,
        swid: swid
      },
      instructions: {
        message: 'Add these cookies to your .env file',
        envVars: {
          ESPN_COOKIE_S2: espnS2,
          ESPN_COOKIE_SWID: swid
        }
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('ESPN login failed', { 
      error: error.message,
      email: email.replace(/(.{3}).*(@.*)/, '$1***$2'),
      status: error.response?.status
    });

    if (error.response?.status === 401) {
      return res.status(401).json({
        error: 'Invalid credentials',
        message: 'The provided email and password are incorrect'
      });
    }

    if (error.response?.status === 429) {
      return res.status(429).json({
        error: 'Too many requests',
        message: 'ESPN has temporarily blocked login attempts. Please try again later.'
      });
    }

    res.status(500).json({
      error: 'Login failed',
      message: 'An error occurred during ESPN login',
      details: error.message
    });
  }
});

/**
 * Validate cookies endpoint
 * Tests if provided cookies are valid for ESPN API access
 */
router.post('/validate-cookies', async (req, res) => {
  const { espn_s2, swid } = req.body;

  if (!espn_s2 || !swid) {
    return res.status(400).json({
      error: 'Missing cookies',
      message: 'Both espn_s2 and swid cookies are required',
      example: {
        espn_s2: 'your-espn-s2-cookie',
        swid: 'your-swid-cookie'
      }
    });
  }

  try {
    // Test the cookies by making a request to ESPN API
    const testResponse = await axios.get('https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2024/segments/0/leagues/123456', {
      headers: {
        'Cookie': `espn_s2=${espn_s2}; SWID=${swid}`,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      timeout: 10000,
      validateStatus: (status) => status < 500 // Accept 404 as valid (just means league doesn't exist)
    });

    const isValid = testResponse.status !== 401 && testResponse.status !== 403;

    res.json({
      success: true,
      valid: isValid,
      message: isValid ? 'Cookies are valid' : 'Cookies appear to be invalid or expired',
      details: {
        status: testResponse.status,
        hasEspnS2: !!espn_s2,
        hasSwid: !!swid,
        espnS2Length: espn_s2.length,
        swidLength: swid.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Cookie validation failed', { error: error.message });

    if (error.response?.status === 401 || error.response?.status === 403) {
      return res.json({
        success: true,
        valid: false,
        message: 'Cookies are invalid or expired',
        details: {
          status: error.response.status,
          hasEspnS2: !!espn_s2,
          hasSwid: !!swid
        },
        timestamp: new Date().toISOString()
      });
    }

    res.status(500).json({
      error: 'Validation failed',
      message: 'An error occurred while validating cookies',
      details: error.message
    });
  }
});

/**
 * Get current cookie status
 */
router.get('/cookie-status', (req, res) => {
  const hasEspnS2 = !!process.env.ESPN_COOKIE_S2;
  const hasSwid = !!process.env.ESPN_COOKIE_SWID;
  
  res.json({
    configured: hasEspnS2 && hasSwid,
    cookies: {
      espn_s2: hasEspnS2 ? 'configured' : 'missing',
      swid: hasSwid ? 'configured' : 'missing'
    },
    message: (hasEspnS2 && hasSwid) ? 
      'ESPN cookies are configured' : 
      'ESPN cookies are not configured - private leagues will not be accessible',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;