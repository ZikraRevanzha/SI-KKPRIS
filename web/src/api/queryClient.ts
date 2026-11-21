import { QueryClient } from '@tanstack/react-query';
import { ApiError } from './client';

const STATUS_TANPA_RETRY = new Set([401, 403, 404]);

export function createAppQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) => {
          if (failureCount >= 1) {
            return false;
          }
          if (error instanceof ApiError && error.status !== undefined) {
            return !STATUS_TANPA_RETRY.has(error.status);
          }
          return true;
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
