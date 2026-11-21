import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthContext, type AuthContextValue, type PenggunaMe, type Peran } from '@/app/authContext';
import { ProtectedRoute, RoleRoute } from '@/app/guards';

function buatPengguna(peran: Peran): PenggunaMe {
  return {
    id: 1,
    username: peran.toLowerCase(),
    nama_lengkap: `Pengguna ${peran}`,
    peran,
    peran_label: peran,
    is_aktif: true,
    anggota: null,
  };
}

function renderDenganAuth(
  user: PenggunaMe | null,
  initialEntry: string,
  allowedRoles: readonly Peran[],
) {
  const ctx: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isInitializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  };

  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<p>Halaman Login</p>} />
          <Route path="/403" element={<p>Halaman 403 Ditolak</p>} />
          <Route element={<ProtectedRoute />}>
            <Route element={<RoleRoute allowedRoles={allowedRoles} />}>
              <Route path="/rahasia" element={<p>Konten Terlindungi</p>} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe('ProtectedRoute & RoleRoute', () => {
  afterEach(() => {
    cleanup();
  });

  it('mengizinkan pengguna dengan peran yang sesuai membuka rute', () => {
    renderDenganAuth(buatPengguna('BENDAHARA'), '/rahasia', ['BENDAHARA', 'KETUA']);
    expect(screen.getByText('Konten Terlindungi')).toBeInTheDocument();
  });

  it('menolak peran yang tidak diizinkan dan mengarahkan ke /403', () => {
    renderDenganAuth(buatPengguna('ANGGOTA'), '/rahasia', ['BENDAHARA', 'KETUA']);
    expect(screen.getByText('Halaman 403 Ditolak')).toBeInTheDocument();
    expect(screen.queryByText('Konten Terlindungi')).not.toBeInTheDocument();
  });

  it('mengarahkan pengguna yang belum login ke /login', () => {
    renderDenganAuth(null, '/rahasia', ['ANGGOTA']);
    expect(screen.getByText('Halaman Login')).toBeInTheDocument();
    expect(screen.queryByText('Konten Terlindungi')).not.toBeInTheDocument();
  });
});
