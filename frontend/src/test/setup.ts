import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// runs a cleanup after each test case
afterEach(() => {
  cleanup()
})

// Mock React Query globally
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query')
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })),
    useMutation: vi.fn(() => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isLoading: false,
      error: null,
    })),
    useQueryClient: vi.fn(() => ({
      invalidateQueries: vi.fn(),
      refetchQueries: vi.fn(),
      getQueryData: vi.fn(),
      setQueryData: vi.fn(),
    })),
  }
})