"""
PembiayaanController & Views Pembiayaan Syariah, Agunan, Persetujuan Kas (Two-Man Rule),
serta Pencatatan Realisasi Pencairan & Auto-Generate Kartu Angsuran
(Tahap 5 — UC-03, UC-04, UC-06, UC-07 | FR-FIN-01 s.d. FR-FIN-06, BR-01 s.d. BR-05).

Selaras dengan:
- 03_Class_Diagram_SI-KKPRIS.mmd (PembiayaanController)
- Sequence Diagram SQ-03 (Ajukan Pembiayaan & Agunan), SQ-05 (Setujui Pengeluaran Kas),
  dan SQ-06 (Catat Realisasi Pencairan Pembiayaan)
- 7 Wireframe Final Tahap 5:
  10. Ajukan Pembiayaan — Pilih Akad.png (WD-19)
  11. Ajukan Pembiayaan — Nominal & Tenor.png (WD-20)
  12. Ajukan Pembiayaan — Agunan.png (WD-21)
  13. Daftar Pembiayaan.png (WD-08)
  14. Detail Pembiayaan.png (WD-09)
  15. Persetujuan Kas.png (WD-18)
  16. Konfirmasi Persetujuan.png (Modal Konfirmasi Persetujuan Two-Man Rule)
"""

import os
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from koperasi.controllers.auth_controller import (
    _ambil_ip_klien,
    login_wajib,
    peran_wajib,
)
from koperasi.models import (
    Agunan,
    Anggota,
    AuditTrailLog,
    DetailRekapPotongGaji,
    JadwalAngsuran,
    JenisAgunanChoices,
    JenisAkad,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    KeputusanOtorisasiChoices,
    MetodeBayarChoices,
    MetodePencairanChoices,
    NamaAkadChoices,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PeranPenggunaChoices,
    PersetujuanPembiayaan,
    RealisasiPencairan,
    RekapPotongGaji,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)
from koperasi.utils import bersihkan_persen, bersihkan_rupiah


def _simpan_berkas_pembiayaan(berkas, subfolder: str, prefix: str) -> str:
    """Menyimpan berkas unggahan (Agunan / Bukti Transfer Pencairan) ke dalam MEDIA_ROOT."""
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
# CLASS CONTROLLER: PembiayaanController (Sesuai 03_Class_Diagram_SI-KKPRIS.mmd)
# ============================================================================

class PembiayaanController:
    """
    Controller Pengelolaan Pembiayaan Syariah, Agunan, Otorisasi Pengeluaran Kas (Two-Man Rule),
    dan Pencatatan Realisasi Pencairan SI-KKPRIS.
    Mencakup:
    - FR-FIN-01 & BR-01: Pengajuan Pembiayaan Syariah (Murabahah, Ijarah, Hawalah) tanggal 1-20
    - FR-FIN-02 & BR-02: Simulasi & Kalkulasi Margin Flat dengan Tenor maks. 72 bulan
    - FR-FIN-03 & BR-03: Validasi wajib unggah Agunan jika plafon > Rp 70.000.000
    - FR-FIN-04: Penomoran antrean pengajuan otomatis
    - FR-FIN-05 & BR-04: Otorisasi Pengeluaran Kas berjenjang (Two-Man Rule oleh Ketua)
    - FR-FIN-06 & BR-05: Pencatatan Realisasi Pencairan off-system & auto-generate Jadwal Angsuran
    """

    # PENDING PND-05: batas wajib agunan > Rp70 juta terkonfirmasi; syarat agunan lain belum.
    BATAS_AGUNAN_DEFAULT = Decimal('70000000.00')

    @staticmethod
    def ambilMarginSementara() -> Decimal:
        """
        Margin sementara dari settings.MARGIN_PERSEN_SEMENTARA (env).
        PENDING PND-01: nilai contoh, BUKAN ketetapan koperasi.
        """
        return settings.MARGIN_PERSEN_SEMENTARA

    @staticmethod
    def generateNoPembiayaan(tahun: int = None) -> str:
        """
        Membangkitkan Nomor Pembiayaan unik dengan format PMB-YYYY-NNN
        (contoh: PMB-2026-001, PMB-2026-002).
        """
        thn = tahun or date.today().year
        prefix = f"PMB-{thn}-"
        terakhir = (
            Pembiayaan.objects.filter(no_pembiayaan__startswith=prefix)
            .order_by('-no_pembiayaan')
            .first()
        )
        urutan = 1
        if terakhir:
            akhiran = terakhir.no_pembiayaan.replace(prefix, '').strip()
            if akhiran.isdigit():
                urutan = int(akhiran) + 1
        else:
            urutan = Pembiayaan.objects.count() + 1

        kandidat = f"{prefix}{urutan:03d}"
        while Pembiayaan.objects.filter(no_pembiayaan=kandidat).exists():
            urutan += 1
            kandidat = f"{prefix}{urutan:03d}"
        return kandidat

    @staticmethod
    def hitungNoAntrean(tanggal_pengajuan: date = None) -> int:
        """
        Menghitung nomor antrean pengajuan pembiayaan pada periode bulan berjalan (FR-FIN-04).
        """
        tgl = tanggal_pengajuan or date.today()
        jumlah_bulan_ini = Pembiayaan.objects.filter(
            tanggal_pengajuan__year=tgl.year,
            tanggal_pengajuan__month=tgl.month,
        ).count()
        return jumlah_bulan_ini + 1

    @classmethod
    def simulasiPembiayaan(
        cls,
        harga_pokok,
        tenor_bulan: int,
        margin_persen=None,
        batas_agunan: Decimal = None,
    ) -> dict:
        """
        Menghitung simulasi pembiayaan syariah metode margin flat berpresisi Decimal(15,2).
        """
        # PENDING PND-02: Hawalah dihitung dengan rumus margin flat yang sama dengan
        # Murabahah/Ijarah (tidak ada cabang khusus). Perlakuan Hawalah belum dikonfirmasi; JANGAN diubah.
        pokok = bersihkan_rupiah(harga_pokok, default='0.00')
        persen = bersihkan_persen(
            cls.ambilMarginSementara() if margin_persen in (None, '') else margin_persen
        )
        batas = batas_agunan or cls.BATAS_AGUNAN_DEFAULT
        hasil = Pembiayaan.hitungSimulasiMarginFlat(
            harga_pokok=pokok,
            margin_persen=persen,
            tenor_bulan=int(tenor_bulan),
        )
        hasil['wajib_agunan'] = pokok > batas
        hasil['batas_agunan'] = batas
        return hasil

    @classmethod
    def inputAgunan(
        cls,
        pembiayaan_id: int,
        data_agunan: dict,
        berkas_agunan=None,
        pengguna_id: int = None,
        ip_address: str = '127.0.0.1',
    ) -> Agunan:
        """
        Menyimpan data dan berkas dokumen agunan (BPKB / Sertifikat) untuk pembiayaan (SQ-03 — UC-04).
        """
        pembiayaan = get_object_or_404(Pembiayaan.objects.select_related('anggota'), pk=pembiayaan_id)
        jenis_agunan = (data_agunan.get('jenis_agunan') or JenisAgunanChoices.BPKB_MOTOR).strip()
        if jenis_agunan not in JenisAgunanChoices.values:
            jenis_agunan = JenisAgunanChoices.BPKB_MOTOR

        no_registrasi = (data_agunan.get('no_registrasi') or '').strip()
        if not no_registrasi:
            no_registrasi = f"REG-AGN-{pembiayaan.no_pembiayaan}"

        raw_taksiran = data_agunan.get('nilai_taksiran')
        nilai_taksiran = (
            bersihkan_rupiah(raw_taksiran)
            if raw_taksiran
            else pembiayaan.harga_pokok
        )
        if nilai_taksiran <= Decimal('0.00'):
            nilai_taksiran = pembiayaan.harga_pokok

        if berkas_agunan:
            berkas_url = _simpan_berkas_pembiayaan(berkas_agunan, 'agunan', pembiayaan.no_pembiayaan)
        elif data_agunan.get('berkas_url'):
            berkas_url = str(data_agunan['berkas_url']).strip()
        else:
            berkas_url = f"media/agunan/agunan_{pembiayaan.no_pembiayaan.lower()}.pdf"

        agunan = Agunan.simpanDataAgunan(
            pembiayaan_id=pembiayaan.id,
            data_agunan={
                'jenis_agunan': jenis_agunan,
                'no_registrasi': no_registrasi,
                'nilai_taksiran': nilai_taksiran,
                'berkas_url': berkas_url,
            },
        )

        actor_id = pengguna_id or pembiayaan.anggota.pengguna_id
        AuditTrailLog.catatLogAudit(
            pengguna_id=actor_id,
            aksi='INPUT_AGUNAN',
            nama_tabel='agunan',
            record_id=agunan.id,
            detail=(
                f"Lampiran agunan {agunan.get_jenis_agunan_display()} ({agunan.no_registrasi}) "
                f"taksiran Rp{agunan.nilai_taksiran:,.2f} untuk pembiayaan {pembiayaan.no_pembiayaan}."
            ),
            ip_address=ip_address,
        )
        return agunan

    @classmethod
    def ajukanPembiayaan(
        cls,
        anggota: Anggota,
        data_pengajuan: dict,
        berkas_agunan=None,
        ip_address: str = '127.0.0.1',
    ) -> Pembiayaan:
        """
        Memvalidasi dan menyimpan pengajuan pembiayaan syariah baru oleh Anggota
        (SQ-03 — UC-03 & UC-04, FR-FIN-01 s.d. FR-FIN-04, BR-01 s.d. BR-03).
        """
        if anggota.status != StatusAnggotaChoices.AKTIF:
            raise ValidationError(
                'Pengajuan pembiayaan hanya dapat dilakukan oleh anggota yang berstatus Aktif.'
            )

        # PENDING PND-04: limit pembiayaan per anggota dan batas jumlah pembiayaan aktif
        # per anggota BELUM divalidasi (rumus/tabel limit belum dikonfirmasi mitra).
        # 1. Validasi Jenis Akad Syariah (Murabahah / Ijarah / Hawalah)
        jenis_akad_id = data_pengajuan.get('jenis_akad_id')
        kode_akad = (data_pengajuan.get('kode_akad') or '').strip()
        nama_akad = (data_pengajuan.get('nama_akad') or '').strip().upper()

        akad = None
        if jenis_akad_id and str(jenis_akad_id).isdigit():
            akad = JenisAkad.objects.filter(pk=int(jenis_akad_id)).first()
        if not akad and kode_akad:
            akad = JenisAkad.objects.filter(kode__iexact=kode_akad).first()
        if not akad and nama_akad:
            akad = JenisAkad.objects.filter(nama=nama_akad).first()

        if not akad:
            raise ValidationError('Skema Akad Syariah (Murabahah / Ijarah / Hawalah) wajib dipilih.')

        # 2. Validasi Nominal Pokok & Tenor (Maks. 72 Bulan)
        harga_pokok = bersihkan_rupiah(
            data_pengajuan.get('harga_pokok') or data_pengajuan.get('nominal'),
            default='0.00',
        )
        if harga_pokok <= Decimal('0.00'):
            raise ValidationError('Nominal pembiayaan harus lebih besar dari Rp 0.')

        try:
            tenor_bulan = int(data_pengajuan.get('tenor_bulan') or data_pengajuan.get('tenor') or 0)
        except (TypeError, ValueError):
            raise ValidationError('Tenor pembiayaan tidak valid.')

        if not JenisAkad.validasiSkemaAkad(akad.id, tenor_bulan):
            raise ValidationError(
                f'Tenor pembiayaan untuk akad {akad.get_nama_display()} wajib berada pada rentang 1 s.d. {akad.tenor_maks_bulan} bulan.'
            )

        raw_margin = data_pengajuan.get('margin_persen')
        margin_persen = bersihkan_persen(
            cls.ambilMarginSementara() if raw_margin in (None, '') else raw_margin
        )
        tujuan_pembiayaan = (data_pengajuan.get('tujuan_pembiayaan') or '').strip()
        if not tujuan_pembiayaan:
            tujuan_pembiayaan = f"Pembiayaan {akad.get_nama_display()} Anggota {anggota.no_anggota}"

        # 3. Validasi Tanggal Pengajuan (Hanya dibuka tanggal 1 s.d. 20 setiap bulan — BR-01)
        tgl_pengajuan = data_pengajuan.get('tanggal_pengajuan') or date.today()
        if isinstance(tgl_pengajuan, str):
            tgl_pengajuan = date.fromisoformat(tgl_pengajuan)

        # 4. Validasi Wajib Agunan jika Nominal > Rp 70.000.000 (BR-03)
        batas_agunan = JenisAkad.ambilBatasPlafonAgunan(akad.id)
        wajib_agunan = harga_pokok > batas_agunan

        jenis_agunan = (data_pengajuan.get('jenis_agunan') or '').strip()
        no_registrasi_agunan = (data_pengajuan.get('no_registrasi') or '').strip()
        berkas_url_manual = (data_pengajuan.get('berkas_url') or '').strip()
        ada_input_agunan = bool(berkas_agunan or no_registrasi_agunan or berkas_url_manual or jenis_agunan)

        if wajib_agunan and not (berkas_agunan or no_registrasi_agunan or berkas_url_manual):
            raise ValidationError(
                f'Pembiayaan dengan nominal di atas Rp {batas_agunan:,.0f} wajib melampirkan dokumen agunan (BPKB / Sertifikat).'
            )

        no_pembiayaan = (
            (data_pengajuan.get('no_pembiayaan') or '').strip()
            or cls.generateNoPembiayaan(tgl_pengajuan.year)
        )
        no_antrean = int(data_pengajuan.get('no_antrean') or cls.hitungNoAntrean(tgl_pengajuan))

        with transaction.atomic():
            pembiayaan = Pembiayaan.simpanPengajuanBaru({
                'no_pembiayaan': no_pembiayaan,
                'anggota_id': anggota.id,
                'jenis_akad_id': akad.id,
                'tanggal_pengajuan': tgl_pengajuan,
                'harga_pokok': harga_pokok,
                'margin_persen': margin_persen,
                'tenor_bulan': tenor_bulan,
                'no_antrean': no_antrean,
                'tujuan_pembiayaan': tujuan_pembiayaan[:255],
            })

            if wajib_agunan or ada_input_agunan:
                cls.inputAgunan(
                    pembiayaan_id=pembiayaan.id,
                    data_agunan={
                        'jenis_agunan': jenis_agunan or JenisAgunanChoices.BPKB_MOTOR,
                        'no_registrasi': no_registrasi_agunan or f"BPKB-{pembiayaan.no_pembiayaan}",
                        'nilai_taksiran': data_pengajuan.get('nilai_taksiran') or harga_pokok,
                        'berkas_url': berkas_url_manual,
                    },
                    berkas_agunan=berkas_agunan,
                    pengguna_id=anggota.pengguna_id,
                    ip_address=ip_address,
                )

            AuditTrailLog.catatLogAudit(
                pengguna_id=anggota.pengguna_id,
                aksi='AJUKAN_PEMBIAYAAN',
                nama_tabel='pembiayaan',
                record_id=pembiayaan.id,
                detail=(
                    f"Pengajuan pembiayaan {pembiayaan.no_pembiayaan} (Antrean #{pembiayaan.no_antrean}) "
                    f"oleh {anggota.no_anggota} ({anggota.nama}) — Akad: {akad.nama}, "
                    f"Pokok: Rp{pembiayaan.harga_pokok:,.2f}, Tenor: {pembiayaan.tenor_bulan} bln, "
                    f"Angsuran: Rp{pembiayaan.angsuran_bulanan:,.2f}/bln."
                ),
                ip_address=ip_address,
            )
            return pembiayaan

    @classmethod
    def verifikasiBendahara(
        cls,
        pembiayaan_id: int,
        bendahara: Pengguna,
        keputusan: str = KeputusanOtorisasiChoices.DISETUJUI,
        catatan: str = '',
        ip_address: str = '127.0.0.1',
    ) -> PersetujuanPembiayaan:
        """
        Memproses verifikasi administrasi tahap 1 oleh Bendahara (Level 1) sebelum diteruskan
        ke antrean Persetujuan Kas Ketua (Level 2 — Two-Man Rule).
        """
        if bendahara.peran != PeranPenggunaChoices.BENDAHARA:
            raise ValidationError('Verifikasi administrasi tahap pertama hanya dapat dilakukan oleh Bendahara.')

        pembiayaan = get_object_or_404(Pembiayaan.objects.select_related('anggota', 'jenis_akad'), pk=pembiayaan_id)
        if pembiayaan.status not in (
            StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
            StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
        ):
            raise ValidationError(
                f'Pembiayaan {pembiayaan.no_pembiayaan} sudah berstatus {pembiayaan.get_status_display()} dan tidak dapat diverifikasi ulang.'
            )

        keputusan_norm = (keputusan or KeputusanOtorisasiChoices.DISETUJUI).strip().upper()
        if keputusan_norm not in KeputusanOtorisasiChoices.values:
            raise ValidationError('Keputusan verifikasi harus berupa DISETUJUI atau DITOLAK.')

        catatan_bersih = (catatan or '').strip() or (
            'Berkas pengajuan & kelayakan diverifikasi Bendahara, diteruskan ke Ketua.'
            if keputusan_norm == KeputusanOtorisasiChoices.DISETUJUI
            else 'Pengajuan pembiayaan ditolak pada tahap verifikasi Bendahara.'
        )

        with transaction.atomic():
            persetujuan = PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                pembiayaan_id=pembiayaan.id,
                pejabat_id=bendahara.id,
                keputusan=keputusan_norm,
                catatan=catatan_bersih[:255],
                level_persetujuan=1,
            )
            status_baru = (
                StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA
                if keputusan_norm == KeputusanOtorisasiChoices.DISETUJUI
                else StatusPembiayaanChoices.DITOLAK
            )
            Pembiayaan.perbaruiStatusPembiayaan(pembiayaan.id, status_baru)

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='VERIFIKASI_PEMBIAYAAN_BENDAHARA',
                nama_tabel='persetujuan_pembiayaan',
                record_id=persetujuan.id,
                detail=(
                    f"Verifikasi Level 1 Bendahara untuk {pembiayaan.no_pembiayaan} "
                    f"({pembiayaan.anggota.nama}): {keputusan_norm} -> Status: {status_baru}."
                ),
                ip_address=ip_address,
            )
            return persetujuan

    @classmethod
    def setujuiPengeluaranKas(
        cls,
        pembiayaan_id: int,
        pejabat: Pengguna,
        keputusan: str,
        catatan: str = '',
        ip_address: str = '127.0.0.1',
    ) -> PersetujuanPembiayaan:
        """
        Memproses otorisasi pengeluaran kas pembiayaan oleh Ketua Koperasi
        (SQ-05 — UC-06, FR-FIN-05, BR-04 Two-Man Rule).
        """
        if pejabat.peran != PeranPenggunaChoices.KETUA:
            raise ValidationError(
                'Otorisasi pengeluaran kas (Two-Man Rule) hanya dapat dieksekusi oleh Ketua Koperasi.'
            )

        pembiayaan = get_object_or_404(
            Pembiayaan.objects.select_related('anggota', 'jenis_akad'),
            pk=pembiayaan_id,
        )
        if pembiayaan.status not in (
            StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
            StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
        ):
            raise ValidationError(
                f'Pembiayaan {pembiayaan.no_pembiayaan} sudah berstatus {pembiayaan.get_status_display()} dan tidak dapat diproses ulang.'
            )

        keputusan_norm = (keputusan or '').strip().upper()
        if keputusan_norm not in KeputusanOtorisasiChoices.values:
            raise ValidationError('Keputusan otorisasi Ketua harus berupa DISETUJUI atau DITOLAK.')

        catatan_bersih = (catatan or '').strip() or (
            'Pengeluaran kas pembiayaan disetujui oleh Ketua Koperasi (Two-Man Rule).'
            if keputusan_norm == KeputusanOtorisasiChoices.DISETUJUI
            else 'Pengajuan pengeluaran kas pembiayaan ditolak oleh Ketua Koperasi.'
        )

        with transaction.atomic():
            persetujuan = PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                pembiayaan_id=pembiayaan.id,
                pejabat_id=pejabat.id,
                keputusan=keputusan_norm,
                catatan=catatan_bersih[:255],
                level_persetujuan=2,
            )
            status_baru = (
                StatusPembiayaanChoices.DISETUJUI_KETUA
                if keputusan_norm == KeputusanOtorisasiChoices.DISETUJUI
                else StatusPembiayaanChoices.DITOLAK
            )
            Pembiayaan.perbaruiStatusPembiayaan(pembiayaan.id, status_baru)

            AuditTrailLog.catatLogAudit(
                pengguna_id=pejabat.id,
                aksi='OTORISASI_KAS_KETUA',
                nama_tabel='persetujuan_pembiayaan',
                record_id=persetujuan.id,
                detail=(
                    f"Otorisasi Kas Ketua (Level 2) untuk {pembiayaan.no_pembiayaan} "
                    f"({pembiayaan.anggota.nama} - Rp{pembiayaan.harga_pokok:,.2f}): "
                    f"{keputusan_norm}. Catatan: {catatan_bersih}"
                ),
                ip_address=ip_address,
            )
            return persetujuan

    @classmethod
    def catatRealisasiPencairan(
        cls,
        pembiayaan_id: int,
        bendahara: Pengguna,
        data_realisasi: dict,
        berkas_bukti=None,
        ip_address: str = '127.0.0.1',
    ) -> RealisasiPencairan:
        """
        Mencatat realisasi pencairan dana off-system oleh Bendahara setelah disetujui Ketua,
        mengubah status pembiayaan menjadi AKTIF, dan otomatis membangkitkan Kartu Jadwal Angsuran
        (SQ-06 — UC-07, FR-FIN-06, BR-04, BR-05).
        """
        if bendahara.peran != PeranPenggunaChoices.BENDAHARA:
            raise ValidationError('Pencatatan realisasi pencairan hanya dapat dilakukan oleh Bendahara.')

        pembiayaan = get_object_or_404(
            Pembiayaan.objects.select_related('anggota', 'jenis_akad'),
            pk=pembiayaan_id,
        )
        if pembiayaan.status != StatusPembiayaanChoices.DISETUJUI_KETUA:
            raise ValidationError(
                'Pencairan hanya dapat direalisasikan untuk pembiayaan yang telah disetujui Ketua (Two-Man Rule).'
            )
        if RealisasiPencairan.objects.filter(pembiayaan=pembiayaan).exists():
            raise ValidationError(f'Realisasi pencairan untuk {pembiayaan.no_pembiayaan} sudah pernah dicatat.')

        metode_pencairan = (
            data_realisasi.get('metode_pencairan') or MetodePencairanChoices.TRANSFER_BANK
        ).strip().upper()
        if metode_pencairan not in MetodePencairanChoices.values:
            metode_pencairan = MetodePencairanChoices.TRANSFER_BANK

        nomor_referensi = (data_realisasi.get('nomor_referensi_bank') or '').strip()
        if not nomor_referensi:
            nomor_referensi = f"REF-{pembiayaan.no_pembiayaan}-{date.today():%Y%m%d}"

        tgl_realisasi = data_realisasi.get('tanggal_realisasi') or date.today()
        if isinstance(tgl_realisasi, str):
            tgl_realisasi = date.fromisoformat(tgl_realisasi)

        raw_nominal_cair = data_realisasi.get('nominal_cair')
        nominal_cair = (
            bersihkan_rupiah(raw_nominal_cair)
            if raw_nominal_cair
            else pembiayaan.harga_pokok
        )

        if berkas_bukti:
            bukti_url = _simpan_berkas_pembiayaan(berkas_bukti, 'pencairan', pembiayaan.no_pembiayaan)
        elif data_realisasi.get('bukti_transfer_url'):
            bukti_url = str(data_realisasi['bukti_transfer_url']).strip()
        else:
            bukti_url = f"media/pencairan/bukti_{pembiayaan.no_pembiayaan.lower()}.pdf"

        with transaction.atomic():
            realisasi = RealisasiPencairan.simpanRealisasiPencairan(
                pembiayaan_id=pembiayaan.id,
                data_realisasi={
                    'bendahara_id': bendahara.id,
                    'tanggal_realisasi': tgl_realisasi,
                    'metode_pencairan': metode_pencairan,
                    'nomor_referensi_bank': nomor_referensi,
                    'nominal_cair': nominal_cair,
                    'bukti_transfer_url': bukti_url,
                },
            )

            Pembiayaan.perbaruiStatusPembiayaan(
                pembiayaan_id=pembiayaan.id,
                status_baru=StatusPembiayaanChoices.AKTIF,
                tanggal_cair=tgl_realisasi,
            )

            # Auto-generate Kartu Jadwal Angsuran sejumlah tenor_bulan jika belum ada
            if not JadwalAngsuran.objects.filter(pembiayaan=pembiayaan).exists():
                JadwalAngsuran.generateJadwalAngsuran(
                    pembiayaan_id=pembiayaan.id,
                    tenor_bulan=pembiayaan.tenor_bulan,
                    harga_pokok=pembiayaan.harga_pokok,
                    margin_persen=pembiayaan.margin_persen,
                    tanggal_mulai=tgl_realisasi,
                )

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='REALISASI_PENCAIRAN_PEMBIAYAAN',
                nama_tabel='realisasi_pencairan',
                record_id=realisasi.id,
                detail=(
                    f"Realisasi pencairan off-system {pembiayaan.no_pembiayaan} ({pembiayaan.anggota.nama}) "
                    f"sebesar Rp{realisasi.nominal_cair:,.2f} via {realisasi.get_metode_pencairan_display()} "
                    f"(Ref: {realisasi.nomor_referensi_bank}). Kartu angsuran {pembiayaan.tenor_bulan} bulan diterbitkan."
                ),
                ip_address=ip_address,
            )
            return realisasi

    @classmethod
    def catatPembayaranAngsuran(
        cls,
        jadwal_id: int,
        bendahara: Pengguna,
        data_bayar: dict,
        ip_address: str = '127.0.0.1',
    ) -> PembayaranAngsuran:
        """
        Mencatat pembayaran angsuran bulanan (Cicilan Mandiri / Potong Gaji) serta
        otomatis melunasi kontrak pembiayaan apabila seluruh jadwal angsuran telah LUNAS.
        (Disiapkan sesuai Class Diagram untuk integrasi penuh Tahap 5 & Tahap 6).
        """
        jadwal = get_object_or_404(
            JadwalAngsuran.objects.select_related('pembiayaan', 'pembiayaan__anggota'),
            pk=jadwal_id,
        )
        no_kuitansi = (data_bayar.get('no_kuitansi') or '').strip()
        if not no_kuitansi:
            no_kuitansi = f"KUI-ANG-{jadwal.pembiayaan.id}-{jadwal.angsuran_ke:02d}-{timezone.now():%H%M%S}"

        nominal_bayar = bersihkan_rupiah(
            data_bayar.get('nominal_bayar') or jadwal.jumlah_angsuran
        )
        potongan_margin = bersihkan_rupiah(
            data_bayar.get('potongan_margin'), default='0.00'
        )  # PENDING PND-08
        metode_bayar = (data_bayar.get('metode_bayar') or MetodeBayarChoices.TUNAI).strip().upper()

        with transaction.atomic():
            pembayaran = PembayaranAngsuran.simpanPembayaranAngsuran(
                jadwal_id=jadwal.id,
                data_bayar={
                    'bendahara_id': bendahara.id,
                    'rekap_potong_gaji_id': data_bayar.get('rekap_potong_gaji_id'),
                    'no_kuitansi': no_kuitansi,
                    'nominal_bayar': nominal_bayar,
                    'potongan_margin': potongan_margin,
                    'metode_bayar': metode_bayar,
                    'nomor_referensi': data_bayar.get('nomor_referensi'),
                    'bukti_bayar_url': data_bayar.get('bukti_bayar_url'),
                },
            )
            masih_belum_lunas = JadwalAngsuran.objects.filter(
                pembiayaan=jadwal.pembiayaan,
                status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
            ).exists()
            if not masih_belum_lunas:
                Pembiayaan.perbaruiStatusPembiayaan(
                    jadwal.pembiayaan_id,
                    StatusPembiayaanChoices.LUNAS,
                )

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='BAYAR_ANGSURAN',
                nama_tabel='pembayaran_angsuran',
                record_id=pembayaran.id,
                detail=(
                    f"Pembayaran angsuran ke-{jadwal.angsuran_ke} [{pembayaran.no_kuitansi}] "
                    f"{jadwal.pembiayaan.no_pembiayaan} ({jadwal.pembiayaan.anggota.nama}) Rp{pembayaran.nominal_bayar:,.2f}."
                ),
                ip_address=ip_address,
            )
            return pembayaran

    @classmethod
    def konfirmasiPelunasanBatch(
        cls,
        rekap_id: int,
        bendahara: Pengguna,
        no_ref_bank: str,
        ip_address: str = '127.0.0.1',
    ) -> bool:
        """
        Mengonfirmasi pelunasan kolektif rekap potong gaji tanggal 24 secara batch
        (Disiapkan sesuai Class Diagram untuk integrasi penuh Tahap 6).
        """
        rekap = get_object_or_404(RekapPotongGaji, pk=rekap_id)
        with transaction.atomic():
            RekapPotongGaji.perbaruiStatusRekapKolektif(rekap.id, no_ref_bank)
            DetailRekapPotongGaji.tandaiRincianLunas(rekap.id)
            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='KONFIRMASI_PELUNASAN_KOLEKTIF',
                nama_tabel='rekap_potong_gaji',
                record_id=rekap.id,
                detail=f"Pelunasan kolektif rekap potong gaji {rekap.kode_rekap} (Ref: {no_ref_bank}).",
                ip_address=ip_address,
            )
            return True


# ============================================================================
# HELPER STATISTIK & PROGRESS BAR PEMBIAYAAN
# ============================================================================

def _rakit_baris_pembiayaan(qs_pembiayaan):
    """Menyiapkan struktur data baris pembiayaan lengkap dengan progress cicilan & agunan."""
    hasil = []
    for pmb in qs_pembiayaan:
        total_tenor = pmb.tenor_bulan or 1
        lunas_count = JadwalAngsuran.objects.filter(
            pembiayaan=pmb,
            status_bayar=StatusBayarAngsuranChoices.LUNAS,
        ).count()
        sisa_kewajiban = (
            JadwalAngsuran.objects.filter(
                pembiayaan=pmb,
                status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
            ).aggregate(sisa=Sum('jumlah_angsuran'))['sisa']
        )
        if sisa_kewajiban is None:
            sisa_kewajiban = (
                pmb.total_kewajiban
                if pmb.status != StatusPembiayaanChoices.LUNAS
                else Decimal('0.00')
            )
        persen_progress = int((lunas_count / total_tenor) * 100) if total_tenor > 0 else 0
        if pmb.status == StatusPembiayaanChoices.LUNAS:
            persen_progress = 100

        rincian_angsuran = Pembiayaan.hitungRincianAngsuran(
            harga_pokok=pmb.harga_pokok,
            margin_persen=pmb.margin_persen,
            tenor_bulan=total_tenor,
        )
        porsi_margin_bulanan = rincian_angsuran[0][1]
        agunan_utama = pmb.agunan_list.first()
        verifikasi_bendahara_log = pmb.persetujuan_list.filter(level_persetujuan=1).first()
        persetujuan_ketua_log = pmb.persetujuan_list.filter(level_persetujuan=2).first()

        hasil.append({
            'obj': pmb,
            'lunas_count': lunas_count,
            'total_tenor': total_tenor,
            'persen_progress': persen_progress,
            'sisa_kewajiban': sisa_kewajiban,
            'porsi_margin_bulanan': porsi_margin_bulanan,
            'agunan': agunan_utama,
            'wajib_agunan': pmb.harga_pokok > PembiayaanController.BATAS_AGUNAN_DEFAULT,
            'verifikasi_bendahara': verifikasi_bendahara_log,
            'persetujuan_ketua': persetujuan_ketua_log,
        })
    return hasil


# ============================================================================
# DJANGO VIEWS: Daftar Pembiayaan, Ajukan Pembiayaan (3 Step), Detail,
#               Persetujuan Kas Ketua & Realisasi Pencairan Bendahara
# ============================================================================

@login_wajib
def kelola_pembiayaan_router_view(request):
    """
    Rute utama /pembiayaan/:
    - BENDAHARA / KETUA -> menampilkan halaman Daftar Pembiayaan (WD-08)
    - ANGGOTA -> menampilkan halaman Pembiayaan Saya (daftar kontrak & pengajuan pribadi)
    """
    if request.pengguna.peran in (PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA):
        return daftar_pembiayaan_pengurus_view(request)
    return pembiayaan_saya_anggota_view(request)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def daftar_pembiayaan_pengurus_view(request):
    """
    Menampilkan Halaman Daftar Pembiayaan untuk Bendahara & Ketua
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Daftar Pembiayaan.png (WD-08).
    """
    # 1. Hitung 4 Kartu Statistik sesuai Daftar Pembiayaan.png:
    #    Total Pembiayaan, Pembiayaan Aktif, Total Angsuran, Sisa Pembiayaan
    qs_all = Pembiayaan.objects.exclude(status=StatusPembiayaanChoices.DITOLAK)
    total_pembiayaan = (
        qs_all.aggregate(total=Sum('harga_pokok'))['total'] or Decimal('0.00')
    )
    jumlah_kontrak_total = Pembiayaan.objects.count()

    qs_aktif = Pembiayaan.objects.filter(status=StatusPembiayaanChoices.AKTIF)
    jumlah_pembiayaan_aktif = qs_aktif.count()
    nominal_pembiayaan_aktif = (
        qs_aktif.aggregate(total=Sum('harga_pokok'))['total'] or Decimal('0.00')
    )

    total_angsuran_masuk = (
        PembayaranAngsuran.objects.aggregate(total=Sum('nominal_bayar'))['total']
        or Decimal('0.00')
    )
    jumlah_cicilan_masuk = PembayaranAngsuran.objects.count()

    sisa_pembiayaan = (
        JadwalAngsuran.objects.filter(
            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
        ).aggregate(total=Sum('jumlah_angsuran'))['total']
        or Decimal('0.00')
    )
    menunggu_tindakan_count = Pembiayaan.objects.filter(
        status__in=[
            StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
            StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
            StatusPembiayaanChoices.DISETUJUI_KETUA,
        ]
    ).count()

    # 2. Parameter Filter (Cari, Akad, Status)
    q = (request.GET.get('q') or '').strip()
    filter_akad = (request.GET.get('akad') or '').strip().upper()
    filter_status = (request.GET.get('status') or '').strip().upper()

    qs_pembiayaan = (
        Pembiayaan.objects.select_related('anggota', 'jenis_akad')
        .prefetch_related('agunan_list', 'persetujuan_list')
        .all()
        .order_by('-tanggal_pengajuan', 'no_antrean', '-id')
    )

    if q:
        qs_pembiayaan = qs_pembiayaan.filter(
            Q(no_pembiayaan__icontains=q)
            | Q(anggota__nama__icontains=q)
            | Q(anggota__no_anggota__icontains=q)
            | Q(tujuan_pembiayaan__icontains=q)
        )
    if filter_akad in NamaAkadChoices.values:
        qs_pembiayaan = qs_pembiayaan.filter(jenis_akad__nama=filter_akad)
    if filter_status in StatusPembiayaanChoices.values:
        qs_pembiayaan = qs_pembiayaan.filter(status=filter_status)

    # 3. Paginasi (Sesuai tombol Sebelumnya & Berikutnya pada Daftar Pembiayaan.png)
    paginator = Paginator(qs_pembiayaan, 6)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    daftar_baris = _rakit_baris_pembiayaan(page_obj.object_list)

    hari_ini = date.today()
    periode_buka = 1 <= hari_ini.day <= 20

    context = {
        'active_menu': 'pembiayaan_syariah',
        'total_pembiayaan': total_pembiayaan,
        'jumlah_kontrak_total': jumlah_kontrak_total,
        'jumlah_pembiayaan_aktif': jumlah_pembiayaan_aktif,
        'nominal_pembiayaan_aktif': nominal_pembiayaan_aktif,
        'total_angsuran_masuk': total_angsuran_masuk,
        'jumlah_cicilan_masuk': jumlah_cicilan_masuk,
        'sisa_pembiayaan': sisa_pembiayaan,
        'menunggu_tindakan_count': menunggu_tindakan_count,
        'q': q,
        'filter_akad': filter_akad,
        'filter_status': filter_status,
        'nama_akad_choices': NamaAkadChoices.choices,
        'status_pembiayaan_choices': StatusPembiayaanChoices.choices,
        'page_obj': page_obj,
        'daftar_baris': daftar_baris,
        'hari_ini': hari_ini,
        'periode_buka': periode_buka,
    }
    return render(request, 'pembiayaan/daftar_pembiayaan.html', context)


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def pembiayaan_saya_anggota_view(request):
    """
    Menampilkan Halaman Portal Mandiri 'Pembiayaan Saya' untuk Anggota.
    Memuat ringkasan pembiayaan milik anggota, status antrean & persetujuan,
    serta akses langsung ke Detail Pembiayaan & Ajukan Pembiayaan Baru.
    """
    anggota = getattr(request.pengguna, 'profil_anggota', None)
    if not anggota:
        messages.error(request, 'Profil keanggotaan tidak ditemukan.')
        return redirect('beranda_anggota')

    qs_milik = (
        Pembiayaan.objects.select_related('anggota', 'jenis_akad')
        .prefetch_related('agunan_list', 'persetujuan_list')
        .filter(anggota=anggota)
        .order_by('-tanggal_pengajuan', '-id')
    )
    daftar_baris = _rakit_baris_pembiayaan(qs_milik)

    total_pokok_anggota = (
        qs_milik.exclude(status=StatusPembiayaanChoices.DITOLAK).aggregate(
            total=Sum('harga_pokok')
        )['total']
        or Decimal('0.00')
    )
    sisa_kewajiban_anggota = Pembiayaan.hitungSisaKewajibanAnggota(anggota.id)
    total_terbayar_anggota = (
        PembayaranAngsuran.objects.filter(
            jadwal_angsuran__pembiayaan__anggota=anggota
        ).aggregate(total=Sum('nominal_bayar'))['total']
        or Decimal('0.00')
    )

    hari_ini = date.today()
    periode_buka = 1 <= hari_ini.day <= 20

    context = {
        'active_menu': 'pembiayaan_syariah',
        'anggota': anggota,
        'daftar_baris': daftar_baris,
        'total_pokok_anggota': total_pokok_anggota,
        'sisa_kewajiban_anggota': sisa_kewajiban_anggota,
        'total_terbayar_anggota': total_terbayar_anggota,
        'hari_ini': hari_ini,
        'periode_buka': periode_buka,
    }
    return render(request, 'pembiayaan/pembiayaan_saya.html', context)


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def ajukan_pembiayaan_view(request):
    """
    Menampilkan & memproses Wizard 3 Langkah 'Ajukan Pembiayaan' untuk Anggota
    Sesuai 3 Wireframe Final:
    - Step 1: Ajukan Pembiayaan — Pilih Akad.png (WD-19)
    - Step 2: Ajukan Pembiayaan — Nominal & Tenor.png (WD-20)
    - Step 3: Ajukan Pembiayaan — Agunan.png (WD-21)
    """
    anggota = getattr(request.pengguna, 'profil_anggota', None)
    if not anggota:
        messages.error(request, 'Profil keanggotaan tidak ditemukan pada akun ini.')
        return redirect('beranda_anggota')

    daftar_akad_db = list(JenisAkad.objects.all().order_by('id'))
    peta_deskripsi_akad = {
        NamaAkadChoices.MURABAHAH: {
            'judul': 'Murabahah',
            'ikon': '🛍',
            'tag': 'Jual Beli Barang (Margin Flat)',
            'deskripsi': (
                'Akad jual beli barang (kendaraan, elektronik, renovasi rumah, atau kebutuhan kerja) '
                'dengan harga pokok ditambah margin keuntungan tetap (flat) yang disepakati di awal.'
            ),
        },
        NamaAkadChoices.IJARAH: {
            'judul': 'Ijarah',
            'ikon': '🎓',
            'tag': 'Sewa Jasa / Manfaat (Ujrah Flat)',
            'deskripsi': (
                'Akad pembiayaan manfaat jasa (biaya pendidikan anak, kesehatan, pernikahan, atau sewa) '
                'dengan imbalan ujrah tetap per bulan hingga masa tenor berakhir.'
            ),
        },
        NamaAkadChoices.HAWALAH: {
            'judul': 'Hawalah',
            'ikon': '🔄',
            'tag': 'Pengalihan Utang / Take Over',
            'deskripsi': (
                'Akad pengalihan kewajiban atau pelunasan utang anggota dari pihak ketiga ke Koperasi '
                'Syariah KKPRIS dengan skema cicilan ujrah administrasi yang ringan dan transparan.'
            ),
        },
    }

    kartu_akad_list = []
    for ak in daftar_akad_db:
        meta = peta_deskripsi_akad.get(ak.nama, {
            'judul': ak.get_nama_display(),
            'ikon': '▤',
            'tag': 'Akad Syariah',
            'deskripsi': 'Skema pembiayaan syariah sesuai ketentuan Koperasi KKPRIS.',
        })
        kartu_akad_list.append({
            'id': ak.id,
            'kode': ak.kode,
            'nama': ak.nama,
            'judul': meta['judul'],
            'ikon': meta['ikon'],
            'tag': meta['tag'],
            'deskripsi': meta['deskripsi'],
            'tenor_maks': ak.tenor_maks_bulan,
            'plafon_tanpa_agunan': ak.plafon_tanpa_agunan,
        })

    step_aktif = request.GET.get('step', '1').strip()
    if step_aktif not in ('1', '2', '3'):
        step_aktif = '1'

    if request.method == 'POST':
        try:
            pembiayaan_baru = PembiayaanController.ajukanPembiayaan(
                anggota=anggota,
                data_pengajuan=request.POST,
                berkas_agunan=request.FILES.get('berkas_agunan'),
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Pengajuan pembiayaan {pembiayaan_baru.no_pembiayaan} ({pembiayaan_baru.jenis_akad.get_nama_display()}) "
                f"sebesar Rp {pembiayaan_baru.harga_pokok:,.0f} berhasil dikirim dengan Nomor Antrean #{pembiayaan_baru.no_antrean}.",
            )
            return redirect('detail_pembiayaan', pembiayaan_id=pembiayaan_baru.id)
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Pengajuan belum dapat diproses: {pesan_err}")
            if 'agunan' in pesan_err.lower():
                step_aktif = '3'
            elif 'tenor' in pesan_err.lower() or 'nominal' in pesan_err.lower():
                step_aktif = '2'
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan saat menyimpan pengajuan: {exc}")

    hari_ini = date.today()
    periode_buka = 1 <= hari_ini.day <= 20
    pilihan_tenor = [6, 10, 12, 18, 24, 36, 48, 60, 72]

    context = {
        'active_menu': 'ajukan_pembiayaan',
        'anggota': anggota,
        'kartu_akad_list': kartu_akad_list,
        'jenis_agunan_choices': JenisAgunanChoices.choices,
        'pilihan_tenor': pilihan_tenor,
        'step_aktif': step_aktif,
        'hari_ini': hari_ini,
        'periode_buka': periode_buka,
        'no_antrean_berikutnya': PembiayaanController.hitungNoAntrean(hari_ini),
        'default_margin_persen': PembiayaanController.ambilMarginSementara(),  # PENDING PND-01
        'batas_agunan': PembiayaanController.BATAS_AGUNAN_DEFAULT,
        'form_post': request.POST if request.method == 'POST' else {},
    }
    return render(request, 'pembiayaan/ajukan_pembiayaan.html', context)


@login_wajib
def detail_pembiayaan_view(request, pembiayaan_id: int):
    """
    Menampilkan Halaman Detail Pembiayaan (Ringkasan Akad, Jadwal Angsuran, Status Persetujuan,
    & Tombol Catat Realisasi Pencairan)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Detail Pembiayaan.png (WD-09).
    """
    pembiayaan = get_object_or_404(
        Pembiayaan.objects.select_related('anggota', 'jenis_akad'),
        pk=pembiayaan_id,
    )

    # Proteksi RBAC: Anggota hanya diizinkan melihat kontrak pembiayaan miliknya sendiri
    if request.pengguna.peran == PeranPenggunaChoices.ANGGOTA:
        anggota_login = getattr(request.pengguna, 'profil_anggota', None)
        if not anggota_login or pembiayaan.anggota_id != anggota_login.id:
            messages.error(request, 'Akses ditolak: Anda hanya dapat melihat detail pembiayaan milik Anda sendiri.')
            return redirect('kelola_pembiayaan')

    # Hitung porsi pokok & margin bulanan untuk tampilan Ringkasan Akad & Pratinjau Jadwal
    simulasi = Pembiayaan.hitungSimulasiMarginFlat(
        harga_pokok=pembiayaan.harga_pokok,
        margin_persen=pembiayaan.margin_persen,
        tenor_bulan=pembiayaan.tenor_bulan,
    )

    qs_jadwal = JadwalAngsuran.objects.filter(pembiayaan=pembiayaan).order_by('angsuran_ke')
    jadwal_sudah_terbit = qs_jadwal.exists()

    if jadwal_sudah_terbit:
        paginator = Paginator(qs_jadwal, 6)
        page_obj = paginator.get_page(request.GET.get('page', 1))
    else:
        # Jika pembiayaan belum dicairkan, tampilkan simulasi pratinjau jadwal angsuran
        # PENDING PND-07: pratinjau memakai aturan awal angsuran sementara (bulan berikutnya, tgl 24).
        pratinjau_list = []
        tgl_acuan = pembiayaan.tanggal_pengajuan or date.today()
        rincian_pratinjau = Pembiayaan.hitungRincianAngsuran(
            harga_pokok=pembiayaan.harga_pokok,
            margin_persen=pembiayaan.margin_persen,
            tenor_bulan=pembiayaan.tenor_bulan,
        )
        for ke, (pokok_ke, margin_ke, jumlah_ke) in enumerate(rincian_pratinjau, start=1):
            tahun = tgl_acuan.year + ((tgl_acuan.month - 1 + ke) // 12)
            bulan = ((tgl_acuan.month - 1 + ke) % 12) + 1
            pratinjau_list.append({
                'angsuran_ke': ke,
                'jatuh_tempo': date(tahun, bulan, 24),
                'porsi_pokok': pokok_ke,
                'porsi_margin': margin_ke,
                'jumlah_angsuran': jumlah_ke,
                'status_bayar': 'PRATINJAU',
                'get_status_bayar_display': 'Pratinjau (Menunggu Cair)',
            })
        paginator = Paginator(pratinjau_list, 6)
        page_obj = paginator.get_page(request.GET.get('page', 1))

    daftar_agunan = Agunan.ambilAgunanPembiayaan(pembiayaan.id)
    log_verifikasi_bendahara = pembiayaan.persetujuan_list.filter(level_persetujuan=1).first()
    log_persetujuan_ketua = pembiayaan.persetujuan_list.filter(level_persetujuan=2).first()
    realisasi_obj = getattr(pembiayaan, 'realisasi_pencairan', None)

    # Status 3 titik pada panel "Status Persetujuan" (Diajukan -> Disetujui Ketua -> Direalisasikan)
    step_diajukan_selesai = True
    step_ketua_selesai = pembiayaan.status in (
        StatusPembiayaanChoices.DISETUJUI_KETUA,
        StatusPembiayaanChoices.AKTIF,
        StatusPembiayaanChoices.LUNAS,
    )
    step_realisasi_selesai = pembiayaan.status in (
        StatusPembiayaanChoices.AKTIF,
        StatusPembiayaanChoices.LUNAS,
    ) or bool(realisasi_obj)

    context = {
        'active_menu': 'pembiayaan_syariah',
        'pembiayaan': pembiayaan,
        'simulasi': simulasi,
        'jadwal_sudah_terbit': jadwal_sudah_terbit,
        'page_obj': page_obj,
        'daftar_agunan': daftar_agunan,
        'log_verifikasi_bendahara': log_verifikasi_bendahara,
        'log_persetujuan_ketua': log_persetujuan_ketua,
        'realisasi_obj': realisasi_obj,
        'step_diajukan_selesai': step_diajukan_selesai,
        'step_ketua_selesai': step_ketua_selesai,
        'step_realisasi_selesai': step_realisasi_selesai,
        'metode_pencairan_choices': MetodePencairanChoices.choices,
        'hari_ini_iso': date.today().isoformat(),
    }
    return render(request, 'pembiayaan/detail_pembiayaan.html', context)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def verifikasi_bendahara_view(request, pembiayaan_id: int):
    """
    Memproses aksi Verifikasi Administrasi Level 1 oleh Bendahara (teruskan ke Ketua atau tolak).
    """
    if request.method == 'POST':
        keputusan = request.POST.get('keputusan', KeputusanOtorisasiChoices.DISETUJUI)
        catatan = request.POST.get('catatan', '')
        try:
            persetujuan = PembiayaanController.verifikasiBendahara(
                pembiayaan_id=pembiayaan_id,
                bendahara=request.pengguna,
                keputusan=keputusan,
                catatan=catatan,
                ip_address=_ambil_ip_klien(request),
            )
            if persetujuan.keputusan == KeputusanOtorisasiChoices.DISETUJUI:
                messages.success(
                    request,
                    f"Pengajuan {persetujuan.pembiayaan.no_pembiayaan} berhasil diverifikasi Bendahara dan diteruskan ke antrean Persetujuan Kas Ketua.",
                )
            else:
                messages.warning(
                    request,
                    f"Pengajuan {persetujuan.pembiayaan.no_pembiayaan} telah ditolak pada tahap verifikasi Bendahara.",
                )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, pesan_err)

    return redirect('detail_pembiayaan', pembiayaan_id=pembiayaan_id)


@peran_wajib(PeranPenggunaChoices.BENDAHARA)
def catat_realisasi_pencairan_view(request, pembiayaan_id: int):
    """
    Memproses form Modal 'Catat Realisasi Pencairan' pada halaman Detail Pembiayaan (WD-09)
    oleh Bendahara (SQ-06 — UC-07).
    """
    if request.method == 'POST':
        try:
            realisasi = PembiayaanController.catatRealisasiPencairan(
                pembiayaan_id=pembiayaan_id,
                bendahara=request.pengguna,
                data_realisasi={
                    'tanggal_realisasi': request.POST.get('tanggal_realisasi') or date.today(),
                    'metode_pencairan': request.POST.get('metode_pencairan'),
                    'nomor_referensi_bank': request.POST.get('nomor_referensi_bank'),
                    'nominal_cair': request.POST.get('nominal_cair'),
                },
                berkas_bukti=request.FILES.get('bukti_transfer'),
                ip_address=_ambil_ip_klien(request),
            )
            messages.success(
                request,
                f"Realisasi pencairan pembiayaan {realisasi.pembiayaan.no_pembiayaan} sebesar "
                f"Rp {realisasi.nominal_cair:,.0f} (Ref: {realisasi.nomor_referensi_bank}) berhasil dicatat. "
                f"Status kini Aktif Berjalan dan Kartu Jadwal Angsuran ({realisasi.pembiayaan.tenor_bulan} bulan) telah diterbitkan.",
            )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal mencatat realisasi pencairan: {pesan_err}")
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan saat mencatat realisasi: {exc}")

    return redirect('detail_pembiayaan', pembiayaan_id=pembiayaan_id)


@peran_wajib(PeranPenggunaChoices.KETUA, PeranPenggunaChoices.BENDAHARA)
def persetujuan_kas_view(request):
    """
    Menampilkan Halaman Persetujuan Kas & Modal Konfirmasi Persetujuan (Two-Man Rule)
    Sesuai Wireframe:
    - 01_Wireframe_Final_PNG/Persetujuan Kas.png (WD-18)
    - 01_Wireframe_Final_PNG/Konfirmasi Persetujuan.png
    """
    # 1. Hitung 3 Kartu Statistik sesuai Persetujuan Kas.png:
    #    Pengajuan Kas, Menunggu Persetujuan, Disetujui
    qs_all = Pembiayaan.objects.select_related('anggota', 'jenis_akad').prefetch_related(
        'agunan_list', 'persetujuan_list'
    )

    total_pengajuan_count = qs_all.count()
    total_pengajuan_nominal = (
        qs_all.aggregate(total=Sum('harga_pokok'))['total'] or Decimal('0.00')
    )

    qs_menunggu = qs_all.filter(
        status__in=[
            StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
            StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
        ]
    )
    menunggu_count = qs_menunggu.count()
    menunggu_nominal = (
        qs_menunggu.aggregate(total=Sum('harga_pokok'))['total'] or Decimal('0.00')
    )

    qs_disetujui = qs_all.filter(
        status__in=[
            StatusPembiayaanChoices.DISETUJUI_KETUA,
            StatusPembiayaanChoices.AKTIF,
            StatusPembiayaanChoices.LUNAS,
        ]
    )
    disetujui_count = qs_disetujui.count()
    disetujui_nominal = (
        qs_disetujui.aggregate(total=Sum('harga_pokok'))['total'] or Decimal('0.00')
    )

    # 2. Urutkan agar yang menunggu persetujuan Ketua tampil paling atas
    daftar_semua = list(qs_all.order_by('-tanggal_pengajuan', 'no_antrean', '-id'))
    prioritas_status = {
        StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA: 0,
        StatusPembiayaanChoices.MENUNGGU_VERIFIKASI: 1,
        StatusPembiayaanChoices.DISETUJUI_KETUA: 2,
        StatusPembiayaanChoices.AKTIF: 3,
        StatusPembiayaanChoices.LUNAS: 4,
        StatusPembiayaanChoices.DITOLAK: 5,
    }
    daftar_semua.sort(key=lambda x: (prioritas_status.get(x.status, 9), -x.id))

    paginator = Paginator(daftar_semua, 6)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    daftar_baris = _rakit_baris_pembiayaan(page_obj.object_list)

    context = {
        'active_menu': 'persetujuan_kas',
        'total_pengajuan_count': total_pengajuan_count,
        'total_pengajuan_nominal': total_pengajuan_nominal,
        'menunggu_count': menunggu_count,
        'menunggu_nominal': menunggu_nominal,
        'disetujui_count': disetujui_count,
        'disetujui_nominal': disetujui_nominal,
        'page_obj': page_obj,
        'daftar_baris': daftar_baris,
    }
    return render(request, 'pembiayaan/persetujuan_kas.html', context)


@peran_wajib(PeranPenggunaChoices.KETUA)
def proses_persetujuan_kas_view(request, pembiayaan_id: int):
    """
    Memproses tombol 'Setujui' atau 'Tolak' dari halaman Persetujuan Kas / Modal Konfirmasi Persetujuan
    oleh Ketua Koperasi (Two-Man Rule — SQ-05, UC-06).
    """
    if request.method == 'POST':
        keputusan = request.POST.get('keputusan', KeputusanOtorisasiChoices.DISETUJUI)
        catatan = request.POST.get('catatan', '')
        try:
            persetujuan = PembiayaanController.setujuiPengeluaranKas(
                pembiayaan_id=pembiayaan_id,
                pejabat=request.pengguna,
                keputusan=keputusan,
                catatan=catatan,
                ip_address=_ambil_ip_klien(request),
            )
            if persetujuan.keputusan == KeputusanOtorisasiChoices.DISETUJUI:
                messages.success(
                    request,
                    f"Pengeluaran kas untuk pembiayaan {persetujuan.pembiayaan.no_pembiayaan} "
                    f"({persetujuan.pembiayaan.anggota.nama} — Rp {persetujuan.pembiayaan.harga_pokok:,.0f}) "
                    f"telah DISETUJUI oleh Ketua. Bendahara kini dapat mencatat realisasi pencairan.",
                )
            else:
                messages.warning(
                    request,
                    f"Permohonan pengeluaran kas pembiayaan {persetujuan.pembiayaan.no_pembiayaan} "
                    f"({persetujuan.pembiayaan.anggota.nama}) telah DITOLAK oleh Ketua.",
                )
        except ValidationError as exc:
            pesan_err = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            messages.error(request, f"Gagal memproses otorisasi kas: {pesan_err}")

    next_url = request.POST.get('next') or 'persetujuan_kas'
    return redirect(next_url)


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def ekspor_pembiayaan_excel_view(request):
    """
    Mengekspor daftar kontrak pembiayaan syariah ke berkas Microsoft Excel (.xlsx)
    sesuai tombol 'Ekspor' pada Wireframe Daftar Pembiayaan.png (WD-08).
    """
    q = (request.GET.get('q') or '').strip()
    filter_akad = (request.GET.get('akad') or '').strip().upper()
    filter_status = (request.GET.get('status') or '').strip().upper()

    qs = Pembiayaan.objects.select_related('anggota', 'jenis_akad').all().order_by(
        '-tanggal_pengajuan', 'no_antrean', '-id'
    )
    if q:
        qs = qs.filter(
            Q(no_pembiayaan__icontains=q)
            | Q(anggota__nama__icontains=q)
            | Q(anggota__no_anggota__icontains=q)
        )
    if filter_akad in NamaAkadChoices.values:
        qs = qs.filter(jenis_akad__nama=filter_akad)
    if filter_status in StatusPembiayaanChoices.values:
        qs = qs.filter(status=filter_status)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Daftar Pembiayaan'

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )

    ws.append(['REKAPITULASI DAFTAR PEMBIAYAAN SYARIAH — SI-KKPRIS SMKN 1 KOTA SOLOK'])
    ws['A1'].font = Font(bold=True, size=12)
    ws.append([f'Tanggal Unduh: {date.today():%d/%m/%Y}'])
    ws.append([])

    headers = [
        'No',
        'No. Pembiayaan',
        'Antrean',
        'Tanggal Pengajuan',
        'No. Anggota',
        'Nama Anggota',
        'Akad Syariah',
        'Harga Pokok (Rp)',
        'Total Margin/Ujrah (Rp)',
        'Total Kewajiban (Rp)',
        'Tenor (Bln)',
        'Angsuran/Bulan (Rp)',
        'Status',
        'Tujuan Pembiayaan',
    ]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    for idx, pmb in enumerate(qs, start=1):
        row_data = [
            idx,
            pmb.no_pembiayaan,
            pmb.no_antrean,
            pmb.tanggal_pengajuan.strftime('%d/%m/%Y'),
            pmb.anggota.no_anggota,
            pmb.anggota.nama,
            pmb.jenis_akad.get_nama_display(),
            float(pmb.harga_pokok),
            float(pmb.total_margin),
            float(pmb.total_kewajiban),
            pmb.tenor_bulan,
            float(pmb.angsuran_bulanan),
            pmb.get_status_display(),
            pmb.tujuan_pembiayaan,
        ]
        ws.append(row_data)
        curr_row = 4 + idx
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=curr_row, column=col_idx)
            c.border = thin_border
            if col_idx in (8, 9, 10, 12):
                c.number_format = '#,##0.00'

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 12), 40)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Daftar_Pembiayaan_SI-KKPRIS_{date.today():%Y%m%d}.xlsx"
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
