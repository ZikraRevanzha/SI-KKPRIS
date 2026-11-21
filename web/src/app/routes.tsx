import { Link, Route, Routes } from 'react-router';
import { BerandaSementaraPage } from '@/features/auth/pages/BerandaSementaraPage';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { ForbiddenPage } from '@/features/system/pages/ForbiddenPage';
import { NotFoundPage } from '@/features/system/pages/NotFoundPage';
import { ProtectedRoute, RoleRoute } from './guards';

function HalamanPeranSementara({ judul }: { judul: string }) {
  return (
    <main>
      <h1>{judul}</h1>
      <p>Halaman sementara untuk memverifikasi guard peran pada Tahap 9B.</p>
      <p>
        <Link to="/">Kembali ke Beranda</Link>
      </p>
    </main>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<BerandaSementaraPage />} />

        <Route element={<RoleRoute allowedRoles={['BENDAHARA', 'KETUA']} />}>
          <Route
            path="/pengurus"
            element={<HalamanPeranSementara judul="Area Pengurus (Bendahara / Ketua)" />}
          />
        </Route>

        <Route element={<RoleRoute allowedRoles={['KETUA']} />}>
          <Route path="/ketua" element={<HalamanPeranSementara judul="Area Khusus Ketua" />} />
        </Route>

        <Route element={<RoleRoute allowedRoles={['ANGGOTA']} />}>
          <Route path="/anggota" element={<HalamanPeranSementara judul="Area Khusus Anggota" />} />
        </Route>
      </Route>

      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
