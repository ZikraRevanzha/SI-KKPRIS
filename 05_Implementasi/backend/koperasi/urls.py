"""
URL Routing Aplikasi Koperasi SI-KKPRIS.
"""

from django.urls import path
from koperasi.controllers import anggota_controller, auth_controller

urlpatterns = [
    # Root & Autentikasi (Tahap 2 — UC-01)
    path('', auth_controller.root_redirect_view, name='root_redirect'),
    path('login/', auth_controller.login_view, name='login'),
    path('logout/', auth_controller.logout_view, name='logout'),
    path('ganti-password/', auth_controller.ganti_password_view, name='ganti_password'),

    # Dashboard Pengurus (Bendahara & Ketua) & Beranda Mandiri Anggota (Tahap 2)
    path('dashboard/', auth_controller.dashboard_pengurus_view, name='dashboard_pengurus'),
    path('beranda/', auth_controller.beranda_anggota_view, name='beranda_anggota'),

    # Manajemen Keanggotaan & Kliring Pengunduran Diri (Tahap 3 — UC-05, UC-08, UC-09)
    path('anggota/', anggota_controller.data_anggota_view, name='data_anggota'),
    path('anggota/tambah/', anggota_controller.tambah_anggota_view, name='tambah_anggota'),
    path('anggota/<int:anggota_id>/edit/', anggota_controller.edit_anggota_view, name='edit_anggota'),
    path('pengunduran-diri/', anggota_controller.pengunduran_diri_router_view, name='pengunduran_diri'),
    path(
        'anggota/verifikasi-resign/',
        anggota_controller.verifikasi_pengunduran_diri_view,
        name='verifikasi_pengunduran_diri',
    ),
    path(
        'anggota/verifikasi-resign/<int:pengunduran_id>/proses/',
        anggota_controller.proses_verifikasi_resign_view,
        name='proses_verifikasi_resign',
    ),

    # Rute Menu Sidebar untuk Tahap 4 s.d. Tahap 7 (Akan diaktifkan penuh per tahapan)
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
