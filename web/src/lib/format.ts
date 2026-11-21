/**
 * Utilitas pemformatan uang (Rupiah) dan tanggal (Asia/Jakarta, id-ID).
 *
 * Aturan presisi finansial (AGENTS.md Bagian 4.E):
 * - Uang diterima sebagai string desimal dari API (DECIMAL(15,2)).
 * - DILARANG menggunakan parseFloat, Number(), +x, atau aritmetika uang di browser.
 * - formatRupiah bekerja 100% melalui manipulasi string murni.
 */

const POLA_DESIMAL = /^(-)?(\d+)(?:\.(\d+))?$/;
const POLA_TANGGAL_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;
const POLA_WAKTU_NAIF = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/;

export interface FormatRupiahOptions {
  /** Paksa tampilkan dua angka sen (,00) meskipun nilainya nol. Default: false. */
  tampilkanSen?: boolean;
}

/**
 * Memformat string desimal uang dari server (mis. "1500000.00" atau "1428571.43")
 * menjadi format Rupiah Indonesia tanpa konversi floating-point.
 */
export function formatRupiah(value: string, options?: FormatRupiahOptions): string {
  const bersih = value.trim();
  const cocok = POLA_DESIMAL.exec(bersih);
  if (!cocok) {
    return '-';
  }

  const negatif = Boolean(cocok[1]);
  const bulatMentah = cocok[2];
  const desimalMentah = cocok[3];

  const bagianBulat = bulatMentah.replace(/^0+(?=\d)/, '');
  const senNormalized = desimalMentah
    ? desimalMentah.length === 1
      ? `${desimalMentah}0`
      : desimalMentah
    : '00';

  const adaSenNonNol = /[1-9]/.test(senNormalized);
  const adalahNol = bagianBulat === '0' && !adaSenNonNol;
  const tanda = negatif && !adalahNol ? '-' : '';
  const bulatTerformat = bagianBulat.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

  if (options?.tampilkanSen || adaSenNonNol) {
    return `${tanda}Rp ${bulatTerformat},${senNormalized}`;
  }
  return `${tanda}Rp ${bulatTerformat}`;
}

export interface FormatTanggalOptions {
  /** Sertakan jam dan menit (WIB). Default: false. */
  denganWaktu?: boolean;
  /** Gaya nama bulan: 'panjang' (November) atau 'pendek' (Nov). Default: 'panjang'. */
  gaya?: 'panjang' | 'pendek';
}

const ZONA_WIB = 'Asia/Jakarta';

/**
 * Memformat string tanggal/waktu ISO 8601 menjadi format Bahasa Indonesia (Asia/Jakarta).
 * Menangani tanggal tanpa jam (YYYY-MM-DD) tanpa pergeseran zona waktu, serta datetime naif
 * dari Django (USE_TZ=False, Asia/Jakarta) dengan menambahkan offset +07:00.
 */
export function formatTanggal(value: string, options?: FormatTanggalOptions): string {
  const bersih = value.trim();
  if (!bersih) {
    return '-';
  }

  let tanggalObj: Date;
  const cocokTanggal = POLA_TANGGAL_ISO.exec(bersih);

  if (cocokTanggal) {
    const tahun = parseInt(cocokTanggal[1], 10);
    const bulan = parseInt(cocokTanggal[2], 10);
    const hari = parseInt(cocokTanggal[3], 10);
    // Tengah hari UTC (19:00 WIB) menjaga tanggal kalender tetap akurat di zona Asia/Jakarta
    tanggalObj = new Date(Date.UTC(tahun, bulan - 1, hari, 12, 0, 0));
    if (
      tanggalObj.getUTCFullYear() !== tahun ||
      tanggalObj.getUTCMonth() !== bulan - 1 ||
      tanggalObj.getUTCDate() !== hari
    ) {
      return '-';
    }
  } else {
    const isoNormal = POLA_WAKTU_NAIF.test(bersih)
      ? `${bersih.replace(' ', 'T')}+07:00`
      : bersih;
    tanggalObj = new Date(isoNormal);
  }

  if (Number.isNaN(tanggalObj.getTime())) {
    return '-';
  }

  const gayaBulan = options?.gaya === 'pendek' ? 'short' : 'long';
  const tanggalTerformat = new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: gayaBulan,
    year: 'numeric',
    timeZone: ZONA_WIB,
  }).format(tanggalObj);

  if (options?.denganWaktu) {
    const waktuTerformat = new Intl.DateTimeFormat('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: ZONA_WIB,
    }).format(tanggalObj);
    return `${tanggalTerformat}, ${waktuTerformat} WIB`;
  }

  return tanggalTerformat;
}
