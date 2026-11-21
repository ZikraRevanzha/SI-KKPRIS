import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/api/client';
import { AuthContext, type AuthContextValue, type PenggunaMe } from '@/app/authContext';
import { LoginPage } from '@/features/auth/pages/LoginPage';

function buatAuthCtx(override?: Partial<AuthContextValue>): AuthContextValue {
  return {
    user: null,
    isAuthenticated: false,
    isInitializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    ...override,
  };
}

function renderLogin(ctx: AuthContextValue) {
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<p>Halaman Dashboard Pengurus</p>} />
          <Route path="/beranda" element={<p>Halaman Beranda Anggota</p>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe('LoginPage', () => {
  afterEach(() => {
    cleanup();
  });

  it('menampilkan validasi Bahasa Indonesia saat username dan kata sandi kosong, tanpa checkbox Ingat saya', async () => {
    const loginMock = vi.fn();
    renderLogin(buatAuthCtx({ login: loginMock }));

    expect(screen.queryByLabelText(/ingat saya/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Masuk' }));

    expect(await screen.findByText('Username atau Nomor Anggota wajib diisi.')).toBeInTheDocument();
    expect(await screen.findByText('Kata sandi wajib diisi.')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('menampilkan tombol loading "Masuk…" lalu mengarahkan ke /dashboard saat Bendahara berhasil masuk', async () => {
    let selesaikanLogin!: (pengguna: PenggunaMe) => void;
    const loginMock = vi.fn(
      () =>
        new Promise<PenggunaMe>((resolve) => {
          selesaikanLogin = resolve;
        }),
    );

    renderLogin(buatAuthCtx({ login: loginMock }));

    fireEvent.change(screen.getByLabelText(/Username \/ No\. Anggota/i, { selector: 'input' }), {
      target: { value: 'bendahara01' },
    });
    fireEvent.change(screen.getByLabelText(/Kata Sandi/i, { selector: 'input' }), {
      target: { value: 'Rahasia123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Masuk' }));

    await waitFor(() => {
      const tombol = screen.getByRole('button', { name: /Masuk…/i });
      expect(tombol).toBeDisabled();
      expect(tombol).toHaveAttribute('aria-busy', 'true');
    });

    selesaikanLogin({
      id: 2,
      username: 'bendahara01',
      nama_lengkap: 'Bendahara Dummy',
      peran: 'BENDAHARA',
      peran_label: 'Bendahara Koperasi',
      is_aktif: true,
      anggota: null,
    });

    expect(await screen.findByText('Halaman Dashboard Pengurus')).toBeInTheDocument();
  });

  it('menampilkan galat server pada role="alert" ketika kredensial ditolak', async () => {
    const loginMock = vi.fn().mockRejectedValue(
      new ApiError({
        kode: 'KREDENSIAL_TIDAK_VALID',
        pesan: 'Username / Nomor Anggota atau Password tidak valid.',
        detail: {},
      }),
    );

    renderLogin(buatAuthCtx({ login: loginMock }));

    fireEvent.change(screen.getByLabelText(/Username \/ No\. Anggota/i, { selector: 'input' }), {
      target: { value: 'bendahara01' },
    });
    fireEvent.change(screen.getByLabelText(/Kata Sandi/i, { selector: 'input' }), {
      target: { value: 'SalahPassword' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Masuk' }));

    expect(
      await screen.findByText('Username / Nomor Anggota atau Password tidak valid.'),
    ).toBeInTheDocument();
  });
});
