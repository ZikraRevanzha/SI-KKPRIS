import { createContext, useContext } from 'react';

export type ToastVariant = 'success' | 'warning' | 'danger' | 'info';

export interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
  /** Durasi auto-tutup (ms). Set 0 untuk notifikasi persisten sampai ditutup manual. */
  durationMs?: number;
}

export interface ToastRecord extends ToastInput {
  id: string;
  variant: ToastVariant;
  durationMs: number;
}

export interface ToastContextValue {
  showToast: (input: ToastInput) => string;
  dismissToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast harus digunakan di dalam ToastProvider.');
  }
  return ctx;
}
