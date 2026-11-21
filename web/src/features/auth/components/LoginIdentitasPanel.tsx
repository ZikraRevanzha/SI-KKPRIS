import { CalendarClock, HandCoins, Wallet } from 'lucide-react';

const PILAR_KKPRIS = [
  {
    judul: '5 Skema Simpanan',
    ringkas: 'Pokok, Khusus, Wajib, Hari Raya, dan Berencana.',
    ikon: Wallet,
  },
  {
    judul: '3 Akad Syariah',
    ringkas: 'Murabahah, Ijarah, dan Hawalah dengan margin flat.',
    ikon: HandCoins,
  },
  {
    judul: 'Otorisasi Berjenjang',
    ringkas: 'Two-Man Rule Ketua & rekap potong gaji setiap tanggal 24.',
    ikon: CalendarClock,
  },
] as const;

export function LoginIdentitasPanel() {
  return (
    <section aria-label="Informasi Koperasi KKPRIS" className="order-2 lg:order-1 lg:col-span-7">
      <div className="rounded-lg border border-border bg-brand p-6 text-brand-ink sm:p-8">
        <div className="inline-flex items-center gap-2 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-ink">
          <span>Koperasi Syariah SMKN 1 Kota Solok</span>
        </div>

        <h2 className="mt-4 text-2xl font-bold leading-snug text-brand-ink sm:text-3xl">
          Sistem Informasi Pembiayaan &amp; Koperasi Syariah
        </h2>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-brand-muted sm:text-base">
          Pengelolaan terpadu simpanan anggota, pengajuan pembiayaan syariah tanpa denda,
          persetujuan kas berjenjang oleh Ketua, dan rekapitulasi potong gaji bulanan.
        </p>

        <ul className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {PILAR_KKPRIS.map((item) => {
            const Icon = item.ikon;
            return (
              <li
                key={item.judul}
                className="rounded-md border border-brand-hover bg-brand-hover/70 p-4"
              >
                <Icon className="h-5 w-5 text-accent" aria-hidden="true" />
                <p className="mt-2.5 text-sm font-semibold text-brand-ink">{item.judul}</p>
                <p className="mt-1 text-xs leading-relaxed text-brand-muted">{item.ringkas}</p>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="mt-4 px-1">
        <p className="text-base font-bold tracking-tight text-ink">SI-KKPRIS</p>
        <p className="text-sm text-ink-secondary">
          Koperasi Pegawai Republik Indonesia Sejahtera (KKPRIS) SMK Negeri 1 Kota Solok
        </p>
      </div>
    </section>
  );
}
