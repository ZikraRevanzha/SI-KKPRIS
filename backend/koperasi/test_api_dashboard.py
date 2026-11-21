"""
Suite Pengujian REST API v1 — Ringkasan Dashboard Pengurus & Beranda Anggota (Tahap 9C).
Menguji 200, 401, 403, format uang string desimal, dan konsistensi hasil terhadap dashboard_service.
"""

from datetime import date
from decimal import Decimal
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from koperasi.models import Anggota, Pengguna, PeranPenggunaChoices, StatusAnggotaChoices, StatusKepegawaianChoices


@override_settings(SEED_PASSWORD='dummy-test-pass-9c')
class DashboardRingkasanAPITestCase(APITestCase):
    TEST_PASSWORD = 'dummy-test-pass-9c'
    URL_LOGIN = '/api/v1/auth/login/'
    URL_DASHBOARD = '/api/v1/dashboard/ringkasan/'
    URL_BERANDA = '/api/v1/anggota/saya/ringkasan/'

    def setUp(self):
        cache.clear()
        call_command('seed_master', '--with-demo', verbosity=0)

    def tearDown(self):
        cache.clear()

    def _autentikasi_sebagai(self, username: str) -> None:
        resp = self.client.post(
            self.URL_LOGIN,
            {'username': username, 'password': self.TEST_PASSWORD},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")

    def _assert_uang_string(self, nilai) -> Decimal:
        self.assertIsInstance(nilai, str)
        self.assertRegex(nilai, r'^-?\d+\.\d{2}$')
        return Decimal(nilai)

    def test_01_dashboard_ringkasan_tolak_401_tanpa_token(self):
        resp = self.client.get(self.URL_DASHBOARD)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        body = resp.json()
        self.assertIn('kode', body)
        self.assertIn('pesan', body)
        self.assertIn('detail', body)

    def test_02_dashboard_ringkasan_tolak_403_untuk_anggota(self):
        self._autentikasi_sebagai('anggota01')
        resp = self.client.get(self.URL_DASHBOARD)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()['kode'], 'AKSES_DITOLAK')

    def test_03_dashboard_ringkasan_200_untuk_bendahara_dan_ketua(self):
        for username in ('bendahara01', 'ketua01'):
            with self.subTest(pengguna=username):
                self._autentikasi_sebagai(username)
                resp = self.client.get(self.URL_DASHBOARD)
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

                data = resp.json()
                self.assertIn('hari_ini', data)
                self.assertGreaterEqual(data['total_anggota_aktif'], 1)
                self.assertGreaterEqual(data['total_seluruh_anggota'], data['total_anggota_aktif'])

                total_simpanan = self._assert_uang_string(data['total_simpanan'])
                self.assertGreater(total_simpanan, Decimal('0.00'))
                self._assert_uang_string(data['sisa_tagihan_aktif'])
                self._assert_uang_string(data['kas_hari_ini'])

                self.assertEqual(len(data['rincian_jenis_simpanan']), 5)
                for item in data['rincian_jenis_simpanan']:
                    self._assert_uang_string(item['saldo'])
                    self.assertIsInstance(item['dapat_ditarik'], bool)
                    self.assertIsInstance(item['tinggi_persen'], int)

                self.assertEqual(len(data['distribusi_akad']), 3)
                for akad in data['distribusi_akad']:
                    self._assert_uang_string(akad['nominal'])
                    self.assertIsInstance(akad['persen'], int)

                self.assertIsInstance(data['aktivitas_terbaru'], list)
                self.assertLessEqual(len(data['aktivitas_terbaru']), 6)

    def test_04_beranda_anggota_tolak_401_tanpa_token(self):
        resp = self.client.get(self.URL_BERANDA)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_05_beranda_anggota_tolak_403_untuk_bendahara_dan_ketua(self):
        for username in ('bendahara01', 'ketua01'):
            with self.subTest(pengguna=username):
                self._autentikasi_sebagai(username)
                resp = self.client.get(self.URL_BERANDA)
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(resp.json()['kode'], 'AKSES_DITOLAK')

    def test_06_beranda_anggota_200_dengan_data_demo_dan_uang_string(self):
        self._autentikasi_sebagai('anggota01')
        resp = self.client.get(self.URL_BERANDA)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertIsNotNone(data['anggota'])
        self.assertEqual(data['anggota']['no_anggota'], 'KKP-2026-001')

        total_simpanan = self._assert_uang_string(data['total_simpanan_anggota'])
        self.assertEqual(len(data['kartu_simpanan']), 5)
        kode_urutan = [item['kode'] for item in data['kartu_simpanan']]
        self.assertEqual(kode_urutan, ['SPK', 'SWJ', 'SKH', 'SHR', 'SBR'])

        jumlah_kartu = Decimal('0.00')
        for kartu in data['kartu_simpanan']:
            jumlah_kartu += self._assert_uang_string(kartu['saldo'])
        self.assertEqual(jumlah_kartu, total_simpanan)

        pembiayaan = data['pembiayaan_aktif']
        self.assertIsNotNone(pembiayaan)
        self._assert_uang_string(pembiayaan['angsuran_bulanan'])
        self._assert_uang_string(pembiayaan['sisa_kewajiban'])
        self.assertGreaterEqual(pembiayaan['progress_persen'], 0)
        self.assertLessEqual(pembiayaan['progress_persen'], 100)

        self.assertIsInstance(data['riwayat_terakhir'], list)
        self.assertLessEqual(len(data['riwayat_terakhir']), 6)
        for riwayat in data['riwayat_terakhir']:
            self._assert_uang_string(riwayat['jumlah'])
            self.assertIn(riwayat['tipe_badge'], ('success', 'warning'))

    def test_07_beranda_anggota_200_anggota_baru_tanpa_pembiayaan_dan_riwayat(self):
        pengguna_baru = Pengguna.objects.create_user(
            username='anggota_kosong_9c',
            password=self.TEST_PASSWORD,
            nama_lengkap='Anggota Dummy Baru',
            peran=PeranPenggunaChoices.ANGGOTA,
            is_aktif=True,
        )
        Anggota.objects.create(
            pengguna=pengguna_baru,
            no_anggota='KKP-2026-999',
            nik='0000000000000999',
            nama='Anggota Dummy Baru',
            status_kepegawaian=StatusKepegawaianChoices.PNS,
            masa_dinas_tahun=2,
            no_hp='080000000999',
            tanggal_masuk=date(2026, 1, 10),
            status=StatusAnggotaChoices.AKTIF,
        )

        self._autentikasi_sebagai('anggota_kosong_9c')
        resp = self.client.get(self.URL_BERANDA)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertEqual(data['total_simpanan_anggota'], '0.00')
        self.assertEqual(len(data['kartu_simpanan']), 5)
        self.assertIsNone(data['pembiayaan_aktif'])
        self.assertEqual(data['riwayat_terakhir'], [])
