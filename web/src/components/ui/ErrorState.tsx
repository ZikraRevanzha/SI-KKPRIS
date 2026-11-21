import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  isRetrying?: boolean;
  className?: string;
}

export function ErrorState({
  title = 'Gagal memuat data',
  message,
  onRetry,
  retryLabel = 'Coba lagi',
  isRetrying = false,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-status-danger-border bg-status-danger-bg px-6 py-8 text-center',
        className,
      )}
    >
      <div
        aria-hidden="true"
        className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-surface text-status-danger"
      >
        <AlertCircle className="h-5 w-5" />
      </div>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <p className="mt-1 max-w-md text-sm text-ink-secondary">{message}</p>
      {onRetry && (
        <div className="mt-4">
          <Button
            variant="secondary"
            onClick={onRetry}
            loading={isRetrying}
            loadingText="Memuat ulang…"
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
