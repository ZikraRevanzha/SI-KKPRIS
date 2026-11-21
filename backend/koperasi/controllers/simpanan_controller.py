"""
SimpananController & Views Pengelolaan Transaksi Multi-Simpanan Anggota
(Tahap 4 — UC-02, UC-10, UC-13 | FR-SMP-01 s.d. FR-SMP-03, BR-08).

Selaras dengan:
- 03_Class_Diagram_SI-KKPRIS.mmd (SimpananController)
- Sequence Diagram SQ-02 (Lihat Saldo & Status) & SQ-09 (Kelola Simpanan Setor & Tarik)
- Wireframe Final:
  1. Kelola Simpanan.png (WD-05)
  2. Transaksi Baru.png (WD-06)
  3. Cetak Bukti Transaksi.png (WD-07)
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from koperasi.controllers.auth_controller import (
    _ambil_ip_klien,
    login_wajib,
    peran_wajib,
)
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    MetodeBayarChoices,
    Pengguna,
    PeranPenggunaChoices,
    StatusAnggotaChoices,
    TransaksiSimpanan,
)
from koperasi.utils import bersihkan_rupiah


def _hitung_saldo_sebelum(ts: TransaksiSimpanan) -> Decimal:
    """
    Menghitung Saldo Sebelum transaksi secara eksak berpresisi Decimal(15,2):
    - Jika SETOR: Saldo Sebelum = Saldo Sesudah - Nominal
    - Jika TARIK: Saldo Sebelum = Saldo Sesudah + Nominal
    """
    if ts.jenis_transaksi == JenisTransaksiSimpananChoices.SETOR:
        return (ts.saldo_sesudah - ts.nominal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return (ts.saldo_sesudah + ts.nominal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# ============================================================================
# CLASS CONTROLLER: SimpananController (Sesuai Class Diagram & Sequence Diagram)
# ============================================================================

class SimpananController:
    """
    Controller Pengelolaan 5 Skema Simpanan Anggota SI-KKPRIS.
    Mencakup:
    - FR-SMP-01: Pengelolaan 5 Skema Simpanan (Pokok, Khusus, Wajib, Hari Raya, Berencana)
    - FR-SMP-02 & BR-08: Pencatatan mutasi Setor & Tarik dengan proteksi simpanan terkunci
      (dapat_ditarik = 0) dan larangan saldo negatif
    - FR-SMP-03: Penerbitan bukti kuitansi transaksi simpanan bernomor unik
    """

    @staticmethod
    def generateNoKuitansiSimpanan(kode_jenis: str = 'SMP') -> str:
        """
        Membangkitkan nomor kuitansi transaksi simpanan unik dengan format:
        KUI-{KODE}-YYYYMMDD-NNN (contoh: KUI-SHR-20261116-001).
        """
        tgl_str = timezone.now().strftime('%Y%m%d')
        prefix = f"KUI-{kode_jenis.upper()}-{tgl_str}-"
        urutan = TransaksiSimpanan.objects.filter(no_kuitansi__startswith=prefix).count() + 1
        kandidat = f"{prefix}{urutan:03d}"
        while TransaksiSimpanan.objects.filter(no_kuitansi=kandidat).exists():
            urutan += 1
            kandidat = f"{prefix}{urutan:03d}"
        return kandidat

    @classmethod
    def lihatSaldoDanStatus(cls, anggota_id: int) -> dict:
        """
        Mengambil rincian saldo berjalan 5 skema simpanan milik seorang anggota
        beserta ringkasan simpanan terkunci vs sukarela (SQ-02 — UC-02, FR-SMP-01).
        """
        urutan_kode = ['SPK', 'SWJ', 'SKH', 'SHR', 'SBR']
        peta_jenis = {js.kode: js for js in JenisSimpanan.objects.all()}

        rincian_saldo = []
        total_terkunci = Decimal('0.00')
        total_sukarela = Decimal('0.00')

        for kode in urutan_kode:
            js = peta_jenis.get(kode)
            if not js:
                continue
            saldo = TransaksiSimpanan.hitungSaldoBerjalan(anggota_id, js.id)
            if js.dapat_ditarik:
                total_sukarela += saldo
            else:
                total_terkunci += saldo

            rincian_saldo.append({
                'id': js.id,
                'kode': js.kode,
                'nama': js.nama,
                'nama_singkat': js.nama.replace('Simpanan ', ''),
                'nominal_default': js.nominal_default,
                'dapat_ditarik': js.dapat_ditarik,
                'is_wajib': js.is_wajib,
                'is_periodik': js.is_periodik,
                'saldo': saldo,
            })

        total_keseluruhan = (total_terkunci + total_sukarela).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        return {
            'rincian_saldo': rincian_saldo,
            'total_terkunci': total_terkunci,
            'total_sukarela': total_sukarela,
            'total_keseluruhan': total_keseluruhan,
        }

    @classmethod
    def catatSetorTarikSimpanan(
        cls,
        bendahara: Pengguna,
        data_input: dict,
        ip_address: str = '127.0.0.1',
    ) -> TransaksiSimpanan:
        """
        Memvalidasi dan mencatat transaksi setoran (SETOR) atau penarikan (TARIK) simpanan
        (SQ-09 — UC-10, FR-SMP-02, BR-08).
        """
        anggota_id = data_input.get('anggota_id')
        jenis_simpanan_id = data_input.get('jenis_simpanan_id')
        jenis_transaksi = (data_input.get('jenis_transaksi') or '').strip().upper()
        metode_bayar = (data_input.get('metode_bayar') or MetodeBayarChoices.TUNAI).strip().upper()
        keterangan = (data_input.get('keterangan') or '').strip()

        if not anggota_id or not jenis_simpanan_id:
            raise ValidationError('Anggota dan Jenis Simpanan wajib dipilih.')

        if jenis_transaksi not in JenisTransaksiSimpananChoices.values:
            raise ValidationError('Jenis transaksi harus berupa SETOR atau TARIK.')

        if metode_bayar not in MetodeBayarChoices.values:
            metode_bayar = MetodeBayarChoices.TUNAI

        nominal = bersihkan_rupiah(data_input.get('nominal'), default='0.00')

        if nominal <= Decimal('0.00'):
            raise ValidationError('Jumlah nominal transaksi harus lebih besar dari Rp 0.')

        anggota = get_object_or_404(Anggota, pk=int(anggota_id))
        if anggota.status == StatusAnggotaChoices.NON_AKTIF_KELUAR:
            raise ValidationError(
                f"Anggota {anggota.nama} ({anggota.no_anggota}) sudah berstatus Non-Aktif Keluar dan tidak dapat bertransaksi."
            )

        jenis_simpanan = get_object_or_404(JenisSimpanan, pk=int(jenis_simpanan_id))
        no_kuitansi = (
            (data_input.get('no_kuitansi') or '').strip()
            or cls.generateNoKuitansiSimpanan(jenis_simpanan.kode)
        )

        if not keterangan:
            aksi_label = 'Setoran' if jenis_transaksi == JenisTransaksiSimpananChoices.SETOR else 'Penarikan'
            keterangan = f"{aksi_label} {jenis_simpanan.nama} ({anggota.no_anggota})"

        with transaction.atomic():
            mutasi = TransaksiSimpanan.simpanMutasiSimpanan({
                'anggota_id': anggota.id,
                'jenis_simpanan_id': jenis_simpanan.id,
                'bendahara_id': bendahara.id,
                'no_kuitansi': no_kuitansi,
                'jenis_transaksi': jenis_transaksi,
                'metode_bayar': metode_bayar,
                'nominal': nominal,
                'keterangan': keterangan,
            })

            saldo_sebelum = _hitung_saldo_sebelum(mutasi)
            aksi_audit = (
                'SETOR_SIMPANAN'
                if jenis_transaksi == JenisTransaksiSimpananChoices.SETOR
                else 'TARIK_SIMPANAN'
            )
            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi=aksi_audit,
                nama_tabel='transaksi_simpanan',
                record_id=mutasi.id,
                detail=(
                    f"{aksi_audit} [{mutasi.no_kuitansi}] {anggota.no_anggota} ({anggota.nama}) — "
                    f"{jenis_simpanan.nama}: Rp{mutasi.nominal:,.2f} "
                    f"(Saldo: Rp{saldo_sebelum:,.2f} -> Rp{mutasi.saldo_sesudah:,.2f})."
                ),
                ip_address=ip_address,
            )
            return mutasi


# ============================================================================
# DJANGO VIEWS: Kelola Simpanan (Pengurus), Simpanan Saya (Anggota), & Ekspor
# ============================================================================

@login_wajib
def kelola_simpanan_router_view(request):
    """
    Rute utama /simpanan/:
    - Jika diakses oleh BENDAHARA / KETUA -> menampilkan halaman Kelola Simpanan (WD-05 & WD-06)
    - Jika diakses oleh ANGGOTA -> menampilkan portal Simpanan Saya (UC-02, FR-SMP-01)
    """
    if request.pengguna.peran in (PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA):
        return kelola_simpanan_pengurus_view(request)
    return simpanan_anggota_view(request)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def kelola_simpanan_pengurus_view(request):
    """
    Menampilkan Halaman Kelola Simpanan, Modal Transaksi Baru, & Dialog Cetak Bukti Transaksi
    Sesuai Wireframe:
    - 01_Wireframe_Final_PNG/Kelola Simpanan.png (WD-05)
    - 01_Wireframe_Final_PNG/Transaksi Baru.png (WD-06)
    - 01_Wireframe_Final_PNG/Cetak Bukti Transaksi.png (WD-07)
    """
    # 1. Hitung 4 Kartu Statistik sesuai Kelola Simpanan.png:
    #    Total Simpanan, Simpanan Pokok, Simpanan Wajib, Simpanan Khusus
    def _saldo_kode(kode_js: str) -> Decimal:
        agg = TransaksiSimpanan.objects.filter(jenis_simpanan__kode=kode_js).aggregate(
            setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
            tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
        )
        return (agg['setor'] or Decimal('0.00')) - (agg['tarik'] or Decimal('0.00'))

    agg_all = TransaksiSimpanan.objects.aggregate(
        setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
        tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
    )
    total_simpanan = (agg_all['setor'] or Decimal('0.00')) - (agg_all['tarik'] or Decimal('0.00'))
    saldo_pokok = _saldo_kode('SPK')
    saldo_wajib = _saldo_kode('SWJ')
    saldo_khusus = _saldo_kode('SKH')
    saldo_hari_raya = _saldo_kode('SHR')
    saldo_berencana = _saldo_kode('SBR')

    # 2. Parameter Filter (Cari, Jenis Simpanan, Jenis Transaksi)
    q = (request.GET.get('q') or '').strip()
    filter_jenis_simpanan = (request.GET.get('jenis_simpanan') or '').strip()
    filter_jenis_transaksi = (request.GET.get('jenis_transaksi') or '').strip().upper()

    qs_mutasi = TransaksiSimpanan.objects.select_related(
        'anggota', 'jenis_simpanan', 'bendahara'
    ).all().order_by('-tanggal_transaksi', '-id')

    if q:
        qs_mutasi = qs_mutasi.filter(
            Q(anggota__nama__icontains=q)
            | Q(anggota__no_anggota__icontains=q)
            | Q(no_kuitansi__icontains=q)
            | Q(keterangan__icontains=q)
        )

    if filter_jenis_simpanan:
        qs_mutasi = qs_mutasi.filter(jenis_simpanan__kode=filter_jenis_simpanan)

    if filter_jenis_transaksi in JenisTransaksiSimpananChoices.values:
        qs_mutasi = qs_mutasi.filter(jenis_transaksi=filter_jenis_transaksi)

    # 3. Paginasi (Sesuai tombol Sebelumnya & Berikutnya pada Kelola Simpanan.png)
    paginator = Paginator(qs_mutasi, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    daftar_baris_mutasi = []
    for ts in page_obj.object_list:
        daftar_baris_mutasi.append({
            'obj': ts,
            'saldo_sebelum': _hitung_saldo_sebelum(ts),
        })

    # 4. Cek apakah ada kuitansi yang baru disimpan untuk memunculkan dialog Cetak Bukti Transaksi (WD-07)
    kuitansi_cetak_kode = (request.GET.get('cetak') or '').strip()
    transaksi_cetak = None
    saldo_sebelum_cetak = Decimal('0.00')
    if kuitansi_cetak_kode:
        transaksi_cetak = TransaksiSimpanan.cariBerdasarkanKuitansi(kuitansi_cetak_kode)
        if transaksi_cetak:
            saldo_sebelum_cetak = _hitung_saldo_sebelum(transaksi_cetak)

    context = {
        'active_menu': 'simpanan',
        'total_simpanan': total_simpanan,
        'saldo_pokok': saldo_pokok,
        'saldo_wajib': saldo_wajib,
        'saldo_khusus': saldo_khusus,
        'saldo_hari_raya': saldo_hari_raya,
        'saldo_berencana': saldo_berencana,
        'q': q,
        'filter_jenis_simpanan': filter_jenis_simpanan,
        'filter_jenis_transaksi': filter_jenis_transaksi,
        'daftar_jenis_simpanan': JenisSimpanan.objects.all(),
        'daftar_anggota_aktif': Anggota.objects.exclude(
            status=StatusAnggotaChoices.NON_AKTIF_KELUAR
        ).order_by('no_anggota'),
        'jenis_transaksi_choices': JenisTransaksiSimpananChoices.choices,
        'metode_bayar_choices': MetodeBayarChoices.choices,
        'page_obj': page_obj,
        'daftar_baris_mutasi': daftar_baris_mutasi,
        'transaksi_cetak': transaksi_cetak,
        'saldo_sebelum_cetak': saldo_sebelum_cetak,
    }
    return render(request, 'simpanan/kelola_simpanan.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def tambah_transaksi_simpanan_view(request):
    """
    Memproses form Modal Transaksi Baru (WD-06) oleh Bendahara.
    Jika berhasil, mengarahkan ke /simpanan/?cetak=<no_kuitansi> agar dialog
    Cetak Bukti Transaksi (WD-07) langsung tampil sesuai alur SRS 3.1 & UC-10.
    """
    if request.method == 'POST':
        try:
            mutasi = SimpananController.catatSetorTarikSimpanan(
                bendahara=request.pengguna,
                data_input={
                    'anggota_id': request.POST.get('anggota_id'),
                    'jenis_simpanan_id': request.POST.get('jenis_simpanan_id'),
                    'jenis_transaksi': request.POST.get('jenis_transaksi'),
                    'metode_bayar': request.POST.get('metode_bayar', MetodeBayarChoices.TUNAI),
                    'nominal': request.POST.get('nominal'),
                    'keterangan': request.POST.get('keterangan'),
                },
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Transaksi {mutasi.get_jenis_transaksi_display()} ({mutasi.jenis_simpanan.nama}) "
                f"sebesar Rp {mutasi.nominal:,.0f} untuk {mutasi.anggota.nama} berhasil disimpan "
                f"dengan No. Kuitansi {mutasi.no_kuitansi}.",
            )
            return redirect(f"/simpanan/?cetak={mutasi.no_kuitansi}")
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Transaksi ditolak: {pesan_err}")
        except Exception as exc:
            messages.error(request, f"Gagal mencatat transaksi simpanan: {exc}")

    return redirect('kelola_simpanan')


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def simpanan_anggota_view(request):
    """
    Menampilkan Halaman Portal Mandiri 'Simpanan Saya' untuk Anggota (UC-02, FR-SMP-01).
    Memuat 5 kartu skema simpanan (Pokok, Wajib, Khusus, Hari Raya, Berencana) beserta
    status Terkunci vs Sukarela dan tabel riwayat mutasi simpanan pribadi.
    """
    anggota = getattr(request.pengguna, 'profil_anggota', None)
    if not anggota:
        messages.error(request, 'Profil keanggotaan tidak ditemukan.')
        return redirect('beranda_anggota')

    data_saldo = SimpananController.lihatSaldoDanStatus(anggota.id)

    filter_jenis = (request.GET.get('jenis_simpanan') or '').strip()
    filter_transaksi = (request.GET.get('jenis_transaksi') or '').strip().upper()

    qs_mutasi = TransaksiSimpanan.objects.select_related('jenis_simpanan', 'bendahara').filter(
        anggota=anggota
    ).order_by('-tanggal_transaksi', '-id')

    if filter_jenis:
        qs_mutasi = qs_mutasi.filter(jenis_simpanan__kode=filter_jenis)
    if filter_transaksi in JenisTransaksiSimpananChoices.values:
        qs_mutasi = qs_mutasi.filter(jenis_transaksi=filter_transaksi)

    paginator = Paginator(qs_mutasi, 8)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    daftar_baris_mutasi = []
    for ts in page_obj.object_list:
        daftar_baris_mutasi.append({
            'obj': ts,
            'saldo_sebelum': _hitung_saldo_sebelum(ts),
        })

    context = {
        'active_menu': 'simpanan',
        'anggota': anggota,
        'rincian_saldo': data_saldo['rincian_saldo'],
        'total_terkunci': data_saldo['total_terkunci'],
        'total_sukarela': data_saldo['total_sukarela'],
        'total_keseluruhan': data_saldo['total_keseluruhan'],
        'filter_jenis': filter_jenis,
        'filter_transaksi': filter_transaksi,
        'daftar_jenis_simpanan': JenisSimpanan.objects.all(),
        'jenis_transaksi_choices': JenisTransaksiSimpananChoices.choices,
        'page_obj': page_obj,
        'daftar_baris_mutasi': daftar_baris_mutasi,
    }
    return render(request, 'simpanan/simpanan_anggota.html', context)


@login_wajib
def cetak_kuitansi_simpanan_view(request, no_kuitansi: str):
    """
    Menampilkan lembar Kuitansi Bukti Transaksi Simpanan Resmi siap cetak / simpan PDF (FR-SMP-03, UC-13).
    Anggota hanya dapat mencetak kuitansi miliknya sendiri; Bendahara & Ketua dapat mencetak seluruh kuitansi.
    """
    mutasi = TransaksiSimpanan.cariBerdasarkanKuitansi(no_kuitansi)
    if not mutasi:
        messages.error(request, f'Kuitansi dengan nomor {no_kuitansi} tidak ditemukan.')
        return redirect('kelola_simpanan')

    if request.pengguna.peran == PeranPenggunaChoices.ANGGOTA:
        anggota_login = getattr(request.pengguna, 'profil_anggota', None)
        if not anggota_login or mutasi.anggota_id != anggota_login.id:
            messages.error(request, 'Akses ditolak: Anda hanya dapat melihat bukti kuitansi milik Anda sendiri.')
            return redirect('kelola_simpanan')

    context = {
        'mutasi': mutasi,
        'saldo_sebelum': _hitung_saldo_sebelum(mutasi),
    }
    return render(request, 'simpanan/kuitansi_simpanan_print.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def ekspor_simpanan_excel_view(request):
    """
    Mengekspor daftar riwayat transaksi simpanan ke berkas Microsoft Excel (.xlsx)
    sesuai tombol 'Ekspor' pada Wireframe Kelola Simpanan.png.
    """
    q = (request.GET.get('q') or '').strip()
    filter_jenis_simpanan = (request.GET.get('jenis_simpanan') or '').strip()
    filter_jenis_transaksi = (request.GET.get('jenis_transaksi') or '').strip().upper()

    qs = TransaksiSimpanan.objects.select_related('anggota', 'jenis_simpanan', 'bendahara').all().order_by(
        '-tanggal_transaksi', '-id'
    )
    if q:
        qs = qs.filter(
            Q(anggota__nama__icontains=q)
            | Q(anggota__no_anggota__icontains=q)
            | Q(no_kuitansi__icontains=q)
        )
    if filter_jenis_simpanan:
        qs = qs.filter(jenis_simpanan__kode=filter_jenis_simpanan)
    if filter_jenis_transaksi in JenisTransaksiSimpananChoices.values:
        qs = qs.filter(jenis_transaksi=filter_jenis_transaksi)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Mutasi Simpanan'

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )

    ws.append(['REKAPITULASI TRANSAKSI SIMPANAN ANGGOTA — SI-KKPRIS SMKN 1 KOTA SOLOK'])
    ws['A1'].font = Font(bold=True, size=12)
    ws.append([f'Tanggal Unduh: {date.today():%d/%m/%Y}'])
    ws.append([])

    headers = [
        'No',
        'No. Kuitansi',
        'Tanggal',
        'No. Anggota',
        'Nama Anggota',
        'Jenis Simpanan',
        'Transaksi',
        'Metode Bayar',
        'Jumlah (Rp)',
        'Saldo Sebelum (Rp)',
        'Saldo Sesudah (Rp)',
        'Keterangan',
    ]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    for idx, ts in enumerate(qs, start=1):
        saldo_sblm = _hitung_saldo_sebelum(ts)
        row_data = [
            idx,
            ts.no_kuitansi,
            ts.tanggal_transaksi.strftime('%d/%m/%Y %H:%M'),
            ts.anggota.no_anggota,
            ts.anggota.nama,
            ts.jenis_simpanan.nama,
            ts.get_jenis_transaksi_display(),
            ts.get_metode_bayar_display(),
            ts.nominal,
            saldo_sblm,
            ts.saldo_sesudah,
            ts.keterangan or '-',
        ]
        ws.append(row_data)
        curr_row = 4 + idx
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=curr_row, column=col_idx)
            c.border = thin_border
            if col_idx in (9, 10, 11):
                c.number_format = '#,##0.00'

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 12), 38)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Mutasi_Simpanan_SI-KKPRIS_{date.today():%Y%m%d}.xlsx"
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
