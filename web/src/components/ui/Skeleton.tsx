import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const ROUNDED_CLASSES: Record<NonNullable<SkeletonProps['rounded']>, string> = {
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  full: 'rounded-full',
};

/**
 * Skeleton Shimmer (Animasi #5 — AGENTS.md Bagian 7.D).
 * Hanya menganimasikan transform/opacity; berubah menjadi blok statis pada prefers-reduced-motion.
 */
export function Skeleton({ rounded = 'md', className, ...props }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn('kkpris-skeleton', ROUNDED_CLASSES[rounded], className)}
      {...props}
    />
  );
}

export interface SkeletonGroupProps {
  label?: string;
  className?: string;
  children: ReactNode;
}

export function SkeletonGroup({ label = 'Memuat…', className, children }: SkeletonGroupProps) {
  return (
    <div aria-busy="true" role="status" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
