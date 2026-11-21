import { cn } from '@/lib/cn';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  /** Sembunyikan teks sr-only bila tombol sudah memiliki teks loading terlihat. */
  decorative?: boolean;
  className?: string;
}

const SIZE_CLASSES: Record<NonNullable<SpinnerProps['size']>, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-9 w-9 border-[3px]',
};

/**
 * Spinner Arc (Animasi #1 — AGENTS.md Bagian 7.D).
 * CSS murni (transform rotate); saat prefers-reduced-motion: reduce menjadi teks "Memuat…" statis.
 */
export function Spinner({
  size = 'md',
  label = 'Memuat…',
  decorative = false,
  className,
}: SpinnerProps) {
  return (
    <span
      role={decorative ? undefined : 'status'}
      aria-live={decorative ? undefined : 'polite'}
      className={cn('inline-flex items-center gap-2', className)}
    >
      <span
        aria-hidden="true"
        className={cn(
          'kkpris-spinner-arc inline-block shrink-0 rounded-full border-current border-r-transparent',
          SIZE_CLASSES[size],
        )}
      />
      {!decorative && (
        <>
          <span className="kkpris-spinner-reduced-label text-sm font-medium">{label}</span>
          <span className="sr-only">{label}</span>
        </>
      )}
    </span>
  );
}
