import { Link } from 'react-router';

export function ForbiddenPage() {
  return (
    <main>
      <h1>403 — Akses Ditolak</h1>
      <p>Anda tidak memiliki izin peran untuk membuka halaman ini.</p>
      <p>
        <Link to="/">Kembali ke Beranda</Link>
      </p>
    </main>
  );
}
