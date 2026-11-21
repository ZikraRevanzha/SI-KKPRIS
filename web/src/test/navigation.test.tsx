import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthContext, type AuthContextValue, type PenggunaMe, type Peran } from '@/app/authContext';
import { AppShell } from '@/components/layout/AppShell';
import { getNavigationByRole } from '@/components/layout/navigation';
import { ToastProvider } from '@/components/ui';

function buatPengguna(peran: Peran): PenggunaMe {
  return {
    id: 1,
    username: peran.toLowerCase(),
    nama_lengkap: `Pengguna ${peran}`,
    peran,
    peran_label: peran,
    is_aktif: true,
    anggota:
      peran === 'ANGGOTA'
        ? {
            id: 10,
            no_anggota: 'KKP-2026-001',
            nama: 'Anggota Dummy',
            status: 'AKTIF',
            status_kepegawaian: 'PNS',
          }
        : null,
  };
}

function renderAppShellDenganPeran(peran: Peran, path: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const ctx: AuthContextValue = {
    user: buatPengguna(peran),
    isAuthenticated: true,
    isInitializing: false,
    login: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
    refreshUser: vi.fn(),
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthContext.Provider value={ctx}>
          <MemoryRouter initialEntries={[path]}>
            <Routes>
              <Route element={<AppShell />}>
                <Route path={path} element={<p>Konten Uji</p>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe('Navigasi sesuai peran', () => {
  afterEach(() => {
    cleanup();
  });

  it('menghasilkan 8 menu untuk BENDAHARA termasuk Angsuran & Notifikasi, tanpa Persetujuan Kas', () => {
    const labels = getNavigationByRole('BENDAHARA').map((item) => item.label);
    expect(labels).toEqual([
      'Dashboard',
      'Data Anggota',
      'Simpanan',
      'Pembiayaan',
      'Angsuran',
      'Rekap Potong Gaji',
      'Notifikasi Tagihan',
      'Laporan Keuangan',
    ]);
    expect(labels).not.toContain('Persetujuan Kas');
  });

  it('menghasilkan 7 menu untuk KETUA termasuk Persetujuan Kas, tanpa Angsuran & Notifikasi', () => {
    const labels = getNavigationByRole('KETUA').map((item) => item.label);
    expect(labels).toEqual([
      'Dashboard',
      'Persetujuan Kas',
      'Data Anggota',
      'Simpanan',
      'Pembiayaan',
      'Rekap Potong Gaji',
      'Laporan Keuangan',
    ]);
    expect(labels).not.toContain('Notifikasi Tagihan');
  });

  it('menghasilkan 5 menu khusus portal ANGGOTA', () => {
    const labels = getNavigationByRole('ANGGOTA').map((item) => item.label);
    expect(labels).toEqual([
      'Beranda',
      'Simpanan Saya',
      'Pembiayaan Saya',
      'Ajukan Pembiayaan',
      'Ajukan Pengunduran Diri',
    ]);
  });

  it('merender menu sidebar sesuai peran KETUA pada AppShell beserta tautan lompat ke konten', () => {
    renderAppShellDenganPeran('KETUA', '/dashboard');

    expect(screen.getByRole('link', { name: 'Lompat ke konten utama' })).toBeInTheDocument();
    const navDesktop = screen.getAllByRole('navigation', { name: 'Navigasi utama' })[0];
    expect(within(navDesktop).getByRole('link', { name: 'Persetujuan Kas' })).toBeInTheDocument();
    expect(within(navDesktop).queryByRole('link', { name: 'Simpanan Saya' })).not.toBeInTheDocument();
  });

  it('merender menu sidebar khusus ANGGOTA pada AppShell', () => {
    renderAppShellDenganPeran('ANGGOTA', '/beranda');

    const navDesktop = screen.getAllByRole('navigation', { name: 'Navigasi utama' })[0];
    expect(within(navDesktop).getByRole('link', { name: 'Beranda' })).toBeInTheDocument();
    expect(within(navDesktop).getByRole('link', { name: 'Ajukan Pembiayaan' })).toBeInTheDocument();
    expect(within(navDesktop).queryByRole('link', { name: 'Data Anggota' })).not.toBeInTheDocument();
  });
});
