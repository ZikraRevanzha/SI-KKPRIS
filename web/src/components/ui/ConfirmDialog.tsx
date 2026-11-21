import type { ReactNode } from 'react';
import { Button } from './Button';
import { Dialog } from './Dialog';

export interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  loadingText?: string;
  variant?: 'primary' | 'danger';
  children?: ReactNode;
}

/**
 * Dialog konfirmasi untuk aksi tak terbalik (AGENTS.md 6.6).
 * Fokus awal diarahkan ke tombol aman ("Batal") saat variant="danger".
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Konfirmasi',
  cancelLabel = 'Batal',
  loading = false,
  loadingText = 'Memproses…',
  variant = 'danger',
  children,
}: ConfirmDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={loading ? () => undefined : onClose}
      title={title}
      description={description}
      lightDismiss={!loading}
      footer={
        <>
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={loading}
            autoFocus={variant === 'danger'}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variant}
            onClick={onConfirm}
            loading={loading}
            loadingText={loadingText}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      {children ?? <p>Pastikan data sudah benar sebelum melanjutkan tindakan ini.</p>}
    </Dialog>
  );
}
