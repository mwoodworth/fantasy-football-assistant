import { vi } from 'vitest'

// Mock useQuery return type
export const useQuery = vi.fn(() => ({
  data: null,
  isLoading: false,
  error: null,
  refetch: vi.fn(),
}))

// Mock useMutation return type
export const useMutation = vi.fn(() => ({
  mutate: vi.fn(),
  mutateAsync: vi.fn(),
  isLoading: false,
  error: null,
}))

// Mock QueryClient
export const QueryClient = vi.fn(() => ({
  invalidateQueries: vi.fn(),
  refetchQueries: vi.fn(),
  getQueryData: vi.fn(),
  setQueryData: vi.fn(),
}))

// Mock QueryClientProvider
export const QueryClientProvider = ({ children }: { children: React.ReactNode }) => children