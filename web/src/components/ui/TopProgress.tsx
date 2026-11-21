import { useIsFetching } from '@tanstack/react-query';
import { useDelayedLoading } from './useDelayedLoading';

export interface TopProgressProps {
  /** Paksa aktif secara manual selain state fetch TanStack Query. */
  active?: boolean;
}

/**
 * Indeterminate Top Progress Bar (Animasi #4 — AGENTS.md Bagian 7.D).
 * Tampil tipis di puncak layar saat background fetching berlangsung (tunda 200 ms, min 400 ms).
 */
export function TopProgress({ active = false }: TopProgressProps) {
  const fetchingCount = useIsFetching();
  const visible = useDelayedLoading(active || fetchingCount > 0, 200, 400);

  if (!visible) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 top-0 z-50 h-1 overflow-hidden bg-brand-tint"
    >
      <span className="sr-only">Memuat…</span>
      <div className="kkpris-top-progress-bar h-full w-1/2 bg-accent" />
    </div>
  );
}
