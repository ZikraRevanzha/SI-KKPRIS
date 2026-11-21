"""
Service autentikasi dan pencatatan audit trail SI-KKPRIS (UC-01, FR-AUTH-01 s.d. FR-AUTH-03).
Digunakan bersama oleh controller MVT lama (AuthController) dan REST API v1 (auth_views).
"""

from django.conf import settings
from django.utils import timezone
from koperasi.models import Anggota, AuditTrailLog, Pengguna


def ambil_ip_klien(request) -> str:
    """
    Mengambil alamat IP pengguna untuk AuditTrailLog.
    Mempercayai REMOTE_ADDR secara baku; X-Forwarded-For hanya dibaca jika settings.TRUSTED_PROXY=True.
    """
    if getattr(settings, 'TRUSTED_PROXY', False):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '127.0.0.1')[:45]


def autentikasi_pengguna(
    identifier: str,
    password: str,
    ip_address: str = '127.0.0.1',
) -> Pengguna | None:
    """
    Memvalidasi kredensial (username atau no_anggota) terhadap hash PBKDF2 dan mencatat AuditTrailLog.
    Mengembalikan objek Pengguna jika valid dan aktif, atau None jika gagal.
    """
    ident = (identifier or '').strip()
    if not ident or not password:
        return None

    pengguna = Pengguna.objects.select_related('profil_anggota').filter(username=ident).first()
    if not pengguna:
        anggota = Anggota.objects.select_related('pengguna', 'pengguna__profil_anggota').filter(
            no_anggota__iexact=ident
        ).first()
        if anggota:
            pengguna = anggota.pengguna

    if not pengguna or not pengguna.cekStatusAktif():
        return None

    if pengguna.check_password(password):
        pengguna.last_login = timezone.now()
        pengguna.save(update_fields=['last_login'])
        AuditTrailLog.catatLogAudit(
            pengguna_id=pengguna.id,
            aksi='LOGIN_BERHASIL',
            nama_tabel='pengguna',
            record_id=pengguna.id,
            detail=f"Pengguna {pengguna.username} ({pengguna.peran}) berhasil masuk ke sistem.",
            ip_address=ip_address,
        )
        return pengguna

    AuditTrailLog.catatLogAudit(
        pengguna_id=pengguna.id,
        aksi='LOGIN_GAGAL',
        nama_tabel='pengguna',
        record_id=pengguna.id,
        detail=f"Percobaan login gagal (password salah) untuk akun {pengguna.username}.",
        ip_address=ip_address,
    )
    return None


def catat_logout(pengguna_id: int, ip_address: str = '127.0.0.1') -> bool:
    """Mencatat jejak logout pada AuditTrailLog."""
    if pengguna_id and Pengguna.objects.filter(pk=pengguna_id).exists():
        AuditTrailLog.catatLogAudit(
            pengguna_id=pengguna_id,
            aksi='LOGOUT',
            nama_tabel='pengguna',
            record_id=pengguna_id,
            detail='Pengguna keluar (logout) dari sistem SI-KKPRIS.',
            ip_address=ip_address,
        )
        return True
    return False


def ganti_password(
    pengguna: Pengguna,
    password_lama: str,
    password_baru: str,
    ip_address: str = '127.0.0.1',
) -> tuple[bool, str]:
    """Memvalidasi password lama dan memperbarui password baru dengan hash PBKDF2."""
    if not pengguna.check_password(password_lama):
        return False, 'Password lama yang Anda masukkan tidak sesuai.'
    if len(password_baru) < 8:
        return False, 'Password baru minimal harus terdiri dari 8 karakter.'

    pengguna.set_password(password_baru)
    pengguna.save(update_fields=['password'])

    AuditTrailLog.catatLogAudit(
        pengguna_id=pengguna.id,
        aksi='GANTI_PASSWORD',
        nama_tabel='pengguna',
        record_id=pengguna.id,
        detail=f"Pengguna {pengguna.username} berhasil memperbarui kata sandi akun.",
        ip_address=ip_address,
    )
    return True, 'Kata sandi Anda berhasil diperbarui.'


def catat_akses_ditolak(
    pengguna_id: int,
    peran: str,
    path: str,
    ip_address: str = '127.0.0.1',
) -> None:
    """Mencatat percobaan akses tidak sah pada AuditTrailLog."""
    AuditTrailLog.catatLogAudit(
        pengguna_id=pengguna_id,
        aksi='AKSES_DITOLAK_RBAC',
        nama_tabel='pengguna',
        record_id=pengguna_id,
        detail=f"Percobaan akses tidak sah ke {path} oleh peran {peran}",
        ip_address=ip_address,
    )
