"""
RekapNotifikasiController & Views Kelola Angsuran, Cetak Bukti Pembayaran,
Rekap Potong Gaji (Tanggal 24), serta Notifikasi Tagihan (Tanggal 10)
(Tahap 6 — UC-11, UC-12, UC-13, UC-14 | FR-ANG-01 s.d. FR-ANG-03, FR-RKP-01 s.d. FR-RKP-03, FR-NTF-01).

Selaras dengan:
- 03_Class_Diagram_SI-KKPRIS.mmd (RekapNotifikasiController & PembiayaanController)
- Sequence Diagram SQ-10 (Kelola Angsuran), SQ-11 (Generate Rekap Potong Gaji), & SQ-13 (Kirim Notifikasi)
- Wireframe Final Tahap 6:
  17. Kelola Angsuran.png (WD-10) & Cetak Bukti Pembayaran.png (WD-11)
  18. Rekap Potong Gaji.png (WD-12)
  19. Notifikasi Tagihan.png (WD-13)
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from xhtml2pdf import pisa
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from koperasi.controllers.auth_controller import (
    _ambil_ip_klien,
    login_wajib,
    peran_wajib,
)
from koperasi.controllers.pembiayaan_controller import PembiayaanController
from koperasi.utils import bersihkan_rupiah
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    DetailRekapPotongGaji,
    JadwalAngsuran,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    KanalNotifikasiChoices,
    MetodeBayarChoices,
    NamaAkadChoices,
    NotifikasiTagihan,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PeranPenggunaChoices,
    RekapPotongGaji,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusKirimNotifikasiChoices,
    StatusPembiayaanChoices,
    StatusPotonganGajiChoices,
    StatusRekapGajiChoices,
    TransaksiSimpanan,
)


def _format_label_periode(periode_bulan: str) -> str:
    """Mengubah string YYYY-MM menjadi label Bahasa Indonesia (contoh: November 2026)."""
    nama_bulan = {
        1: 'Januari',
        2: 'Februari',
        3: 'Maret',
        4: 'April',
        5: 'Mei',
        6: 'Juni',
        7: 'Juli',
        8: 'Agustus',
        9: 'September',
        10: 'Oktober',
        11: 'November',
        12: 'Desember',
    }
    try:
        tahun, bulan = [int(x) for x in periode_bulan.split('-')]
        return f"{nama_bulan.get(bulan, str(bulan))} {tahun}"
    except Exception:
        return periode_bulan


# ============================================================================
# CLASS CONTROLLER: RekapNotifikasiController (Sesuai Class Diagram)
# ============================================================================

class RekapNotifikasiController:
    """
    Controller Otomatisasi Rekap Potong Gaji Tanggal 24, Ekspor Dokumen Bendahara Gaji Sekolah,
    dan Pengiriman Notifikasi Pengingat Tagihan Tanggal 10 SI-KKPRIS.
    """

    @classmethod
    def generateRekapPotongGaji(
        cls,
        periode_bulan: str,
        bendahara: Pengguna,
        ip_address: str = '127.0.0.1',
    ) -> RekapPotongGaji:
        """
        One-Click Generator Rekap Potong Gaji Tanggal 24 (SQ-11 — UC-12, FR-RKP-01, BR-06).
        Mengompilasi tagihan Simpanan Wajib (Rp 150.000), Angsuran Pembiayaan jatuh tempo,
        serta potongan sukarela / belanja toko untuk seluruh anggota aktif pada periode YYYY-MM.
        """
        periode = (periode_bulan or '').strip()
        if len(periode) != 7 or '-' not in periode:
            periode = date.today().strftime('%Y-%m')

        try:
            tahun, bulan = [int(x) for x in periode.split('-')]
            tgl_cutoff = date(tahun, bulan, 24)
        except ValueError:
            raise ValidationError('Format periode rekap potong gaji harus YYYY-MM (contoh: 2026-11).')

        js_wajib = JenisSimpanan.ambilJenisSimpananWajib()
        default_wajib = js_wajib.nominal_default if js_wajib else Decimal('150000.00')

        with transaction.atomic():
            rekap = RekapPotongGaji.objects.filter(periode_bulan=periode).first()
            if rekap and rekap.status_rekap == StatusRekapGajiChoices.LUNAS_KOLEKTIF:
                raise ValidationError(
                    f"Rekap potong gaji periode {_format_label_periode(periode)} ({rekap.kode_rekap}) "
                    f"sudah berstatus Lunas Kolektif dan tidak dapat di-generate ulang."
                )

            # Simpan nilai belanja toko / sukarela yang mungkin sudah diinput sebelumnya per anggota
            peta_sukarela_lama = {}
            if rekap:
                for d in rekap.detail_list.all():
                    peta_sukarela_lama[d.anggota_id] = d.nominal_simpanan_sukarela
                rekap.detail_list.all().delete()
                rekap.tanggal_cut_off = tgl_cutoff
                rekap.bendahara = bendahara
                rekap.status_rekap = StatusRekapGajiChoices.DIKUNCI
            else:
                rekap = RekapPotongGaji.buatHeaderRekap(
                    periode_bulan=periode,
                    bendahara_id=bendahara.id,
                )

            anggota_aktif_list = Anggota.objects.filter(
                status=StatusAnggotaChoices.AKTIF
            ).order_by('no_anggota')

            rincian_items = []
            total_wajib_akumulasi = Decimal('0.00')
            total_angsuran_akumulasi = Decimal('0.00')
            total_tagihan_akumulasi = Decimal('0.00')

            for ag in anggota_aktif_list:
                # Cari jadwal angsuran belum lunas pada bulan & tahun periode,
                # atau angsuran belum lunas paling awal milik anggota jika kontraknya aktif
                jadwal = (
                    JadwalAngsuran.objects.filter(
                        pembiayaan__anggota=ag,
                        pembiayaan__status=StatusPembiayaanChoices.AKTIF,
                        status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
                        jatuh_tempo__year=tahun,
                        jatuh_tempo__month=bulan,
                    )
                    .order_by('angsuran_ke')
                    .first()
                )
                if not jadwal:
                    jadwal = (
                        JadwalAngsuran.objects.filter(
                            pembiayaan__anggota=ag,
                            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
                            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
                        )
                        .order_by('angsuran_ke')
                        .first()
                    )

                nom_wajib = default_wajib.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                nom_angsuran = (
                    jadwal.jumlah_angsuran.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    if jadwal
                    else Decimal('0.00')
                )
                nom_sukarela = peta_sukarela_lama.get(ag.id, Decimal('0.00')).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                subtotal = (nom_wajib + nom_angsuran + nom_sukarela).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )

                rincian_items.append({
                    'anggota_id': ag.id,
                    'jadwal_angsuran_id': jadwal.id if jadwal else None,
                    'nominal_simpanan_wajib': nom_wajib,
                    'nominal_simpanan_sukarela': nom_sukarela,
                    'nominal_angsuran': nom_angsuran,
                    'subtotal_potongan': subtotal,
                    'status_potongan': StatusPotonganGajiChoices.TERTAGIH,
                })

                total_wajib_akumulasi += nom_wajib
                total_angsuran_akumulasi += nom_angsuran
                total_tagihan_akumulasi += subtotal

            if rincian_items:
                DetailRekapPotongGaji.simpanRincianRekapAnggota(rekap.id, rincian_items)

            rekap.total_simpanan_wajib = total_wajib_akumulasi
            rekap.total_angsuran = total_angsuran_akumulasi
            rekap.total_tagihan = total_tagihan_akumulasi
            rekap.save()

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='GENERATE_REKAP_POTONG_GAJI',
                nama_tabel='rekap_potong_gaji',
                record_id=rekap.id,
                detail=(
                    f"Generate Rekap Potong Gaji {rekap.kode_rekap} (Periode {periode}, Cut-off {tgl_cutoff:%d/%m/%Y}): "
                    f"{len(rincian_items)} anggota, Total Tagihan Rp{rekap.total_tagihan:,.2f}."
                ),
                ip_address=ip_address,
            )
            return rekap

    @classmethod
    def perbaruiPotonganTambahanAnggota(
        cls,
        detail_id: int,
        nominal_belanja_toko,
        bendahara: Pengguna,
        ip_address: str = '127.0.0.1',
    ) -> DetailRekapPotongGaji:
        """
        Memperbarui komponen potongan tambahan (Belanja Toko / Simpanan Sukarela) pada satu baris
        DetailRekapPotongGaji dan menyegarkan total tagihan pada header RekapPotongGaji.
        """
        detail = get_object_or_404(
            DetailRekapPotongGaji.objects.select_related('rekap_potong_gaji', 'anggota'),
            pk=detail_id,
        )
        rekap = detail.rekap_potong_gaji
        if rekap.status_rekap == StatusRekapGajiChoices.LUNAS_KOLEKTIF:
            raise ValidationError('Rekap sudah berstatus Lunas Kolektif dan tidak dapat diubah.')

        nom_toko = bersihkan_rupiah(nominal_belanja_toko, default='0.00')
        if nom_toko < Decimal('0.00'):
            raise ValidationError('Nominal potongan belanja toko / sukarela tidak boleh negatif.')

        with transaction.atomic():
            detail.nominal_simpanan_sukarela = nom_toko
            detail.subtotal_potongan = (
                detail.nominal_simpanan_wajib + detail.nominal_angsuran + nom_toko
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            detail.save()

            agg = rekap.detail_list.aggregate(
                sum_wajib=Sum('nominal_simpanan_wajib'),
                sum_angsuran=Sum('nominal_angsuran'),
                sum_total=Sum('subtotal_potongan'),
            )
            rekap.total_simpanan_wajib = agg['sum_wajib'] or Decimal('0.00')
            rekap.total_angsuran = agg['sum_angsuran'] or Decimal('0.00')
            rekap.total_tagihan = agg['sum_total'] or Decimal('0.00')
            rekap.save()

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='UPDATE_RINCIAN_REKAP_GAJI',
                nama_tabel='detail_rekap_potong_gaji',
                record_id=detail.id,
                detail=(
                    f"Pembaruan potongan Belanja Toko / Sukarela {detail.anggota.no_anggota} "
                    f"pada {rekap.kode_rekap} menjadi Rp{nom_toko:,.2f} (Subtotal: Rp{detail.subtotal_potongan:,.2f})."
                ),
                ip_address=ip_address,
            )
            return detail

    @classmethod
    def konfirmasiPelunasanKolektif(
        cls,
        rekap_id: int,
        bendahara: Pengguna,
        no_ref_bank: str,
        ip_address: str = '127.0.0.1',
    ) -> RekapPotongGaji:
        """
        Memproses pelunasan kolektif (batch) rekap potong gaji tanggal 24 setelah dana diterima
        dari Bendahara Gaji Sekolah:
        - Menandai seluruh DetailRekapPotongGaji menjadi TERPOTONG_LUNAS
        - Mencatat setoran Simpanan Wajib (SWJ) otomatis untuk setiap anggota pada rekap
        - Mencatat PembayaranAngsuran & melunasi JadwalAngsuran terkait secara batch
        """
        rekap = get_object_or_404(
            RekapPotongGaji.objects.prefetch_related(
                'detail_list__anggota',
                'detail_list__jadwal_angsuran',
                'detail_list__jadwal_angsuran__pembiayaan',
            ),
            pk=rekap_id,
        )
        if rekap.status_rekap == StatusRekapGajiChoices.LUNAS_KOLEKTIF:
            raise ValidationError(f'Rekap {rekap.kode_rekap} sudah berstatus Lunas Kolektif.')

        no_ref = (no_ref_bank or '').strip() or f"TRF-GAJI-{rekap.kode_rekap}"
        js_wajib = JenisSimpanan.ambilJenisSimpananWajib()

        with transaction.atomic():
            for idx, det in enumerate(rekap.detail_list.all(), start=1):
                # 1. Catat Setoran Simpanan Wajib (SWJ) jika > 0
                if js_wajib and det.nominal_simpanan_wajib > Decimal('0.00'):
                    no_kui_swj = f"KUI-SWJ-{rekap.kode_rekap}-{det.anggota.id}"
                    if not TransaksiSimpanan.objects.filter(no_kuitansi=no_kui_swj).exists():
                        TransaksiSimpanan.simpanMutasiSimpanan({
                            'anggota_id': det.anggota_id,
                            'jenis_simpanan_id': js_wajib.id,
                            'bendahara_id': bendahara.id,
                            'no_kuitansi': no_kui_swj,
                            'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                            'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
                            'nominal': det.nominal_simpanan_wajib,
                            'keterangan': f"Potong Gaji Simpanan Wajib Periode {rekap.periode_bulan} ({rekap.kode_rekap})",
                        })

                # 2. Catat Pembayaran Angsuran jika ada jadwal_angsuran yang belum lunas
                if (
                    det.jadwal_angsuran
                    and det.jadwal_angsuran.status_bayar == StatusBayarAngsuranChoices.BELUM_LUNAS
                    and det.nominal_angsuran > Decimal('0.00')
                ):
                    no_kui_ang = f"KUI-ANG-{rekap.kode_rekap}-{det.jadwal_angsuran_id}"
                    if not PembayaranAngsuran.objects.filter(no_kuitansi=no_kui_ang).exists():
                        PembayaranAngsuran.simpanPembayaranAngsuran(
                            jadwal_id=det.jadwal_angsuran_id,
                            data_bayar={
                                'bendahara_id': bendahara.id,
                                'rekap_potong_gaji_id': rekap.id,
                                'no_kuitansi': no_kui_ang,
                                'nominal_bayar': det.nominal_angsuran,
                                'potongan_margin': Decimal('0.00'),
                                'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
                                'nomor_referensi': no_ref,
                            },
                        )
                        masih_belum_lunas = JadwalAngsuran.objects.filter(
                            pembiayaan_id=det.jadwal_angsuran.pembiayaan_id,
                            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
                        ).exists()
                        if not masih_belum_lunas:
                            Pembiayaan.perbaruiStatusPembiayaan(
                                det.jadwal_angsuran.pembiayaan_id,
                                StatusPembiayaanChoices.LUNAS,
                            )

            PembiayaanController.konfirmasiPelunasanBatch(
                rekap_id=rekap.id,
                bendahara=bendahara,
                no_ref_bank=no_ref,
                ip_address=ip_address,
            )
            rekap.refresh_from_db()
            return rekap

    @classmethod
    def eksporFileRekapGaji(cls, rekap_id: int, format_file: str = 'xlsx') -> HttpResponse:
        """
        Mengekspor dokumen Rekapitulasi Potong Gaji Tanggal 24 ke format Microsoft Excel (.xlsx)
        atau PDF resmi siap cetak untuk diserahkan kepada Bendahara Gaji SMKN 1 Kota Solok
        (SQ-11 — UC-12, FR-RKP-02).
        """
        rekap = get_object_or_404(
            RekapPotongGaji.objects.select_related('bendahara').prefetch_related(
                'detail_list__anggota',
                'detail_list__jadwal_angsuran',
                'detail_list__jadwal_angsuran__pembiayaan',
            ),
            pk=rekap_id,
        )
        rincian = list(rekap.detail_list.all().order_by('anggota__no_anggota'))
        total_toko = sum(
            (d.nominal_simpanan_sukarela for d in rincian),
            Decimal('0.00'),
        )

        fmt = (format_file or 'xlsx').strip().lower()
        if fmt == 'pdf':
            html_string = render_to_string(
                'angsuran/rekap_potong_gaji_pdf.html',
                {
                    'rekap': rekap,
                    'label_periode': _format_label_periode(rekap.periode_bulan),
                    'rincian': rincian,
                    'total_toko': total_toko,
                    'tanggal_cetak': date.today(),
                },
            )
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
            if pisa_status.err:
                return HttpResponse(html_string, content_type='text/html')
            pdf_buffer.seek(0)
            filename = f"Rekap_Potong_Gaji_{rekap.kode_rekap}.pdf"
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        # Default: Ekspor Microsoft Excel (.xlsx)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Rekap {rekap.periode_bulan}"

        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
        total_fill = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1'),
        )

        ws.append(['DAFTAR REKAPITULASI POTONG GAJI ANGGOTA (CUT-OFF TANGGAL 24) — SI-KKPRIS SMKN 1 KOTA SOLOK'])
        ws['A1'].font = Font(bold=True, size=12)
        ws.append([
            f"Kode Rekap: {rekap.kode_rekap} | Periode: {_format_label_periode(rekap.periode_bulan)} | "
            f"Tanggal Cut-off: {rekap.tanggal_cut_off:%d/%m/%Y} | Status: {rekap.get_status_rekap_display()}"
        ])
        ws.append([])

        headers = [
            'No',
            'No. Anggota',
            'Nama Anggota',
            'Simpanan Wajib (Rp)',
            'Angsuran Pembiayaan (Rp)',
            'Belanja Toko / Sukarela (Rp)',
            'Total Potongan (Rp)',
            'Status Potongan',
        ]
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=4, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for idx, d in enumerate(rincian, start=1):
            ws.append([
                idx,
                d.anggota.no_anggota,
                d.anggota.nama,
                float(d.nominal_simpanan_wajib),
                float(d.nominal_angsuran),
                float(d.nominal_simpanan_sukarela),
                float(d.subtotal_potongan),
                d.get_status_potongan_display(),
            ])
            curr_row = 4 + idx
            for col_idx in range(1, len(headers) + 1):
                c = ws.cell(row=curr_row, column=col_idx)
                c.border = thin_border
                if col_idx in (4, 5, 6, 7):
                    c.number_format = '#,##0.00'

        # Baris Total di bagian bawah tabel (Sesuai Wireframe Rekap Potong Gaji.png)
        total_row_idx = 4 + len(rincian) + 1
        ws.append([
            '',
            '',
            'TOTAL KESELURUHAN',
            float(rekap.total_simpanan_wajib),
            float(rekap.total_angsuran),
            float(total_toko),
            float(rekap.total_tagihan),
            rekap.get_status_rekap_display(),
        ])
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=total_row_idx, column=col_idx)
            c.font = Font(bold=True)
            c.fill = total_fill
            c.border = thin_border
            if col_idx in (4, 5, 6, 7):
                c.number_format = '#,##0.00'

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 14), 38)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"Rekap_Potong_Gaji_{rekap.kode_rekap}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @classmethod
    def kirimNotifikasiTagihan(
        cls,
        bendahara: Pengguna,
        jadwal_ids: list,
        kanal_list: list = None,
        template_pesan: str = '',
        jadwal_kirim_label: str = 'Setiap tanggal 10',
        ip_address: str = '127.0.0.1',
    ) -> list:
        """
        Mengirim dan mencatat log pengingat tagihan angsuran jatuh tempo setiap tanggal 10
        melalui kanal WhatsApp dan/atau Email (SQ-13 — UC-14, FR-NTF-01).
        """
        kanal_dipilih = [k.upper() for k in (kanal_list or ['WHATSAPP']) if k]
        if not kanal_dipilih:
            kanal_dipilih = [KanalNotifikasiChoices.WHATSAPP]

        qs_jadwal = JadwalAngsuran.objects.select_related(
            'pembiayaan', 'pembiayaan__anggota', 'pembiayaan__jenis_akad'
        ).filter(status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS)

        if jadwal_ids:
            valid_ids = [int(x) for x in jadwal_ids if str(x).isdigit()]
            qs_jadwal = qs_jadwal.filter(id__in=valid_ids)
        else:
            qs_jadwal = qs_jadwal.filter(pembiayaan__status=StatusPembiayaanChoices.AKTIF)

        daftar_jadwal = list(qs_jadwal)
        if not daftar_jadwal:
            raise ValidationError('Pilih minimal satu penerima tagihan angsuran untuk dikirimkan notifikasi.')

        log_terkirim = []
        with transaction.atomic():
            for jdw in daftar_jadwal:
                ag = jdw.pembiayaan.anggota
                pesan_final = (template_pesan or '').strip()
                if not pesan_final:
                    pesan_final = (
                        f"Assalamu'alaikum Bapak/Ibu {ag.nama} ({ag.no_anggota}), "
                        f"pengingat tagihan Koperasi Syariah KKPRIS SMKN 1 Kota Solok ({jadwal_kirim_label}): "
                        f"Angsuran ke-{jdw.angsuran_ke} akad {jdw.pembiayaan.jenis_akad.get_nama_display()} "
                        f"({jdw.pembiayaan.no_pembiayaan}) sebesar Rp {jdw.jumlah_angsuran:,.0f} "
                        f"(Jatuh Tempo: {jdw.jatuh_tempo:%d/%m/%Y}) beserta Simpanan Wajib Rp 150.000. Terima kasih."
                    )
                else:
                    pesan_final = (
                        pesan_final.replace('{nama}', ag.nama)
                        .replace('{no_anggota}', ag.no_anggota)
                        .replace('{no_pembiayaan}', jdw.pembiayaan.no_pembiayaan)
                        .replace('{angsuran_ke}', str(jdw.angsuran_ke))
                        .replace('{nominal}', f"Rp {jdw.jumlah_angsuran:,.0f}")
                        .replace('{jatuh_tempo}', jdw.jatuh_tempo.strftime('%d/%m/%Y'))
                    )

                for kanal in kanal_dipilih:
                    if kanal not in KanalNotifikasiChoices.values:
                        continue
                    tujuan = (
                        ag.no_hp
                        if kanal == KanalNotifikasiChoices.WHATSAPP
                        else f"{ag.no_anggota.lower()}@smkn1solok.sch.id"
                    )
                    notif = NotifikasiTagihan.simpanLogNotifikasi({
                        'anggota_id': ag.id,
                        'jadwal_angsuran_id': jdw.id,
                        'bendahara_id': bendahara.id,
                        'kanal_kirim': kanal,
                        'tujuan_kirim': tujuan,
                        'isi_pesan': pesan_final[:500],
                        'status_kirim': StatusKirimNotifikasiChoices.TERKIRIM,
                    })
                    log_terkirim.append(notif)

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='KIRIM_NOTIFIKASI_TAGIHAN',
                nama_tabel='notifikasi_tagihan',
                record_id=log_terkirim[0].id if log_terkirim else bendahara.id,
                detail=(
                    f"Pengiriman {len(log_terkirim)} notifikasi pengingat tagihan ({', '.join(kanal_dipilih)}) "
                    f"dengan jadwal '{jadwal_kirim_label}' kepada {len(daftar_jadwal)} anggota."
                ),
                ip_address=ip_address,
            )
        return log_terkirim


# ============================================================================
# DJANGO VIEWS: Kelola Angsuran, Cetak Bukti Pembayaran, Rekap Potong Gaji,
#               & Notifikasi Tagihan
# ============================================================================

@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def kelola_angsuran_view(request):
    """
    Menampilkan Halaman Kelola Angsuran & Modal Cetak Bukti Pembayaran
    Sesuai Wireframe:
    - 01_Wireframe_Final_PNG/Kelola Angsuran.png (WD-10)
    - 01_Wireframe_Final_PNG/Cetak Bukti Pembayaran.png (WD-11)
    """
    filter_anggota_id = (request.GET.get('anggota_id') or '').strip()
    filter_akad = (request.GET.get('akad') or '').strip().upper()
    filter_pembiayaan_id = (request.GET.get('pembiayaan_id') or '').strip()

    qs_pembiayaan = (
        Pembiayaan.objects.select_related('anggota', 'jenis_akad')
        .filter(status__in=[StatusPembiayaanChoices.AKTIF, StatusPembiayaanChoices.LUNAS])
        .order_by('-id')
    )
    if filter_anggota_id and filter_anggota_id.isdigit():
        qs_pembiayaan = qs_pembiayaan.filter(anggota_id=int(filter_anggota_id))
    if filter_akad in NamaAkadChoices.values:
        qs_pembiayaan = qs_pembiayaan.filter(jenis_akad__nama=filter_akad)

    pembiayaan_terpilih = None
    if filter_pembiayaan_id and filter_pembiayaan_id.isdigit():
        pembiayaan_terpilih = qs_pembiayaan.filter(pk=int(filter_pembiayaan_id)).first()
    if not pembiayaan_terpilih and filter_anggota_id and filter_anggota_id.isdigit():
        pembiayaan_terpilih = qs_pembiayaan.first()

    qs_jadwal = JadwalAngsuran.objects.select_related(
        'pembiayaan', 'pembiayaan__anggota', 'pembiayaan__jenis_akad'
    ).prefetch_related('pembayaran_list').filter(
        pembiayaan__in=qs_pembiayaan
    ).order_by('status_bayar', 'jatuh_tempo', 'angsuran_ke')

    if pembiayaan_terpilih:
        qs_jadwal = qs_jadwal.filter(pembiayaan=pembiayaan_terpilih).order_by('angsuran_ke')

    # Hitung 3 Kartu Statistik sesuai Kelola Angsuran.png: Total Pembiayaan, Terbayar, Sisa
    if pembiayaan_terpilih:
        total_pembiayaan = pembiayaan_terpilih.total_kewajiban
        terbayar_nominal = (
            JadwalAngsuran.objects.filter(
                pembiayaan=pembiayaan_terpilih,
                status_bayar=StatusBayarAngsuranChoices.LUNAS,
            ).aggregate(total=Sum('jumlah_angsuran'))['total']
            or Decimal('0.00')
        )
        sisa_nominal = (
            JadwalAngsuran.objects.filter(
                pembiayaan=pembiayaan_terpilih,
                status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
            ).aggregate(total=Sum('jumlah_angsuran'))['total']
            or Decimal('0.00')
        )
        lunas_count = JadwalAngsuran.objects.filter(
            pembiayaan=pembiayaan_terpilih,
            status_bayar=StatusBayarAngsuranChoices.LUNAS,
        ).count()
        belum_count = JadwalAngsuran.objects.filter(
            pembiayaan=pembiayaan_terpilih,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
        ).count()
    else:
        total_pembiayaan = (
            qs_pembiayaan.aggregate(total=Sum('total_kewajiban'))['total'] or Decimal('0.00')
        )
        terbayar_nominal = (
            qs_jadwal.filter(status_bayar=StatusBayarAngsuranChoices.LUNAS).aggregate(
                total=Sum('jumlah_angsuran')
            )['total']
            or Decimal('0.00')
        )
        sisa_nominal = (
            qs_jadwal.filter(status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS).aggregate(
                total=Sum('jumlah_angsuran')
            )['total']
            or Decimal('0.00')
        )
        lunas_count = qs_jadwal.filter(status_bayar=StatusBayarAngsuranChoices.LUNAS).count()
        belum_count = qs_jadwal.filter(status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS).count()

    paginator = Paginator(qs_jadwal, 8)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    daftar_baris_jadwal = []
    for jdw in page_obj.object_list:
        bukti_terakhir = jdw.pembayaran_list.first()
        daftar_baris_jadwal.append({
            'obj': jdw,
            'bukti': bukti_terakhir,
        })

    # Cek parameter ?cetak=<no_kuitansi> untuk menampilkan Modal Cetak Bukti Pembayaran (WD-11)
    kode_cetak = (request.GET.get('cetak') or '').strip()
    pembayaran_cetak = None
    if kode_cetak:
        pembayaran_cetak = PembayaranAngsuran.cariBuktiAngsuran(kode_cetak)

    daftar_anggota_pembiayaan = Anggota.objects.filter(
        pembiayaan_list__status__in=[StatusPembiayaanChoices.AKTIF, StatusPembiayaanChoices.LUNAS]
    ).distinct().order_by('no_anggota')

    context = {
        'active_menu': 'kelola_angsuran',
        'filter_anggota_id': filter_anggota_id,
        'filter_akad': filter_akad,
        'pembiayaan_terpilih': pembiayaan_terpilih,
        'daftar_anggota_pembiayaan': daftar_anggota_pembiayaan,
        'nama_akad_choices': NamaAkadChoices.choices,
        'metode_bayar_choices': MetodeBayarChoices.choices,
        'total_pembiayaan': total_pembiayaan,
        'terbayar_nominal': terbayar_nominal,
        'sisa_nominal': sisa_nominal,
        'lunas_count': lunas_count,
        'belum_count': belum_count,
        'page_obj': page_obj,
        'daftar_baris_jadwal': daftar_baris_jadwal,
        'pembayaran_cetak': pembayaran_cetak,
    }
    return render(request, 'angsuran/kelola_angsuran.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def catat_pembayaran_angsuran_view(request, jadwal_id: int):
    """
    Memproses pencatatan pembayaran cicilan angsuran mandiri / potong gaji oleh Bendahara (UC-11).
    Jika berhasil, mengarahkan ke /angsuran/?cetak=<no_kuitansi> agar modal
    Cetak Bukti Pembayaran (WD-11) langsung tampil.
    """
    if request.method == 'POST':
        try:
            pembayaran = PembiayaanController.catatPembayaranAngsuran(
                jadwal_id=jadwal_id,
                bendahara=request.pengguna,
                data_bayar={
                    'nominal_bayar': request.POST.get('nominal_bayar'),
                    'potongan_margin': request.POST.get('potongan_margin', '0.00'),
                    'metode_bayar': request.POST.get('metode_bayar', MetodeBayarChoices.TUNAI),
                    'nomor_referensi': request.POST.get('nomor_referensi'),
                },
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Pembayaran Angsuran ke-{pembayaran.jadwal_angsuran.angsuran_ke} "
                f"({pembayaran.jadwal_angsuran.pembiayaan.no_pembiayaan} — {pembayaran.jadwal_angsuran.pembiayaan.anggota.nama}) "
                f"sebesar Rp {pembayaran.nominal_bayar:,.0f} berhasil dicatat dengan No. Kuitansi {pembayaran.no_kuitansi}.",
            )
            anggota_id = pembayaran.jadwal_angsuran.pembiayaan.anggota_id
            return redirect(f"/angsuran/?anggota_id={anggota_id}&cetak={pembayaran.no_kuitansi}")
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal mencatat pembayaran angsuran: {pesan_err}")
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan: {exc}")

    return redirect('kelola_angsuran')


@login_wajib
def cetak_kuitansi_angsuran_view(request, no_kuitansi: str):
    """
    Menampilkan lembar Kuitansi Bukti Pembayaran Angsuran resmi siap cetak / simpan PDF (UC-13).
    """
    pembayaran = PembayaranAngsuran.cariBuktiAngsuran(no_kuitansi)
    if not pembayaran:
        messages.error(request, f'Bukti pembayaran angsuran {no_kuitansi} tidak ditemukan.')
        return redirect('kelola_angsuran')

    if request.pengguna.peran == PeranPenggunaChoices.ANGGOTA:
        anggota_login = getattr(request.pengguna, 'profil_anggota', None)
        if not anggota_login or pembayaran.jadwal_angsuran.pembiayaan.anggota_id != anggota_login.id:
            messages.error(request, 'Akses ditolak: Anda hanya dapat mencetak kuitansi milik Anda sendiri.')
            return redirect('beranda_anggota')

    return render(
        request,
        'angsuran/kuitansi_angsuran_print.html',
        {'pembayaran': pembayaran},
    )


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def rekap_potong_gaji_view(request):
    """
    Menampilkan Halaman Rekap Potong Gaji Tanggal 24
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Rekap Potong Gaji.png (WD-12).
    """
    periode_default = date.today().strftime('%Y-%m')
    periode_terpilih = (request.GET.get('periode') or '').strip()

    semua_rekap = list(RekapPotongGaji.objects.all().order_by('-periode_bulan'))
    if not periode_terpilih:
        periode_terpilih = semua_rekap[0].periode_bulan if semua_rekap else periode_default

    rekap_aktif = (
        RekapPotongGaji.objects.select_related('bendahara')
        .prefetch_related('detail_list__anggota', 'detail_list__jadwal_angsuran', 'detail_list__jadwal_angsuran__pembiayaan')
        .filter(periode_bulan=periode_terpilih)
        .first()
    )

    # Susun daftar pilihan periode (periode yang sudah ada di DB + 3 bulan sekitar bulan ini)
    kumpulan_periode = {periode_default, '2026-10', '2026-11', '2026-12'}
    for r in semua_rekap:
        kumpulan_periode.add(r.periode_bulan)
    pilihan_periode = [
        {'kode': p, 'label': f"{_format_label_periode(p)} ({p})"}
        for p in sorted(kumpulan_periode, reverse=True)
    ]

    rincian_qs = (
        rekap_aktif.detail_list.select_related('anggota', 'jadwal_angsuran', 'jadwal_angsuran__pembiayaan')
        .all()
        .order_by('anggota__no_anggota')
        if rekap_aktif
        else DetailRekapPotongGaji.objects.none()
    )

    total_belanja_toko = (
        rincian_qs.aggregate(total=Sum('nominal_simpanan_sukarela'))['total']
        or Decimal('0.00')
    )

    paginator = Paginator(rincian_qs, 8)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'active_menu': 'rekap_potong_gaji',
        'periode_terpilih': periode_terpilih,
        'label_periode_terpilih': _format_label_periode(periode_terpilih),
        'pilihan_periode': pilihan_periode,
        'rekap_aktif': rekap_aktif,
        'total_belanja_toko': total_belanja_toko,
        'page_obj': page_obj,
    }
    return render(request, 'angsuran/rekap_potong_gaji.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def generate_rekap_potong_gaji_view(request):
    """
    Memproses tombol 'Generate Rekap' (One-Click Generator Tanggal 24 — UC-12).
    """
    if request.method == 'POST':
        periode = (request.POST.get('periode') or date.today().strftime('%Y-%m')).strip()
        try:
            rekap = RekapNotifikasiController.generateRekapPotongGaji(
                periode_bulan=periode,
                bendahara=request.pengguna,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Rekap Potong Gaji {rekap.kode_rekap} untuk periode {_format_label_periode(rekap.periode_bulan)} "
                f"(Cut-off Tanggal 24) berhasil di-generate dengan total tagihan Rp {rekap.total_tagihan:,.0f}.",
            )
            return redirect(f"/rekap-potong-gaji/?periode={rekap.periode_bulan}")
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal men-generate rekap potong gaji: {pesan_err}")
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan: {exc}")

    return redirect('rekap_potong_gaji')


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def update_potongan_toko_rekap_view(request, detail_id: int):
    """
    Memperbarui nilai potongan Belanja Toko / Sukarela pada salah satu anggota di Rekap Potong Gaji.
    """
    if request.method == 'POST':
        try:
            detail = RekapNotifikasiController.perbaruiPotonganTambahanAnggota(
                detail_id=detail_id,
                nominal_belanja_toko=request.POST.get('nominal_simpanan_sukarela', '0'),
                bendahara=request.pengguna,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Potongan Belanja Toko / Sukarela untuk {detail.anggota.nama} berhasil diperbarui menjadi "
                f"Rp {detail.nominal_simpanan_sukarela:,.0f}.",
            )
            return redirect(f"/rekap-potong-gaji/?periode={detail.rekap_potong_gaji.periode_bulan}")
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    return redirect('rekap_potong_gaji')


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def konfirmasi_lunas_rekap_gaji_view(request, rekap_id: int):
    """
    Memproses konfirmasi pelunasan kolektif (batch) setelah dana potong gaji diterima dari Bendahara Gaji Sekolah.
    """
    if request.method == 'POST':
        no_ref = request.POST.get('nomor_referensi_transfer', '')
        try:
            rekap = RekapNotifikasiController.konfirmasiPelunasanKolektif(
                rekap_id=rekap_id,
                bendahara=request.pengguna,
                no_ref_bank=no_ref,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Pelunasan kolektif Rekap {rekap.kode_rekap} (Ref: {rekap.nomor_referensi_transfer}) berhasil dikonfirmasi. "
                f"Seluruh Simpanan Wajib & Angsuran anggota pada periode ini telah ditandai LUNAS.",
            )
            return redirect(f"/rekap-potong-gaji/?periode={rekap.periode_bulan}")
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    return redirect('rekap_potong_gaji')


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def ekspor_rekap_potong_gaji_view(request, rekap_id: int):
    """
    Mengekspor dokumen Rekap Potong Gaji Tanggal 24 ke format Excel (.xlsx) atau PDF (.pdf).
    """
    fmt = request.GET.get('format', 'xlsx')
    return RekapNotifikasiController.eksporFileRekapGaji(rekap_id=rekap_id, format_file=fmt)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def notifikasi_tagihan_view(request):
    """
    Menampilkan & memproses Halaman Notifikasi Tagihan (Pengingat Tanggal 10 via WhatsApp & Email)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Notifikasi Tagihan.png (WD-13).
    """
    if request.method == 'POST':
        jadwal_ids = request.POST.getlist('jadwal_ids')
        kanal_list = request.POST.getlist('kanal')
        jadwal_label = request.POST.get('jadwal_pengiriman', 'Setiap tanggal 10')
        isi_pesan_template = request.POST.get('isi_pesan', '')

        try:
            terkirim = RekapNotifikasiController.kirimNotifikasiTagihan(
                bendahara=request.pengguna,
                jadwal_ids=jadwal_ids,
                kanal_list=kanal_list,
                template_pesan=isi_pesan_template,
                jadwal_kirim_label=jadwal_label,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Berhasil mengirim dan mencatat {len(terkirim)} notifikasi pengingat tagihan "
                f"({', '.join(kanal_list or ['WHATSAPP'])}) dengan jadwal '{jadwal_label}'.",
            )
            return redirect('notifikasi_tagihan')
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    q = (request.GET.get('q') or '').strip()

    # Ambil satu jadwal angsuran belum lunas paling awal untuk setiap pembiayaan aktif
    qs_jadwal_aktif = (
        JadwalAngsuran.objects.select_related(
            'pembiayaan', 'pembiayaan__anggota', 'pembiayaan__jenis_akad'
        )
        .filter(
            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
        )
        .order_by('pembiayaan_id', 'angsuran_ke')
    )
    if q:
        qs_jadwal_aktif = qs_jadwal_aktif.filter(
            Q(pembiayaan__anggota__nama__icontains=q)
            | Q(pembiayaan__anggota__no_anggota__icontains=q)
            | Q(pembiayaan__no_pembiayaan__icontains=q)
            | Q(pembiayaan__anggota__no_hp__icontains=q)
        )

    seen_pembiayaan = set()
    daftar_penerima = []
    for jdw in qs_jadwal_aktif:
        if jdw.pembiayaan_id in seen_pembiayaan:
            continue
        seen_pembiayaan.add(jdw.pembiayaan_id)
        notif_terakhir = NotifikasiTagihan.objects.filter(
            anggota=jdw.pembiayaan.anggota,
            jadwal_angsuran=jdw,
        ).first()
        daftar_penerima.append({
            'jadwal': jdw,
            'anggota': jdw.pembiayaan.anggota,
            'pembiayaan': jdw.pembiayaan,
            'notif_terakhir': notif_terakhir,
        })

    riwayat_notifikasi = NotifikasiTagihan.objects.select_related(
        'anggota', 'jadwal_angsuran', 'jadwal_angsuran__pembiayaan', 'bendahara'
    )[:8]

    template_default = (
        "Assalamu'alaikum Bapak/Ibu {nama} ({no_anggota}),\n\n"
        "Kami menginformasikan pengingat tagihan rutin Koperasi Syariah KKPRIS SMKN 1 Kota Solok:\n"
        "• Kontrak Pembiayaan: {no_pembiayaan} (Angsuran ke-{angsuran_ke})\n"
        "• Nominal Angsuran: {nominal}\n"
        "• Simpanan Wajib Bulanan: Rp 150.000\n"
        "• Tanggal Cut-off Potong Gaji: {jatuh_tempo}\n\n"
        "Terima kasih atas kerja sama dan kepercayaan Bapak/Ibu."
    )

    context = {
        'active_menu': 'notifikasi_tagihan',
        'q': q,
        'daftar_penerima': daftar_penerima,
        'riwayat_notifikasi': riwayat_notifikasi,
        'template_default': template_default,
    }
    return render(request, 'angsuran/notifikasi_tagihan.html', context)
