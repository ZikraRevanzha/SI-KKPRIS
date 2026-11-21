"""
Suite Pengujian REST API v1 — Fondasi API, Autentikasi JWT, Cookie httpOnly,
Permission Class, Throttle, Audit Trail, dan Swagger/OpenAPI (Tahap 9A).
"""

import importlib
from unittest.mock import patch
from django.conf import settings as django_settings
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.urls import clear_url_caches
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView
from koperasi.api.v1.permissions import (
    IsAnggota,
    IsBendahara,
    IsBendaharaAtauKetua,
    IsKetua,
)
from koperasi.api.v1.throttling import LoginRateThrottle
from koperasi.models import AuditTrailLog, Pengguna
import si_kkpris.urls as root_urls


def _buat_view_uji_izin(permission_cls):
    """Membuat view DRF terisolasi hanya untuk pengujian unit permission class."""

    class _ViewUjiIzin(APIView):
        permission_classes = [permission_cls]

        def get(self, request):
            return Response({'ok': True, 'peran': request.user.peran})

    return _ViewUjiIzin.as_view()


@override_settings(SEED_PASSWORD='dummy-test-pass-9a')
class AuthJWTAPITestCase(APITestCase):
    TEST_PASSWORD = 'dummy-test-pass-9a'
    URL_LOGIN = '/api/v1/auth/login/'
    URL_REFRESH = '/api/v1/auth/refresh/'
    URL_LOGOUT = '/api/v1/auth/logout/'
    URL_ME = '/api/v1/auth/me/'
    URL_GANTI_PASSWORD = '/api/v1/auth/ganti-password/'

    def setUp(self):
        cache.clear()
        call_command('seed_master', verbosity=0)
        self.ketua = Pengguna.objects.get(username='ketua01')
        self.bendahara = Pengguna.objects.get(username='bendahara01')
        self.user_anggota = Pengguna.objects.get(username='anggota01')

    def tearDown(self):
        cache.clear()

    def _login_api(self, username: str, password: str | None = None, **extra):
        return self.client.post(
            self.URL_LOGIN,
            {'username': username, 'password': self.TEST_PASSWORD if password is None else password},
            format='json',
            **extra,
        )

    def _set_bearer(self, access_token: str):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def _assert_format_galat_seragam(self, response, expected_status: int, expected_kode: str | None = None):
        self.assertEqual(response.status_code, expected_status)
        body = response.json()
        self.assertIn('kode', body)
        self.assertIn('pesan', body)
        self.assertIn('detail', body)
        self.assertIsInstance(body['detail'], dict)
        self.assertTrue(body['pesan'])
        if expected_kode is not None:
            self.assertEqual(body['kode'], expected_kode)
        return body

    # ------------------------------------------------------------------
    # 1. Login sukses & gagal + AuditTrailLog
    # ------------------------------------------------------------------
    def test_01_login_sukses_username_dan_no_anggota_serta_audit_trail(self):
        # Login Bendahara dengan username
        resp = self._login_api('bendahara01', REMOTE_ADDR='10.10.0.5')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('access', data)
        self.assertTrue(data['access'])
        self.assertNotIn('refresh', data)  # Refresh wajib di cookie httpOnly, bukan body
        self.assertEqual(data['pengguna']['username'], 'bendahara01')
        self.assertEqual(data['pengguna']['peran'], 'BENDAHARA')
        self.assertIsNone(data['pengguna']['anggota'])

        log_berhasil = AuditTrailLog.objects.filter(
            pengguna=self.bendahara,
            aksi='LOGIN_BERHASIL',
        ).first()
        self.assertIsNotNone(log_berhasil)
        self.assertEqual(log_berhasil.ip_address, '10.10.0.5')

        # Login Anggota menggunakan Nomor Anggota (KKP-2026-001)
        resp_anggota = self._login_api('KKP-2026-001')
        self.assertEqual(resp_anggota.status_code, status.HTTP_200_OK)
        data_anggota = resp_anggota.json()
        self.assertEqual(data_anggota['pengguna']['username'], 'anggota01')
        self.assertEqual(data_anggota['pengguna']['peran'], 'ANGGOTA')
        self.assertIsNotNone(data_anggota['pengguna']['anggota'])
        self.assertEqual(data_anggota['pengguna']['anggota']['no_anggota'], 'KKP-2026-001')

    def test_02_login_gagal_password_salah_nonaktif_dan_validasi(self):
        # Password salah -> 401 & AuditTrailLog LOGIN_GAGAL
        resp_salah = self._login_api('bendahara01', password='PasswordSalah999!')
        self._assert_format_galat_seragam(
            resp_salah,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='KREDENSIAL_TIDAK_VALID',
        )
        self.assertTrue(
            AuditTrailLog.objects.filter(pengguna=self.bendahara, aksi='LOGIN_GAGAL').exists()
        )

        # Username tidak dikenal -> 401
        resp_unknown = self._login_api('tidak_ada_user', password='PasswordSalah999!')
        self._assert_format_galat_seragam(
            resp_unknown,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='KREDENSIAL_TIDAK_VALID',
        )

        # Akun nonaktif (is_aktif=False) -> 401
        self.user_anggota.is_aktif = False
        self.user_anggota.save(update_fields=['is_aktif'])
        resp_nonaktif = self._login_api('anggota01')
        self._assert_format_galat_seragam(
            resp_nonaktif,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='KREDENSIAL_TIDAK_VALID',
        )

        # Input kosong -> 400 format seragam dengan detail per field
        resp_kosong = self.client.post(self.URL_LOGIN, {'username': '', 'password': ''}, format='json')
        body = self._assert_format_galat_seragam(
            resp_kosong,
            status.HTTP_400_BAD_REQUEST,
            expected_kode='VALIDASI_GAGAL',
        )
        self.assertIn('username', body['detail'])
        self.assertIn('password', body['detail'])

    # ------------------------------------------------------------------
    # 2. Atribut cookie refresh (httpOnly, SameSite, Path, Secure)
    # ------------------------------------------------------------------
    @override_settings(DEBUG=True, JWT_REFRESH_COOKIE_SECURE=None)
    def test_03_atribut_cookie_refresh_saat_debug_true(self):
        resp = self._login_api('bendahara01')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cookie_name = django_settings.JWT_REFRESH_COOKIE_NAME
        self.assertIn(cookie_name, resp.cookies)
        cookie = resp.cookies[cookie_name]
        self.assertTrue(cookie.value)
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Strict')
        self.assertEqual(cookie['path'], '/api/v1/auth/')
        self.assertEqual(int(cookie['max-age']), 1800)
        self.assertFalse(cookie['secure'])

    @override_settings(DEBUG=False, JWT_REFRESH_COOKIE_SECURE=None, SECURE_SSL_REDIRECT=False)
    def test_04_atribut_cookie_refresh_secure_saat_debug_false(self):
        resp = self._login_api('bendahara01')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cookie = resp.cookies[django_settings.JWT_REFRESH_COOKIE_NAME]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Strict')
        self.assertEqual(cookie['path'], '/api/v1/auth/')
        self.assertTrue(cookie['secure'])

    # ------------------------------------------------------------------
    # 3. Refresh, rotasi, blacklist token lama, dan akun nonaktif
    # ------------------------------------------------------------------
    def test_05_refresh_rotasi_dan_blacklist_token_lama(self):
        resp_login = self._login_api('ketua01')
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)
        cookie_name = django_settings.JWT_REFRESH_COOKIE_NAME
        refresh_lama = resp_login.cookies[cookie_name].value

        # Refresh pertama: berhasil, terbitkan access baru & cookie refresh baru
        resp_refresh = self.client.post(self.URL_REFRESH)
        self.assertEqual(resp_refresh.status_code, status.HTTP_200_OK)
        access_baru = resp_refresh.json()['access']
        self.assertTrue(access_baru)
        refresh_baru = resp_refresh.cookies[cookie_name].value
        self.assertTrue(refresh_baru)
        self.assertNotEqual(refresh_baru, refresh_lama)

        # Access baru dapat dipakai pada GET /api/v1/auth/me/
        self._set_bearer(access_baru)
        resp_me = self.client.get(self.URL_ME)
        self.assertEqual(resp_me.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_me.json()['username'], 'ketua01')

        # Mencoba memakai ulang refresh token lama -> ditolak (401 blacklist)
        self.client.credentials()
        self.client.cookies[cookie_name] = refresh_lama
        resp_reuse = self.client.post(self.URL_REFRESH)
        self._assert_format_galat_seragam(
            resp_reuse,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='REFRESH_TOKEN_TIDAK_VALID',
        )

    def test_06_refresh_ditolak_tanpa_cookie_dan_saat_akun_nonaktif(self):
        # Tanpa cookie -> 401
        resp_kosong = self.client.post(self.URL_REFRESH)
        self._assert_format_galat_seragam(
            resp_kosong,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='REFRESH_TOKEN_TIDAK_ADA',
        )

        # Login lalu akun dinonaktifkan (mis. selesai resign) -> refresh ditolak
        resp_login = self._login_api('anggota01')
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)
        self.user_anggota.is_aktif = False
        self.user_anggota.save(update_fields=['is_aktif'])

        resp_refresh = self.client.post(self.URL_REFRESH)
        self._assert_format_galat_seragam(
            resp_refresh,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='AKUN_TIDAK_AKTIF',
        )

    # ------------------------------------------------------------------
    # 4. Logout (blacklist + hapus cookie + AuditTrailLog)
    # ------------------------------------------------------------------
    def test_07_logout_blacklist_refresh_hapus_cookie_dan_audit_trail(self):
        resp_login = self._login_api('bendahara01')
        cookie_name = django_settings.JWT_REFRESH_COOKIE_NAME
        refresh_token = resp_login.cookies[cookie_name].value
        self._set_bearer(resp_login.json()['access'])

        resp_logout = self.client.post(self.URL_LOGOUT)
        self.assertEqual(resp_logout.status_code, status.HTTP_200_OK)
        self.assertIn('pesan', resp_logout.json())
        self.assertEqual(resp_logout.cookies[cookie_name].value, '')

        # Audit trail LOGOUT tercatat
        self.assertTrue(
            AuditTrailLog.objects.filter(pengguna=self.bendahara, aksi='LOGOUT').exists()
        )

        # Refresh token yang sudah logout wajib ditolak (blacklist)
        self.client.credentials()
        self.client.cookies[cookie_name] = refresh_token
        resp_after_logout = self.client.post(self.URL_REFRESH)
        self._assert_format_galat_seragam(
            resp_after_logout,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='REFRESH_TOKEN_TIDAK_VALID',
        )

    # ------------------------------------------------------------------
    # 5. Endpoint /me/ & /ganti-password/ + 401 tanpa token
    # ------------------------------------------------------------------
    def test_08_me_dan_401_tanpa_token(self):
        # Tanpa token -> 401 format seragam
        resp_unauth = self.client.get(self.URL_ME)
        self._assert_format_galat_seragam(
            resp_unauth,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='AUTENTIKASI_DIPERLUKAN',
        )

        # Token rusak -> 401 format seragam
        self._set_bearer('token.tidak.valid')
        resp_invalid = self.client.get(self.URL_ME)
        self._assert_format_galat_seragam(
            resp_invalid,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='AUTENTIKASI_GAGAL',
        )

        # Dengan token Anggota valid -> 200 memuat data profil anggota
        self.client.credentials()
        resp_login = self._login_api('anggota01')
        self._set_bearer(resp_login.json()['access'])
        resp_me = self.client.get(self.URL_ME)
        self.assertEqual(resp_me.status_code, status.HTTP_200_OK)
        body = resp_me.json()
        self.assertEqual(body['id'], self.user_anggota.id)
        self.assertEqual(body['username'], 'anggota01')
        self.assertEqual(body['peran'], 'ANGGOTA')
        self.assertEqual(body['anggota']['no_anggota'], 'KKP-2026-001')

    def test_09_ganti_password_sukses_gagal_dan_audit_trail(self):
        # Tanpa token -> 401
        resp_unauth = self.client.post(self.URL_GANTI_PASSWORD, {}, format='json')
        self._assert_format_galat_seragam(
            resp_unauth,
            status.HTTP_401_UNAUTHORIZED,
            expected_kode='AUTENTIKASI_DIPERLUKAN',
        )

        resp_login = self._login_api('bendahara01')
        self._set_bearer(resp_login.json()['access'])

        # Konfirmasi tidak cocok -> 400
        resp_mismatch = self.client.post(
            self.URL_GANTI_PASSWORD,
            {
                'password_lama': self.TEST_PASSWORD,
                'password_baru': 'PasswordBaru2026!',
                'konfirmasi_password': 'BedaPassword2026!',
            },
            format='json',
        )
        body_mismatch = self._assert_format_galat_seragam(
            resp_mismatch,
            status.HTTP_400_BAD_REQUEST,
            expected_kode='VALIDASI_GAGAL',
        )
        self.assertIn('konfirmasi_password', body_mismatch['detail'])

        # Password lama salah -> 400
        resp_lama_salah = self.client.post(
            self.URL_GANTI_PASSWORD,
            {
                'password_lama': 'PasswordLamaSalah!',
                'password_baru': 'PasswordBaru2026!',
                'konfirmasi_password': 'PasswordBaru2026!',
            },
            format='json',
        )
        body_salah = self._assert_format_galat_seragam(
            resp_lama_salah,
            status.HTTP_400_BAD_REQUEST,
            expected_kode='VALIDASI_GAGAL',
        )
        self.assertIn('password_lama', body_salah['detail'])

        # Ganti password valid -> 200 & AuditTrailLog GANTI_PASSWORD
        resp_ok = self.client.post(
            self.URL_GANTI_PASSWORD,
            {
                'password_lama': self.TEST_PASSWORD,
                'password_baru': 'PasswordBaru2026!',
                'konfirmasi_password': 'PasswordBaru2026!',
            },
            format='json',
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditTrailLog.objects.filter(pengguna=self.bendahara, aksi='GANTI_PASSWORD').exists()
        )

        # Verifikasi login memakai password baru berhasil, password lama ditolak
        self.client.credentials()
        self.assertEqual(self._login_api('bendahara01', password=self.TEST_PASSWORD).status_code, 401)
        self.assertEqual(self._login_api('bendahara01', password='PasswordBaru2026!').status_code, 200)

    # ------------------------------------------------------------------
    # 6. Permission class (403 peran salah & 200 peran benar)
    # ------------------------------------------------------------------
    def test_10_permission_class_per_peran_dan_403_seragam(self):
        factory = APIRequestFactory()
        token_per_peran = {
            'ANGGOTA': self._login_api('anggota01').json()['access'],
            'BENDAHARA': self._login_api('bendahara01').json()['access'],
            'KETUA': self._login_api('ketua01').json()['access'],
        }

        matriks_uji = [
            (IsAnggota, {'ANGGOTA'}, {'BENDAHARA', 'KETUA'}),
            (IsBendahara, {'BENDAHARA'}, {'ANGGOTA', 'KETUA'}),
            (IsKetua, {'KETUA'}, {'ANGGOTA', 'BENDAHARA'}),
            (IsBendaharaAtauKetua, {'BENDAHARA', 'KETUA'}, {'ANGGOTA'}),
        ]

        for perm_cls, peran_lolos, peran_ditolak in matriks_uji:
            view = _buat_view_uji_izin(perm_cls)

            # Tanpa token -> 401
            req_anon = factory.get('/uji-izin/')
            resp_anon = view(req_anon)
            resp_anon.render()
            self.assertEqual(resp_anon.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(resp_anon.data['kode'], 'AUTENTIKASI_DIPERLUKAN')

            # Peran diizinkan -> 200
            for peran in peran_lolos:
                req = factory.get('/uji-izin/', HTTP_AUTHORIZATION=f'Bearer {token_per_peran[peran]}')
                resp = view(req)
                resp.render()
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

            # Peran salah -> 403 format seragam
            for peran in peran_ditolak:
                req = factory.get('/uji-izin/', HTTP_AUTHORIZATION=f'Bearer {token_per_peran[peran]}')
                resp = view(req)
                resp.render()
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(resp.data['kode'], 'AKSES_DITOLAK')
                self.assertIn('Akses ditolak', resp.data['pesan'])
                self.assertEqual(resp.data['detail'], {})

    # ------------------------------------------------------------------
    # 7. Throttle login (429 Too Many Requests)
    # ------------------------------------------------------------------
    def test_11_throttle_login_kembalikan_429_seragam(self):
        with patch.object(LoginRateThrottle, 'get_rate', return_value='3/min'):
            for _ in range(3):
                resp = self._login_api('bendahara01', password='SalahPassword!', REMOTE_ADDR='10.20.30.40')
                self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

            resp_ke_4 = self._login_api('bendahara01', password=self.TEST_PASSWORD, REMOTE_ADDR='10.20.30.40')
            self._assert_format_galat_seragam(
                resp_ke_4,
                status.HTTP_429_TOO_MANY_REQUESTS,
                expected_kode='TERLALU_BANYAK_PERMINTAAN',
            )

    # ------------------------------------------------------------------
    # 8. Swagger & OpenAPI (/api/schema/ & /api/docs/) berbasis API_DOCS_ENABLED
    # ------------------------------------------------------------------
    def test_12_swagger_dan_schema_hanya_aktif_saat_api_docs_enabled(self):
        try:
            with override_settings(API_DOCS_ENABLED=True):
                importlib.reload(root_urls)
                clear_url_caches()
                resp_schema = self.client.get('/api/schema/')
                self.assertEqual(resp_schema.status_code, status.HTTP_200_OK)
                self.assertIn(b'SI-KKPRIS API', resp_schema.content)

                resp_docs = self.client.get('/api/docs/')
                self.assertEqual(resp_docs.status_code, status.HTTP_200_OK)
                self.assertIn(b'swagger-ui', resp_docs.content.lower())

            with override_settings(API_DOCS_ENABLED=False):
                importlib.reload(root_urls)
                clear_url_caches()
                self.assertEqual(self.client.get('/api/schema/').status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(self.client.get('/api/docs/').status_code, status.HTTP_404_NOT_FOUND)
        finally:
            importlib.reload(root_urls)
            clear_url_caches()

    # ------------------------------------------------------------------
    # 9. Custom User Model (PenggunaManager & alias is_active)
    # ------------------------------------------------------------------
    def test_13_pengguna_custom_user_manager_dan_is_active(self):
        superuser = Pengguna.objects.create_superuser(
            username='admin_uji_9a',
            password='SuperUserPass2026!',
            nama_lengkap='Admin Uji',
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.check_password('SuperUserPass2026!'))

        superuser.is_active = False
        superuser.save(update_fields=['is_aktif'])
        superuser.refresh_from_db()
        self.assertFalse(superuser.is_aktif)
        self.assertFalse(superuser.is_active)
