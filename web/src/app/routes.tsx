import { Navigate, Route, Routes } from 'react-router';
import { AppShell } from '@/components/layout/AppShell';
import { getHomePathByRole } from '@/components/layout/navigation';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { BerandaAnggotaPage } from '@/features/dashboard/pages/BerandaAnggotaPage';
import { DashboardPengurusPage } from '@/features/dashboard/pages/DashboardPengurusPage';
import { ForbiddenPage } from '@/features/system/pages/ForbiddenPage';
import { ModulTerjadwalPage } from '@/features/system/pages/ModulTerjadwalPage';
import { NotFoundPage } from '@/features/system/pages/NotFoundPage';
import { useAuth } from './authContext';
import { ProtectedRoute, RoleRoute } from './guards';

function RedirectBerandaPeran() {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={getHomePathByRole(user.peran)} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<RedirectBerandaPeran />} />

        <Route element={<AppShell />}>
          {/* Area Pengurus: Bendahara & Ketua */}
          <Route element={<RoleRoute allowedRoles={['BENDAHARA', 'KETUA']} />}>
            <Route path="/dashboard" element={<DashboardPengurusPage />} />
            <Route
              path="/anggota"
              element={
                <ModulTerjadwalPage
                  judul="Data Anggota"
                  tahap="Tahap 10"
                  deskripsi="Manajemen keanggotaan guru & pegawai SMKN 1 Kota Solok serta kliring pengunduran diri."
                />
              }
            />
            <Route
              path="/simpanan"
              element={
                <ModulTerjadwalPage
                  judul="Simpanan"
                  tahap="Tahap 11"
                  deskripsi="Pencatatan setor dan tarik 5 skema simpanan anggota koperasi."
                />
              }
            />
            <Route
              path="/pembiayaan"
              element={
                <ModulTerjadwalPage
                  judul="Pembiayaan"
                  tahap="Tahap 12B"
                  deskripsi="Daftar, detail kontrak, jadwal angsuran, dan pencatatan realisasi pencairan."
                />
              }
            />
            <Route
              path="/rekap-gaji"
              element={
                <ModulTerjadwalPage
                  judul="Rekap Potong Gaji"
                  tahap="Tahap 13"
                  deskripsi="Pembuatan rekap potong gaji tanggal 24 serta ekspor Excel dan PDF."
                />
              }
            />
            <Route
              path="/laporan"
              element={
                <ModulTerjadwalPage
                  judul="Laporan Keuangan"
                  tahap="Tahap 14A"
                  deskripsi="Laporan simpanan, pembiayaan, arus kas, dan ikhtisar RAT."
                />
              }
            />
          </Route>

          {/* Area Khusus Bendahara */}
          <Route element={<RoleRoute allowedRoles={['BENDAHARA']} />}>
            <Route
              path="/angsuran"
              element={
                <ModulTerjadwalPage
                  judul="Angsuran"
                  tahap="Tahap 13"
                  deskripsi="Pencatatan pembayaran angsuran dan pemantauan jadwal cicilan anggota."
                />
              }
            />
            <Route
              path="/notifikasi"
              element={
                <ModulTerjadwalPage
                  judul="Notifikasi Tagihan"
                  tahap="Tahap 13"
                  deskripsi="Daftar pengingat tagihan tanggal 10 bagi anggota koperasi."
                />
              }
            />
          </Route>

          {/* Area Khusus Ketua */}
          <Route element={<RoleRoute allowedRoles={['KETUA']} />}>
            <Route
              path="/persetujuan-kas"
              element={
                <ModulTerjadwalPage
                  judul="Persetujuan Kas"
                  tahap="Tahap 12B"
                  deskripsi="Otorisasi pengeluaran kas pembiayaan oleh Ketua Koperasi (Two-Man Rule)."
                />
              }
            />
          </Route>

          {/* Area Khusus Anggota */}
          <Route element={<RoleRoute allowedRoles={['ANGGOTA']} />}>
            <Route path="/beranda" element={<BerandaAnggotaPage />} />
            <Route
              path="/simpanan-saya"
              element={
                <ModulTerjadwalPage
                  judul="Simpanan Saya"
                  tahap="Tahap 11"
                  deskripsi="Rincian saldo dan riwayat 5 skema simpanan pribadi anggota."
                />
              }
            />
            <Route
              path="/pembiayaan-saya"
              element={
                <ModulTerjadwalPage
                  judul="Pembiayaan Saya"
                  tahap="Tahap 12B"
                  deskripsi="Daftar kontrak pembiayaan pribadi, nomor antrean, dan jadwal cicilan."
                />
              }
            />
            <Route
              path="/pembiayaan/ajukan"
              element={
                <ModulTerjadwalPage
                  judul="Ajukan Pembiayaan"
                  tahap="Tahap 12A"
                  deskripsi="Simulasi margin flat dan pengajuan pembiayaan syariah (tanggal 1–20)."
                />
              }
            />
            <Route
              path="/pengunduran-diri"
              element={
                <ModulTerjadwalPage
                  judul="Ajukan Pengunduran Diri"
                  tahap="Tahap 10"
                  deskripsi="Permohonan pengunduran diri anggota dan estimasi kliring saldo."
                />
              }
            />
          </Route>
        </Route>
      </Route>

      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
