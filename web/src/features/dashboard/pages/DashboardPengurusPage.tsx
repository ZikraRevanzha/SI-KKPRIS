import { Banknote, CheckSquare, Download, HandCoins, Plus, Users, Wallet } from 'lucide-react';
import { Link } from 'react-router';
import { useAuth } from '@/app/authContext';
import { ErrorState, PageHeader } from '@/components/ui';
import { formatRupiah, formatTanggal } from '@/lib/format';
import { AktivitasTerbaruCard, DashboardVisualPanels } from '../components/DashboardPanels';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import { StatCard } from '../components/StatCard';
import { useDashboardRingkasan } from '../hooks/useDashboardRingkasan';

export function DashboardPengurusPage() {
  const { user } = useAuth();
  const { data, isPending, isError, error, refetch, isFetching } = useDashboardRingkasan();

  const adalahKetua = user?.peran === 'KETUA';
  const subjudul = adalahKetua
    ? 'Panel eksekutif Ketua Koperasi — pemantauan likuiditas, otorisasi pengeluaran kas, dan jejak audit.'
    : 'Ringkasan operasional keuangan, simpanan, pembiayaan syariah, dan rekap potong gaji KKPRIS SMKN 1 Kota Solok.';

  const tombolHeader = (
    <>
      <Link
        to="/laporan"
        className="inline-flex min-h-11 items-center gap-2 rounded-md border border-border-input bg-surface px-4 text-sm font-medium text-ink transition-colors hover:bg-surface-subtle"
      >
        <Download className="h-4 w-4" aria-hidden="true" />
        <span>Ekspor</span>
      </Link>
      {adalahKetua ? (
        <Link
          to="/persetujuan-kas"
          className="inline-flex min-h-11 items-center gap-2 rounded-md bg-brand px-4 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-hover"
        >
          <CheckSquare className="h-4 w-4" aria-hidden="true" />
          <span>Persetujuan Kas ({data?.menunggu_approval_ketua ?? 0})</span>
        </Link>
      ) : (
        <Link
          to="/simpanan"
          className="inline-flex min-h-11 items-center gap-2 rounded-md bg-brand px-4 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-hover"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          <span>Transaksi</span>
        </Link>
      )}
    </>
  );

  if (isPending) {
    return (
      <section>
        <PageHeader title="Dashboard" description={subjudul} actions={tombolHeader} />
        <DashboardSkeleton />
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <PageHeader title="Dashboard" description={subjudul} actions={tombolHeader} />
        <ErrorState
          title="Gagal memuat ringkasan dashboard"
          message={error.pesan}
          onRetry={() => void refetch()}
          isRetrying={isFetching}
        />
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <PageHeader title="Dashboard" description={subjudul} actions={tombolHeader} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Anggota"
          value={`${data.total_anggota_aktif} Anggota`}
          meta={`Aktif dari ${data.total_seluruh_anggota} terdaftar`}
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="Total Simpanan"
          value={formatRupiah(data.total_simpanan)}
          meta="Akumulasi 5 skema simpanan"
          icon={<Wallet className="h-5 w-5" />}
          highlight
          numeric
        />
        <StatCard
          label="Pembiayaan Aktif"
          value={formatRupiah(data.sisa_tagihan_aktif)}
          meta={`${data.jumlah_pembiayaan_aktif} akad berjalan · ${data.menunggu_approval_ketua} antrean`}
          icon={<HandCoins className="h-5 w-5" />}
          numeric
        />
        <StatCard
          label="Kas Hari Ini"
          value={formatRupiah(data.kas_hari_ini)}
          meta={`Penerimaan ${formatTanggal(data.hari_ini, { gaya: 'pendek' })}`}
          icon={<Banknote className="h-5 w-5" />}
          numeric
        />
      </div>

      <DashboardVisualPanels data={data} />
      <AktivitasTerbaruCard aktivitas={data.aktivitas_terbaru} />
    </section>
  );
}
