"""
AuthController & Base Dashboard Views (Tahap 2 — UC-01, FR-AUTH-01 s.d. FR-AUTH-03).
Mengelola autentikasi multi-peran (ANGGOTA, BENDAHARA, KETUA), RBAC, Session Timeout,
serta pencatatan otomatis AuditTrailLog.
"""

from datetime import date
from decimal import Decimal
from functools import wraps
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JadwalAngsuran,
    JenisAkad,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    NamaAkadChoices,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PeranPenggunaChoices,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)
from koperasi.services import auth_service


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
    hari_ini = date.today()

    # 1. Kartu Statistik #1: Total Anggota
    total_anggota_aktif = Anggota.objects.filter(status=StatusAnggotaChoices.AKTIF).count()
    total_seluruh_anggota = Anggota.objects.count()

    # 2. Kartu Statistik #2: Total Simpanan Keseluruhan
    agregat_simpanan = TransaksiSimpanan.objects.aggregate(
        total_setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
        total_tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
    )
    total_setor = agregat_simpanan['total_setor'] or Decimal('0.00')
    total_tarik = agregat_simpanan['total_tarik'] or Decimal('0.00')
    total_simpanan = total_setor - total_tarik

    # 3. Kartu Statistik #3: Pembiayaan Aktif & Menunggu Approval
    qs_pembiayaan_aktif = Pembiayaan.objects.filter(status=StatusPembiayaanChoices.AKTIF)
    jumlah_pembiayaan_aktif = qs_pembiayaan_aktif.count()
    sisa_tagihan_aktif = (
        JadwalAngsuran.objects.filter(
            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
        ).aggregate(total=Sum('jumlah_angsuran'))['total']
        or Decimal('0.00')
    )
    menunggu_approval_ketua = Pembiayaan.objects.filter(
        status__in=[
            StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
            StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
            StatusPembiayaanChoices.DISETUJUI_KETUA,
        ]
    ).count()

    # 4. Kartu Statistik #4: Kas Hari Ini (Setoran Simpanan + Pembayaran Angsuran Hari Ini)
    setor_hari_ini = (
        TransaksiSimpanan.objects.filter(
            tanggal_transaksi__date=hari_ini,
            jenis_transaksi=JenisTransaksiSimpananChoices.SETOR,
        ).aggregate(total=Sum('nominal'))['total']
        or Decimal('0.00')
    )
    angsuran_hari_ini = (
        PembayaranAngsuran.objects.filter(tanggal_bayar__date=hari_ini).aggregate(
            total=Sum('nominal_bayar')
        )['total']
        or Decimal('0.00')
    )
    kas_hari_ini = setor_hari_ini + angsuran_hari_ini

    # 5. Distribusi Akad Syariah (Murabahah, Ijarah, Hawalah)
    distribusi_akad = []
    total_kontrak_akad = Pembiayaan.objects.count() or 1
    for kode_nama, label_nama in NamaAkadChoices.choices:
        jml = Pembiayaan.objects.filter(jenis_akad__nama=kode_nama).count()
        nominal_akad = (
            Pembiayaan.objects.filter(jenis_akad__nama=kode_nama).aggregate(
                total=Sum('harga_pokok')
            )['total']
            or Decimal('0.00')
        )
        persen = round((jml / total_kontrak_akad) * 100) if Pembiayaan.objects.exists() else 0
        distribusi_akad.append({
            'kode': kode_nama,
            'label': label_nama,
            'jumlah': jml,
            'nominal': nominal_akad,
            'persen': persen,
        })

    # 6. Ringkasan Saldo per 5 Jenis Simpanan untuk Grafik Tren Simpanan
    rincian_jenis_simpanan = []
    max_saldo_jenis = Decimal('1.00')
    for js in JenisSimpanan.objects.all():
        agg = TransaksiSimpanan.objects.filter(jenis_simpanan=js).aggregate(
            setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
            tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
        )
        saldo_js = (agg['setor'] or Decimal('0.00')) - (agg['tarik'] or Decimal('0.00'))
        if saldo_js > max_saldo_jenis:
            max_saldo_jenis = saldo_js
        rincian_jenis_simpanan.append({
            'kode': js.kode,
            'nama': js.nama,
            'saldo': saldo_js,
            'dapat_ditarik': js.dapat_ditarik,
        })
    for item in rincian_jenis_simpanan:
        item['tinggi_persen'] = max(12, int((item['saldo'] / max_saldo_jenis) * 100)) if item['saldo'] > 0 else 8

    # 7. Aktivitas Terbaru (Gabungan Transaksi & Jejak Audit Terbaru)
    aktivitas_terbaru = AuditTrailLog.objects.select_related('pengguna')[:6]

    context = {
        'active_menu': 'dashboard',
        'hari_ini': hari_ini,
        'total_anggota_aktif': total_anggota_aktif,
        'total_seluruh_anggota': total_seluruh_anggota,
        'total_simpanan': total_simpanan,
        'jumlah_pembiayaan_aktif': jumlah_pembiayaan_aktif,
        'sisa_tagihan_aktif': sisa_tagihan_aktif,
        'menunggu_approval_ketua': menunggu_approval_ketua,
        'kas_hari_ini': kas_hari_ini,
        'distribusi_akad': distribusi_akad,
        'rincian_jenis_simpanan': rincian_jenis_simpanan,
        'aktivitas_terbaru': aktivitas_terbaru,
    }
    return render(request, 'dashboard/dashboard_pengurus.html', context)


@peran_wajib(PeranPenggunaChoices.ANGGOTA)
def beranda_anggota_view(request):
    """
    Menampilkan Halaman Portal Mandiri Anggota (Beranda Anggota)
    Sesuai Wireframe: 01_Wireframe_Final_PNG/Beranda Anggota.png.
    """
    anggota = getattr(request.pengguna, 'profil_anggota', None)

    # 1. 5 Kartu Saldo Simpanan (Pokok, Wajib, Khusus, Hari Raya, Berencana)
    urutan_kode = ['SPK', 'SWJ', 'SKH', 'SHR', 'SBR']
    peta_jenis = {js.kode: js for js in JenisSimpanan.objects.all()}
    kartu_simpanan = []
    total_simpanan_anggota = Decimal('0.00')

    for kode in urutan_kode:
        js = peta_jenis.get(kode)
        if not js:
            continue
        saldo = (
            TransaksiSimpanan.hitungSaldoBerjalan(anggota.id, js.id)
            if anggota
            else Decimal('0.00')
        )
        total_simpanan_anggota += saldo
        label_singkat = js.nama.replace('Simpanan ', '')
        kartu_simpanan.append({
            'kode': js.kode,
            'nama': label_singkat,
            'nama_lengkap': js.nama,
            'saldo': saldo,
            'dapat_ditarik': js.dapat_ditarik,
        })

    # 2. Status Pembiayaan Aktif / Terakhir Milik Anggota
    pembiayaan_aktif = None
    sisa_kewajiban = Decimal('0.00')
    angsuran_lunas_count = 0
    total_tenor = 0
    progress_persen = 0

    if anggota:
        pembiayaan_aktif = (
            Pembiayaan.objects.select_related('jenis_akad')
            .filter(anggota=anggota)
            .order_by('-id')
            .first()
        )
        if pembiayaan_aktif:
            total_tenor = pembiayaan_aktif.tenor_bulan
            angsuran_lunas_count = JadwalAngsuran.objects.filter(
                pembiayaan=pembiayaan_aktif,
                status_bayar=StatusBayarAngsuranChoices.LUNAS,
            ).count()
            sisa_kewajiban = (
                JadwalAngsuran.objects.filter(
                    pembiayaan=pembiayaan_aktif,
                    status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
                ).aggregate(sisa=Sum('jumlah_angsuran'))['sisa']
                or Decimal('0.00')
            )
            if total_tenor > 0:
                progress_persen = int((angsuran_lunas_count / total_tenor) * 100)

    # 3. Tabel Riwayat Terakhir (Mutasi Simpanan & Pembayaran Angsuran Anggota)
    riwayat_terakhir = []
    if anggota:
        for ts in TransaksiSimpanan.objects.select_related('jenis_simpanan').filter(anggota=anggota)[:5]:
            riwayat_terakhir.append({
                'tanggal': ts.tanggal_transaksi,
                'jenis': f"{ts.get_jenis_transaksi_display()} - {ts.jenis_simpanan.nama}",
                'keterangan': ts.keterangan or f"Kuitansi {ts.no_kuitansi} ({ts.get_metode_bayar_display()})",
                'jumlah': ts.nominal,
                'status': 'SELESAI',
                'tipe_badge': 'success' if ts.jenis_transaksi == 'SETOR' else 'warning',
            })
        for pa in PembayaranAngsuran.objects.select_related('jadwal_angsuran', 'jadwal_angsuran__pembiayaan').filter(
            jadwal_angsuran__pembiayaan__anggota=anggota
        )[:5]:
            riwayat_terakhir.append({
                'tanggal': pa.tanggal_bayar,
                'jenis': f"Angsuran Ke-{pa.jadwal_angsuran.angsuran_ke} ({pa.jadwal_angsuran.pembiayaan.no_pembiayaan})",
                'keterangan': f"Kuitansi {pa.no_kuitansi} ({pa.get_metode_bayar_display()})",
                'jumlah': pa.nominal_bayar,
                'status': 'LUNAS',
                'tipe_badge': 'success',
            })
        riwayat_terakhir.sort(key=lambda x: x['tanggal'], reverse=True)
        riwayat_terakhir = riwayat_terakhir[:6]

    context = {
        'active_menu': 'beranda',
        'anggota': anggota,
        'kartu_simpanan': kartu_simpanan,
        'total_simpanan_anggota': total_simpanan_anggota,
        'pembiayaan_aktif': pembiayaan_aktif,
        'sisa_kewajiban': sisa_kewajiban,
        'angsuran_lunas_count': angsuran_lunas_count,
        'total_tenor': total_tenor,
        'progress_persen': progress_persen,
        'riwayat_terakhir': riwayat_terakhir,
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

