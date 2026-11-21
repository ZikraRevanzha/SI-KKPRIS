import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiClient } from '@/api/client';
import { AuthContext, type AuthContextValue, type PenggunaMe, type Peran } from '@/app/authContext';
import { BerandaAnggotaPage } from '@/features/dashboard/pages/BerandaAnggotaPage';
import { DashboardPengurusPage } from '@/features/dashboard/pages/DashboardPengurusPage';

function buatWrapper(peran: Peran, element: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const user: PenggunaMe = {
    id: 1,
    username: peran.toLowerCase(),
    nama_lengkap: `Pengguna ${peran}`,
    peran,
    peran_label: peran,
    is_aktif: true,
    anggota:
      peran === 'ANGGOTA'
        ? {
            id: 1,
            no_anggota: 'KKP-2026-001',
            nama: 'Anggota Dummy 01',
            status: 'AKTIF',
            status_kepegawaian: 'PNS',
          }
        : null,
  };
  const ctx: AuthContextValue = {
    user,
    isAuthenticated: true,
    isInitializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={ctx}>
        <MemoryRouter>{element}</MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  );
}

describe('DashboardPengurusPage & BerandaAnggotaPage', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('menampilkan skeleton memuat, lalu data ringkasan Rupiah pada DashboardPengurusPage', async () => {
    vi.spyOn(apiClient, 'GET').mockResolvedValue({
      data: {
        hari_ini: '2026-11-21',
        total_anggota_aktif: 12,
        total_seluruh_anggota: 14,
        total_simpanan: '25500000.00',
        jumlah_pembiayaan_aktif: 3,
        sisa_tagihan_aktif: '18000000.00',
        menunggu_approval_ketua: 2,
        kas_hari_ini: '1500000.00',
        distribusi_akad: [
          { kode: 'MURABAHAH', label: 'Murabahah', jumlah: 2, nominal: '15000000.00', persen: 67 },
          { kode: 'IJARAH', label: 'Ijarah', jumlah: 1, nominal: '5000000.00', persen: 33 },
          { kode: 'HAWALAH', label: 'Hawalah', jumlah: 0, nominal: '0.00', persen: 0 },
        ],
        rincian_jenis_simpanan: [
          { kode: 'SPK', nama: 'Simpanan Pokok', saldo: '4200000.00', dapat_ditarik: false, tinggi_persen: 60 },
          { kode: 'SWJ', nama: 'Simpanan Wajib', saldo: '9000000.00', dapat_ditarik: false, tinggi_persen: 100 },
          { kode: 'SKH', nama: 'Simpanan Khusus', saldo: '6000000.00', dapat_ditarik: false, tinggi_persen: 70 },
          { kode: 'SHR', nama: 'Simpanan Hari Raya', saldo: '4000000.00', dapat_ditarik: true, tinggi_persen: 45 },
          { kode: 'SBR', nama: 'Simpanan Berencana', saldo: '2300000.00', dapat_ditarik: true, tinggi_persen: 25 },
        ],
        aktivitas_terbaru: [],
      },
      error: undefined,
      response: new Response(null, { status: 200 }),
    } as never);

    buatWrapper('BENDAHARA', <DashboardPengurusPage />);

    expect(screen.getByText('Memuat ringkasan dashboard…')).toBeInTheDocument();
    expect(await screen.findByText('Rp 25.500.000')).toBeInTheDocument();
    expect(screen.getByText('12 Anggota')).toBeInTheDocument();
    expect(screen.getByText('Belum ada aktivitas tercatat')).toBeInTheDocument();
  });

  it('menampilkan ErrorState dan tombol Coba lagi ketika fetch Dashboard gagal', async () => {
    const getSpy = vi.spyOn(apiClient, 'GET').mockRejectedValue(
      new ApiError({
        kode: 'GALAT_JARINGAN',
        pesan: 'Tidak dapat terhubung ke server.',
        detail: {},
      }),
    );

    buatWrapper('KETUA', <DashboardPengurusPage />);

    expect(await screen.findByText('Gagal memuat ringkasan dashboard')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));
    expect(getSpy).toHaveBeenCalledTimes(2);
  });

  it('menampilkan 5 kartu simpanan dan keadaan kosong pembiayaan/riwayat pada BerandaAnggotaPage', async () => {
    vi.spyOn(apiClient, 'GET').mockResolvedValue({
      data: {
        anggota: {
          id: 1,
          no_anggota: 'KKP-2026-001',
          nama: 'Anggota Dummy 01',
          status: 'AKTIF',
          status_kepegawaian: 'PNS',
        },
        total_simpanan_anggota: '1000000.00',
        kartu_simpanan: [
          { kode: 'SPK', nama: 'Pokok', nama_lengkap: 'Simpanan Pokok', saldo: '350000.00', dapat_ditarik: false },
          { kode: 'SWJ', nama: 'Wajib', nama_lengkap: 'Simpanan Wajib', saldo: '150000.00', dapat_ditarik: false },
          { kode: 'SKH', nama: 'Khusus', nama_lengkap: 'Simpanan Khusus', saldo: '500000.00', dapat_ditarik: false },
          { kode: 'SHR', nama: 'Hari Raya', nama_lengkap: 'Simpanan Hari Raya', saldo: '0.00', dapat_ditarik: true },
          { kode: 'SBR', nama: 'Berencana', nama_lengkap: 'Simpanan Berencana', saldo: '0.00', dapat_ditarik: true },
        ],
        pembiayaan_aktif: null,
        riwayat_terakhir: [],
      },
      error: undefined,
      response: new Response(null, { status: 200 }),
    } as never);

    buatWrapper('ANGGOTA', <BerandaAnggotaPage />);

    expect(await screen.findByText('Rp 350.000')).toBeInTheDocument();
    expect(screen.getByText('Rp 500.000')).toBeInTheDocument();
    expect(screen.getByText('Belum memiliki pembiayaan aktif')).toBeInTheDocument();
    expect(screen.getByText('Belum ada riwayat transaksi')).toBeInTheDocument();
  });
});
