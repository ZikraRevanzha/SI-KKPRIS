import { Clock } from 'lucide-react';
import { Link } from 'react-router';
import { useAuth } from '@/app/authContext';
import { getHomePathByRole } from '@/components/layout/navigation';
import { EmptyState, PageHeader } from '@/components/ui';

export interface ModulTerjadwalPageProps {
  judul: string;
  tahap: string;
  deskripsi: string;
}

export function ModulTerjadwalPage({ judul, tahap, deskripsi }: ModulTerjadwalPageProps) {
  const { user } = useAuth();
  const beranda = user ? getHomePathByRole(user.peran) : '/';

  return (
    <section>
      <PageHeader title={judul} description={deskripsi} />
      <EmptyState
        icon={<Clock className="h-5 w-5" />}
        title={`Modul dijadwalkan pada ${tahap}`}
        description={`Antarmuka React untuk modul ${judul} belum dibangun pada Tahap 9C dan akan diaktifkan sesuai roadmap pada ${tahap}.`}
        action={
          <Link
            to={beranda}
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-border-input bg-surface px-4 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle"
          >
            Kembali ke Ringkasan
          </Link>
        }
      />
    </section>
  );
}
