import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import {
  ApiError,
  apiClient,
  clearAccessToken,
  getAccessToken,
  normalizeApiError,
  refreshAccessToken,
  setAccessToken,
  setSessionExpiredHandler,
} from '@/api/client';
import { AuthContext, type LoginInput, type PenggunaMe } from './authContext';

// Mencegah rotasi refresh token ganda saat React StrictMode melakukan mount -> unmount -> mount
let bootstrapSessionPromise: Promise<PenggunaMe | null> | null = null;

async function pulihkanSesiAwal(): Promise<PenggunaMe | null> {
  if (bootstrapSessionPromise) {
    return bootstrapSessionPromise;
  }

  bootstrapSessionPromise = (async () => {
    const token = getAccessToken() ?? (await refreshAccessToken({ notifyOnFailure: false }));
    if (!token) {
      return null;
    }

    const { data, error } = await apiClient.GET('/api/v1/auth/me/');
    if (error || !data) {
      clearAccessToken();
      return null;
    }
    return data;
  })().finally(() => {
    bootstrapSessionPromise = null;
  });

  return bootstrapSessionPromise;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [user, setUser] = useState<PenggunaMe | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null);
      queryClient.clear();
      void navigate('/login', { replace: true });
    });

    return () => {
      setSessionExpiredHandler(null);
    };
  }, [navigate, queryClient]);

  useEffect(() => {
    let aktif = true;

    void pulihkanSesiAwal()
      .then((pengguna) => {
        if (aktif) {
          setUser(pengguna);
        }
      })
      .finally(() => {
        if (aktif) {
          setIsInitializing(false);
        }
      });

    return () => {
      aktif = false;
    };
  }, []);

  const login = useCallback(async (input: LoginInput): Promise<PenggunaMe> => {
    let hasil;
    try {
      hasil = await apiClient.POST('/api/v1/auth/login/', {
        body: input,
      });
    } catch (err) {
      throw new ApiError(normalizeApiError(null), { cause: err });
    }

    if (hasil.error || !hasil.data) {
      throw new ApiError(normalizeApiError(hasil.error, hasil.response.status));
    }

    setAccessToken(hasil.data.access);
    setUser(hasil.data.pengguna);
    return hasil.data.pengguna;
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.POST('/api/v1/auth/logout/');
    } finally {
      clearAccessToken();
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  const refreshUser = useCallback(async (): Promise<PenggunaMe | null> => {
    let hasil;
    try {
      hasil = await apiClient.GET('/api/v1/auth/me/');
    } catch (err) {
      throw new ApiError(normalizeApiError(null), { cause: err });
    }

    if (hasil.error || !hasil.data) {
      throw new ApiError(normalizeApiError(hasil.error, hasil.response.status));
    }

    setUser(hasil.data);
    return hasil.data;
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isInitializing,
      login,
      logout,
      refreshUser,
    }),
    [user, isInitializing, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
