import type { ReactNode } from 'react';
import { Card } from '@/components/ui';
import { cn } from '@/lib/cn';

export interface StatCardProps {
  label: string;
  value: string;
  meta: string;
  icon: ReactNode;
  /** Menandai angka kunci dengan aksen emas tipis di sisi atas (dipakai hemat). */
  highlight?: boolean;
  numeric?: boolean;
}

export function StatCard({
  label,
  value,
  meta,
  icon,
  highlight = false,
  numeric = false,
}: StatCardProps) {
  return (
    <Card
      className={cn(
        'relative overflow-hidden p-4 sm:p-5',
        highlight && 'border-t-[3px] border-t-accent',
      )}
    >
      <div className="flex items-start gap-3.5">
        <div
          aria-hidden="true"
          className={cn(
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-md',
            highlight ? 'bg-accent-tint text-accent-ink' : 'bg-brand-tint text-brand',
          )}
        >
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-ink-muted">{label}</p>
          <p
            className={cn(
              'mt-1 truncate text-lg font-bold leading-snug text-ink sm:text-xl',
              numeric && 'uang-tabular',
            )}
            title={value}
          >
            {value}
          </p>
          <p className="mt-1 text-xs text-ink-secondary">{meta}</p>
        </div>
      </div>
    </Card>
  );
}
