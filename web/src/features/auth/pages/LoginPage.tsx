import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { Navigate, useLocation, useNavigate } from 'react-router';
import { z } from 'zod';
import { ApiError } from '@/api/client';
import { useAuth } from '@/app/authContext';

const skemaLogin = z.object({
  username: z.string().trim().min(1, 'Username atau Nomor Anggota wajib diisi.'),
  password: z.string().min(1, 'Kata sandi wajib diisi.'),
});

type NilaiFormLogin = z.infer<typeof skemaLogin>;

export function LoginPage() {
  const { isAuthenticated, isInitializing, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [galatServer, setGalatServer] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<NilaiFormLogin>({
    resolver: zodResolver(skemaLogin),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  if (isInitializing) {
    return (
      <main>
        <p role="status">Memuat sesi…</p>
      </main>
    );
  }

  if (isAuthenticated) {
    const tujuan = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    return <Navigate to={tujuan && tujuan !== '/login' ? tujuan : '/'} replace />;
  }

  const kirimLogin = async (nilai: NilaiFormLogin) => {
    setGalatServer(null);
    try {
      await login(nilai);
      const tujuan = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      void navigate(tujuan && tujuan !== '/login' ? tujuan : '/', { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setGalatServer(err.pesan);
        if (err.detail.username?.[0]) {
          setError('username', { message: err.detail.username[0] });
        }
        if (err.detail.password?.[0]) {
          setError('password', { message: err.detail.password[0] });
        }
      } else {
        setGalatServer('Terjadi kesalahan saat masuk. Silakan coba lagi.');
      }
    }
  };

  return (
    <main>
      <h1>Masuk SI-KKPRIS</h1>
      <p>Halaman login sederhana (Tahap 9B) untuk verifikasi autentikasi JWT terhadap backend.</p>

      {galatServer && <p role="alert">{galatServer}</p>}

      <form onSubmit={handleSubmit(kirimLogin)} noValidate>
        <div>
          <label htmlFor="username">Username atau Nomor Anggota</label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            aria-invalid={Boolean(errors.username)}
            {...register('username')}
          />
          {errors.username && <p role="alert">{errors.username.message}</p>}
        </div>

        <div>
          <label htmlFor="password">Kata Sandi</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={Boolean(errors.password)}
            {...register('password')}
          />
          {errors.password && <p role="alert">{errors.password.message}</p>}
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Memproses…' : 'Masuk'}
        </button>
      </form>
    </main>
  );
}
