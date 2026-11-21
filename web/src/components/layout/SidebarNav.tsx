import { LogOut, X } from 'lucide-react';
import { NavLink } from 'react-router';
import { Spinner } from '@/components/ui';
import { cn } from '@/lib/cn';
import type { NavigationItem } from './navigation';

export interface SidebarNavProps {
  items: readonly NavigationItem[];
  onNavigate?: () => void;
  onLogout: () => void;
  isLoggingOut: boolean;
  showCloseButton?: boolean;
  onClose?: () => void;
}

export function SidebarNav({
  items,
  onNavigate,
  onLogout,
  isLoggingOut,
  showCloseButton = false,
  onClose,
}: SidebarNavProps) {
  return (
    <div className="flex h-full flex-col bg-brand text-brand-ink">
      <div className="flex items-center justify-between gap-3 border-b border-brand-hover px-4 py-4">
        <div className="flex items-center gap-3 min-w-0">
          <div
            aria-hidden="true"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-accent text-sm font-bold text-accent-ink"
          >
            KK
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-bold leading-tight tracking-tight text-brand-ink">
              SI-KKPRIS
            </p>
            <p className="truncate text-xs text-brand-muted">SMKN 1 Kota Solok</p>
          </div>
        </div>

        {showCloseButton && onClose && (
          <button
            type="button"
            onClick={onClose}
            autoFocus
            aria-label="Tutup menu navigasi"
            className="inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center rounded-md text-brand-muted transition-colors hover:bg-brand-hover hover:text-brand-ink focus-visible:outline-accent"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        )}
      </div>

      <nav aria-label="Navigasi utama" className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <NavLink
                  to={item.to}
                  end={item.to === '/dashboard' || item.to === '/beranda'}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      'relative flex min-h-11 items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors duration-150 focus-visible:outline-accent',
                      isActive
                        ? 'bg-brand-active text-brand-ink'
                        : 'text-brand-muted hover:bg-brand-hover hover:text-brand-ink',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span
                          aria-hidden="true"
                          className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-accent"
                        />
                      )}
                      <Icon
                        className={cn(
                          'h-5 w-5 shrink-0',
                          isActive ? 'text-accent' : 'text-brand-muted',
                        )}
                        aria-hidden="true"
                      />
                      <span className="truncate">{item.label}</span>
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-brand-hover p-3">
        <button
          type="button"
          onClick={onLogout}
          disabled={isLoggingOut}
          aria-busy={isLoggingOut || undefined}
          className="flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-brand-muted transition-colors duration-150 hover:bg-brand-hover hover:text-brand-ink disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-accent"
        >
          {isLoggingOut ? (
            <>
              <Spinner size="sm" decorative />
              <span>Keluar…</span>
            </>
          ) : (
            <>
              <LogOut className="h-5 w-5 shrink-0" aria-hidden="true" />
              <span>Keluar</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
