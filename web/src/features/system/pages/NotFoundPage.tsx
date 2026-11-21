import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <main>
      <h1>404 — Halaman Tidak Ditemukan</h1>
      <p>Halaman yang Anda cari tidak tersedia di SI-KKPRIS.</p>
      <p>
        <Link to="/">Kembali ke Beranda</Link>
      </p>
    </main>
  );
}
