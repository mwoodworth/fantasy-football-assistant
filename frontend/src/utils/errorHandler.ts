/**
 * Global error handling utilities for the frontend
 */

import { AxiosError } from 'axios'
import { toast } from './toast'

export interface ErrorResponse {
  error: {
    type: string
    message: string
    timestamp: string
    request_id?: string
    details?: any
  }
}

export class APIError extends Error {
  public statusCode: number
  public errorType: string
  public requestId?: string
  public details?: any

  constructor(
    message: string,
    statusCode: number,
    errorType: string,
    requestId?: string,
    details?: any
  ) {
    super(message)
    this.name = 'APIError'
    this.statusCode = statusCode
    this.errorType = errorType
    this.requestId = requestId
    this.details = details
  }
}

/**
 * Handle Axios errors and convert to APIError
 */
export function handleAxiosError(error: AxiosError): APIError {
  if (error.response) {
    const data = error.response.data as ErrorResponse

    // Rate limit error
    if (error.response.status === 429) {
      const retryAfter = error.response.headers['retry-after']
      return new APIError(
        `Rate limit exceeded. Please try again in ${retryAfter || '60'} seconds.`,
        429,
        'rate_limit_exceeded',
        data?.error?.request_id
      )
    }

    // ESPN authentication error
    if (data?.error?.type === 'espn_auth_error') {
      return new APIError(
        'ESPN authentication failed. Please update your league settings with valid cookies.',
        401,
        'espn_auth_error',
        data.error.request_id,
        data.error.details
      )
    }

    // Validation error
    if (error.response.status === 422 && data?.error?.details?.errors) {
      const errors = data.error.details.errors
      const message = errors.map((e: any) => `${e.field}: ${e.message}`).join(', ')
      return new APIError(
        message || 'Validation error',
        422,
        'validation_error',
        data.error.request_id,
        errors
      )
    }

    // Generic error from API
    if (data?.error) {
      return new APIError(
        data.error.message || 'An error occurred',
        error.response.status,
        data.error.type || 'unknown_error',
        data.error.request_id,
        data.error.details
      )
    }

    // Fallback for non-standard error responses
    return new APIError(
      error.response.statusText || 'An error occurred',
      error.response.status,
      'http_error'
    )
  }

  // Network error
  if (error.request) {
    return new APIError(
      'Network error. Please check your connection.',
      0,
      'network_error'
    )
  }

  // Other errors
  return new APIError(
    error.message || 'An unexpected error occurred',
    0,
    'unknown_error'
  )
}

/**
 * Display error to user
 */
export function displayError(error: APIError | Error): void {
  if (error instanceof APIError) {
    switch (error.errorType) {
      case 'rate_limit_exceeded':
        toast.error(error.message, { duration: 10000 })
        break
        
      case 'espn_auth_error':
        toast.error(error.message, {
          duration: 10000,
          icon: '🔒'
        })
        break
        
      case 'validation_error':
        toast.error(error.message, {
          duration: 5000,
          icon: '⚠️'
        })
        break
        
      case 'network_error':
        toast.error(error.message, {
          duration: 5000,
          icon: '📡'
        })
        break
        
      default:
        toast.error(error.message, { duration: 5000 })
    }
    
    // Log error details for debugging
    if (error.requestId) {
      console.error(`Error ID: ${error.requestId}`, error.details)
    }
  } else {
    toast.error(error.message || 'An unexpected error occurred')
  }
}

/**
 * React Query error handler
 */
export function queryErrorHandler(error: unknown): void {
  if (error instanceof AxiosError) {
    const apiError = handleAxiosError(error)
    displayError(apiError)
  } else if (error instanceof Error) {
    displayError(error)
  } else {
    displayError(new Error('An unexpected error occurred'))
  }
}

/**
 * Retry logic for failed requests
 */
export function shouldRetryRequest(failureCount: number, error: unknown): boolean {
  // Don't retry on certain errors
  if (error instanceof APIError) {
    const noRetryErrors = [
      'validation_error',
      'espn_auth_error',
      'rate_limit_exceeded'
    ]
    
    if (noRetryErrors.includes(error.errorType)) {
      return false
    }
    
    // Don't retry 4xx errors (except 429 which is handled above)
    if (error.statusCode >= 400 && error.statusCode < 500) {
      return false
    }
  }
  
  // Retry up to 3 times for other errors
  return failureCount < 3
}

/**
 * Global unhandled error boundary
 */
export function setupGlobalErrorHandlers(): void {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    displayError(new Error('An unexpected error occurred'))
    event.preventDefault()
  })
  
  // Handle global errors
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error)
    displayError(new Error('An unexpected error occurred'))
    event.preventDefault()
  })
}