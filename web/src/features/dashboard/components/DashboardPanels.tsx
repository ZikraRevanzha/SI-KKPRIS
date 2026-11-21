import { Activity } from 'lucide-react';
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ProgressBar,
  type BadgeVariant,
} from '@/components/ui';
import { cn } from '@/lib/cn';
import { formatRupiah, formatTanggal } from '@/lib/format';
import type { DashboardRingkasan } from '../hooks/useDashboardRingkasan';

function varianBadgeAksi(aksi: string): BadgeVariant {
  if (aksi.includes('GAGAL') || aksi.includes('DITOLAK') || aksi.includes('HAPUS')) {
    return 'danger';
  }
  if (aksi.includes('LOGOUT') || aksi.includes('RESIGN') || aksi.includes('TARIK')) {
    return 'warning';
  }
  return 'success';
}

export function DashboardVisualPanels({ data }: { data: DashboardRingkasan }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <Card className="lg:col-span-7">
        <CardHeader action={<Badge variant="brand">5 Skema Simpanan</Badge>}>
          <CardTitle>Tren Simpanan</CardTitle>
        </CardHeader>
        <CardBody>
          {data.rincian_jenis_simpanan.length === 0 ? (
            <EmptyState
              title="Belum ada skema simpanan"
              description="Master jenis simpanan belum tersedia pada sistem."
            />
          ) : (
            <>
              <div className="grid grid-cols-5 items-end gap-2 pt-4 sm:gap-4">
                {data.rincian_jenis_simpanan.map((item) => (
                  <div key={item.kode} className="flex min-w-0 flex-col items-center gap-2">
                    <span
                      className="uang-tabular w-full truncate text-center text-[0.7rem] font-semibold text-ink-secondary sm:text-xs"
                      title={`${item.nama}: ${formatRupiah(item.saldo)}`}
                    >
                      {formatRupiah(item.saldo)}
                    </span>
                    <div className="flex h-40 w-full items-end justify-center rounded-md bg-surface-subtle p-1.5">
                      <div
                        aria-label={`${item.nama} sebesar ${formatRupiah(item.saldo)}`}
                        className={cn(
                          'w-full max-w-12 rounded-sm transition-[height] duration-200',
                          item.dapat_ditarik ? 'bg-accent' : 'bg-brand',
                        )}
                        style={{ height: `${Math.max(8, Math.min(100, item.tinggi_persen))}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-ink">{item.kode}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3 text-xs text-ink-muted">
                <span className="inline-flex items-center gap-1.5">
                  <span className="inline-block h-2.5 w-2.5 rounded-xs bg-brand" aria-hidden="true" />
                  Terkunci (Pokok, Wajib, Khusus)
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="inline-block h-2.5 w-2.5 rounded-xs bg-accent" aria-hidden="true" />
                  Sukarela (Hari Raya, Berencana)
                </span>
              </div>
            </>
          )}
        </CardBody>
      </Card>

      <Card className="lg:col-span-5">
        <CardHeader action={<Badge variant="neutral">Margin Flat</Badge>}>
          <CardTitle>Distribusi Akad</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col justify-between gap-5">
          {data.distribusi_akad.length === 0 ? (
            <EmptyState
              title="Belum ada data akad"
              description="Belum ada pengajuan pembiayaan syariah yang tercatat."
            />
          ) : (
            <div className="space-y-4">
              {data.distribusi_akad.map((akad) => (
                <div key={akad.kode} className="space-y-1.5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
                    <span className="font-medium text-ink">{akad.label}</span>
                    <span className="uang-tabular text-xs font-medium text-ink-secondary">
                      {akad.jumlah} akad · {formatRupiah(akad.nominal)}
                    </span>
                  </div>
                  <ProgressBar
                    value={akad.persen}
                    label={`Porsi ${akad.label}`}
                    showPercent={false}
                    tone="brand"
                  />
                </div>
              ))}
            </div>
          )}

          <p className="border-t border-border pt-3 text-xs text-ink-muted">
            Batas pokok tanpa agunan: <strong className="text-ink">Rp 70.000.000</strong> · Tenor
            maksimal: <strong className="text-ink">72 bulan</strong>
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

export function AktivitasTerbaruCard({
  aktivitas,
}: {
  aktivitas: DashboardRingkasan['aktivitas_terbaru'];
}) {
  return (
    <Card>
      <CardHeader action={<Badge variant="info">Audit Trail</Badge>}>
        <CardTitle>Aktivitas Terbaru</CardTitle>
      </CardHeader>
      <CardBody className="p-0">
        {aktivitas.length === 0 ? (
          <div className="p-4 sm:p-5">
            <EmptyState
              icon={<Activity className="h-5 w-5" />}
              title="Belum ada aktivitas tercatat"
              description="Riwayat transaksi dan aktivitas pengguna akan muncul di sini secara otomatis."
            />
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {aktivitas.map((log) => (
              <li
                key={log.id}
                className="flex flex-col gap-2 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-5"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-ink">{log.detail_perubahan}</p>
                  <p className="mt-0.5 text-xs text-ink-muted">
                    Oleh <strong className="text-ink-secondary">{log.pengguna_nama}</strong> (
                    {log.pengguna_peran}) · Tabel{' '}
                    <code className="rounded-xs bg-surface-subtle px-1 py-0.5 text-ink-secondary">
                      {log.nama_tabel}
                    </code>{' '}
                    · {formatTanggal(log.created_at, { denganWaktu: true, gaya: 'pendek' })}
                  </p>
                </div>
                <div className="shrink-0">
                  <Badge variant={varianBadgeAksi(log.aksi)}>{log.aksi}</Badge>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
