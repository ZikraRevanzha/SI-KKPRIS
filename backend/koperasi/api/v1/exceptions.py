"""
Exception handler seragam untuk seluruh endpoint REST API SI-KKPRIS.
Format respons galat wajib mengikuti AGENTS.md Bagian 4.C.3:
{ "kode": "...", "pesan": "...", "detail": { "field": ["..."] } }
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def _normalisasi_detail_validasi(data) -> dict[str, list[str]]:
    """Menormalisasi struktur galat validasi DRF menjadi dict[str, list[str]]."""
    if isinstance(data, dict):
        hasil: dict[str, list[str]] = {}
        for kunci, nilai in data.items():
            if isinstance(nilai, list):
                hasil[str(kunci)] = [str(item) for item in nilai]
            elif isinstance(nilai, dict):
                sub = _normalisasi_detail_validasi(nilai)
                for sub_kunci, sub_nilai in sub.items():
                    hasil[f"{kunci}.{sub_kunci}"] = sub_nilai
            else:
                hasil[str(kunci)] = [str(nilai)]
        return hasil
    if isinstance(data, list):
        return {'non_field_errors': [str(item) for item in data]}
    return {'non_field_errors': [str(data)]}


def buat_respons_galat(
    kode: str,
    pesan: str,
    status_code: int,
    detail: dict[str, list[str]] | None = None,
) -> Response:
    """Helper untuk membuat Response galat seragam pada view DRF."""
    return Response(
        {
            'kode': kode,
            'pesan': pesan,
            'detail': detail if detail is not None else {},
        },
        status=status_code,
    )


def handler_galat_seragam(exc, context):
    """Mengubah seluruh exception DRF & validasi Django menjadi format galat seragam Bahasa Indonesia."""
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            exc = DRFValidationError(exc.message_dict)
        else:
            exc = DRFValidationError({'non_field_errors': exc.messages})

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, DRFValidationError):
        detail = _normalisasi_detail_validasi(response.data)
        pesan_non_field = detail.get('non_field_errors')
        pesan = pesan_non_field[0] if pesan_non_field else 'Data yang dikirimkan tidak valid.'
        response.data = {
            'kode': 'VALIDASI_GAGAL',
            'pesan': pesan,
            'detail': detail,
        }
        return response

    if isinstance(exc, NotAuthenticated):
        response.data = {
            'kode': 'AUTENTIKASI_DIPERLUKAN',
            'pesan': 'Autentikasi diperlukan. Silakan login terlebih dahulu.',
            'detail': {},
        }
        return response

    if isinstance(exc, (InvalidToken, TokenError, AuthenticationFailed)):
        response.data = {
            'kode': 'AUTENTIKASI_GAGAL',
            'pesan': 'Token tidak valid atau sesi telah berakhir. Silakan login kembali.',
            'detail': {},
        }
        return response

    if isinstance(exc, PermissionDenied):
        pesan_asli = str(exc.detail) if getattr(exc, 'detail', None) else ''
        if not pesan_asli or pesan_asli == 'You do not have permission to perform this action.':
            pesan = 'Akses ditolak: Anda tidak memiliki izin untuk mengakses sumber daya ini.'
        else:
            pesan = pesan_asli
        response.data = {
            'kode': 'AKSES_DITOLAK',
            'pesan': pesan,
            'detail': {},
        }
        return response

    if isinstance(exc, (NotFound, Http404)):
        response.data = {
            'kode': 'TIDAK_DITEMUKAN',
            'pesan': 'Data yang diminta tidak ditemukan.',
            'detail': {},
        }
        return response

    if isinstance(exc, MethodNotAllowed):
        response.data = {
            'kode': 'METODE_TIDAK_DIIZINKAN',
            'pesan': 'Metode HTTP tidak diizinkan pada endpoint ini.',
            'detail': {},
        }
        return response

    if isinstance(exc, Throttled):
        if exc.wait is not None:
            detik = max(1, int(exc.wait))
            pesan = f'Terlalu banyak percobaan. Silakan coba lagi dalam {detik} detik.'
        else:
            pesan = 'Terlalu banyak percobaan. Silakan coba lagi beberapa saat lagi.'
        response.data = {
            'kode': 'TERLALU_BANYAK_PERMINTAAN',
            'pesan': pesan,
            'detail': {},
        }
        return response

    kode_bawaan = (
        'GALAT_SERVER'
        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
        else 'PERMINTAAN_GAGAL'
    )
    pesan_bawaan = str(getattr(exc, 'detail', 'Terjadi kesalahan saat memproses permintaan.'))
    response.data = {
        'kode': kode_bawaan,
        'pesan': pesan_bawaan,
        'detail': {},
    }
    return response
