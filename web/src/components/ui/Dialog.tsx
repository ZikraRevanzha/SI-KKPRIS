import { useEffect, useId, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/cn';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  /** Mengizinkan tutup saat klik backdrop (closedby="any" + fallback koordinat). Default: true. */
  lightDismiss?: boolean;
  footer?: ReactNode;
  className?: string;
  children: ReactNode;
}

/**
 * Dialog modal berbasis elemen <dialog> native (AGENTS.md 7.A & modern-web-guidance/dialog).
 * Memakai showModal() untuk fokus terkunci, top layer, inert halaman, Esc, dan fokus kembali.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  lightDismiss = true,
  footer,
  className,
  children,
}: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const pressedOutsideRef = useRef(false);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    dialog.setAttribute('closedby', lightDismiss ? 'any' : 'closerequest');

    if (open) {
      if (!dialog.open) {
        if (typeof dialog.showModal === 'function') {
          dialog.showModal();
        } else {
          dialog.setAttribute('open', '');
        }
      }
    } else if (dialog.open) {
      if (typeof dialog.close === 'function') {
        dialog.close();
      } else {
        dialog.removeAttribute('open');
      }
    }
  }, [open, lightDismiss]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    const handleClose = () => {
      dialog.returnValue = '';
      onClose();
    };

    dialog.addEventListener('close', handleClose);
    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  // Fallback light-dismiss untuk browser tanpa HTMLDialogElement.prototype.closedBy (Safari)
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || !lightDismiss || 'closedBy' in HTMLDialogElement.prototype) {
      return;
    }

    const diLuarDialog = (event: PointerEvent) => {
      const rect = dialog.getBoundingClientRect();
      return (
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom
      );
    };

    const handlePointerDown = (event: PointerEvent) => {
      pressedOutsideRef.current = diLuarDialog(event);
    };

    const handlePointerUp = (event: PointerEvent) => {
      if (pressedOutsideRef.current && diLuarDialog(event) && dialog.open) {
        dialog.close();
      }
      pressedOutsideRef.current = false;
    };

    dialog.addEventListener('pointerdown', handlePointerDown);
    dialog.addEventListener('pointerup', handlePointerUp);
    return () => {
      dialog.removeEventListener('pointerdown', handlePointerDown);
      dialog.removeEventListener('pointerup', handlePointerUp);
    };
  }, [lightDismiss]);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      className={cn('kkpris-modal', className)}
    >
      <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
        <div className="min-w-0">
          <h2 id={titleId} className="text-lg font-semibold text-ink">
            {title}
          </h2>
          {description && (
            <p id={descId} className="mt-1 text-sm text-ink-secondary">
              {description}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Tutup dialog"
          className="inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center rounded-md text-ink-secondary transition-colors hover:bg-surface-subtle hover:text-ink"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <div className="px-5 py-4 text-sm text-ink-secondary">{children}</div>

      {footer && (
        <div className="flex flex-col-reverse gap-2 border-t border-border bg-surface-subtle px-5 py-3.5 sm:flex-row sm:justify-end">
          {footer}
        </div>
      )}
    </dialog>
  );
}
