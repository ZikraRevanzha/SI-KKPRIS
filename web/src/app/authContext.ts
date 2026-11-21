import { createContext, useContext } from 'react';
import type { components } from '@/api/schema';

export type PenggunaMe = components['schemas']['PenggunaMe'];
export type Peran = components['schemas']['PeranEnum'];
export type LoginInput = components['schemas']['LoginInputRequest'];

export interface AuthContextValue {
  user: PenggunaMe | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (input: LoginInput) => Promise<PenggunaMe>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<PenggunaMe | null>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth harus digunakan di dalam AuthProvider.');
  }
  return ctx;
}
