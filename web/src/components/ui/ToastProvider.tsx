import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';
import { cn } from '@/lib/cn';
import {
  ToastContext,
  type ToastInput,
  type ToastRecord,
  type ToastVariant,
} from './toastContext';

const VARIANT_STYLES: Record<ToastVariant, string> = {
  success: 'border-status-success-border bg-status-success-bg text-status-success',
  warning: 'border-status-warning-border bg-status-warning-bg text-status-warning',
  danger: 'border-status-danger-border bg-status-danger-bg text-status-danger',
  info: 'border-status-info-border bg-status-info-bg text-status-info',
};

function IkonToast({ variant }: { variant: ToastVariant }) {
  switch (variant) {
    case 'success':
      return <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />;
    case 'warning':
      return <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />;
    case 'danger':
      return <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />;
    case 'info':
      return <Info className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />;
  }
}

interface ToastItemProps {
  toast: ToastRecord;
  onDismiss: (id: string) => void;
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [dijeda, setDijeda] = useState(false);

  useEffect(() => {
    if (toast.durationMs <= 0 || dijeda) {
      return;
    }
    const timer = window.setTimeout(() => {
      onDismiss(toast.id);
    }, toast.durationMs);
    return () => window.clearTimeout(timer);
  }, [toast.id, toast.durationMs, dijeda, onDismiss]);

  return (
    <div
      role="status"
      onFocus={() => setDijeda(true)}
      onBlur={() => setDijeda(false)}
      onMouseEnter={() => setDijeda(true)}
      onMouseLeave={() => setDijeda(false)}
      className={cn(
        'kkpris-toast-item flex items-start gap-3 border px-4 py-3 text-sm',
        VARIANT_STYLES[toast.variant],
      )}
    >
      <IkonToast variant={toast.variant} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{toast.title}</p>
        {toast.description && <p className="mt-0.5 text-ink-secondary">{toast.description}</p>}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label={`Tutup notifikasi: ${toast.title}`}
        className="inline-flex min-h-9 min-w-9 shrink-0 cursor-pointer items-center justify-center rounded-md text-ink-secondary transition-colors hover:bg-surface hover:text-ink"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}

/**
 * Provider Toast dengan live region (AGENTS.md 7.D & modern-web-guidance/persistent-toast-notifications).
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const [pengumuman, setPengumuman] = useState('');
  const counterRef = useRef(0);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const showToast = useCallback((input: ToastInput): string => {
    counterRef.current += 1;
    const id = `toast-${counterRef.current}`;
    const record: ToastRecord = {
      id,
      title: input.title,
      description: input.description,
      variant: input.variant ?? 'info',
      durationMs: input.durationMs ?? 5000,
    };
    setToasts((prev) => [...prev.slice(-3), record]);
    const teksUmum = input.description ? `${input.title}. ${input.description}` : input.title;
    setPengumuman(teksUmum);
    return id;
  }, []);

  const value = useMemo(
    () => ({ showToast, dismissToast }),
    [showToast, dismissToast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {pengumuman}
      </div>
      {toasts.length > 0 && (
        <div
          role="region"
          aria-label="Notifikasi"
          className="kkpris-toast-region"
        >
          {toasts.map((toast) => (
            <ToastItem key={toast.id} toast={toast} onDismiss={dismissToast} />
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}
