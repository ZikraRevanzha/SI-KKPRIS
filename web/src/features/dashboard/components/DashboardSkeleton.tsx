import { Card, CardBody, CardHeader, Skeleton, SkeletonGroup } from '@/components/ui';

export function DashboardSkeleton() {
  return (
    <SkeletonGroup label="Memuat ringkasan dashboard…" className="space-y-6">
      {/* 4 Kartu Statistik */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Card key={idx} className="p-4 sm:p-5">
            <div className="flex items-start gap-3.5">
              <Skeleton className="h-10 w-10 shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-6 w-36" />
                <Skeleton className="h-3 w-28" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 2 Panel Visualisasi */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Card className="lg:col-span-7">
          <CardHeader>
            <Skeleton className="h-5 w-36" />
          </CardHeader>
          <CardBody>
            <div className="flex h-52 items-end justify-between gap-4 pt-6">
              {Array.from({ length: 5 }).map((_, idx) => (
                <div key={idx} className="flex flex-1 flex-col items-center gap-2">
                  <Skeleton className="h-28 w-full max-w-12" />
                  <Skeleton className="h-3.5 w-10" />
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="lg:col-span-5">
          <CardHeader>
            <Skeleton className="h-5 w-36" />
          </CardHeader>
          <CardBody className="space-y-5">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between gap-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-2.5 w-full" rounded="full" />
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Aktivitas Terbaru */}
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardBody className="space-y-3">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="flex items-center justify-between gap-4 py-2">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-6 w-24" rounded="full" />
            </div>
          ))}
        </CardBody>
      </Card>
    </SkeletonGroup>
  );
}

export function BerandaAnggotaSkeleton() {
  return (
    <SkeletonGroup label="Memuat beranda anggota…" className="space-y-6">
      {/* 5 Kartu Simpanan */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, idx) => (
          <Card key={idx} className="p-4">
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-10" />
              </div>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
          </Card>
        ))}
      </div>

      {/* Status Pembiayaan */}
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="space-y-2">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-5 w-36" />
              </div>
            ))}
          </div>
          <Skeleton className="h-2.5 w-full" rounded="full" />
        </CardBody>
      </Card>

      {/* Tabel Riwayat */}
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-36" />
        </CardHeader>
        <CardBody className="space-y-3">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-10 w-full" />
          ))}
        </CardBody>
      </Card>
    </SkeletonGroup>
  );
}
