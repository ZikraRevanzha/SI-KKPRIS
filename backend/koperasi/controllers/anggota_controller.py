"""
AnggotaController & Views Manajemen Keanggotaan serta Kliring Pengunduran Diri
(Tahap 3 — UC-05, UC-08, UC-09 | FR-MBR-01 s.d. FR-MBR-04).

Selaras dengan:
- 03_Class_Diagram_SI-KKPRIS.mmd (AnggotaController)
- Sequence Diagram SQ-04, SQ-07, SQ-08
- 4 Wireframe Tahap 3:
  1. Data Anggota.png (WD-03)
  2. Form Anggota Baru.png (WD-04)
  3. Ajukan Pengunduran Diri.png (WD-22)
  4. Verifikasi Pengunduran Diri.png (WD-17)
"""

import os
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from koperasi.controllers.auth_controller import (
    _ambil_ip_klien,
    login_wajib,
    peran_wajib,
)
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JadwalAngsuran,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    MetodeBayarChoices,
    Pembiayaan,
    Pengguna,
    PengunduranDiri,
    PeranPenggunaChoices,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusKepegawaianChoices,
    StatusKliringResignChoices,
    StatusPembiayaanChoices,
    StatusPengajuanResignChoices,
    TransaksiSimpanan,
)


def _simpan_berkas_unggah(berkas, subfolder: str, prefix: str) -> str:
    """Menyimpan berkas unggahan ke dalam MEDIA_ROOT dan mengembalikan path relatif."""
    if not berkas:
        return ''
    nama_aman = get_valid_filename(berkas.name)
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    rel_path = os.path.join(subfolder, f"{prefix}_{timestamp}_{nama_aman}").replace('\\', '/')
    full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    saved_path = default_storage.save(rel_path, berkas)
    return f"media/{saved_path}".replace('\\', '/')


# ============================================================================
# CLASS CONTROLLER: AnggotaController (Sesuai Class Diagram & Sequence Diagram)
# ============================================================================

class AnggotaController:
    """
    Controller Manajemen Data Anggota & Pengunduran Diri (Kliring) SI-KKPRIS.
    Mencakup:
    - FR-MBR-01: Registrasi anggota baru & auto-generate Nomor Anggota
    - FR-MBR-02: Pencarian, penyaringan, dan pembaruan profil kepegawaian
    - FR-MBR-03: Pengajuan pengunduran diri mandiri oleh Anggota
    - FR-MBR-04: Verifikasi & perhitungan kliring (Total Simpanan - Sisa Kewajiban)
    """

    @staticmethod
    def generateNoAnggota(tahun: int = None) -> str:
        """
        Membangkitkan Nomor Anggota unik secara otomatis dengan format KKP-YYYY-NNN
        (contoh: KKP-2026-001, KKP-2026-002).
        """
        thn = tahun or date.today().year
        prefix = f"KKP-{thn}-"
        terakhir = (
            Anggota.objects.filter(no_anggota__startswith=prefix)
            .order_by('-no_anggota')
            .first()
        )
        urutan_baru = 1
        if terakhir:
            bagian_akhir = terakhir.no_anggota.replace(prefix, '').strip()
            if bagian_akhir.isdigit():
                urutan_baru = int(bagian_akhir) + 1
        else:
            urutan_baru = Anggota.objects.count() + 1

        kandidat = f"{prefix}{urutan_baru:03d}"
        while Anggota.objects.filter(no_anggota=kandidat).exists():
            urutan_baru += 1
            kandidat = f"{prefix}{urutan_baru:03d}"
        return kandidat

    @classmethod
    def kelolaDataAnggota(
        cls,
        bendahara: Pengguna,
        data_input: dict,
        berkas_ktp=None,
        ip_address: str = '127.0.0.1',
    ) -> Anggota:
        """
        Mendaftarkan anggota koperasi baru beserta akun pengguna (login),
        dan mencatat setoran awal Simpanan Pokok / Khusus sesuai skema cicilan yang dipilih
        (SQ-07: Kelola Data Anggota — UC-08, FR-MBR-01).
        """
        nama = (data_input.get('nama') or '').strip()
        nik = (data_input.get('nik') or '').strip()
        no_anggota = (data_input.get('no_anggota') or '').strip() or cls.generateNoAnggota()
        username = (data_input.get('username') or nik or no_anggota).strip()
        password_awal = data_input.get('password') or 'Kkpris2026!'
        status_kepegawaian = data_input.get('status_kepegawaian') or StatusKepegawaianChoices.PNS
        masa_dinas_tahun = int(data_input.get('masa_dinas_tahun') or 0)
        no_hp = (data_input.get('no_hp') or '081200000000').strip()
        tanggal_masuk = data_input.get('tanggal_masuk') or date.today()
        if isinstance(tanggal_masuk, str):
            tanggal_masuk = date.fromisoformat(tanggal_masuk)

        if not nama or not nik:
            raise ValidationError('Nama lengkap dan Nomor KTP (NIK) wajib diisi.')
        if Anggota.objects.filter(nik=nik).exists():
            raise ValidationError(f'NIK {nik} sudah terdaftar pada data anggota lain.')
        if Anggota.objects.filter(no_anggota=no_anggota).exists():
            raise ValidationError(f'Nomor Anggota {no_anggota} sudah digunakan.')
        if Pengguna.objects.filter(username=username).exists():
            username = no_anggota

        ktp_url = ''
        if berkas_ktp:
            ktp_url = _simpan_berkas_unggah(berkas_ktp, 'ktp', no_anggota)

        with transaction.atomic():
            akun_baru = Pengguna.buatAkunPengguna({
                'username': username,
                'password': password_awal,
                'nama_lengkap': nama,
                'peran': PeranPenggunaChoices.ANGGOTA,
                'is_aktif': True,
            })

            anggota_baru = Anggota.simpanDataAnggota({
                'pengguna': akun_baru,
                'no_anggota': no_anggota,
                'nik': nik,
                'nama': nama,
                'status_kepegawaian': status_kepegawaian,
                'masa_dinas_tahun': masa_dinas_tahun,
                'no_hp': no_hp,
                'tanggal_masuk': tanggal_masuk,
                'status': StatusAnggotaChoices.AKTIF,
            })

            # Proses skema Cicilan Simpanan Pokok (Rp350.000) & Simpanan Khusus (Rp500.000)
            skema_pokok = data_input.get('cicilan_simpanan_pokok', 'LUNAS_AWAL')
            skema_khusus = data_input.get('cicilan_simpanan_khusus', 'LUNAS_AWAL')

            peta_nominal_pokok = {
                'LUNAS_AWAL': (Decimal('350000.00'), 'Setoran Lunas Simpanan Pokok Anggota Baru'),
                'CICIL_2X': (Decimal('175000.00'), 'Cicilan Ke-1 (dari 2x) Simpanan Pokok Anggota Baru'),
                'CICIL_5X': (Decimal('70000.00'), 'Cicilan Ke-1 (dari 5x) Simpanan Pokok Anggota Baru'),
            }
            peta_nominal_khusus = {
                'LUNAS_AWAL': (Decimal('500000.00'), 'Setoran Lunas Simpanan Khusus Anggota Baru'),
                'CICIL_2X': (Decimal('250000.00'), 'Cicilan Ke-1 (dari 2x) Simpanan Khusus Anggota Baru'),
                'CICIL_5X': (Decimal('100000.00'), 'Cicilan Ke-1 (dari 5x) Simpanan Khusus Anggota Baru'),
            }

            js_spk = JenisSimpanan.objects.filter(kode='SPK').first()
            if js_spk and skema_pokok in peta_nominal_pokok:
                nom_spk, ket_spk = peta_nominal_pokok[skema_pokok]
                no_kui_spk = f"KUI-SPK-{anggota_baru.id}-{timezone.now().strftime('%H%M%S')}"
                TransaksiSimpanan.simpanMutasiSimpanan({
                    'anggota_id': anggota_baru.id,
                    'jenis_simpanan_id': js_spk.id,
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': no_kui_spk,
                    'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                    'metode_bayar': MetodeBayarChoices.TUNAI,
                    'nominal': nom_spk,
                    'bukti_transaksi_url': ktp_url or None,
                    'keterangan': ket_spk,
                })

            js_skh = JenisSimpanan.objects.filter(kode='SKH').first()
            if js_skh and skema_khusus in peta_nominal_khusus:
                nom_skh, ket_skh = peta_nominal_khusus[skema_khusus]
                no_kui_skh = f"KUI-SKH-{anggota_baru.id}-{timezone.now().strftime('%H%M%S')}"
                TransaksiSimpanan.simpanMutasiSimpanan({
                    'anggota_id': anggota_baru.id,
                    'jenis_simpanan_id': js_skh.id,
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': no_kui_skh,
                    'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                    'metode_bayar': MetodeBayarChoices.TUNAI,
                    'nominal': nom_skh,
                    'bukti_transaksi_url': ktp_url or None,
                    'keterangan': ket_skh,
                })

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='TAMBAH_ANGGOTA_BARU',
                nama_tabel='anggota',
                record_id=anggota_baru.id,
                detail=(
                    f"Registrasi anggota baru {anggota_baru.no_anggota} - {anggota_baru.nama} "
                    f"(Status: {anggota_baru.status_kepegawaian}, Pokok: {skema_pokok}, Khusus: {skema_khusus})."
                ),
                ip_address=ip_address,
            )
            return anggota_baru

    @classmethod
    def perbaruiDataAnggota(
        cls,
        bendahara: Pengguna,
        anggota_id: int,
        data_update: dict,
        ip_address: str = '127.0.0.1',
    ) -> Anggota:
        """
        Memperbarui profil kepegawaian, nomor HP, atau masa dinas anggota (FR-MBR-02).
        """
        anggota = get_object_or_404(Anggota.objects.select_related('pengguna'), pk=anggota_id)

        nama_baru = (data_update.get('nama') or anggota.nama).strip()
        nik_baru = (data_update.get('nik') or anggota.nik).strip()
        status_kepeg = data_update.get('status_kepegawaian') or anggota.status_kepegawaian
        masa_dinas = int(data_update.get('masa_dinas_tahun', anggota.masa_dinas_tahun))
        no_hp_baru = (data_update.get('no_hp') or anggota.no_hp).strip()

        if Anggota.objects.exclude(pk=anggota.id).filter(nik=nik_baru).exists():
            raise ValidationError(f'NIK {nik_baru} sudah terdaftar pada anggota lain.')

        with transaction.atomic():
            anggota.nama = nama_baru
            anggota.nik = nik_baru
            anggota.status_kepegawaian = status_kepeg
            anggota.masa_dinas_tahun = masa_dinas
            anggota.no_hp = no_hp_baru
            anggota.save()

            if anggota.pengguna.nama_lengkap != nama_baru:
                anggota.pengguna.nama_lengkap = nama_baru
                anggota.pengguna.save(update_fields=['nama_lengkap'])

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='UPDATE_PROFIL_ANGGOTA',
                nama_tabel='anggota',
                record_id=anggota.id,
                detail=(
                    f"Pembaruan data anggota {anggota.no_anggota} ({anggota.nama}) — "
                    f"Kepegawaian: {anggota.status_kepegawaian}, Masa Dinas: {anggota.masa_dinas_tahun} thn."
                ),
                ip_address=ip_address,
            )
            return anggota

    @classmethod
    def ajukanPengunduranDiri(
        cls,
        anggota: Anggota,
        alasan_kategori: str,
        keterangan: str = '',
        berkas_surat=None,
        surat_url_manual: str = '',
        ip_address: str = '127.0.0.1',
    ) -> PengunduranDiri:
        """
        Memproses pengajuan pengunduran diri mandiri oleh Anggota (SQ-04 — UC-05, FR-MBR-03).
        Memvalidasi tidak adanya pengajuan aktif yang masih menunggu verifikasi,
        menyimpan berkas surat permohonan, menghitung neraca kliring awal, dan
        mengubah status anggota menjadi PROSES_RESIGN.
        """
        if anggota.status == StatusAnggotaChoices.NON_AKTIF_KELUAR:
            raise ValidationError('Keanggotaan Anda sudah berstatus Non-Aktif Keluar.')

        masih_menunggu = PengunduranDiri.objects.filter(
            anggota=anggota,
            status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI,
        ).exists()
        if masih_menunggu:
            raise ValidationError(
                'Anda sudah memiliki permohonan pengunduran diri yang sedang menunggu verifikasi Bendahara.'
            )

        alasan_kategori = (alasan_kategori or '').strip()
        keterangan = (keterangan or '').strip()
        if not alasan_kategori and not keterangan:
            raise ValidationError('Alasan pengunduran diri wajib diisi.')

        alasan_lengkap = (
            f"{alasan_kategori} — {keterangan}" if (alasan_kategori and keterangan) else (alasan_kategori or keterangan)
        )[:255]

        if berkas_surat:
            surat_url = _simpan_berkas_unggah(berkas_surat, 'resign', anggota.no_anggota)
        elif surat_url_manual:
            surat_url = surat_url_manual
        else:
            surat_url = f"media/resign/surat_{anggota.no_anggota.lower()}.pdf"

        resign = PengunduranDiri.simpanPermohonanResign(
            anggota_id=anggota.id,
            alasan=alasan_lengkap,
            surat_url=surat_url,
        )

        AuditTrailLog.catatLogAudit(
            pengguna_id=anggota.pengguna_id,
            aksi='AJUKAN_PENGUNDURAN_DIRI',
            nama_tabel='pengunduran_diri',
            record_id=resign.id,
            detail=(
                f"Anggota {anggota.no_anggota} ({anggota.nama}) mengajukan pengunduran diri. "
                f"Hak Simpanan: Rp{resign.total_hak_simpanan:,.2f}, "
                f"Kewajiban: Rp{resign.total_kewajiban_pembiayaan:,.2f}, "
                f"Selisih: Rp{resign.selisih_akhir:,.2f}."
            ),
            ip_address=ip_address,
        )
        return resign

    @classmethod
    def verifikasiPengunduranDiri(
        cls,
        bendahara: Pengguna,
        pengunduran_id: int,
        keputusan: str = 'VERIFIKASI',
        catatan: str = '',
        berita_acara_berkas=None,
        ip_address: str = '127.0.0.1',
    ) -> PengunduranDiri:
        """
        Memproses verifikasi kliring pengunduran diri oleh Bendahara (SQ-08 — UC-09, FR-MBR-04).
        - Jika keputusan == 'HITUNG_ULANG': menyegarkan nilai Total Simpanan, Sisa Pembiayaan, dan Selisih.
        - Jika keputusan == 'TOLAK': menolak pengajuan resign dan mengembalikan status anggota ke AKTIF.
        - Jika keputusan == 'VERIFIKASI': menyelesaikan kliring, menonaktifkan anggota (NON_AKTIF_KELUAR)
          dan menonaktifkan akun login pengguna (is_aktif = False).
        """
        resign = get_object_or_404(
            PengunduranDiri.objects.select_related('anggota', 'anggota__pengguna'),
            pk=pengunduran_id,
        )
        anggota = resign.anggota

        # Hitung ulang nilai kliring terbaru dari tabel transaksi_simpanan & pembiayaan
        total_simpanan = TransaksiSimpanan.hitungTotalSimpananAnggota(anggota.id)
        total_kewajiban = Pembiayaan.hitungSisaKewajibanAnggota(anggota.id)
        resign = PengunduranDiri.hitungKliringResign(
            pengunduran_id=resign.id,
            total_simpanan=total_simpanan,
            total_kewajiban=total_kewajiban,
        )

        if keputusan == 'HITUNG_ULANG':
            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='HITUNG_KLIRING_RESIGN',
                nama_tabel='pengunduran_diri',
                record_id=resign.id,
                detail=(
                    f"Perhitungan ulang kliring resign {anggota.no_anggota}: "
                    f"Simpanan Rp{resign.total_hak_simpanan:,.2f} - Kewajiban Rp{resign.total_kewajiban_pembiayaan:,.2f} "
                    f"= Rp{resign.selisih_akhir:,.2f}."
                ),
                ip_address=ip_address,
            )
            return resign

        if keputusan == 'TOLAK':
            with transaction.atomic():
                resign.bendahara = bendahara
                resign.status_pengajuan = StatusPengajuanResignChoices.DITOLAK
                resign.tanggal_keputusan = date.today()
                resign.save()

                Anggota.ubahStatusAnggota(anggota.id, StatusAnggotaChoices.AKTIF)

                AuditTrailLog.catatLogAudit(
                    pengguna_id=bendahara.id,
                    aksi='TOLAK_PENGUNDURAN_DIRI',
                    nama_tabel='pengunduran_diri',
                    record_id=resign.id,
                    detail=(
                        f"Pengajuan pengunduran diri {anggota.no_anggota} ({anggota.nama}) ditolak oleh Bendahara. "
                        f"Status anggota dikembalikan ke AKTIF. {catatan}"
                    ).strip(),
                    ip_address=ip_address,
                )
            return resign

        # Keputusan VERIFIKASI (Setujui Keluar & Selesai Kliring)
        if berita_acara_berkas:
            ba_url = _simpan_berkas_unggah(berita_acara_berkas, 'resign', f"ba_{anggota.no_anggota}")
        else:
            ba_url = resign.berita_acara_url or f"media/resign/ba_kliring_{anggota.no_anggota.lower()}.pdf"

        PengunduranDiri.selesaikanVerifikasiResign(
            pengunduran_id=resign.id,
            bendahara_id=bendahara.id,
            berita_acara_url=ba_url,
        )
        resign.refresh_from_db()

        AuditTrailLog.catatLogAudit(
            pengguna_id=bendahara.id,
            aksi='VERIFIKASI_KLIRING_RESIGN',
            nama_tabel='pengunduran_diri',
            record_id=resign.id,
            detail=(
                f"Kliring pengunduran diri {anggota.no_anggota} ({anggota.nama}) diselesaikan. "
                f"Selisih Akhir: Rp{resign.selisih_akhir:,.2f}. Akun & status anggota dinonaktifkan."
            ),
            ip_address=ip_address,
        )
        return resign


# ============================================================================
# DJANGO VIEWS: Data Anggota, Tambah/Edit Anggota, Ajukan & Verifikasi Resign
# ============================================================================

@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def data_anggota_view(request):
    """
    Menampilkan Halaman Master Data Anggota & Modal Form Anggota Baru
    Sesuai Wireframe:
    - 01_Wireframe_Final_PNG/Data Anggota.png (WD-03)
    - 01_Wireframe_Final_PNG/Form Anggota Baru.png (WD-04)
    """
    # 1. 3 Kartu Statistik sesuai Data Anggota.png (Total Anggota, Anggota Aktif, Anggota Nonaktif)
    total_anggota = Anggota.objects.count()
    anggota_aktif = Anggota.objects.filter(status=StatusAnggotaChoices.AKTIF).count()
    anggota_nonaktif = Anggota.objects.exclude(status=StatusAnggotaChoices.AKTIF).count()
    resign_menunggu_count = PengunduranDiri.objects.filter(
        status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI
    ).count()

    # 2. Parameter Filter (Cari, Status, Jenis Simpanan)
    q = (request.GET.get('q') or '').strip()
    filter_status = (request.GET.get('status') or '').strip()
    filter_jenis_simpanan = (request.GET.get('jenis_simpanan') or '').strip()

    qs_anggota = Anggota.objects.select_related('pengguna').all().order_by('no_anggota')

    if q:
        qs_anggota = qs_anggota.filter(
            Q(nama__icontains=q)
            | Q(no_anggota__icontains=q)
            | Q(nik__icontains=q)
            | Q(no_hp__icontains=q)
        )

    if filter_status in StatusAnggotaChoices.values:
        qs_anggota = qs_anggota.filter(status=filter_status)

    jenis_simpanan_terpilih = None
    if filter_jenis_simpanan:
        jenis_simpanan_terpilih = JenisSimpanan.objects.filter(kode=filter_jenis_simpanan).first()
        if jenis_simpanan_terpilih:
            anggota_ids_simpanan = (
                TransaksiSimpanan.objects.filter(jenis_simpanan=jenis_simpanan_terpilih)
                .values_list('anggota_id', flat=True)
                .distinct()
            )
            qs_anggota = qs_anggota.filter(id__in=anggota_ids_simpanan)

    # 3. Paginasi (Sesuai tombol Sebelumnya & Berikutnya pada Data Anggota.png)
    paginator = Paginator(qs_anggota, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 4. Hitung Total Simpanan & Sisa Pembiayaan per baris anggota
    daftar_baris_anggota = []
    for ag in page_obj.object_list:
        if jenis_simpanan_terpilih:
            total_simpanan = TransaksiSimpanan.hitungSaldoBerjalan(ag.id, jenis_simpanan_terpilih.id)
        else:
            total_simpanan = TransaksiSimpanan.hitungTotalSimpananAnggota(ag.id)
        sisa_pembiayaan = Pembiayaan.hitungSisaKewajibanAnggota(ag.id)
        daftar_baris_anggota.append({
            'obj': ag,
            'total_simpanan': total_simpanan,
            'sisa_pembiayaan': sisa_pembiayaan,
        })

    context = {
        'active_menu': 'data_anggota',
        'total_anggota': total_anggota,
        'anggota_aktif': anggota_aktif,
        'anggota_nonaktif': anggota_nonaktif,
        'resign_menunggu_count': resign_menunggu_count,
        'q': q,
        'filter_status': filter_status,
        'filter_jenis_simpanan': filter_jenis_simpanan,
        'jenis_simpanan_terpilih': jenis_simpanan_terpilih,
        'daftar_jenis_simpanan': JenisSimpanan.objects.all(),
        'status_anggota_choices': StatusAnggotaChoices.choices,
        'status_kepegawaian_choices': StatusKepegawaianChoices.choices,
        'page_obj': page_obj,
        'daftar_baris_anggota': daftar_baris_anggota,
        'no_anggota_otomatis': AnggotaController.generateNoAnggota(),
        'hari_ini_iso': date.today().isoformat(),
    }
    return render(request, 'anggota/data_anggota.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def tambah_anggota_view(request):
    """
    Memproses form tambah anggota baru dari Modal Form Anggota Baru (WD-04).
    Hanya dapat dieksekusi oleh Bendahara (FR-MBR-01).
    """
    if request.method == 'POST':
        try:
            anggota_baru = AnggotaController.kelolaDataAnggota(
                bendahara=request.pengguna,
                data_input=request.POST,
                berkas_ktp=request.FILES.get('berkas_ktp'),
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Anggota baru {anggota_baru.nama} ({anggota_baru.no_anggota}) berhasil ditambahkan.",
            )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal menyimpan anggota baru: {pesan_err}")
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan saat menyimpan anggota: {exc}")

    return redirect('data_anggota')


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def edit_anggota_view(request, anggota_id: int):
    """
    Memproses pembaruan profil dan status kepegawaian anggota (FR-MBR-02).
    """
    if request.method == 'POST':
        try:
            anggota = AnggotaController.perbaruiDataAnggota(
                bendahara=request.pengguna,
                anggota_id=anggota_id,
                data_update=request.POST,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Profil anggota {anggota.no_anggota} ({anggota.nama}) berhasil diperbarui.",
            )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal memperbarui data anggota: {pesan_err}")

    return redirect('data_anggota')


@login_wajib
def pengunduran_diri_router_view(request):
    """
    Rute cerdas untuk /pengunduran-diri/:
    - Jika diakses oleh ANGGOTA -> menampilkan formulir Ajukan Pengunduran Diri (WD-22)
    - Jika diakses oleh BENDAHARA / KETUA -> menampilkan halaman Verifikasi Pengunduran Diri (WD-17)
    """
    if request.pengguna.peran in (PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA):
        return verifikasi_pengunduran_diri_view(request)
    return ajukan_pengunduran_diri_view(request)


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def ajukan_pengunduran_diri_view(request):
    """
    Menampilkan & memproses Halaman Ajukan Pengunduran Diri untuk Anggota
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Ajukan Pengunduran Diri.png (WD-22).
    """
    anggota = getattr(request.pengguna, 'profil_anggota', None)
    if not anggota:
        messages.error(request, 'Profil keanggotaan tidak ditemukan pada akun ini.')
        return redirect('beranda_anggota')

    if request.method == 'POST':
        alasan_kategori = request.POST.get('alasan', '').strip()
        keterangan = request.POST.get('keterangan', '').strip()
        berkas_surat = request.FILES.get('surat_pengunduran_diri')

        try:
            resign = AnggotaController.ajukanPengunduranDiri(
                anggota=anggota,
                alasan_kategori=alasan_kategori,
                keterangan=keterangan,
                berkas_surat=berkas_surat,
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Permohonan pengunduran diri Anda telah berhasil diajukan (Estimasi Selisih Kliring: Rp {resign.selisih_akhir:,.0f}) "
                f"dan sedang menunggu verifikasi Bendahara.",
            )
            return redirect('pengunduran_diri')
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    # Ambil estimasi hak simpanan & sisa kewajiban saat ini untuk transparansi informasi
    estimasi_simpanan = TransaksiSimpanan.hitungTotalSimpananAnggota(anggota.id)
    estimasi_kewajiban = Pembiayaan.hitungSisaKewajibanAnggota(anggota.id)
    estimasi_selisih = (estimasi_simpanan - estimasi_kewajiban).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    riwayat_resign = PengunduranDiri.objects.filter(anggota=anggota).order_by('-id')
    pengajuan_aktif = riwayat_resign.filter(
        status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI
    ).first()

    pilihan_alasan = [
        'Pensiun / Purna Tugas',
        'Pindah Tugas / Mutasi Sekolah',
        'Keinginan Sendiri',
        'Kesehatan / Keluarga',
        'Lainnya',
    ]

    context = {
        'active_menu': 'pengunduran_diri',
        'anggota': anggota,
        'pilihan_alasan': pilihan_alasan,
        'estimasi_simpanan': estimasi_simpanan,
        'estimasi_kewajiban': estimasi_kewajiban,
        'estimasi_selisih': estimasi_selisih,
        'pengajuan_aktif': pengajuan_aktif,
        'riwayat_resign': riwayat_resign,
    }
    return render(request, 'anggota/ajukan_pengunduran_diri.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def verifikasi_pengunduran_diri_view(request):
    """
    Menampilkan Halaman Verifikasi Pengunduran Diri (2 Kolom: Daftar Pengajuan & Perhitungan Kliring)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Verifikasi Pengunduran Diri.png (WD-17).
    """
    qs_resign = PengunduranDiri.objects.select_related('anggota', 'bendahara').all().order_by(
        'status_pengajuan', '-tanggal_pengajuan', '-id'
    )

    paginator = Paginator(qs_resign, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Tentukan item pengajuan yang sedang dipilih untuk ditampilkan di panel kanan ("Perhitungan")
    selected_id = request.GET.get('pilih')
    resign_terpilih = None
    if selected_id and str(selected_id).isdigit():
        resign_terpilih = qs_resign.filter(pk=int(selected_id)).first()
    if not resign_terpilih:
        resign_terpilih = (
            qs_resign.filter(status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI).first()
            or qs_resign.first()
        )

    # Jika pengajuan masih MENUNGGU_VERIFIKASI, pastikan angka kliring sinkron real-time dengan transaksi terbaru
    rincian_simpanan_terpilih = []
    if resign_terpilih:
        if resign_terpilih.status_pengajuan == StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI:
            simpanan_terbaru = TransaksiSimpanan.hitungTotalSimpananAnggota(resign_terpilih.anggota_id)
            kewajiban_terbaru = Pembiayaan.hitungSisaKewajibanAnggota(resign_terpilih.anggota_id)
            if (
                simpanan_terbaru != resign_terpilih.total_hak_simpanan
                or kewajiban_terbaru != resign_terpilih.total_kewajiban_pembiayaan
            ):
                resign_terpilih = PengunduranDiri.hitungKliringResign(
                    pengunduran_id=resign_terpilih.id,
                    total_simpanan=simpanan_terbaru,
                    total_kewajiban=kewajiban_terbaru,
                )

        for js in JenisSimpanan.objects.all():
            saldo_js = TransaksiSimpanan.hitungSaldoBerjalan(resign_terpilih.anggota_id, js.id)
            rincian_simpanan_terpilih.append({
                'kode': js.kode,
                'nama': js.nama,
                'saldo': saldo_js,
            })

    context = {
        'active_menu': 'data_anggota',
        'page_obj': page_obj,
        'resign_terpilih': resign_terpilih,
        'rincian_simpanan_terpilih': rincian_simpanan_terpilih,
        'total_menunggu': qs_resign.filter(
            status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI
        ).count(),
    }
    return render(request, 'anggota/verifikasi_pengunduran_diri.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def proses_verifikasi_resign_view(request, pengunduran_id: int):
    """
    Memproses tombol 'Verifikasi', 'Tolak', atau 'Hitung Ulang' pada Halaman Verifikasi Pengunduran Diri.
    """
    if request.method == 'POST':
        keputusan = request.POST.get('keputusan', 'VERIFIKASI').upper()
        catatan = request.POST.get('catatan', '').strip()
        berita_acara_berkas = request.FILES.get('berita_acara')

        try:
            resign = AnggotaController.verifikasiPengunduranDiri(
                bendahara=request.pengguna,
                pengunduran_id=pengunduran_id,
                keputusan=keputusan,
                catatan=catatan,
                berita_acara_berkas=berita_acara_berkas,
                ip_address=_ambil_ip_klien(request),
            )
            if keputusan == 'TOLAK':
                messages.warning(
                    request,
                    f"Pengajuan pengunduran diri {resign.anggota.nama} telah ditolak dan status anggota kembali Aktif.",
                )
            elif keputusan == 'HITUNG_ULANG':
                messages.info(
                    request,
                    f"Perhitungan kliring {resign.anggota.nama} berhasil diperbarui (Selisih: Rp {resign.selisih_akhir:,.0f}).",
                )
            else:
                messages.success(
                    request,
                    f"Verifikasi kliring pengunduran diri {resign.anggota.nama} ({resign.anggota.no_anggota}) selesai. "
                    f"Status anggota kini Non-Aktif Keluar.",
                )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    return redirect(f"/anggota/verifikasi-resign/?pilih={pengunduran_id}")
