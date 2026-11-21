"""
LaporanKeuangan (Service) & LaporanBuktiController serta Views Laporan Keuangan
Triwulanan & Tahunan RAT (SHU & Neraca), Cetak Kuitansi PDF Digital, dan Audit Trail Log
(Tahap 7 — UC-13, UC-15 | FR-RPT-01 s.d. FR-RPT-04, NFR-SEC-03).

Selaras dengan:
- 03_Class_Diagram_SI-KKPRIS.mmd (LaporanKeuangan & LaporanBuktiController)
- Sequence Diagram SQ-12 (Cetak Bukti Transaksi & Angsuran) & SQ-14 (Lihat & Ekspor Laporan Keuangan)
- Wireframe Final Tahap 7:
  20. Cetak Bukti Transaksi.png (WD-07)
  21. Cetak Bukti Pembayaran.png (WD-11)
  22. Laporan Keuangan.png (WD-14)
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from xhtml2pdf import pisa
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from koperasi.controllers.auth_controller import (
    _ambil_ip_klien,
    login_wajib,
    peran_wajib,
)
from koperasi.controllers.simpanan_controller import _hitung_saldo_sebelum
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JadwalAngsuran,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    NamaAkadChoices,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PengunduranDiri,
    PeranPenggunaChoices,
    RealisasiPencairan,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)


def _rentang_tanggal_periode(kode_periode: str, tahun: int) -> tuple[date, date, str]:
    """
    Menentukan tanggal mulai, tanggal selesai, dan label periode berdasarkan pilihan
    Triwulan (TW1..TW4) atau Tahunan (TAHUNAN / RAT).
    """
    thn = int(tahun or date.today().year)
    kode = (kode_periode or 'TAHUNAN').strip().upper()
    peta = {
        'TW1': (date(thn, 1, 1), date(thn, 3, 31), f'Triwulan I (Januari – Maret {thn})'),
        'TW2': (date(thn, 4, 1), date(thn, 6, 30), f'Triwulan II (April – Juni {thn})'),
        'TW3': (date(thn, 7, 1), date(thn, 9, 30), f'Triwulan III (Juli – September {thn})'),
        'TW4': (date(thn, 10, 1), date(thn, 12, 31), f'Triwulan IV (Oktober – Desember {thn})'),
        'TAHUNAN': (date(thn, 1, 1), date(thn, 12, 31), f'Laporan Tahunan RAT ({thn})'),
    }
    return peta.get(kode, peta['TAHUNAN'])


# ============================================================================
# CLASS SERVICE: LaporanKeuangan (Sesuai 03_Class_Diagram_SI-KKPRIS.mmd)
# ============================================================================

class LaporanKeuangan:
    """
    Service Kompilasi Laporan Keuangan Triwulanan (Arus Kas & Realisasi),
    Perhitungan Neraca & Sisa Hasil Usaha (SHU) Tahunan RAT, serta Generator PDF/Excel.
    Seluruh kalkulasi menggunakan tipe Decimal(15,2) tanpa konversi float.
    """

    def __init__(
        self,
        jenis_laporan: str = 'KAS_MASUK_KELUAR',
        periode_mulai: date = None,
        periode_selesai: date = None,
    ):
        self.jenis_laporan = (jenis_laporan or 'SIMPANAN').upper()
        hari_ini = date.today()
        self.periode_mulai = periode_mulai or date(hari_ini.year, 1, 1)
        self.periode_selesai = periode_selesai or date(hari_ini.year, 12, 31)

    @classmethod
    def kompilasiArusKasDanRealisasi(
        cls,
        periode_mulai: date,
        periode_selesai: date,
        tab_aktif: str = 'SIMPANAN',
    ) -> dict:
        """
        Mengompilasi jurnal mutasi Debit (Kas Masuk), Kredit (Kas Keluar), dan Saldo Berjalan
        berdasarkan tab laporan ('SIMPANAN', 'PEMBIAYAAN', atau 'KAS_MASUK_KELUAR').
        """
        tab = (tab_aktif or 'SIMPANAN').strip().upper()
        entri_mentah = []

        # 1. Komponen Transaksi Simpanan (Setor = Debit/Kas Masuk, Tarik = Kredit/Kas Keluar)
        if tab in ('SIMPANAN', 'KAS_MASUK_KELUAR'):
            qs_smp = (
                TransaksiSimpanan.objects.select_related('anggota', 'jenis_simpanan')
                .filter(
                    tanggal_transaksi__date__gte=periode_mulai,
                    tanggal_transaksi__date__lte=periode_selesai,
                )
                .order_by('tanggal_transaksi', 'id')
            )
            for ts in qs_smp:
                is_setor = ts.jenis_transaksi == JenisTransaksiSimpananChoices.SETOR
                entri_mentah.append({
                    'tanggal': ts.tanggal_transaksi.date(),
                    'waktu_urut': ts.tanggal_transaksi,
                    'no_referensi': ts.no_kuitansi,
                    'tipe_kuitansi': 'SIMPANAN',
                    'kategori': ts.jenis_simpanan.nama,
                    'keterangan': (
                        f"{ts.get_jenis_transaksi_display()} {ts.jenis_simpanan.nama} — "
                        f"{ts.anggota.nama} ({ts.anggota.no_anggota}) [{ts.no_kuitansi}]"
                    ),
                    'debit': ts.nominal if is_setor else Decimal('0.00'),
                    'kredit': Decimal('0.00') if is_setor else ts.nominal,
                })

        # 2. Komponen Pembiayaan & Angsuran (Angsuran Masuk = Debit, Pencairan/Realisasi = Kredit)
        if tab in ('PEMBIAYAAN', 'KAS_MASUK_KELUAR'):
            # Realisasi Pencairan Pembiayaan (Kredit / Kas Keluar)
            qs_cair = (
                RealisasiPencairan.objects.select_related(
                    'pembiayaan', 'pembiayaan__anggota', 'pembiayaan__jenis_akad'
                )
                .filter(
                    tanggal_realisasi__gte=periode_mulai,
                    tanggal_realisasi__lte=periode_selesai,
                )
                .order_by('tanggal_realisasi', 'id')
            )
            for rc in qs_cair:
                pmb = rc.pembiayaan
                entri_mentah.append({
                    'tanggal': rc.tanggal_realisasi,
                    'waktu_urut': timezone.make_aware(
                        datetime.combine(rc.tanggal_realisasi, datetime.min.time())
                    ),
                    'no_referensi': pmb.no_pembiayaan,
                    'tipe_kuitansi': 'REALISASI',
                    'kategori': f"Pencairan {pmb.jenis_akad.get_nama_display()}",
                    'keterangan': (
                        f"Realisasi Pencairan {pmb.jenis_akad.get_nama_display()} ({pmb.no_pembiayaan}) — "
                        f"{pmb.anggota.nama} (Ref: {rc.nomor_referensi_bank})"
                    ),
                    'debit': Decimal('0.00'),
                    'kredit': rc.nominal_cair,
                })

            # Pembayaran Angsuran Masuk (Debit / Kas Masuk)
            qs_ang = (
                PembayaranAngsuran.objects.select_related(
                    'jadwal_angsuran',
                    'jadwal_angsuran__pembiayaan',
                    'jadwal_angsuran__pembiayaan__anggota',
                    'jadwal_angsuran__pembiayaan__jenis_akad',
                )
                .filter(
                    tanggal_bayar__date__gte=periode_mulai,
                    tanggal_bayar__date__lte=periode_selesai,
                )
                .order_by('tanggal_bayar', 'id')
            )
            for pa in qs_ang:
                jdw = pa.jadwal_angsuran
                pmb = jdw.pembiayaan
                entri_mentah.append({
                    'tanggal': pa.tanggal_bayar.date(),
                    'waktu_urut': pa.tanggal_bayar,
                    'no_referensi': pa.no_kuitansi,
                    'tipe_kuitansi': 'ANGSURAN',
                    'kategori': f"Angsuran {pmb.jenis_akad.get_nama_display()}",
                    'keterangan': (
                        f"Angsuran ke-{jdw.angsuran_ke} {pmb.no_pembiayaan} — "
                        f"{pmb.anggota.nama} ({pmb.anggota.no_anggota}) [{pa.no_kuitansi}]"
                    ),
                    'debit': pa.nominal_bayar,
                    'kredit': Decimal('0.00'),
                })

        # Urutkan kronologis dari terlama ke terbaru untuk menghitung Saldo Berjalan (Running Balance)
        entri_mentah.sort(key=lambda x: (x['tanggal'], x['no_referensi']))

        total_debit = Decimal('0.00')
        total_kredit = Decimal('0.00')
        saldo_berjalan = Decimal('0.00')
        baris_jurnal = []

        for item in entri_mentah:
            debit = item['debit'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            kredit = item['kredit'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_debit += debit
            total_kredit += kredit
            saldo_berjalan = (saldo_berjalan + debit - kredit).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            baris_jurnal.append({
                'tanggal': item['tanggal'],
                'no_referensi': item['no_referensi'],
                'tipe_kuitansi': item['tipe_kuitansi'],
                'kategori': item['kategori'],
                'keterangan': item['keterangan'],
                'debit': debit,
                'kredit': kredit,
                'saldo': saldo_berjalan,
            })

        # Tampilkan urutan terbaru di atas pada tabel UI, namun tetap menyimpan saldo berjalan yang akurat
        baris_jurnal_terbaru = list(reversed(baris_jurnal))

        return {
            'tab_aktif': tab,
            'periode_mulai': periode_mulai,
            'periode_selesai': periode_selesai,
            'total_debit': total_debit,
            'total_kredit': total_kredit,
            'saldo_akhir': (total_debit - total_kredit).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'baris_jurnal': baris_jurnal_terbaru,
            'baris_jurnal_kronologis': baris_jurnal,
        }

    @classmethod
    def hitungNeracaDanSHU(cls, tahun_buku: int = None) -> dict:
        """
        Menghitung Neraca Keuangan Koperasi & Sisa Hasil Usaha (SHU) untuk Laporan Tahunan RAT
        (FR-RPT-02):
        - Pendapatan Margin / Ujrah Syariah Terealisasi (dari angsuran LUNAS pada tahun buku)
        - Total Simpanan Anggota (Terkunci: Pokok, Wajib, Khusus vs Sukarela: Hari Raya, Berencana)
        - Total Piutang Pembiayaan Berjalan (Pokok & Margin Belum Lunas)
        - Alokasi Pembagian SHU (Cadangan Koperasi, Jasa Simpanan Anggota, Jasa Pembiayaan, Pengurus & Sosial)
        """
        # PENDING PND-09: rumus SHU, format neraca, dan daftar akun belum dikonfirmasi mitra
        # (terkait TBD-05 SRS v4.0). Seluruh perhitungan di fungsi ini bersifat sementara.
        thn = int(tahun_buku or date.today().year)
        akhir_tahun = date(thn, 12, 31)

        # 1. Akumulasi Simpanan Anggota s.d. akhir tahun buku
        agg_smp = TransaksiSimpanan.objects.filter(
            tanggal_transaksi__date__lte=akhir_tahun
        ).aggregate(
            setor_terkunci=Sum(
                'nominal',
                filter=Q(jenis_transaksi='SETOR', jenis_simpanan__dapat_ditarik=False),
            ),
            tarik_terkunci=Sum(
                'nominal',
                filter=Q(jenis_transaksi='TARIK', jenis_simpanan__dapat_ditarik=False),
            ),
            setor_sukarela=Sum(
                'nominal',
                filter=Q(jenis_transaksi='SETOR', jenis_simpanan__dapat_ditarik=True),
            ),
            tarik_sukarela=Sum(
                'nominal',
                filter=Q(jenis_transaksi='TARIK', jenis_simpanan__dapat_ditarik=True),
            ),
        )
        simpanan_terkunci = (
            (agg_smp['setor_terkunci'] or Decimal('0.00'))
            - (agg_smp['tarik_terkunci'] or Decimal('0.00'))
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        simpanan_sukarela = (
            (agg_smp['setor_sukarela'] or Decimal('0.00'))
            - (agg_smp['tarik_sukarela'] or Decimal('0.00'))
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_modal_simpanan = (simpanan_terkunci + simpanan_sukarela).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # 2. Piutang Pembiayaan Aktif & Pendapatan Margin/Ujrah Syariah (SHU)
        agg_jadwal = JadwalAngsuran.objects.filter(
            pembiayaan__status__in=[StatusPembiayaanChoices.AKTIF, StatusPembiayaanChoices.LUNAS]
        ).aggregate(
            piutang_pokok=Sum(
                'porsi_pokok',
                filter=Q(status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS),
            ),
            piutang_margin=Sum(
                'porsi_margin',
                filter=Q(status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS),
            ),
            margin_terealisasi=Sum(
                'porsi_margin',
                filter=Q(status_bayar=StatusBayarAngsuranChoices.LUNAS),
            ),
            pokok_tertagih=Sum(
                'porsi_pokok',
                filter=Q(status_bayar=StatusBayarAngsuranChoices.LUNAS),
            ),
        )
        piutang_pokok = (agg_jadwal['piutang_pokok'] or Decimal('0.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        piutang_margin = (agg_jadwal['piutang_margin'] or Decimal('0.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        pendapatan_margin_shu = (agg_jadwal['margin_terealisasi'] or Decimal('0.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Potongan margin (Muqashah) mengurangi pendapatan margin kotor
        # PENDING PND-08: aturan potongan pelunasan dipercepat belum dikonfirmasi.
        total_muqashah = (
            PembayaranAngsuran.objects.filter(tanggal_bayar__year=thn).aggregate(
                pot=Sum('potongan_margin')
            )['pot']
            or Decimal('0.00')
        )
        shu_bersih = max(
            Decimal('0.00'),
            (pendapatan_margin_shu - total_muqashah).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        )

        # 3. Distribusi Alokasi SHU RAT (Jasa Simpanan 40%, Jasa Pembiayaan 25%, Cadangan Modal 20%, Pengurus & Sosial 15%)
        # PENDING PND-09: persentase alokasi SHU di bawah TIDAK bersumber dari wawancara/SRS
        # (nilai contoh). Wajib diganti dengan ketentuan AD/ART KKPRIS setelah dikonfirmasi.
        alokasi_shu = [
            {
                'komponen': 'Jasa Simpanan Anggota (Modal)',
                'persen': 40,
                'nominal': (shu_bersih * Decimal('0.40')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            },
            {
                'komponen': 'Jasa Transaksi Pembiayaan Anggota',
                'persen': 25,
                'nominal': (shu_bersih * Decimal('0.25')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            },
            {
                'komponen': 'Cadangan Modal Koperasi KKPRIS',
                'persen': 20,
                'nominal': (shu_bersih * Decimal('0.20')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            },
            {
                'komponen': 'Dana Pengurus, Pendidikan & Sosial',
                'persen': 15,
                'nominal': (shu_bersih * Decimal('0.15')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            },
        ]

        # 4. Ringkasan per Triwulan (TW1..TW4) untuk Grafik Batang pada Kartu Visual Laporan Keuangan
        ringkasan_triwulan = []
        max_nilai_tw = Decimal('1.00')
        for idx_tw, (bln_awal, bln_akhir, label_tw) in enumerate(
            [
                (1, 3, 'Triwulan I'),
                (4, 6, 'Triwulan II'),
                (7, 9, 'Triwulan III'),
                (10, 12, 'Triwulan IV'),
            ],
            start=1,
        ):
            tgl_a = date(thn, bln_awal, 1)
            tgl_b = date(thn, bln_akhir, 31 if bln_akhir in (3, 12) else 30)
            komp = cls.kompilasiArusKasDanRealisasi(tgl_a, tgl_b, 'KAS_MASUK_KELUAR')
            if komp['total_debit'] > max_nilai_tw:
                max_nilai_tw = komp['total_debit']
            if komp['total_kredit'] > max_nilai_tw:
                max_nilai_tw = komp['total_kredit']
            ringkasan_triwulan.append({
                'kode': f'TW{idx_tw}',
                'label': label_tw,
                'debit': komp['total_debit'],
                'kredit': komp['total_kredit'],
                'saldo': komp['saldo_akhir'],
            })

        for item in ringkasan_triwulan:
            item['tinggi_debit'] = (
                max(12, int((item['debit'] / max_nilai_tw) * 100))
                if item['debit'] > Decimal('0.00')
                else 8
            )
            item['tinggi_kredit'] = (
                max(12, int((item['kredit'] / max_nilai_tw) * 100))
                if item['kredit'] > Decimal('0.00')
                else 8
            )

        return {
            'tahun_buku': thn,
            'simpanan_terkunci': simpanan_terkunci,
            'simpanan_sukarela': simpanan_sukarela,
            'total_modal_simpanan': total_modal_simpanan,
            'piutang_pokok': piutang_pokok,
            'piutang_margin': piutang_margin,
            'total_piutang_pembiayaan': (piutang_pokok + piutang_margin).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ),
            'pendapatan_margin_shu': pendapatan_margin_shu,
            'total_muqashah': total_muqashah,
            'shu_bersih': shu_bersih,
            'alokasi_shu': alokasi_shu,
            'ringkasan_triwulan': ringkasan_triwulan,
        }

    @classmethod
    def renderDokumenLaporan(cls, data_laporan: dict, format_file: str = 'pdf') -> HttpResponse:
        """
        Merender dokumen Laporan Keuangan (Triwulanan / Tahunan RAT) ke dalam berkas
        PDF (.pdf) atau Microsoft Excel (.xlsx) (FR-RPT-03).
        """
        fmt = (format_file or 'pdf').strip().lower()
        tab = data_laporan['kompilasi']['tab_aktif']
        thn = data_laporan['neraca_shu']['tahun_buku']
        kode_periode = data_laporan.get('kode_periode', 'TAHUNAN')

        if fmt == 'xlsx':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Laporan {tab[:12]}"

            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
            total_fill = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')
            thin_border = Border(
                left=Side(style='thin', color='CBD5E1'),
                right=Side(style='thin', color='CBD5E1'),
                top=Side(style='thin', color='CBD5E1'),
                bottom=Side(style='thin', color='CBD5E1'),
            )

            ws.append([f"LAPORAN KEUANGAN & RAT ({tab}) — KOPERASI SYARIAH KKPRIS SMKN 1 KOTA SOLOK"])
            ws['A1'].font = Font(bold=True, size=12)
            ws.append([
                f"Periode: {data_laporan['label_periode']} | "
                f"Total Debit: Rp {data_laporan['kompilasi']['total_debit']:,.2f} | "
                f"Total Kredit: Rp {data_laporan['kompilasi']['total_kredit']:,.2f} | "
                f"Saldo: Rp {data_laporan['kompilasi']['saldo_akhir']:,.2f}"
            ])
            ws.append([])

            headers = ['No', 'Tanggal', 'No. Referensi', 'Kategori', 'Keterangan', 'Debit (Rp)', 'Kredit (Rp)', 'Saldo (Rp)']
            ws.append(headers)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=4, column=col_idx)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')

            baris_list = data_laporan['kompilasi']['baris_jurnal_kronologis']
            for idx, b in enumerate(baris_list, start=1):
                ws.append([
                    idx,
                    b['tanggal'].strftime('%d/%m/%Y'),
                    b['no_referensi'],
                    b['kategori'],
                    b['keterangan'],
                    float(b['debit']),
                    float(b['kredit']),
                    float(b['saldo']),
                ])
                curr_row = 4 + idx
                for col_idx in range(1, len(headers) + 1):
                    c = ws.cell(row=curr_row, column=col_idx)
                    c.border = thin_border
                    if col_idx in (6, 7, 8):
                        c.number_format = '#,##0.00'

            total_row = 4 + len(baris_list) + 1
            ws.append([
                '',
                '',
                '',
                '',
                'TOTAL AKUMULASI PERIODE',
                float(data_laporan['kompilasi']['total_debit']),
                float(data_laporan['kompilasi']['total_kredit']),
                float(data_laporan['kompilasi']['saldo_akhir']),
            ])
            for col_idx in range(1, len(headers) + 1):
                c = ws.cell(row=total_row, column=col_idx)
                c.font = Font(bold=True)
                c.fill = total_fill
                c.border = thin_border
                if col_idx in (6, 7, 8):
                    c.number_format = '#,##0.00'

            # Sheet ke-2: Ringkasan Neraca & SHU RAT
            ws_rat = wb.create_sheet(title=f"Neraca & SHU {thn}")
            ws_rat.append([f"NERACA & SISA HASIL USAHA (SHU) RAT TAHUN BUKU {thn} — SI-KKPRIS"])
            ws_rat['A1'].font = Font(bold=True, size=12)
            ws_rat.append([])
            neraca = data_laporan['neraca_shu']
            ws_rat.append(['Komponen Neraca / SHU', 'Nilai (Rp)'])
            for k_label, k_val in [
                ('Simpanan Terkunci (Pokok, Wajib, Khusus)', neraca['simpanan_terkunci']),
                ('Simpanan Sukarela (Hari Raya, Berencana)', neraca['simpanan_sukarela']),
                ('Total Modal Simpanan Anggota', neraca['total_modal_simpanan']),
                ('Piutang Pokok Pembiayaan Berjalan', neraca['piutang_pokok']),
                ('Piutang Margin Pembiayaan Berjalan', neraca['piutang_margin']),
                ('Pendapatan Margin/Ujrah Terealisasi (SHU Kotor)', neraca['pendapatan_margin_shu']),
                ('Potongan Margin Pelunasan Dipercepat (Muqashah)', neraca['total_muqashah']),
                ('Sisa Hasil Usaha (SHU) Bersih Tahun Buku', neraca['shu_bersih']),
            ]:
                ws_rat.append([k_label, float(k_val)])

            for sheet in (ws, ws_rat):
                for col in sheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    sheet.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 14), 45)

            output = BytesIO()
            wb.save(output)
            output.seek(0)
            filename = f"Laporan_Keuangan_SI-KKPRIS_{tab}_{kode_periode}_{thn}.xlsx"
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        # Default: Render PDF menggunakan xhtml2pdf
        html_string = render_to_string('laporan/laporan_keuangan_pdf.html', data_laporan)
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
        if pisa_status.err:
            return HttpResponse(html_string, content_type='text/html')
        pdf_buffer.seek(0)
        filename = f"Laporan_Keuangan_SI-KKPRIS_{tab}_{kode_periode}_{thn}.pdf"
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @classmethod
    def generatePdfKuitansi(cls, data_bukti: dict) -> HttpResponse:
        """
        Membangkitkan berkas PDF Kuitansi Digital resmi untuk transaksi Simpanan maupun Angsuran (UC-13).
        """
        html_string = render_to_string(data_bukti['template_name'], data_bukti['context'])
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
        if pisa_status.err:
            return HttpResponse(html_string, content_type='text/html')
        pdf_buffer.seek(0)
        filename = f"Kuitansi_{data_bukti['no_kuitansi']}.pdf"
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ============================================================================
# CLASS CONTROLLER: LaporanBuktiController (Sesuai Class Diagram)
# ============================================================================

class LaporanBuktiController:
    """
    Controller Cetak Bukti Transaksi/Pembayaran Kuitansi Digital & Laporan Keuangan RAT SI-KKPRIS.
    """

    @classmethod
    def cetakBuktiTransaksi(
        cls,
        no_kuitansi: str,
        tipe_transaksi: str = 'AUTO',
        format_output: str = 'pdf',
    ) -> HttpResponse:
        """
        Mencari bukti transaksi berdasarkan nomor kuitansi (Simpanan atau Angsuran)
        dan mengembalikan dokumen kuitansi resmi (PDF / HTML).
        """
        kode = (no_kuitansi or '').strip()
        tipe = (tipe_transaksi or 'AUTO').strip().upper()

        if tipe in ('AUTO', 'SIMPANAN'):
            mutasi = TransaksiSimpanan.cariBerdasarkanKuitansi(kode)
            if mutasi:
                ctx = {
                    'mutasi': mutasi,
                    'saldo_sebelum': _hitung_saldo_sebelum(mutasi),
                }
                if format_output == 'pdf':
                    return LaporanKeuangan.generatePdfKuitansi({
                        'no_kuitansi': mutasi.no_kuitansi,
                        'template_name': 'simpanan/kuitansi_simpanan_print.html',
                        'context': ctx,
                    })

        if tipe in ('AUTO', 'ANGSURAN'):
            pembayaran = PembayaranAngsuran.cariBuktiAngsuran(kode)
            if pembayaran:
                ctx = {'pembayaran': pembayaran}
                if format_output == 'pdf':
                    return LaporanKeuangan.generatePdfKuitansi({
                        'no_kuitansi': pembayaran.no_kuitansi,
                        'template_name': 'angsuran/kuitansi_angsuran_print.html',
                        'context': ctx,
                    })

        return None

    @classmethod
    def lihatLaporanKeuangan(
        cls,
        jenis_laporan: str,
        kode_periode: str,
        tahun_buku: int,
    ) -> dict:
        """
        Mengambil kompilasi laporan keuangan (Simpanan / Pembiayaan / Kas Masuk-Keluar)
        beserta perhitungan Neraca & SHU RAT.
        """
        tgl_mulai, tgl_selesai, label_periode = _rentang_tanggal_periode(kode_periode, tahun_buku)
        kompilasi = LaporanKeuangan.kompilasiArusKasDanRealisasi(
            periode_mulai=tgl_mulai,
            periode_selesai=tgl_selesai,
            tab_aktif=jenis_laporan,
        )
        neraca_shu = LaporanKeuangan.hitungNeracaDanSHU(tahun_buku=tahun_buku)
        return {
            'kode_periode': kode_periode,
            'label_periode': label_periode,
            'kompilasi': kompilasi,
            'neraca_shu': neraca_shu,
            'tanggal_cetak': date.today(),
        }

    @classmethod
    def eksporLaporan(
        cls,
        jenis_laporan: str,
        format_file: str,
        kode_periode: str,
        tahun_buku: int,
        pengguna: Pengguna = None,
        ip_address: str = '127.0.0.1',
    ) -> HttpResponse:
        """
        Mengekspor Laporan Keuangan Triwulanan / Tahunan RAT ke PDF atau Excel (.xlsx)
        serta mencatat AuditTrailLog.
        """
        data = cls.lihatLaporanKeuangan(
            jenis_laporan=jenis_laporan,
            kode_periode=kode_periode,
            tahun_buku=tahun_buku,
        )
        if pengguna:
            AuditTrailLog.catatLogAudit(
                pengguna_id=pengguna.id,
                aksi='EKSPOR_LAPORAN_KEUANGAN',
                nama_tabel='transaksi_simpanan',
                record_id=pengguna.id,
                detail=(
                    f"Ekspor Laporan Keuangan ({jenis_laporan} - {data['label_periode']}) "
                    f"ke format {format_file.upper()} oleh {pengguna.username}."
                ),
                ip_address=ip_address,
            )
        return LaporanKeuangan.renderDokumenLaporan(data, format_file=format_file)


# ============================================================================
# DJANGO VIEWS: Laporan Keuangan (WD-14), Ekspor PDF/Excel, Kuitansi PDF,
#               & Halaman Audit Trail Log Sistem
# ============================================================================

@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def laporan_keuangan_view(request):
    """
    Menampilkan Halaman Laporan Keuangan (Tab Simpanan, Pembiayaan, Kas Masuk/Keluar,
    Filter Triwulan/Tahunan, 3 Kartu Debit/Kredit/Saldo, Kartu Grafik & Neraca SHU RAT,
    serta Tabel Mutasi Buku Besar)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Laporan Keuangan.png (WD-14).
    """
    tab_aktif = (request.GET.get('tab') or 'SIMPANAN').strip().upper()
    if tab_aktif not in ('SIMPANAN', 'PEMBIAYAAN', 'KAS_MASUK_KELUAR'):
        tab_aktif = 'SIMPANAN'

    kode_periode = (request.GET.get('periode') or 'TAHUNAN').strip().upper()
    if kode_periode not in ('TAHUNAN', 'TW1', 'TW2', 'TW3', 'TW4'):
        kode_periode = 'TAHUNAN'

    tahun_sekarang = date.today().year
    raw_tahun = (request.GET.get('tahun') or str(tahun_sekarang)).strip()
    tahun_buku = int(raw_tahun) if raw_tahun.isdigit() else tahun_sekarang

    data_laporan = LaporanBuktiController.lihatLaporanKeuangan(
        jenis_laporan=tab_aktif,
        kode_periode=kode_periode,
        tahun_buku=tahun_buku,
    )
    kompilasi = data_laporan['kompilasi']
    neraca_shu = data_laporan['neraca_shu']

    paginator = Paginator(kompilasi['baris_jurnal'], 8)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    pilihan_periode = [
        ('TAHUNAN', 'Tahunan (RAT — Januari s.d. Desember)'),
        ('TW1', 'Triwulan I (Januari – Maret)'),
        ('TW2', 'Triwulan II (April – Juni)'),
        ('TW3', 'Triwulan III (Juli – September)'),
        ('TW4', 'Triwulan IV (Oktober – Desember)'),
    ]
    pilihan_tahun = [tahun_sekarang, tahun_sekarang - 1, tahun_sekarang - 2]

    context = {
        'active_menu': 'laporan_keuangan',
        'tab_aktif': tab_aktif,
        'kode_periode': kode_periode,
        'tahun_buku': tahun_buku,
        'label_periode': data_laporan['label_periode'],
        'pilihan_periode': pilihan_periode,
        'pilihan_tahun': pilihan_tahun,
        'total_debit': kompilasi['total_debit'],
        'total_kredit': kompilasi['total_kredit'],
        'saldo_akhir': kompilasi['saldo_akhir'],
        'neraca_shu': neraca_shu,
        'page_obj': page_obj,
    }
    return render(request, 'laporan/laporan_keuangan.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def ekspor_laporan_keuangan_view(request):
    """
    Memproses tombol 'Ekspor PDF/Excel' pada halaman Laporan Keuangan (WD-14).
    """
    tab_aktif = (request.GET.get('tab') or 'SIMPANAN').strip().upper()
    kode_periode = (request.GET.get('periode') or 'TAHUNAN').strip().upper()
    raw_tahun = (request.GET.get('tahun') or str(date.today().year)).strip()
    tahun_buku = int(raw_tahun) if raw_tahun.isdigit() else date.today().year
    format_file = (request.GET.get('format') or 'pdf').strip().lower()

    return LaporanBuktiController.eksporLaporan(
        jenis_laporan=tab_aktif,
        format_file=format_file,
        kode_periode=kode_periode,
        tahun_buku=tahun_buku,
        pengguna=request.pengguna,
        ip_address=_ambil_ip_klien(request),
    )


@login_wajib
def unduh_kuitansi_pdf_view(request, no_kuitansi: str):
    """
    Mengunduh berkas PDF Kuitansi Digital resmi untuk transaksi Simpanan maupun Angsuran (UC-13).
    """
    kode = (no_kuitansi or '').strip()

    # Proteksi RBAC apabila diakses oleh Anggota
    if request.pengguna.peran == PeranPenggunaChoices.ANGGOTA:
        anggota_login = getattr(request.pengguna, 'profil_anggota', None)
        mutasi = TransaksiSimpanan.cariBerdasarkanKuitansi(kode)
        pembayaran = PembayaranAngsuran.cariBuktiAngsuran(kode)
        milik_sendiri = (
            (mutasi and anggota_login and mutasi.anggota_id == anggota_login.id)
            or (pembayaran and anggota_login and pembayaran.jadwal_angsuran.pembiayaan.anggota_id == anggota_login.id)
        )
        if not milik_sendiri:
            messages.error(request, 'Akses ditolak: Anda hanya dapat mengunduh kuitansi milik Anda sendiri.')
            return redirect('beranda_anggota')

    response = LaporanBuktiController.cetakBuktiTransaksi(
        no_kuitansi=kode,
        tipe_transaksi='AUTO',
        format_output='pdf',
    )
    if not response:
        messages.error(request, f'Kuitansi dengan nomor {kode} tidak ditemukan.')
        return redirect('root_redirect')
    return response


@peran_wajib(PeranPenggunaChoices.KETUA, PeranPenggunaChoices.BENDAHARA)
def audit_trail_log_view(request):
    """
    Menampilkan Halaman Jejak Audit Keamanan Sistem (Audit Trail Log — Append-Only, NFR-SEC-03)
    untuk pengawasan Ketua & Bendahara Koperasi.
    """
    q = (request.GET.get('q') or '').strip()
    filter_peran = (request.GET.get('peran') or '').strip().upper()

    qs_logs = AuditTrailLog.objects.select_related('pengguna').all().order_by('-created_at', '-id')
    if q:
        qs_logs = qs_logs.filter(
            Q(aksi__icontains=q)
            | Q(nama_tabel__icontains=q)
            | Q(detail_perubahan__icontains=q)
            | Q(pengguna__username__icontains=q)
            | Q(pengguna__nama_lengkap__icontains=q)
        )
    if filter_peran in PeranPenggunaChoices.values:
        qs_logs = qs_logs.filter(pengguna__peran=filter_peran)

    paginator = Paginator(qs_logs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'active_menu': 'laporan_keuangan',
        'q': q,
        'filter_peran': filter_peran,
        'peran_choices': PeranPenggunaChoices.choices,
        'total_logs': AuditTrailLog.objects.count(),
        'page_obj': page_obj,
    }
    return render(request, 'laporan/audit_trail_log.html', context)
