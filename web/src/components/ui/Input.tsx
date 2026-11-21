import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { hasError = false, className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      aria-invalid={hasError || undefined}
      className={cn(
        'min-h-11 w-full rounded-md border bg-surface px-3.5 py-2 text-base text-ink',
        'placeholder:text-ink-muted transition-colors duration-150',
        'disabled:cursor-not-allowed disabled:bg-surface-subtle disabled:text-ink-muted',
        hasError
          ? 'border-status-danger focus-visible:outline-status-danger'
          : 'border-border-input hover:border-ink focus-visible:border-brand',
        className,
      )}
      {...props}
    />
  );
});
