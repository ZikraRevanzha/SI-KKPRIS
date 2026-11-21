import { LogOut, Menu } from 'lucide-react';
import type { PenggunaMe } from '@/app/authContext';
import { Button } from '@/components/ui';

function ambilInisialNama(nama: string): string {
  const bagian = nama.trim().split(/\s+/).filter(Boolean);
  if (bagian.length === 0) {
    return 'KK';
  }
  if (bagian.length === 1) {
    return bagian[0].slice(0, 2).toUpperCase();
  }
  return `${bagian[0][0]}${bagian[1][0]}`.toUpperCase();
}

export interface TopbarProps {
  tanggalHariIni: string;
  user: PenggunaMe | null;
  drawerId: string;
  drawerOpen: boolean;
  onOpenDrawer: () => void;
  onLogout: () => void;
  isLoggingOut: boolean;
}

export function Topbar({
  tanggalHariIni,
  user,
  drawerId,
  drawerOpen,
  onOpenDrawer,
  onLogout,
  isLoggingOut,
}: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex min-h-16 items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2.5 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onOpenDrawer}
          aria-label="Buka menu navigasi"
          aria-expanded={drawerOpen}
          aria-controls={drawerId}
          className="inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center rounded-md border border-border bg-surface text-ink transition-colors hover:bg-surface-subtle lg:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-ink-secondary">{tanggalHariIni}</p>
        </div>
      </div>

      {user && (
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-2.5">
            <div
              aria-hidden="true"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-tint text-xs font-bold text-brand"
            >
              {ambilInisialNama(user.nama_lengkap)}
            </div>
            <div className="hidden min-w-0 text-right sm:block">
              <p className="truncate text-sm font-semibold leading-tight text-ink">
                {user.nama_lengkap}
              </p>
              <p className="truncate text-xs text-ink-muted">
                {user.peran_label}
                {user.anggota ? ` · ${user.anggota.no_anggota}` : ''}
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            loading={isLoggingOut}
            loadingText="Keluar…"
            leftIcon={<LogOut className="h-4 w-4" />}
            aria-label="Keluar dari sistem"
            className="min-h-11 shrink-0 text-ink-secondary hover:text-ink"
          >
            <span className="hidden md:inline">Keluar</span>
          </Button>
        </div>
      )}
    </header>
  );
}
