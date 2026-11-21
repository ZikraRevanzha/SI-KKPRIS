import { useQuery } from '@tanstack/react-query';
import { ApiError, apiClient, normalizeApiError } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import type { components } from '@/api/schema';

export type DashboardRingkasan = components['schemas']['DashboardRingkasan'];

export function useDashboardRingkasan() {
  return useQuery<DashboardRingkasan, ApiError>({
    queryKey: queryKeys.dashboard.ringkasan(),
    queryFn: async () => {
      let hasil;
      try {
        hasil = await apiClient.GET('/api/v1/dashboard/ringkasan/');
      } catch (err) {
        throw new ApiError(normalizeApiError(null), { cause: err });
      }
      if (hasil.error || !hasil.data) {
        throw new ApiError(normalizeApiError(hasil.error, hasil.response.status));
      }
      return hasil.data;
    },
  });
}
