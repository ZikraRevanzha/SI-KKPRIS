import { cn } from '@/lib/cn';

export interface ProgressBarProps {
  /** Persentase deterministik 0–100 dari server atau XHR. */
  value: number;
  label?: string;
  showPercent?: boolean;
  tone?: 'brand' | 'accent';
  className?: string;
}

/**
 * Percent Bar (Animasi #16 — AGENTS.md Bagian 7.D).
 * Hanya dipakai bila progres deterministik diketahui (pelunasan angsuran, unggah berkas, distribusi).
 */
export function ProgressBar({
  value,
  label,
  showPercent = true,
  tone = 'brand',
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent) && (
        <div className="mb-1.5 flex items-baseline justify-between gap-2 text-sm">
          {label ? <span className="text-ink-secondary">{label}</span> : <span />}
          {showPercent && (
            <span className="uang-tabular font-semibold text-ink">{clamped}%</span>
          )}
        </div>
      )}
      <div
        role="progressbar"
        aria-label={label ?? 'Progres'}
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2.5 w-full overflow-hidden rounded-full bg-border"
      >
        <div
          className={cn(
            'h-full rounded-full transition-[width] duration-200 ease-out motion-reduce:transition-none',
            tone === 'accent' ? 'bg-accent' : 'bg-brand',
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
