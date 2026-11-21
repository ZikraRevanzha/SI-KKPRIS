import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Navigate, useLocation, useNavigate } from 'react-router';
import { z } from 'zod';
import { ApiError } from '@/api/client';
import { useAuth } from '@/app/authContext';
import { getHomePathByRole } from '@/components/layout/navigation';
import { Button, Dialog, Field, Input, Spinner } from '@/components/ui';
import { LoginIdentitasPanel } from '../components/LoginIdentitasPanel';

const skemaLogin = z.object({
  username: z.string().trim().min(1, 'Username atau Nomor Anggota wajib diisi.'),
  password: z.string().min(1, 'Kata sandi wajib diisi.'),
});

type NilaiFormLogin = z.infer<typeof skemaLogin>;

export function LoginPage() {
  const { isAuthenticated, isInitializing, user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [galatServer, setGalatServer] = useState<string | null>(null);
  const [tampilPassword, setTampilPassword] = useState(false);
  const [dialogLupaOpen, setDialogLupaOpen] = useState(false);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<NilaiFormLogin>({
    resolver: zodResolver(skemaLogin),
    defaultValues: { username: '', password: '' },
  });

  if (isInitializing) {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-canvas px-4">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" label="Memuat…" className="text-brand" />
          <p className="text-sm font-medium text-ink-secondary">Memuat…</p>
        </div>
      </main>
    );
  }

  if (isAuthenticated && user) {
    const tujuan = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    const target = tujuan && tujuan !== '/login' ? tujuan : getHomePathByRole(user.peran);
    return <Navigate to={target} replace />;
  }

  const kirimLogin = async (nilai: NilaiFormLogin) => {
    setGalatServer(null);
    try {
      const pengguna = await login(nilai);
      const tujuan = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      const target = tujuan && tujuan !== '/login' ? tujuan : getHomePathByRole(pengguna.peran);
      void navigate(target, { replace: true });
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
    <main className="flex min-h-dvh items-center bg-canvas px-4 py-8 sm:px-6 lg:px-10">
      <div className="mx-auto grid w-full max-w-5xl grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12">
        <section aria-labelledby="judul-login" className="order-1 lg:order-2 lg:col-span-5">
          <div className="rounded-lg border border-border bg-surface p-6 shadow-[var(--shadow-card)] sm:p-8">
            <div className="mb-6 flex items-center gap-3">
              <div
                aria-hidden="true"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-brand text-sm font-bold text-brand-ink"
              >
                KK
              </div>
              <div>
                <h1 id="judul-login" className="text-xl font-bold leading-tight text-ink">
                  Masuk ke SI-KKPRIS
                </h1>
                <p className="text-sm text-ink-secondary">
                  Gunakan username atau nomor anggota terdaftar
                </p>
              </div>
            </div>

            {galatServer && (
              <div
                role="alert"
                className="mb-5 flex items-start gap-2.5 rounded-md border border-status-danger-border bg-status-danger-bg px-3.5 py-3 text-sm text-status-danger"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{galatServer}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(kirimLogin)} noValidate className="space-y-4">
              <Field
                id="login-username"
                label="Username / No. Anggota"
                required
                error={errors.username?.message}
              >
                <Input
                  id="login-username"
                  type="text"
                  autoComplete="username"
                  spellCheck={false}
                  autoCapitalize="none"
                  autoCorrect="off"
                  enterKeyHint="next"
                  required
                  placeholder="Contoh: bendahara01 atau KKP-2026-001"
                  hasError={Boolean(errors.username)}
                  aria-describedby={errors.username ? 'login-username-error' : undefined}
                  {...register('username')}
                />
              </Field>

              <Field
                id="login-password"
                label="Kata Sandi"
                required
                error={errors.password?.message}
              >
                <div className="relative">
                  <Input
                    id="login-password"
                    type={tampilPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    enterKeyHint="done"
                    required
                    placeholder="Masukkan kata sandi"
                    hasError={Boolean(errors.password)}
                    aria-describedby={errors.password ? 'login-password-error' : undefined}
                    className="pr-12"
                    {...register('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setTampilPassword((prev) => !prev)}
                    aria-label={tampilPassword ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'}
                    aria-pressed={tampilPassword}
                    className="absolute inset-y-0 right-0 inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-r-md text-ink-secondary transition-colors hover:text-ink"
                  >
                    {tampilPassword ? (
                      <EyeOff className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <Eye className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </Field>

              <div className="flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => setDialogLupaOpen(true)}
                  className="min-h-10 cursor-pointer text-sm font-medium text-brand underline-offset-4 hover:underline"
                >
                  Lupa kata sandi?
                </button>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={isSubmitting}
                loadingText="Masuk…"
              >
                Masuk
              </Button>
            </form>

            <p className="mt-5 flex items-center gap-2 border-t border-border pt-4 text-xs text-ink-muted">
              <ShieldCheck className="h-4 w-4 shrink-0 text-brand" aria-hidden="true" />
              <span>Demi keamanan, sesi akan berakhir otomatis setelah 30 menit tidak aktif.</span>
            </p>
          </div>
        </section>

        <LoginIdentitasPanel />
      </div>

      <Dialog
        open={dialogLupaOpen}
        onClose={() => setDialogLupaOpen(false)}
        title="Bantuan Reset Kata Sandi"
        description="Reset kata sandi dilakukan langsung oleh pengurus koperasi untuk menjaga keamanan akun."
        footer={
          <Button variant="primary" onClick={() => setDialogLupaOpen(false)}>
            Mengerti
          </Button>
        }
      >
        <p className="leading-relaxed">
          Silakan hubungi <strong>Bendahara Koperasi KKPRIS SMK Negeri 1 Kota Solok</strong> dengan
          menunjukkan identitas atau nomor anggota Anda untuk mengatur ulang kata sandi.
        </p>
      </Dialog>
    </main>
  );
}
