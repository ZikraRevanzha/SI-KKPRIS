"""
Permission class berbasis peran (RBAC) untuk REST API v1 SI-KKPRIS.
Selaras dengan dekorator @peran_wajib pada controller MVT lama (AGENTS.md 4.C.2).
"""

from rest_framework.permissions import BasePermission
from koperasi.models import PeranPenggunaChoices


def _memiliki_peran(request, *peran_diizinkan: str) -> bool:
    user = getattr(request, 'user', None)
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_active', False)
        and getattr(user, 'peran', None) in peran_diizinkan
    )


class IsAnggota(BasePermission):
    message = 'Akses ditolak: Endpoint ini hanya dapat diakses oleh Anggota.'

    def has_permission(self, request, view) -> bool:
        return _memiliki_peran(request, PeranPenggunaChoices.ANGGOTA)


class IsBendahara(BasePermission):
    message = 'Akses ditolak: Endpoint ini hanya dapat diakses oleh Bendahara Koperasi.'

    def has_permission(self, request, view) -> bool:
        return _memiliki_peran(request, PeranPenggunaChoices.BENDAHARA)


class IsKetua(BasePermission):
    message = 'Akses ditolak: Endpoint ini hanya dapat diakses oleh Ketua Koperasi.'

    def has_permission(self, request, view) -> bool:
        return _memiliki_peran(request, PeranPenggunaChoices.KETUA)


class IsBendaharaAtauKetua(BasePermission):
    message = 'Akses ditolak: Endpoint ini hanya dapat diakses oleh Bendahara atau Ketua Koperasi.'

    def has_permission(self, request, view) -> bool:
        return _memiliki_peran(
            request,
            PeranPenggunaChoices.BENDAHARA,
            PeranPenggunaChoices.KETUA,
        )
