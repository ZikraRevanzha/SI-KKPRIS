import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router';
import { useAuth } from '@/app/authContext';
import { TopProgress, useToast } from '@/components/ui';
import { formatTanggal } from '@/lib/format';
import { getNavigationByRole } from './navigation';
import { SidebarNav } from './SidebarNav';
import { Topbar } from './Topbar';

export function AppShell() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const drawerId = useId();
  const drawerRef = useRef<HTMLDialogElement>(null);
  const sheetRef = useRef<HTMLDivElement>(null);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const menuItems = useMemo(() => (user ? getNavigationByRole(user.peran) : []), [user]);

  const tanggalHariIni = useMemo(() => {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return formatTanggal(`${y}-${m}-${d}`);
  }, []);

  const tutupDrawer = useCallback(() => {
    const dialog = drawerRef.current;
    if (dialog?.open) {
      if (typeof dialog.close === 'function') {
        dialog.close();
      } else {
        dialog.removeAttribute('open');
      }
    }
    setDrawerOpen(false);
  }, []);

  const bukaDrawer = useCallback(() => {
    const dialog = drawerRef.current;
    if (dialog && !dialog.open) {
      if (typeof dialog.showModal === 'function') {
        dialog.showModal();
      } else {
        dialog.setAttribute('open', '');
      }
      setDrawerOpen(true);
    }
  }, []);

  useEffect(() => {
    const dialog = drawerRef.current;
    if (dialog?.open && typeof dialog.close === 'function') {
      dialog.close();
    }
  }, [location.pathname]);

  useEffect(() => {
    const dialog = drawerRef.current;
    if (!dialog) {
      return;
    }
    const handleClose = () => setDrawerOpen(false);
    dialog.addEventListener('close', handleClose);
    return () => dialog.removeEventListener('close', handleClose);
  }, []);

  const handleLogout = useCallback(async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      showToast({
        title: 'Berhasil keluar',
        description: 'Sesi Anda telah diakhiri dengan aman.',
        variant: 'info',
      });
      void navigate('/login', { replace: true });
    } finally {
      setIsLoggingOut(false);
    }
  }, [logout, navigate, showToast]);

  return (
    <div className="min-h-dvh bg-canvas text-ink lg:flex">
      <a
        href="#konten-utama"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-accent focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-accent-ink focus:shadow-[var(--shadow-dialog)]"
      >
        Lompat ke konten utama
      </a>

      <TopProgress />

      <aside className="hidden lg:sticky lg:top-0 lg:flex lg:h-dvh lg:w-64 lg:shrink-0 lg:flex-col">
        <SidebarNav
          items={menuItems}
          onLogout={() => void handleLogout()}
          isLoggingOut={isLoggingOut}
        />
      </aside>

      <dialog
        ref={drawerRef}
        id={drawerId}
        aria-label="Menu navigasi utama"
        className="kkpris-drawer lg:hidden"
        onClick={(event) => {
          if (sheetRef.current && !sheetRef.current.contains(event.target as Node)) {
            tutupDrawer();
          }
        }}
      >
        <div ref={sheetRef} className="kkpris-drawer-panel">
          <SidebarNav
            items={menuItems}
            onNavigate={tutupDrawer}
            onLogout={() => void handleLogout()}
            isLoggingOut={isLoggingOut}
            showCloseButton
            onClose={tutupDrawer}
          />
        </div>
      </dialog>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          tanggalHariIni={tanggalHariIni}
          user={user}
          drawerId={drawerId}
          drawerOpen={drawerOpen}
          onOpenDrawer={bukaDrawer}
          onLogout={() => void handleLogout()}
          isLoggingOut={isLoggingOut}
        />

        <main
          id="konten-utama"
          tabIndex={-1}
          className="mx-auto w-full max-w-7xl flex-1 px-4 py-5 sm:px-6 sm:py-6 lg:px-8 focus:outline-none"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
