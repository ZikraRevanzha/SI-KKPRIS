import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { ApiError } from '@/api/client';
import { useAuth } from '@/app/authContext';

export function BerandaSementaraPage() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [sedangKeluar, setSedangKeluar] = useState(false);
  const [sedangMuatProfil, setSedangMuatProfil] = useState(false);
  const [pesanStatus, setPesanStatus] = useState<string | null>(null);

  if (!user) {
    return null;
  }

  const tanganiMuatProfil = async () => {
    setSedangMuatProfil(true);
    setPesanStatus(null);
    try {
      await refreshUser();
      setPesanStatus('Profil berhasil dimuat ulang dari /api/v1/auth/me/.');
    } catch (err) {
      setPesanStatus(err instanceof ApiError ? err.pesan : 'Gagal memuat ulang profil.');
    } finally {
      setSedangMuatProfil(false);
    }
  };

  const tanganiKeluar = async () => {
    setSedangKeluar(true);
    try {
      await logout();
      void navigate('/login', { replace: true });
    } finally {
      setSedangKeluar(false);
    }
  };

  return (
    <main>
      <h1>Beranda Sementara SI-KKPRIS</h1>
      <p>Sesi autentikasi aktif. Muat ulang halaman untuk memverifikasi pemulihan sesi JWT.</p>

      <dl>
        <dt>Nama Lengkap</dt>
        <dd>{user.nama_lengkap}</dd>
        <dt>Username</dt>
        <dd>{user.username}</dd>
        <dt>Peran</dt>
        <dd>
          {user.peran_label} ({user.peran})
        </dd>
        {user.anggota && (
          <>
            <dt>Nomor Anggota</dt>
            <dd>{user.anggota.no_anggota}</dd>
          </>
        )}
      </dl>

      {pesanStatus && <p role="status">{pesanStatus}</p>}

      <div>
        <button type="button" onClick={tanganiMuatProfil} disabled={sedangMuatProfil}>
          {sedangMuatProfil ? 'Memuat…' : 'Muat Ulang Profil (/me)'}
        </button>
        <button type="button" onClick={tanganiKeluar} disabled={sedangKeluar}>
          {sedangKeluar ? 'Keluar…' : 'Keluar'}
        </button>
      </div>

      <nav aria-label="Tautan uji guard peran">
        <ul>
          <li>
            <Link to="/pengurus">Uji Rute Pengurus (Bendahara/Ketua)</Link>
          </li>
          <li>
            <Link to="/ketua">Uji Rute Khusus Ketua</Link>
          </li>
          <li>
            <Link to="/anggota">Uji Rute Khusus Anggota</Link>
          </li>
        </ul>
      </nav>
    </main>
  );
}
