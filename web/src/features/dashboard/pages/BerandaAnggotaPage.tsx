import { Lock, ReceiptText, Unlock } from 'lucide-react';
import type { components } from '@/api/schema';
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorState,
  PageHeader,
  Table,
  type TableColumn,
} from '@/components/ui';
import { formatRupiah, formatTanggal } from '@/lib/format';
import { BerandaAnggotaSkeleton } from '../components/DashboardSkeleton';
import { StatusPembiayaanCard } from '../components/StatusPembiayaanCard';
import { useBerandaAnggotaRingkasan } from '../hooks/useBerandaAnggotaRingkasan';

type RiwayatItem = components['schemas']['RiwayatTerakhirAnggotaItem'];

const KOLOM_RIWAYAT: readonly TableColumn<RiwayatItem>[] = [
  {
    key: 'tanggal',
    header: 'Tanggal',
    render: (row) => (
      <span className="whitespace-nowrap text-ink-secondary">
        {formatTanggal(row.tanggal, { denganWaktu: true, gaya: 'pendek' })}
      </span>
    ),
  },
  {
    key: 'jenis',
    header: 'Jenis',
    render: (row) => <span className="font-medium text-ink">{row.jenis}</span>,
  },
  {
    key: 'keterangan',
    header: 'Keterangan',
    render: (row) => <span className="text-ink-secondary">{row.keterangan}</span>,
  },
  {
    key: 'jumlah',
    header: 'Jumlah',
    numeric: true,
    render: (row) => formatRupiah(row.jumlah),
  },
  {
    key: 'status',
    header: 'Status',
    render: (row) => (
      <Badge variant={row.tipe_badge === 'success' ? 'success' : 'warning'}>{row.status}</Badge>
    ),
  },
];

export function BerandaAnggotaPage() {
  const { data, isPending, isError, error, refetch, isFetching } = useBerandaAnggotaRingkasan();

  if (isPending) {
    return (
      <section>
        <PageHeader
          title="Beranda Anggota"
          description="Portal mandiri keanggotaan Koperasi KKPRIS SMK Negeri 1 Kota Solok."
        />
        <BerandaAnggotaSkeleton />
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <PageHeader
          title="Beranda Anggota"
          description="Portal mandiri keanggotaan Koperasi KKPRIS SMK Negeri 1 Kota Solok."
        />
        <ErrorState
          title="Gagal memuat beranda anggota"
          message={error.pesan}
          onRetry={() => void refetch()}
          isRetrying={isFetching}
        />
      </section>
    );
  }

  const profil = data.anggota;

  return (
    <section className="space-y-6">
      <PageHeader
        title={profil ? `Beranda Anggota — ${profil.nama}` : 'Beranda Anggota'}
        description={
          <>
            {profil ? `No. Anggota ${profil.no_anggota} · ` : ''}
            Total akumulasi simpanan pribadi:{' '}
            <strong className="uang-tabular text-ink">
              {formatRupiah(data.total_simpanan_anggota)}
            </strong>
          </>
        }
      />

      {data.kartu_simpanan.length === 0 ? (
        <EmptyState
          title="Data skema simpanan belum tersedia"
          description="Silakan hubungi Bendahara Koperasi jika daftar simpanan Anda belum tampil."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {data.kartu_simpanan.map((item) => (
            <Card key={item.kode} className="p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-ink">{item.nama}</span>
                <span className="rounded-sm bg-brand-tint px-2 py-0.5 text-xs font-bold text-brand">
                  {item.kode}
                </span>
              </div>
              <p className="uang-tabular mt-3 text-lg font-bold text-ink">
                {formatRupiah(item.saldo)}
              </p>
              <p className="mt-1.5 flex items-center gap-1.5 text-xs text-ink-muted">
                {item.dapat_ditarik ? (
                  <>
                    <Unlock className="h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" />
                    <span>Sukarela (dapat ditarik)</span>
                  </>
                ) : (
                  <>
                    <Lock className="h-3.5 w-3.5 shrink-0 text-ink-muted" aria-hidden="true" />
                    <span>Terkunci (wajib anggota)</span>
                  </>
                )}
              </p>
            </Card>
          ))}
        </div>
      )}

      <StatusPembiayaanCard pembiayaan={data.pembiayaan_aktif} />

      <Card>
        <CardHeader action={<Badge variant="brand">Mutasi Simpanan &amp; Angsuran</Badge>}>
          <CardTitle>Riwayat Terakhir</CardTitle>
        </CardHeader>
        <CardBody>
          {data.riwayat_terakhir.length === 0 ? (
            <EmptyState
              icon={<ReceiptText className="h-5 w-5" />}
              title="Belum ada riwayat transaksi"
              description="Mutasi setoran, penarikan simpanan, dan pembayaran angsuran Anda akan tampil di sini."
            />
          ) : (
            <Table
              caption="Riwayat transaksi simpanan dan angsuran terakhir"
              columns={KOLOM_RIWAYAT}
              rows={data.riwayat_terakhir}
              rowKey={(row, idx) => `${row.tanggal}-${row.jenis}-${idx}`}
            />
          )}
        </CardBody>
      </Card>
    </section>
  );
}
