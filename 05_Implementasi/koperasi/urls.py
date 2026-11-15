"""
URL Routing Aplikasi Koperasi SI-KKPRIS.
"""

from django.urls import path
from koperasi.controllers import auth_controller

urlpatterns = [
    # Root & Autentikasi (Tahap 2 — UC-01)
    path('', auth_controller.root_redirect_view, name='root_redirect'),
    path('login/', auth_controller.login_view, name='login'),
    path('logout/', auth_controller.logout_view, name='logout'),
    path('ganti-password/', auth_controller.ganti_password_view, name='ganti_password'),

    # Dashboard Pengurus (Bendahara & Ketua) & Beranda Mandiri Anggota (Tahap 2)
    path('dashboard/', auth_controller.dashboard_pengurus_view, name='dashboard_pengurus'),
    path('beranda/', auth_controller.beranda_anggota_view, name='beranda_anggota'),

    # Rute Menu Sidebar untuk Tahap 3 s.d. Tahap 7 (Akan diaktifkan penuh per tahapan)
    path(
        'anggota/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Data Anggota', 'tahap': 3},
        name='data_anggota',
    ),
    path(
        'pengunduran-diri/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Pengunduran Diri', 'tahap': 3},
        name='pengunduran_diri',
    ),
    path(
        'simpanan/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Simpanan', 'tahap': 4},
        name='kelola_simpanan',
    ),
    path(
        'pembiayaan/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Pembiayaan Syariah', 'tahap': 5},
        name='kelola_pembiayaan',
    ),
    path(
        'persetujuan-kas/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Persetujuan Pengeluaran Kas', 'tahap': 5},
        name='persetujuan_kas',
    ),
    path(
        'angsuran/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Kelola Angsuran', 'tahap': 6},
        name='kelola_angsuran',
    ),
    path(
        'rekap-potong-gaji/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Rekap Potong Gaji (Tgl 24)', 'tahap': 6},
        name='rekap_potong_gaji',
    ),
    path(
        'notifikasi-tagihan/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Notifikasi Tagihan (Tgl 10)', 'tahap': 6},
        name='notifikasi_tagihan',
    ),
    path(
        'laporan-keuangan/',
        auth_controller.modul_terjadwal_view,
        {'nama_modul': 'Laporan Keuangan & RAT', 'tahap': 7},
        name='laporan_keuangan',
    ),
]

