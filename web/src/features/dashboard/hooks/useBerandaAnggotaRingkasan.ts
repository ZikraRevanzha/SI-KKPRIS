import { useQuery } from '@tanstack/react-query';
import { ApiError, apiClient, normalizeApiError } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import type { components } from '@/api/schema';

export type BerandaAnggotaRingkasan = components['schemas']['BerandaAnggotaRingkasan'];

export function useBerandaAnggotaRingkasan() {
  return useQuery<BerandaAnggotaRingkasan, ApiError>({
    queryKey: queryKeys.dashboard.berandaAnggota(),
    queryFn: async () => {
      let hasil;
      try {
        hasil = await apiClient.GET('/api/v1/anggota/saya/ringkasan/');
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
