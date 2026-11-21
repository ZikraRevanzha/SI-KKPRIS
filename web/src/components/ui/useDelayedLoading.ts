import { useEffect, useRef, useState } from 'react';

/**
 * Hook anti-kedip indikator loading sesuai AGENTS.md Bagian 7.D:
 * - Menunda tampilan ±200 ms agar fetch cepat tidak berkedip.
 * - Bila sudah tampil, mempertahankan minimal ±400 ms.
 */
export function useDelayedLoading(
  isLoading: boolean,
  delayMs = 200,
  minDisplayMs = 400,
): boolean {
  const [visible, setVisible] = useState(false);
  const shownAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (isLoading) {
      if (visible) {
        return;
      }
      const timer = window.setTimeout(() => {
        shownAtRef.current = Date.now();
        setVisible(true);
      }, delayMs);
      return () => window.clearTimeout(timer);
    }

    if (!visible) {
      return;
    }

    const elapsed = shownAtRef.current ? Date.now() - shownAtRef.current : minDisplayMs;
    const remaining = Math.max(0, minDisplayMs - elapsed);
    const timer = window.setTimeout(() => {
      shownAtRef.current = null;
      setVisible(false);
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [isLoading, visible, delayMs, minDisplayMs]);

  return visible;
}
