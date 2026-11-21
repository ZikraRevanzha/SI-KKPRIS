import { ShieldAlert } from 'lucide-react';
import { Link } from 'react-router';
import { useAuth } from '@/app/authContext';
import { getHomePathByRole } from '@/components/layout/navigation';

export function ForbiddenPage() {
  const { user } = useAuth();
  const tujuan = user ? getHomePathByRole(user.peran) : '/login';

  return (
    <main className="flex min-h-dvh items-center justify-center bg-canvas px-4 py-12">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-8 text-center shadow-[var(--shadow-card)]">
        <div
          aria-hidden="true"
          className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-status-danger-bg text-status-danger"
        >
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h1 className="text-xl font-bold text-ink">403 — Akses Ditolak</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Akun Anda tidak memiliki izin peran untuk membuka halaman ini.
        </p>
        <div className="mt-6">
          <Link
            to={tujuan}
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-brand px-5 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-hover"
          >
            Kembali ke Beranda
          </Link>
        </div>
      </div>
    </main>
  );
}
