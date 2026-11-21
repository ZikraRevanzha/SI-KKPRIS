import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { hasError = false, className, children, ...props },
  ref,
) {
  return (
    <select
      ref={ref}
      aria-invalid={hasError || undefined}
      className={cn(
        'min-h-11 w-full rounded-md border bg-surface px-3.5 py-2 text-base text-ink',
        'transition-colors duration-150',
        'disabled:cursor-not-allowed disabled:bg-surface-subtle disabled:text-ink-muted',
        hasError
          ? 'border-status-danger focus-visible:outline-status-danger'
          : 'border-border-input hover:border-ink focus-visible:border-brand',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
});
