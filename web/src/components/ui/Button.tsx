import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';
import { Spinner } from './Spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  loadingText?: string;
  leftIcon?: ReactNode;
  fullWidth?: boolean;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-brand text-brand-ink hover:bg-brand-hover active:bg-brand-active border border-transparent',
  secondary:
    'bg-surface text-ink hover:bg-surface-subtle active:bg-canvas border border-border-input',
  ghost:
    'bg-transparent text-ink hover:bg-brand-tint active:bg-border border border-transparent',
  danger:
    'bg-status-danger text-status-danger-ink hover:bg-status-danger-hover border border-transparent',
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'min-h-10 px-3 text-sm gap-1.5',
  md: 'min-h-11 px-4 text-sm sm:text-base gap-2',
  lg: 'min-h-12 px-5 text-base gap-2',
};

export function Button({
  type = 'button',
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingText = 'Menyimpan…',
  leftIcon,
  fullWidth = false,
  disabled,
  className,
  children,
  onClick,
  ...props
}: ButtonProps) {
  const isDisabled = Boolean(disabled || loading);

  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      onClick={isDisabled ? undefined : onClick}
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors duration-150',
        'cursor-pointer disabled:cursor-not-allowed disabled:opacity-60',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {loading ? (
        <>
          <Spinner size="sm" decorative />
          <span>{loadingText}</span>
        </>
      ) : (
        <>
          {leftIcon && <span aria-hidden="true" className="inline-flex shrink-0">{leftIcon}</span>}
          <span>{children}</span>
        </>
      )}
    </button>
  );
}
