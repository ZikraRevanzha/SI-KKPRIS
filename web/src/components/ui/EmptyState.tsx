import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/cn';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-border-strong bg-surface-subtle px-6 py-10 text-center',
        className,
      )}
    >
      <div
        aria-hidden="true"
        className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-brand-tint text-brand"
      >
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-ink-secondary">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
