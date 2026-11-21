"""
View REST API v1 untuk modul Autentikasi JWT + Refresh Cookie httpOnly (Tahap 9A).
Seluruh logika validasi kredensial & audit trail dipanggil dari koperasi.services.auth_service.
"""

from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from koperasi.api.v1.exceptions import buat_respons_galat
from koperasi.api.v1.serializers.auth_serializers import (
    GalatSeragamSerializer,
    GantiPasswordInputSerializer,
    LoginInputSerializer,
    LoginOutputSerializer,
    PenggunaMeSerializer,
    PesanOutputSerializer,
    RefreshOutputSerializer,
)
from koperasi.api.v1.throttling import LoginRateThrottle
from koperasi.models import Pengguna
from koperasi.services import auth_service


def _cookie_secure() -> bool:
    override = getattr(settings, 'JWT_REFRESH_COOKIE_SECURE', None)
    if override is not None:
        return bool(override)
    return not settings.DEBUG


def _pasang_cookie_refresh(response: Response, refresh_token: str) -> None:
    """Menyetel cookie httpOnly untuk refresh token JWT sesuai AGENTS.md Bagian 4.D."""
    lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=_cookie_secure(),
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
    )


def _hapus_cookie_refresh(response: Response) -> None:
    """Menghapus cookie refresh token JWT pada path yang sama."""
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


class LoginAPIView(APIView):
    """Autentikasi pengguna (username atau no_anggota) dan penerbitan JWT."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        tags=['Autentikasi'],
        operation_id='auth_login',
        summary='Login pengguna dan terbitkan JWT',
        description=(
            'Memvalidasi kredensial (username atau Nomor Anggota) menggunakan PBKDF2. '
            'Access token (10 menit) dikembalikan di body JSON, sedangkan refresh token (30 menit) '
            'disimpan pada cookie httpOnly (SameSite=Strict, Path=/api/v1/auth/).'
        ),
        auth=[],
        request=LoginInputSerializer,
        responses={
            200: LoginOutputSerializer,
            400: OpenApiResponse(response=GalatSeragamSerializer, description='Validasi input gagal.'),
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Kredensial tidak valid atau akun nonaktif.'),
            429: OpenApiResponse(response=GalatSeragamSerializer, description='Terlalu banyak percobaan login.'),
        },
    )
    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pengguna = auth_service.autentikasi_pengguna(
            identifier=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            ip_address=auth_service.ambil_ip_klien(request),
        )
        if pengguna is None:
            return buat_respons_galat(
                kode='KREDENSIAL_TIDAK_VALID',
                pesan='Username / Nomor Anggota atau Password tidak valid, atau akun tidak aktif.',
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(pengguna)
        access_token = str(refresh.access_token)

        response = Response(
            {
                'access': access_token,
                'pengguna': PenggunaMeSerializer(pengguna).data,
            },
            status=status.HTTP_200_OK,
        )
        _pasang_cookie_refresh(response, str(refresh))
        return response


class RefreshAPIView(APIView):
    """Menyegarkan access token dari cookie refresh token dengan rotasi & blacklist."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Autentikasi'],
        operation_id='auth_refresh',
        summary='Perbarui access token melalui cookie refresh',
        description=(
            'Membaca refresh token dari cookie httpOnly, merotasi refresh token baru, '
            'memasukkan refresh token lama ke blacklist, dan mengembalikan access token baru.'
        ),
        auth=[],
        request=None,
        responses={
            200: RefreshOutputSerializer,
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Refresh token tidak ada, kedaluwarsa, atau diblacklist.'),
        },
    )
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return buat_respons_galat(
                kode='REFRESH_TOKEN_TIDAK_ADA',
                pesan='Sesi berakhir atau token penyegar tidak ditemukan. Silakan login kembali.',
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            token_obj = RefreshToken(raw_refresh)
        except (TokenError, InvalidToken):
            response = buat_respons_galat(
                kode='REFRESH_TOKEN_TIDAK_VALID',
                pesan='Sesi Anda telah berakhir atau token tidak valid. Silakan login kembali.',
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            _hapus_cookie_refresh(response)
            return response

        user_id = token_obj.get(jwt_api_settings.USER_ID_CLAIM)
        pengguna = Pengguna.objects.filter(pk=user_id).first()
        if pengguna is None or not pengguna.cekStatusAktif():
            try:
                token_obj.blacklist()
            except (TokenError, AttributeError):
                pass
            response = buat_respons_galat(
                kode='AKUN_TIDAK_AKTIF',
                pesan='Akun pengguna tidak aktif. Silakan hubungi pengurus koperasi.',
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            _hapus_cookie_refresh(response)
            return response

        serializer = TokenRefreshSerializer(data={'refresh': raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            response = buat_respons_galat(
                kode='REFRESH_TOKEN_TIDAK_VALID',
                pesan='Sesi Anda telah berakhir atau token tidak valid. Silakan login kembali.',
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            _hapus_cookie_refresh(response)
            return response

        data_token = serializer.validated_data
        response = Response(
            {'access': data_token['access']},
            status=status.HTTP_200_OK,
        )
        if 'refresh' in data_token:
            _pasang_cookie_refresh(response, data_token['refresh'])
        return response


class LogoutAPIView(APIView):
    """Mengakhiri sesi JWT: mem-blacklist refresh token, mencatat AuditTrailLog, dan menghapus cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Autentikasi'],
        operation_id='auth_logout',
        summary='Logout dan blacklist refresh token',
        description=(
            'Memasukkan refresh token dari cookie ke daftar blacklist, mencatat LOGOUT di AuditTrailLog, '
            'serta menghapus cookie refresh token.'
        ),
        request=None,
        responses={
            200: PesanOutputSerializer,
        },
    )
    def post(self, request):
        pengguna_id = None

        # Ambil pengguna dari Bearer token bila masih valid (opsional agar tetap aman meski access sudah expired)
        try:
            hasil_auth = JWTAuthentication().authenticate(request)
            if hasil_auth is not None:
                pengguna_id = hasil_auth[0].id
        except Exception:
            pass

        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if raw_refresh:
            try:
                token_obj = RefreshToken(raw_refresh)
                if pengguna_id is None:
                    pengguna_id = token_obj.get(jwt_api_settings.USER_ID_CLAIM)
                token_obj.blacklist()
            except (TokenError, InvalidToken):
                pass

        if pengguna_id is not None:
            auth_service.catat_logout(
                pengguna_id=pengguna_id,
                ip_address=auth_service.ambil_ip_klien(request),
            )

        response = Response(
            {'pesan': 'Anda telah berhasil keluar dari sistem SI-KKPRIS.'},
            status=status.HTTP_200_OK,
        )
        _hapus_cookie_refresh(response)
        return response


class MeAPIView(APIView):
    """Mengembalikan informasi pengguna yang sedang terautentikasi beserta profil anggota (bila ada)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Autentikasi'],
        operation_id='auth_me',
        summary='Ambil profil pengguna aktif',
        description='Mengembalikan identitas, peran, dan profil ringkas anggota bagi pengguna yang sedang login.',
        responses={
            200: PenggunaMeSerializer,
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Token tidak ada atau tidak valid.'),
        },
    )
    def get(self, request):
        pengguna = Pengguna.objects.select_related('profil_anggota').get(pk=request.user.pk)
        return Response(PenggunaMeSerializer(pengguna).data, status=status.HTTP_200_OK)


class GantiPasswordAPIView(APIView):
    """Mengubah kata sandi pengguna yang sedang terautentikasi."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Autentikasi'],
        operation_id='auth_ganti_password',
        summary='Ganti kata sandi pengguna aktif',
        description='Memvalidasi password lama dan memperbarui password baru (minimal 8 karakter, hash PBKDF2).',
        request=GantiPasswordInputSerializer,
        responses={
            200: PesanOutputSerializer,
            400: OpenApiResponse(response=GalatSeragamSerializer, description='Password lama salah atau validasi gagal.'),
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Token tidak ada atau tidak valid.'),
        },
    )
    def post(self, request):
        serializer = GantiPasswordInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sukses, pesan = auth_service.ganti_password(
            pengguna=request.user,
            password_lama=serializer.validated_data['password_lama'],
            password_baru=serializer.validated_data['password_baru'],
            ip_address=auth_service.ambil_ip_klien(request),
        )
        if not sukses:
            return buat_respons_galat(
                kode='VALIDASI_GAGAL',
                pesan=pesan,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'password_lama': [pesan]},
            )
        return Response({'pesan': pesan}, status=status.HTTP_200_OK)
