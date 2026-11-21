import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { hasError = false, className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      aria-invalid={hasError || undefined}
      className={cn(
        'min-h-24 w-full rounded-md border bg-surface px-3.5 py-2.5 text-base text-ink',
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
