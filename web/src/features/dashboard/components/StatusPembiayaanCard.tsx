import { HandCoins } from 'lucide-react';
import { Link } from 'react-router';
import type { components } from '@/api/schema';
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
import { formatRupiah } from '@/lib/format';

type StatusPembiayaan = components['schemas']['StatusPembiayaanAnggota'];

function varianStatusPembiayaan(status: string): BadgeVariant {
  if (status === 'AKTIF' || status === 'LUNAS') {
    return 'success';
  }
  if (status === 'DITOLAK') {
    return 'danger';
  }
  return 'warning';
}

export function StatusPembiayaanCard({ pembiayaan }: { pembiayaan: StatusPembiayaan | null }) {
  return (
    <Card>
      <CardHeader
        action={
          pembiayaan ? (
            <Badge variant={varianStatusPembiayaan(pembiayaan.status)}>
              {pembiayaan.status_label} (Antrean #{pembiayaan.no_antrean})
            </Badge>
          ) : (
            <Badge variant="neutral">Tidak Ada Akad Aktif</Badge>
          )
        }
      >
        <CardTitle>Status Pembiayaan</CardTitle>
      </CardHeader>
      <CardBody>
        {pembiayaan ? (
          <div className="space-y-5">
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-md bg-surface-subtle p-3.5">
                <dt className="text-xs font-medium text-ink-muted">Akad</dt>
                <dd className="mt-1 text-sm font-semibold text-ink">
                  {pembiayaan.jenis_akad_label}{' '}
                  <span className="text-ink-secondary">({pembiayaan.no_pembiayaan})</span>
                </dd>
              </div>
              <div className="rounded-md bg-surface-subtle p-3.5">
                <dt className="text-xs font-medium text-ink-muted">Sisa Pembiayaan</dt>
                <dd className="uang-tabular mt-1 text-base font-bold text-ink">
                  {formatRupiah(pembiayaan.sisa_kewajiban)}
                </dd>
              </div>
              <div className="rounded-md bg-surface-subtle p-3.5">
                <dt className="text-xs font-medium text-ink-muted">Angsuran / Bulan</dt>
                <dd className="uang-tabular mt-1 text-base font-bold text-ink">
                  {formatRupiah(pembiayaan.angsuran_bulanan)}
                </dd>
              </div>
            </dl>

            <ProgressBar
              value={pembiayaan.progress_persen}
              label={`Progres pelunasan (${pembiayaan.angsuran_lunas_count} dari ${pembiayaan.total_tenor} bulan)`}
              tone="brand"
            />
          </div>
        ) : (
          <EmptyState
            icon={<HandCoins className="h-5 w-5" />}
            title="Belum memiliki pembiayaan aktif"
            description="Pengajuan pembiayaan syariah dibuka setiap tanggal 1 sampai 20 tiap bulan melalui portal anggota."
            action={
              <Link
                to="/pembiayaan/ajukan"
                className="inline-flex min-h-11 items-center justify-center rounded-md bg-brand px-4 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-hover"
              >
                Ajukan Pembiayaan
              </Link>
            }
          />
        )}
      </CardBody>
    </Card>
  );
}
