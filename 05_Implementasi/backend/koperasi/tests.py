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

    def test_06_anggota_controller_dan_kliring_resign_tahap_3(self):
        """Menguji fitur Tahap 3: Data Anggota, Form Anggota Baru, Ajukan & Verifikasi Resign."""
        # 1. Login sebagai Bendahara & buka halaman Data Anggota (WD-03 & WD-04)
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})
        resp_list = self.client.get('/anggota/')
        self.assertEqual(resp_list.status_code, 200)
        self.assertTemplateUsed(resp_list, 'anggota/data_anggota.html')
        self.assertContains(resp_list, 'Form Anggota Baru')
        self.assertContains(resp_list, 'KKP-2026-001')

        # 2. Tambah Anggota Baru oleh Bendahara (Setor Lunas Simpanan Pokok Rp350.000 & Khusus Rp500.000)
        resp_tambah = self.client.post(
            '/anggota/tambah/',
            {
                'nama': 'Rina Marlina, S.Pd.',
                'nik': '1372019988770009',
                'no_anggota': 'KKP-2026-009',
                'status_kepegawaian': 'PNS',
                'masa_dinas_tahun': 8,
                'no_hp': '081299887766',
                'tanggal_masuk': '2026-11-16',
                'cicilan_simpanan_pokok': 'LUNAS_AWAL',
                'cicilan_simpanan_khusus': 'LUNAS_AWAL',
            },
            follow=True,
        )
        self.assertEqual(resp_tambah.status_code, 200)
        anggota_rina = Anggota.objects.get(no_anggota='KKP-2026-009')
        self.assertEqual(anggota_rina.nama, 'Rina Marlina, S.Pd.')
        self.assertEqual(
            TransaksiSimpanan.hitungTotalSimpananAnggota(anggota_rina.id),
            Decimal('850000.00'),
        )

        # 3. Edit Profil Anggota oleh Bendahara
        resp_edit = self.client.post(
            f'/anggota/{anggota_rina.id}/edit/',
            {
                'nama': 'Rina Marlina, S.Pd., M.Pd.',
                'nik': '1372019988770009',
                'status_kepegawaian': 'PNS',
                'masa_dinas_tahun': 9,
                'no_hp': '081299887700',
            },
            follow=True,
        )
        self.assertEqual(resp_edit.status_code, 200)
        anggota_rina.refresh_from_db()
        self.assertEqual(anggota_rina.nama, 'Rina Marlina, S.Pd., M.Pd.')
        self.assertEqual(anggota_rina.masa_dinas_tahun, 9)

        # 4. Logout Bendahara, Login sebagai Anggota Rina & Ajukan Pengunduran Diri (WD-22)
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'KKP-2026-009', 'password': 'Kkpris2026!'})

        resp_form_resign = self.client.get('/pengunduran-diri/')
        self.assertEqual(resp_form_resign.status_code, 200)
        self.assertTemplateUsed(resp_form_resign, 'anggota/ajukan_pengunduran_diri.html')
        self.assertContains(
            resp_form_resign,
            'Total simpanan dikurangi sisa pembiayaan akan dihitung oleh Bendahara',
        )

        resp_submit_resign = self.client.post(
            '/pengunduran-diri/',
            {
                'alasan': 'Pindah Tugas / Mutasi Sekolah',
                'keterangan': 'Mutasi ke SMKN 2 Padang TMT Desember 2026',
            },
            follow=True,
        )
        self.assertEqual(resp_submit_resign.status_code, 200)
        anggota_rina.refresh_from_db()
        self.assertEqual(anggota_rina.status, StatusAnggotaChoices.PROSES_RESIGN)

        resign_obj = PengunduranDiri.objects.get(anggota=anggota_rina)
        self.assertEqual(resign_obj.total_hak_simpanan, Decimal('850000.00'))
        self.assertEqual(resign_obj.total_kewajiban_pembiayaan, Decimal('0.00'))
        self.assertEqual(resign_obj.selisih_akhir, Decimal('850000.00'))

        # 5. Logout Anggota, Login Bendahara & Verifikasi Kliring Pengunduran Diri (WD-17)
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})

        resp_verif_page = self.client.get(f'/anggota/verifikasi-resign/?pilih={resign_obj.id}')
        self.assertEqual(resp_verif_page.status_code, 200)
        self.assertTemplateUsed(resp_verif_page, 'anggota/verifikasi_pengunduran_diri.html')
        self.assertContains(resp_verif_page, 'Dikembalikan ke anggota / Disetor anggota')

        resp_verif_post = self.client.post(
            f'/anggota/verifikasi-resign/{resign_obj.id}/proses/',
            {'keputusan': 'VERIFIKASI'},
            follow=True,
        )
        self.assertEqual(resp_verif_post.status_code, 200)

        resign_obj.refresh_from_db()
        anggota_rina.refresh_from_db()
        anggota_rina.pengguna.refresh_from_db()
        self.assertEqual(resign_obj.status_pengajuan, 'DISETUJUI_KELUAR')
        self.assertEqual(resign_obj.status_kliring, 'SELESAI_KLIRING')
        self.assertEqual(anggota_rina.status, StatusAnggotaChoices.NON_AKTIF_KELUAR)
        self.assertFalse(anggota_rina.pengguna.is_aktif)

    def test_07_simpanan_controller_dan_ui_tahap_4(self):
        """Menguji fitur Tahap 4: Kelola Simpanan, Transaksi Baru, Proteksi BR-08, Cetak Bukti & Ekspor."""
        swj = JenisSimpanan.objects.get(kode='SWJ')
        shr = JenisSimpanan.objects.get(kode='SHR')

        # 1. Login sebagai Bendahara & buka halaman Kelola Simpanan (WD-05 & WD-06)
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})
        resp_smp = self.client.get('/simpanan/')
        self.assertEqual(resp_smp.status_code, 200)
        self.assertTemplateUsed(resp_smp, 'simpanan/kelola_simpanan.html')
        self.assertContains(resp_smp, 'Kelola Simpanan')
        self.assertContains(resp_smp, 'Simpanan Pokok')
        self.assertContains(resp_smp, 'Simpanan Wajib')
        self.assertContains(resp_smp, 'Simpanan Khusus')
        self.assertContains(resp_smp, 'Saldo Sebelum')
        self.assertContains(resp_smp, 'Saldo Sesudah')

        # 2. Catat Setor Simpanan Wajib (Rp 150.000) & Simpanan Hari Raya (Rp 600.000)
        self.client.post(
            '/simpanan/tambah/',
            {
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': swj.id,
                'jenis_transaksi': 'SETOR',
                'metode_bayar': 'POTONG_GAJI',
                'nominal': '150000',
                'keterangan': 'Setoran Simpanan Wajib Bulan November',
            },
            follow=True,
        )
        resp_setor_shr = self.client.post(
            '/simpanan/tambah/',
            {
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': shr.id,
                'jenis_transaksi': 'SETOR',
                'metode_bayar': 'TUNAI',
                'nominal': '600000',
                'keterangan': 'Setoran Simpanan Hari Raya',
            },
            follow=True,
        )
        self.assertEqual(resp_setor_shr.status_code, 200)
        self.assertContains(resp_setor_shr, 'Cetak Bukti Transaksi')
        self.assertEqual(
            TransaksiSimpanan.hitungSaldoBerjalan(self.anggota.id, shr.id),
            Decimal('600000.00'),
        )

        # 3. Proteksi BR-08: Percobaan tarik Simpanan Wajib (dapat_ditarik = 0) wajib ditolak
        resp_tarik_terkunci = self.client.post(
            '/simpanan/tambah/',
            {
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': swj.id,
                'jenis_transaksi': 'TARIK',
                'metode_bayar': 'TUNAI',
                'nominal': '50000',
            },
            follow=True,
        )
        self.assertContains(resp_tarik_terkunci, 'terkunci')
        self.assertEqual(
            TransaksiSimpanan.hitungSaldoBerjalan(self.anggota.id, swj.id),
            Decimal('150000.00'),
        )

        # 4. Proteksi BR-08: Percobaan tarik Simpanan Hari Raya melebihi saldo (Rp 900.000 > Rp 600.000) ditolak
        resp_tarik_lebih = self.client.post(
            '/simpanan/tambah/',
            {
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': shr.id,
                'jenis_transaksi': 'TARIK',
                'metode_bayar': 'TUNAI',
                'nominal': '900000',
            },
            follow=True,
        )
        self.assertContains(resp_tarik_lebih, 'melebihi saldo')

        # 5. Penarikan valid Simpanan Hari Raya (Rp 250.000 -> sisa Rp 350.000)
        resp_tarik_valid = self.client.post(
            '/simpanan/tambah/',
            {
                'anggota_id': self.anggota.id,
                'jenis_simpanan_id': shr.id,
                'jenis_transaksi': 'TARIK',
                'metode_bayar': 'TUNAI',
                'nominal': '250000',
                'keterangan': 'Penarikan sebagian Simpanan Hari Raya',
            },
            follow=True,
        )
        self.assertEqual(resp_tarik_valid.status_code, 200)
        self.assertEqual(
            TransaksiSimpanan.hitungSaldoBerjalan(self.anggota.id, shr.id),
            Decimal('350000.00'),
        )

        # 6. Cetak Kuitansi & Ekspor Excel (.xlsx)
        mutasi_terakhir = TransaksiSimpanan.objects.filter(anggota=self.anggota).first()
        resp_kuitansi = self.client.get(f'/simpanan/kuitansi/{mutasi_terakhir.no_kuitansi}/')
        self.assertEqual(resp_kuitansi.status_code, 200)
        self.assertTemplateUsed(resp_kuitansi, 'simpanan/kuitansi_simpanan_print.html')

        resp_excel = self.client.get('/simpanan/ekspor/')
        self.assertEqual(resp_excel.status_code, 200)
        self.assertEqual(
            resp_excel['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        # 7. Portal Mandiri 'Simpanan Saya' untuk Peran ANGGOTA (UC-02)
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'KKP-2026-001', 'password': 'Kkpris2026!'})
        resp_anggota_smp = self.client.get('/simpanan/')
        self.assertEqual(resp_anggota_smp.status_code, 200)
        self.assertTemplateUsed(resp_anggota_smp, 'simpanan/simpanan_anggota.html')
        self.assertContains(resp_anggota_smp, 'Simpanan Saya')
        self.assertContains(resp_anggota_smp, 'Simpanan Terkunci')

    def test_08_pembiayaan_controller_agunan_approval_realisasi_tahap_5(self):
        """Menguji fitur Tahap 5: Wizard 3 Step Ajukan Pembiayaan, Agunan >70Jt, Persetujuan Kas Ketua & Realisasi."""
        akad_mrb = JenisAkad.objects.get(kode='AKD-MRB')
        akad_ijr = JenisAkad.objects.get(kode='AKD-IJR')

        # 1. Login sebagai Anggota & buka halaman Wizard 3 Langkah Ajukan Pembiayaan (WD-19, WD-20, WD-21)
        self.client.post('/login/', {'username': 'KKP-2026-001', 'password': 'Kkpris2026!'})
        resp_wizard = self.client.get('/pembiayaan/ajukan/')
        self.assertEqual(resp_wizard.status_code, 200)
        self.assertTemplateUsed(resp_wizard, 'pembiayaan/ajukan_pembiayaan.html')
        self.assertContains(resp_wizard, 'Pengajuan dibuka tanggal 1-20 setiap bulan')
        self.assertContains(resp_wizard, 'Pilih Akad')
        self.assertContains(resp_wizard, 'Nominal &amp; Tenor')
        self.assertContains(resp_wizard, 'Pratinjau Angsuran')
        self.assertContains(resp_wizard, 'Hanya muncul jika nominal &gt; Rp 70.000.000')

        # 2. Ajukan Pembiayaan Ijarah <= Rp 70.000.000 (Tanpa Agunan: Rp 15.000.000, Tenor 10 bulan)
        resp_ajukan_kecil = self.client.post(
            '/pembiayaan/ajukan/',
            {
                'jenis_akad_id': akad_ijr.id,
                'harga_pokok': '15000000',
                'tenor_bulan': '10',
                'margin_persen': '1.00',
                'tujuan_pembiayaan': 'Biaya Pendidikan Kuliah Anak',
                'tanggal_pengajuan': '2026-11-15',
            },
            follow=True,
        )
        self.assertEqual(resp_ajukan_kecil.status_code, 200)
        pmb_kecil = Pembiayaan.objects.get(tujuan_pembiayaan='Biaya Pendidikan Kuliah Anak')
        self.assertEqual(pmb_kecil.harga_pokok, Decimal('15000000.00'))
        self.assertEqual(pmb_kecil.total_margin, Decimal('1500000.00'))
        self.assertEqual(pmb_kecil.angsuran_bulanan, Decimal('1650000.00'))
        self.assertEqual(pmb_kecil.status, StatusPembiayaanChoices.MENUNGGU_VERIFIKASI)

        # 3. Proteksi BR-03: Pengajuan > Rp 70.000.000 TANPA agunan wajib ditolak
        resp_tanpa_agunan = self.client.post(
            '/pembiayaan/ajukan/',
            {
                'jenis_akad_id': akad_mrb.id,
                'harga_pokok': '80000000',
                'tenor_bulan': '20',
                'margin_persen': '1.00',
                'tujuan_pembiayaan': 'Pembelian Kendaraan Roda Empat Tanpa Agunan',
                'tanggal_pengajuan': '2026-11-16',
            },
            follow=True,
        )
        self.assertContains(resp_tanpa_agunan, 'wajib melampirkan dokumen agunan')
        self.assertFalse(
            Pembiayaan.objects.filter(
                tujuan_pembiayaan='Pembelian Kendaraan Roda Empat Tanpa Agunan'
            ).exists()
        )

        # 4. Pengajuan > Rp 70.000.000 DENGAN Agunan BPKB berhasil disimpan (Rp 90.000.000, Tenor 18 bulan)
        resp_dengan_agunan = self.client.post(
            '/pembiayaan/ajukan/',
            {
                'jenis_akad_id': akad_mrb.id,
                'harga_pokok': '90000000',
                'tenor_bulan': '18',
                'margin_persen': '1.00',
                'tujuan_pembiayaan': 'Renovasi Rumah & Pengadaan Kendaraan',
                'tanggal_pengajuan': '2026-11-16',
                'jenis_agunan': JenisAgunanChoices.BPKB_MOBIL,
                'no_registrasi': 'BPKB-BA-9988-SLK',
                'nilai_taksiran': '135000000',
            },
            follow=True,
        )
        self.assertEqual(resp_dengan_agunan.status_code, 200)
        pmb_besar = Pembiayaan.objects.get(tujuan_pembiayaan='Renovasi Rumah & Pengadaan Kendaraan')
        self.assertEqual(pmb_besar.harga_pokok, Decimal('90000000.00'))
        self.assertEqual(pmb_besar.angsuran_bulanan, Decimal('5900000.00'))
        self.assertEqual(Agunan.objects.filter(pembiayaan=pmb_besar).count(), 1)

        # 5. Buka halaman Pembiayaan Saya (Anggota)
        resp_milik = self.client.get('/pembiayaan/')
        self.assertEqual(resp_milik.status_code, 200)
        self.assertTemplateUsed(resp_milik, 'pembiayaan/pembiayaan_saya.html')
        self.assertContains(resp_milik, pmb_besar.no_pembiayaan)

        # 6. Login sebagai Bendahara -> Buka Daftar Pembiayaan (WD-08) & Detail Pembiayaan (WD-09)
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})

        resp_daftar = self.client.get('/pembiayaan/')
        self.assertEqual(resp_daftar.status_code, 200)
        self.assertTemplateUsed(resp_daftar, 'pembiayaan/daftar_pembiayaan.html')
        self.assertContains(resp_daftar, 'Daftar Pembiayaan')
        self.assertContains(resp_daftar, 'Total Pembiayaan')
        self.assertContains(resp_daftar, 'Pembiayaan Aktif')

        resp_detail = self.client.get(f'/pembiayaan/{pmb_besar.id}/')
        self.assertEqual(resp_detail.status_code, 200)
        self.assertTemplateUsed(resp_detail, 'pembiayaan/detail_pembiayaan.html')
        self.assertContains(resp_detail, 'Ringkasan Akad')
        self.assertContains(resp_detail, 'Status Persetujuan')
        self.assertContains(
            resp_detail,
            'Pencairan fisik dana dilakukan di luar sistem; sistem hanya mencatat konfirmasi.',
        )

        # 7. Proteksi Two-Man Rule: Bendahara mencoba catat realisasi sebelum disetujui Ketua -> ditolak
        resp_realisasi_dini = self.client.post(
            f'/pembiayaan/{pmb_besar.id}/realisasi/',
            {
                'tanggal_realisasi': '2026-11-17',
                'metode_pencairan': 'TRANSFER_BANK',
                'nomor_referensi_bank': 'REF-GAGAL-001',
                'nominal_cair': '90000000',
            },
            follow=True,
        )
        self.assertContains(resp_realisasi_dini, 'Two-Man Rule')
        pmb_besar.refresh_from_db()
        self.assertNotEqual(pmb_besar.status, StatusPembiayaanChoices.AKTIF)

        # 8. Bendahara melakukan Verifikasi Level 1 -> status naik ke MENUNGGU_PERSETUJUAN_KETUA
        resp_verif_bendahara = self.client.post(
            f'/pembiayaan/{pmb_besar.id}/verifikasi/',
            {
                'keputusan': 'DISETUJUI',
                'catatan': 'Agunan BPKB asli valid, diteruskan ke Ketua.',
            },
            follow=True,
        )
        self.assertEqual(resp_verif_bendahara.status_code, 200)
        pmb_besar.refresh_from_db()
        self.assertEqual(pmb_besar.status, StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA)

        # 9. Login sebagai Ketua -> Buka Persetujuan Kas (WD-18 & Konfirmasi Persetujuan.png) & Setujui Kas
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'ketua', 'password': 'Kkpris2026!'})

        resp_persetujuan_kas = self.client.get('/persetujuan-kas/')
        self.assertEqual(resp_persetujuan_kas.status_code, 200)
        self.assertTemplateUsed(resp_persetujuan_kas, 'pembiayaan/persetujuan_kas.html')
        self.assertContains(resp_persetujuan_kas, 'Persetujuan Kas')
        self.assertContains(resp_persetujuan_kas, 'Konfirmasi Persetujuan')
        self.assertContains(resp_persetujuan_kas, pmb_besar.no_pembiayaan)

        resp_approve_ketua = self.client.post(
            f'/persetujuan-kas/{pmb_besar.id}/proses/',
            {
                'keputusan': 'DISETUJUI',
                'catatan': 'Disetujui Ketua Koperasi untuk dicairkan.',
            },
            follow=True,
        )
        self.assertEqual(resp_approve_ketua.status_code, 200)
        pmb_besar.refresh_from_db()
        self.assertEqual(pmb_besar.status, StatusPembiayaanChoices.DISETUJUI_KETUA)

        # 10. Login kembali sebagai Bendahara -> Catat Realisasi Pencairan & Auto-Generate Jadwal Angsuran
        self.client.get('/logout/')
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})

        resp_realisasi_valid = self.client.post(
            f'/pembiayaan/{pmb_besar.id}/realisasi/',
            {
                'tanggal_realisasi': '2026-11-17',
                'metode_pencairan': 'TRANSFER_BANK',
                'nomor_referensi_bank': 'BNI-SOLOK-20261117',
                'nominal_cair': '90000000',
            },
            follow=True,
        )
        self.assertEqual(resp_realisasi_valid.status_code, 200)
        pmb_besar.refresh_from_db()
        self.assertEqual(pmb_besar.status, StatusPembiayaanChoices.AKTIF)
        self.assertEqual(
            JadwalAngsuran.objects.filter(pembiayaan=pmb_besar).count(),
            18,
        )
        self.assertTrue(RealisasiPencairan.objects.filter(pembiayaan=pmb_besar).exists())

        # 11. Uji Ekspor Excel Daftar Pembiayaan (.xlsx)
        resp_excel_pmb = self.client.get('/pembiayaan/ekspor/')
        self.assertEqual(resp_excel_pmb.status_code, 200)
        self.assertEqual(
            resp_excel_pmb['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_09_rekap_potong_gaji_kelola_angsuran_dan_notifikasi_tahap_6(self):
        """Menguji fitur Tahap 6: Kelola Angsuran, Cetak Bukti Pembayaran, Rekap Potong Gaji (Tgl 24) & Notifikasi (Tgl 10)."""
        akad_mrb = JenisAkad.objects.get(kode='AKD-MRB')

        # Siapkan 1 pembiayaan AKTIF dengan 6 jadwal angsuran
        pmb = Pembiayaan.simpanPengajuanBaru({
            'no_pembiayaan': 'PMB-2026-601',
            'anggota_id': self.anggota.id,
            'jenis_akad_id': akad_mrb.id,
            'tanggal_pengajuan': date(2026, 10, 10),
            'harga_pokok': Decimal('12000000.00'),
            'margin_persen': Decimal('1.00'),
            'tenor_bulan': 6,
            'no_antrean': 1,
            'tujuan_pembiayaan': 'Pengadaan Peralatan Praktik Kejuruan',
        })
        PersetujuanPembiayaan.simpanKeputusanOtorisasi(
            pembiayaan_id=pmb.id,
            pejabat_id=self.ketua.id,
            keputusan=KeputusanOtorisasiChoices.DISETUJUI,
            catatan='Disetujui Ketua',
            level_persetujuan=2,
        )
        Pembiayaan.perbaruiStatusPembiayaan(pmb.id, StatusPembiayaanChoices.DISETUJUI_KETUA)
        RealisasiPencairan.simpanRealisasiPencairan(pmb.id, {
            'bendahara_id': self.bendahara.id,
            'tanggal_realisasi': date(2026, 10, 12),
            'metode_pencairan': MetodePencairanChoices.TRANSFER_BANK,
            'nomor_referensi_bank': 'REF-601',
            'nominal_cair': Decimal('12000000.00'),
            'bukti_transfer_url': 'media/pencairan/ref601.pdf',
        })
        Pembiayaan.perbaruiStatusPembiayaan(pmb.id, StatusPembiayaanChoices.AKTIF, tanggal_cair=date(2026, 10, 12))
        JadwalAngsuran.generateJadwalAngsuran(
            pembiayaan_id=pmb.id,
            tenor_bulan=6,
            porsi_pokok=Decimal('2000000.00'),
            porsi_margin=Decimal('120000.00'),
            tanggal_mulai=date(2026, 10, 12),
        )
        jadwal_1 = JadwalAngsuran.objects.get(pembiayaan=pmb, angsuran_ke=1)
        jadwal_2 = JadwalAngsuran.objects.get(pembiayaan=pmb, angsuran_ke=2)

        # 1. Login sebagai Bendahara & buka halaman Kelola Angsuran (WD-10)
        self.client.post('/login/', {'username': 'bendahara', 'password': 'Kkpris2026!'})
        resp_ang = self.client.get('/angsuran/')
        self.assertEqual(resp_ang.status_code, 200)
        self.assertTemplateUsed(resp_ang, 'angsuran/kelola_angsuran.html')
        self.assertContains(resp_ang, 'Kelola Angsuran')
        self.assertContains(resp_ang, 'Pilih Pembiayaan')
        self.assertContains(resp_ang, 'Total Pembiayaan')
        self.assertContains(resp_ang, 'Terbayar')
        self.assertContains(resp_ang, 'Sisa')
        self.assertContains(resp_ang, 'Catat Pembayaran')

        # 2. Catat Pembayaran Cicilan Mandiri untuk Angsuran ke-1 -> Memunculkan Modal Cetak Bukti Pembayaran (WD-11)
        resp_bayar_1 = self.client.post(
            f'/angsuran/{jadwal_1.id}/bayar/',
            {
                'nominal_bayar': '2120000',
                'potongan_margin': '0',
                'metode_bayar': 'TUNAI',
                'nomor_referensi': 'TUNAI-KASIR-01',
            },
            follow=True,
        )
        self.assertEqual(resp_bayar_1.status_code, 200)
        self.assertContains(resp_bayar_1, 'Cetak Bukti Pembayaran')
        jadwal_1.refresh_from_db()
        self.assertEqual(jadwal_1.status_bayar, StatusBayarAngsuranChoices.LUNAS)

        bukti_1 = PembayaranAngsuran.objects.get(jadwal_angsuran=jadwal_1)
        resp_print_ang = self.client.get(f'/angsuran/kuitansi/{bukti_1.no_kuitansi}/')
        self.assertEqual(resp_print_ang.status_code, 200)
        self.assertTemplateUsed(resp_print_ang, 'angsuran/kuitansi_angsuran_print.html')

        # 3. Buka halaman Notifikasi Tagihan (WD-13) & Kirim Notifikasi Pengingat Tanggal 10 (WA & Email)
        resp_notif_page = self.client.get('/notifikasi-tagihan/')
        self.assertEqual(resp_notif_page.status_code, 200)
        self.assertTemplateUsed(resp_notif_page, 'angsuran/notifikasi_tagihan.html')
        self.assertContains(resp_notif_page, 'Daftar Penerima')
        self.assertContains(resp_notif_page, 'Pengaturan Pesan')
        self.assertContains(resp_notif_page, 'Setiap tanggal 10')
        self.assertContains(resp_notif_page, 'Pratinjau Pesan')

        resp_kirim_notif = self.client.post(
            '/notifikasi-tagihan/',
            {
                'jadwal_ids': [str(jadwal_2.id)],
                'kanal': ['WHATSAPP', 'EMAIL'],
                'jadwal_pengiriman': 'Setiap tanggal 10',
                'isi_pesan': 'Pengingat tagihan angsuran ke-{angsuran_ke} sebesar {nominal} untuk {nama}.',
            },
            follow=True,
        )
        self.assertEqual(resp_kirim_notif.status_code, 200)
        self.assertEqual(NotifikasiTagihan.objects.filter(jadwal_angsuran=jadwal_2).count(), 2)

        # 4. Buka halaman Rekap Potong Gaji (WD-12) & Generate Rekap Tanggal 24 (Periode 2026-12)
        resp_rekap_page = self.client.get('/rekap-potong-gaji/')
        self.assertEqual(resp_rekap_page.status_code, 200)
        self.assertTemplateUsed(resp_rekap_page, 'angsuran/rekap_potong_gaji.html')
        self.assertContains(resp_rekap_page, 'Rekap dibuat tanggal 24')
        self.assertContains(resp_rekap_page, 'Belanja Toko')

        resp_gen = self.client.post(
            '/rekap-potong-gaji/generate/',
            {'periode': '2026-12'},
            follow=True,
        )
        self.assertEqual(resp_gen.status_code, 200)
        rekap_des = RekapPotongGaji.objects.get(periode_bulan='2026-12')
        self.assertEqual(rekap_des.total_simpanan_wajib, Decimal('150000.00'))
        self.assertEqual(rekap_des.total_angsuran, Decimal('2120000.00'))
        self.assertEqual(rekap_des.total_tagihan, Decimal('2270000.00'))

        # 5. Update Potongan Belanja Toko Anggota (Rp 80.000) -> Total Tagihan menjadi Rp 2.350.000
        detail_budi = DetailRekapPotongGaji.objects.get(rekap_potong_gaji=rekap_des, anggota=self.anggota)
        resp_toko = self.client.post(
            f'/rekap-potong-gaji/detail/{detail_budi.id}/update-toko/',
            {'nominal_simpanan_sukarela': '80000'},
            follow=True,
        )
        self.assertEqual(resp_toko.status_code, 200)
        rekap_des.refresh_from_db()
        self.assertEqual(rekap_des.total_tagihan, Decimal('2350000.00'))

        # 6. Ekspor Rekap Potong Gaji ke Excel (.xlsx) & PDF (.pdf)
        resp_rekap_xlsx = self.client.get(f'/rekap-potong-gaji/{rekap_des.id}/ekspor/?format=xlsx')
        self.assertEqual(resp_rekap_xlsx.status_code, 200)
        self.assertEqual(
            resp_rekap_xlsx['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        resp_rekap_pdf = self.client.get(f'/rekap-potong-gaji/{rekap_des.id}/ekspor/?format=pdf')
        self.assertEqual(resp_rekap_pdf.status_code, 200)
        self.assertEqual(resp_rekap_pdf['Content-Type'], 'application/pdf')

        # 7. Konfirmasi Pelunasan Kolektif Batch -> Otomatis membukukan Simpanan Wajib & melunasi Angsuran ke-2
        resp_lunas_batch = self.client.post(
            f'/rekap-potong-gaji/{rekap_des.id}/konfirmasi-lunas/',
            {'nomor_referensi_transfer': 'TRF-GAJI-DES-2026'},
            follow=True,
        )
        self.assertEqual(resp_lunas_batch.status_code, 200)
        rekap_des.refresh_from_db()
        jadwal_2.refresh_from_db()
        self.assertEqual(rekap_des.status_rekap, 'LUNAS_KOLEKTIF')
        self.assertEqual(jadwal_2.status_bayar, StatusBayarAngsuranChoices.LUNAS)
        self.assertTrue(
            TransaksiSimpanan.objects.filter(
                anggota=self.anggota,
                jenis_simpanan__kode='SWJ',
                metode_bayar='POTONG_GAJI',
            ).exists()
        )





