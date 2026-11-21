import type { ReactNode } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { cn } from '@/lib/cn';

export type BadgeVariant =
  | 'neutral'
  | 'brand'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info';

export interface BadgeProps {
  variant?: BadgeVariant;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: 'bg-surface-subtle text-ink-secondary border-border',
  brand: 'bg-brand-tint text-brand border-brand-tint',
  accent: 'bg-accent-tint text-accent-ink border-accent',
  success: 'bg-status-success-bg text-status-success border-status-success-border',
  warning: 'bg-status-warning-bg text-status-warning border-status-warning-border',
  danger: 'bg-status-danger-bg text-status-danger border-status-danger-border',
  info: 'bg-status-info-bg text-status-info border-status-info-border',
};

function ambilIkonBawaanStatus(variant: BadgeVariant): ReactNode {
  switch (variant) {
    case 'success':
      return <CheckCircle2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    case 'warning':
      return <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    case 'danger':
      return <AlertCircle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    case 'info':
      return <Info className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    default:
      return null;
  }
}

/**
 * Badge status & label (AGENTS.md Bagian 7.B).
 * Varian status (success, warning, danger, info) selalu menyertakan ikon lucide-react + teks.
 */
export function Badge({ variant = 'neutral', icon, className, children }: BadgeProps) {
  const ikonTampil = icon ?? ambilIkonBawaanStatus(variant);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium leading-5',
        VARIANT_CLASSES[variant],
        className,
      )}
    >
      {ikonTampil}
      <span>{children}</span>
    </span>
  );
}
