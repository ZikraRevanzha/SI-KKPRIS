"""
Unit Test untuk 16 Model & Aturan Bisnis Utama SI-KKPRIS (SRS v4.0).
"""

from datetime import date
from decimal import Decimal
from django.contrib.staticfiles.finders import find
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.template.loader import get_template
from django.test import TestCase
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
    KanalNotifikasiChoices,
    KeputusanOtorisasiChoices,
    MetodeBayarChoices,
    MetodePencairanChoices,
    NotifikasiTagihan,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PengunduranDiri,
    PersetujuanPembiayaan,
    RealisasiPencairan,
    RekapPotongGaji,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)


class SIKKPRISModelsTestCase(TestCase):
    def setUp(self):
        call_command('seed_master', verbosity=0)
        self.ketua = Pengguna.objects.get(username='ketua')
        self.bendahara = Pengguna.objects.get(username='bendahara')
        self.anggota = Anggota.objects.get(no_anggota='KKP-2026-001')

    def test_01_autentikasi_dan_audit_log(self):
        user_valid = Pengguna.verifikasiKredensial('bendahara', 'Kkpris2026!')
        self.assertIsNotNone(user_valid)
        self.assertEqual(user_valid.peran, 'BENDAHARA')

        log = AuditTrailLog.catatLogAudit(
            pengguna_id=self.bendahara.id,
            aksi='LOGIN',
            nama_tabel='pengguna',
            record_id=self.bendahara.id,
            detail='Login berhasil ke sistem SI-KKPRIS',
        )
        self.assertEqual(AuditTrailLog.objects.count(), 1)
        self.assertEqual(log.nama_tabel, 'pengguna')

    def test_02_simpanan_terkunci_vs_sukarela(self):
        spk = JenisSimpanan.objects.get(kode='SPK')
        shr = JenisSimpanan.objects.get(kode='SHR')

        # Setor Simpanan Pokok Rp350.000
        TransaksiSimpanan.simpanMutasiSimpanan({
            'anggota_id': self.anggota.id,
            'jenis_simpanan_id': spk.id,
            'bendahara_id': self.bendahara.id,
            'no_kuitansi': 'KUI-SMP-001',
            'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
            'nominal': Decimal('350000.00'),
        })

        # Percobaan tarik Simpanan Pokok wajib ditolak (dapat_ditarik = False)
        with self.assertRaises(ValidationError):
            TransaksiSimpanan.simpanMutasiSimpanan({
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': spk.id,
                'bendahara_id': self.bendahara.id,
                'no_kuitansi': 'KUI-SMP-002',
                'jenis_transaksi': JenisTransaksiSimpananChoices.TARIK,
                'nominal': Decimal('100000.00'),
            })

        # Setor & Tarik Simpanan Hari Raya (dapat_ditarik = True)
        TransaksiSimpanan.simpanMutasiSimpanan({
            'anggota_id': self.anggota.id,
            'jenis_simpanan_id': shr.id,
            'bendahara_id': self.bendahara.id,
            'no_kuitansi': 'KUI-SMP-003',
            'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
            'nominal': Decimal('500000.00'),
        })
        mutasi_tarik = TransaksiSimpanan.simpanMutasiSimpanan({
            'anggota_id': self.anggota.id,
            'jenis_simpanan_id': shr.id,
            'bendahara_id': self.bendahara.id,
            'no_kuitansi': 'KUI-SMP-004',
            'jenis_transaksi': JenisTransaksiSimpananChoices.TARIK,
            'nominal': Decimal('200000.00'),
        })
        self.assertEqual(mutasi_tarik.saldo_sesudah, Decimal('300000.00'))
        self.assertEqual(
            TransaksiSimpanan.hitungTotalSimpananAnggota(self.anggota.id),
            Decimal('650000.00'),
        )

    def test_03_alur_pembiayaan_agunan_approval_realisasi_rekap_dan_resign(self):
        akad_mrb = JenisAkad.objects.get(kode='AKD-MRB')

        # Pengajuan di luar tanggal 1-20 wajib ditolak
        with self.assertRaises(ValidationError):
            Pembiayaan.simpanPengajuanBaru({
                'no_pembiayaan': 'PMB-2026-ERR',
                'anggota_id': self.anggota.id,
                'jenis_akad_id': akad_mrb.id,
                'tanggal_pengajuan': date(2026, 11, 25),
                'harga_pokok': Decimal('12000000.00'),
                'margin_persen': Decimal('1.00'),
                'tenor_bulan': 12,
                'no_antrean': 1,
                'tujuan_pembiayaan': 'Pembelian Laptop Kerja',
            })

        # Pengajuan valid pada tanggal 15
        pembiayaan = Pembiayaan.simpanPengajuanBaru({
            'no_pembiayaan': 'PMB-2026-001',
            'anggota_id': self.anggota.id,
            'jenis_akad_id': akad_mrb.id,
            'tanggal_pengajuan': date(2026, 11, 15),
            'harga_pokok': Decimal('80000000.00'),
            'margin_persen': Decimal('1.00'),
            'tenor_bulan': 10,
            'no_antrean': 1,
            'tujuan_pembiayaan': 'Renovasi Rumah (> Rp70 Juta)',
        })
        self.assertEqual(pembiayaan.total_margin, Decimal('8000000.00'))
        self.assertEqual(pembiayaan.total_kewajiban, Decimal('88000000.00'))
        self.assertEqual(pembiayaan.angsuran_bulanan, Decimal('8800000.00'))

        # Tambah Agunan karena plafon > Rp70.000.000
        agunan = Agunan.simpanDataAgunan(pembiayaan.id, {
            'jenis_agunan': JenisAgunanChoices.BPKB_MOBIL,
            'no_registrasi': 'BA-1234-PK',
            'nilai_taksiran': Decimal('120000000.00'),
            'berkas_url': 'media/agunan/bpkb_ba1234pk.pdf',
        })
        self.assertEqual(agunan.pembiayaan_id, pembiayaan.id)

        # Two-Man Rule: Realisasi sebelum disetujui Ketua harus gagal
        with self.assertRaises(ValidationError):
            RealisasiPencairan.simpanRealisasiPencairan(pembiayaan.id, {
                'bendahara_id': self.bendahara.id,
                'metode_pencairan': MetodePencairanChoices.TRANSFER_BANK,
                'nomor_referensi_bank': 'REF-BNI-001',
                'nominal_cair': Decimal('80000000.00'),
                'bukti_transfer_url': 'media/pencairan/ref001.pdf',
            })

        # Persetujuan Ketua (Two-Man Rule)
        PersetujuanPembiayaan.simpanKeputusanOtorisasi(
            pembiayaan_id=pembiayaan.id,
            pejabat_id=self.ketua.id,
            keputusan=KeputusanOtorisasiChoices.DISETUJUI,
            catatan='Likuiditas kas mencukupi, disetujui cair.',
            level_persetujuan=2,
        )
        Pembiayaan.perbaruiStatusPembiayaan(pembiayaan.id, StatusPembiayaanChoices.DISETUJUI_KETUA)

        # Realisasi Pencairan Off-System oleh Bendahara
        realisasi = RealisasiPencairan.simpanRealisasiPencairan(pembiayaan.id, {
            'bendahara_id': self.bendahara.id,
            'tanggal_realisasi': date(2026, 11, 16),
            'metode_pencairan': MetodePencairanChoices.TRANSFER_BANK,
            'nomor_referensi_bank': 'REF-BNI-001',
            'nominal_cair': Decimal('80000000.00'),
            'bukti_transfer_url': 'media/pencairan/ref001.pdf',
        })
        self.assertEqual(realisasi.nominal_cair, Decimal('80000000.00'))
        Pembiayaan.perbaruiStatusPembiayaan(
            pembiayaan.id,
            StatusPembiayaanChoices.AKTIF,
            tanggal_cair=date(2026, 11, 16),
        )

        # Generate 10 Jadwal Angsuran
        jadwal_list = JadwalAngsuran.generateJadwalAngsuran(
            pembiayaan_id=pembiayaan.id,
            tenor_bulan=10,
            porsi_pokok=Decimal('8000000.00'),
            porsi_margin=Decimal('800000.00'),
            tanggal_mulai=date(2026, 11, 16),
        )
        self.assertEqual(len(jadwal_list), 10)
        jadwal_pertama = JadwalAngsuran.objects.get(pembiayaan=pembiayaan, angsuran_ke=1)

        # Log Notifikasi Tagihan (Tgl 10)
        NotifikasiTagihan.simpanLogNotifikasi({
            'anggota_id': self.anggota.id,
            'jadwal_angsuran_id': jadwal_pertama.id,
            'bendahara_id': self.bendahara.id,
            'kanal_kirim': KanalNotifikasiChoices.WHATSAPP,
            'tujuan_kirim': self.anggota.no_hp,
            'isi_pesan': 'Pengingat tagihan angsuran ke-1 SI-KKPRIS.',
        })
        self.assertEqual(NotifikasiTagihan.objects.count(), 1)

        # Rekap Potong Gaji Tanggal 24 & Detail Rekap
        rekap = RekapPotongGaji.buatHeaderRekap('2026-12', self.bendahara.id)
        DetailRekapPotongGaji.simpanRincianRekapAnggota(rekap.id, [{
            'anggota_id': self.anggota.id,
            'jadwal_angsuran_id': jadwal_pertama.id,
            'nominal_simpanan_wajib': Decimal('150000.00'),
            'nominal_simpanan_sukarela': Decimal('0.00'),
            'nominal_angsuran': Decimal('8800000.00'),
            'subtotal_potongan': Decimal('8950000.00'),
        }])
        self.assertEqual(DetailRekapPotongGaji.objects.count(), 1)

        # Pembayaran Angsuran ke-1
        bayar = PembayaranAngsuran.simpanPembayaranAngsuran(jadwal_pertama.id, {
            'bendahara_id': self.bendahara.id,
            'rekap_potong_gaji_id': rekap.id,
            'no_kuitansi': 'KUI-ANG-001',
            'nominal_bayar': Decimal('8800000.00'),
            'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
        })
        jadwal_pertama.refresh_from_db()
        self.assertEqual(jadwal_pertama.status_bayar, StatusBayarAngsuranChoices.LUNAS)
        self.assertEqual(bayar.nominal_bayar, Decimal('8800000.00'))

        # Pengunduran Diri & Kliring Otomatis (Sisa 9 bulan x 8.800.000 = 79.200.000)
        resign = PengunduranDiri.simpanPermohonanResign(
            anggota_id=self.anggota.id,
            alasan='Pindah Tugas ke Provinsi Lain',
            surat_url='media/resign/surat_budi.pdf',
        )
        self.anggota.refresh_from_db()
        self.assertEqual(self.anggota.status, StatusAnggotaChoices.PROSES_RESIGN)
        self.assertEqual(resign.total_kewajiban_pembiayaan, Decimal('79200000.00'))

    def test_04_auth_controller_rbac_dan_dashboard_ui(self):
        # 1. Akses tanpa login diarahkan ke /login/
        resp = self.client.get('/dashboard/')
        self.assertRedirects(resp, '/login/')

        # 2. Login Bendahara & akses Dashboard Pengurus
        resp_login_bendahara = self.client.post(
            '/login/',
            {'username': 'bendahara', 'password': 'Kkpris2026!'},
            follow=True,
        )
        self.assertEqual(resp_login_bendahara.status_code, 200)
        self.assertContains(resp_login_bendahara, 'Total Anggota')
        self.assertContains(resp_login_bendahara, 'Tren Simpanan')

        # 3. Proteksi RBAC: Bendahara mencoba akses /beranda/ milik Anggota -> ditolak & diarahkan ke /dashboard/
        resp_forbidden = self.client.get('/beranda/', follow=True)
        self.assertContains(resp_forbidden, 'Akses ditolak')

        # 4. Logout Bendahara
        self.client.get('/logout/')

        # 5. Login Anggota menggunakan Nomor Anggota (KKP-2026-001) & akses Beranda Anggota
        resp_login_anggota = self.client.post(
            '/login/',
            {'username': 'KKP-2026-001', 'password': 'Kkpris2026!'},
            follow=True,
        )
        self.assertEqual(resp_login_anggota.status_code, 200)
        self.assertContains(resp_login_anggota, 'Beranda Anggota')
        self.assertContains(resp_login_anggota, 'Status Pembiayaan')
        self.assertContains(resp_login_anggota, 'Riwayat Terakhir')

        # 6. Proteksi RBAC: Anggota mencoba akses /dashboard/ pengurus -> ditolak & diarahkan ke /beranda/
        resp_anggota_forbidden = self.client.get('/dashboard/', follow=True)
        self.assertContains(resp_anggota_forbidden, 'Akses ditolak')

    def test_05_integrasi_frontend_templates_dan_static(self):
        """Memastikan pemisahan folder backend/ & frontend/ terhubung sempurna."""
        # 1. Verifikasi resolusi template di frontend/templates/
        for tpl_name in (
            'base.html',
            'auth/login.html',
            'dashboard/dashboard_pengurus.html',
            'dashboard/beranda_anggota.html',
            'dashboard/modul_terjadwal.html',
        ):
            tpl = get_template(tpl_name)
            self.assertIn('frontend', str(tpl.origin.name).replace('\\', '/'))

        # 2. Verifikasi resolusi aset statis di frontend/static/
        css_path = find('css/style.css')
        self.assertIsNotNone(css_path)
        self.assertIn('frontend/static/css/style.css', css_path.replace('\\', '/'))

        # 3. Verifikasi HTTP render GET /login/ beserta referensi stylesheet
        resp_login = self.client.get('/login/')
        self.assertEqual(resp_login.status_code, 200)
        self.assertTemplateUsed(resp_login, 'auth/login.html')
        self.assertContains(resp_login, 'css/style.css')

