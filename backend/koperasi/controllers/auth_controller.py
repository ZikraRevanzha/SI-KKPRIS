"""
AuthController & Base Dashboard Views (Tahap 2 — UC-01, FR-AUTH-01 s.d. FR-AUTH-03).
Mengelola autentikasi multi-peran (ANGGOTA, BENDAHARA, KETUA), RBAC, Session Timeout,
serta pencatatan otomatis AuditTrailLog.
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect, render
from koperasi.models import (
    Pengguna,
    PeranPenggunaChoices,
)
from koperasi.services import auth_service, dashboard_service


def _ambil_ip_klien(request) -> str:
    """Wrapper kompatibilitas untuk auth_service.ambil_ip_klien."""
    return auth_service.ambil_ip_klien(request)


def ambil_pengguna_aktif(request):
    """Mengambil objek Pengguna dari session aktif jika masih valid dan is_aktif=True."""
    pengguna_id = request.session.get('pengguna_id')
    if not pengguna_id:
        return None
    try:
        pengguna = Pengguna.objects.select_related('profil_anggota').get(
            pk=pengguna_id,
            is_aktif=True,
        )
        return pengguna
    except Pengguna.DoesNotExist:
        request.session.flush()
        return None


# ============================================================================
# DEKORATOR RBAC (Role-Based Access Control — FR-AUTH-02)
# ============================================================================

def login_wajib(view_func):
    """Memastikan pengguna telah login dan sesinya masih aktif."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        pengguna = ambil_pengguna_aktif(request)
        if not pengguna:
            messages.warning(request, 'Sesi Anda telah berakhir atau Anda belum masuk. Silakan login kembali.')
            return redirect('login')
        request.pengguna = pengguna
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def peran_wajib(*peran_diizinkan):
    """Membatasi akses halaman hanya untuk peran tertentu (ANGGOTA / BENDAHARA / KETUA)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_wajib
        def _wrapped_view(request, *args, **kwargs):
            if request.pengguna.peran not in peran_diizinkan:
                auth_service.catat_akses_ditolak(
                    pengguna_id=request.pengguna.id,
                    peran=request.pengguna.peran,
                    path=request.path,
                    ip_address=_ambil_ip_klien(request),
                )
                messages.error(
                    request,
                    f"Akses ditolak: Halaman tersebut hanya dapat diakses oleh {', '.join(peran_diizinkan)}.",
                )
                return redirect('root_redirect')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# ============================================================================
# CLASS CONTROLLER: AuthController (Sesuai 03_Class_Diagram_SI-KKPRIS.mmd)
# ============================================================================

class AuthController:
    """
    Controller Autentikasi & Otorisasi SI-KKPRIS (UC-01).
    Mendelegasikan logika autentikasi, logout, dan ganti password ke koperasi.services.auth_service.
    """

    @staticmethod
    def login(identifier: str, password: str, ip_address: str = '127.0.0.1'):
        """Memvalidasi kredensial (username atau no_anggota) melalui auth_service."""
        return auth_service.autentikasi_pengguna(
            identifier=identifier,
            password=password,
            ip_address=ip_address,
        )

    @staticmethod
    def logout(pengguna_id: int, ip_address: str = '127.0.0.1') -> bool:
        """Mencatat jejak logout pada AuditTrailLog melalui auth_service."""
        return auth_service.catat_logout(
            pengguna_id=pengguna_id,
            ip_address=ip_address,
        )

    @staticmethod
    def gantiPassword(
        pengguna: Pengguna,
        password_lama: str,
        password_baru: str,
        ip_address: str = '127.0.0.1',
    ) -> tuple[bool, str]:
        """Memvalidasi password lama dan memperbarui password baru melalui auth_service."""
        return auth_service.ganti_password(
            pengguna=pengguna,
            password_lama=password_lama,
            password_baru=password_baru,
            ip_address=ip_address,
        )


# ============================================================================
# DJANGO VIEWS: Login, Logout, Ganti Password, Dashboard & Beranda Anggota
# ============================================================================

def root_redirect_view(request):
    """Mengarahkan pengguna ke halaman sesuai status login dan perannya."""
    pengguna = ambil_pengguna_aktif(request)
    if not pengguna:
        return redirect('login')
    if pengguna.peran in (PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA):
        return redirect('dashboard_pengurus')
    return redirect('beranda_anggota')


def login_view(request):
    """Menampilkan dan memproses Halaman Login (Sesuai Wireframe Login.png)."""
    pengguna_aktif = ambil_pengguna_aktif(request)
    if pengguna_aktif:
        return redirect('root_redirect')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        ingat_saya = request.POST.get('remember_me') == 'on'

        pengguna = AuthController.login(
            identifier=identifier,
            password=password,
            ip_address=_ambil_ip_klien(request),
        )
        if pengguna:
            request.session['pengguna_id'] = pengguna.id
            request.session['username'] = pengguna.username
            request.session['nama_lengkap'] = pengguna.nama_lengkap
            request.session['peran'] = pengguna.peran
            # Jika "Ingat saya" dicentang, perpanjang sesi ke 12 jam; jika tidak, 30 menit (FR-AUTH-03)
            request.session.set_expiry(43200 if ingat_saya else 1800)

            messages.success(
                request,
                f"Selamat datang kembali, {pengguna.nama_lengkap} ({pengguna.get_peran_display()}).",
            )
            return redirect('root_redirect')

        messages.error(
            request,
            'Username / Nomor Anggota atau Password tidak valid, atau akun tidak aktif.',
        )

    return render(request, 'auth/login.html')


def logout_view(request):
    """Memproses keluar (logout) pengguna dan membersihkan session."""
    pengguna_id = request.session.get('pengguna_id')
    if pengguna_id:
        AuthController.logout(pengguna_id=pengguna_id, ip_address=_ambil_ip_klien(request))
    request.session.flush()
    messages.info(request, 'Anda telah berhasil keluar dari sistem SI-KKPRIS.')
    return redirect('login')


@login_wajib
def ganti_password_view(request):
    """Memproses penggantian password pengguna yang sedang login (FR-AUTH-03)."""
    if request.method == 'POST':
        password_lama = request.POST.get('password_lama', '')
        password_baru = request.POST.get('password_baru', '')
        konfirmasi = request.POST.get('konfirmasi_password', '')

        if password_baru != konfirmasi:
            messages.error(request, 'Konfirmasi password baru tidak cocok.')
        else:
            sukses, pesan = AuthController.gantiPassword(
                pengguna=request.pengguna,
                password_lama=password_lama,
                password_baru=password_baru,
                ip_address=_ambil_ip_klien(request),
            )
            if sukses:
                messages.success(request, pesan)
            else:
                messages.error(request, pesan)

    return redirect(request.META.get('HTTP_REFERER') or 'root_redirect')


@peran_wajib(PeranPenggunaChoices.BENDAHARA, PeranPenggunaChoices.KETUA)
def dashboard_pengurus_view(request):
    """
    Menampilkan Halaman Dashboard Pengurus (Bendahara & Ketua)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Dashboard.png.
    """
    ringkasan = dashboard_service.ambil_ringkasan_dashboard_pengurus()
    context = {
        'active_menu': 'dashboard',
        **ringkasan,
    }
    return render(request, 'dashboard/dashboard_pengurus.html', context)


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def beranda_anggota_view(request):
    """
    Menampilkan Halaman Portal Mandiri Anggota (Beranda Anggota)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Beranda Anggota.png.
    """
    ringkasan = dashboard_service.ambil_ringkasan_beranda_anggota(request.pengguna)
    context = {
        'active_menu': 'beranda',
        **ringkasan,
    }
    return render(request, 'dashboard/beranda_anggota.html', context)


@login_wajib
def modul_terjadwal_view(request, nama_modul: str, tahap: int):
    """Halaman informasi bersih untuk menu navigasi yang dijadwalkan pada Tahap 3 s.d. 7."""
    context = {
        'active_menu': nama_modul.lower().replace(' ', '_'),
        'nama_modul': nama_modul,
        'tahap': tahap,
    }
    return render(request, 'dashboard/modul_terjadwal.html', context)

