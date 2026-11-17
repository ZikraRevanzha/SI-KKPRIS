"""
URL Routing Aplikasi Koperasi SI-KKPRIS (Lengkap Tahap 1 s.d. Tahap 7).
"""

from django.urls import path
from koperasi.controllers import (
    anggota_controller,
    auth_controller,
    laporan_bukti_controller,
    pembiayaan_controller,
    rekap_notifikasi_controller,
    simpanan_controller,
)

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

    # Transaksi Multi-Simpanan Anggota (Tahap 4 — UC-02, UC-10, UC-13)
    path('simpanan/', simpanan_controller.kelola_simpanan_router_view, name='kelola_simpanan'),
    path(
        'simpanan/tambah/',
        simpanan_controller.tambah_transaksi_simpanan_view,
        name='tambah_transaksi_simpanan',
    ),
    path(
        'simpanan/ekspor/',
        simpanan_controller.ekspor_simpanan_excel_view,
        name='ekspor_simpanan_excel',
    ),
    path(
        'simpanan/kuitansi/<str:no_kuitansi>/',
        simpanan_controller.cetak_kuitansi_simpanan_view,
        name='cetak_kuitansi_simpanan',
    ),

    # Pembiayaan Syariah, Agunan, Approval Kas & Realisasi (Tahap 5 — UC-03, UC-04, UC-06, UC-07)
    path(
        'pembiayaan/',
        pembiayaan_controller.kelola_pembiayaan_router_view,
        name='kelola_pembiayaan',
    ),
    path(
        'pembiayaan/ajukan/',
        pembiayaan_controller.ajukan_pembiayaan_view,
        name='ajukan_pembiayaan',
    ),
    path(
        'pembiayaan/ekspor/',
        pembiayaan_controller.ekspor_pembiayaan_excel_view,
        name='ekspor_pembiayaan_excel',
    ),
    path(
        'pembiayaan/<int:pembiayaan_id>/',
        pembiayaan_controller.detail_pembiayaan_view,
        name='detail_pembiayaan',
    ),
    path(
        'pembiayaan/<int:pembiayaan_id>/verifikasi/',
        pembiayaan_controller.verifikasi_bendahara_view,
        name='verifikasi_pembiayaan_bendahara',
    ),
    path(
        'pembiayaan/<int:pembiayaan_id>/realisasi/',
        pembiayaan_controller.catat_realisasi_pencairan_view,
        name='catat_realisasi_pencairan',
    ),
    path(
        'persetujuan-kas/',
        pembiayaan_controller.persetujuan_kas_view,
        name='persetujuan_kas',
    ),
    path(
        'persetujuan-kas/<int:pembiayaan_id>/proses/',
        pembiayaan_controller.proses_persetujuan_kas_view,
        name='proses_persetujuan_kas',
    ),

    # Rekap Potong Gaji (Tgl 24), Kelola Angsuran & Notifikasi Tagihan (Tahap 6 — UC-11, UC-12, UC-14)
    path(
        'angsuran/',
        rekap_notifikasi_controller.kelola_angsuran_view,
        name='kelola_angsuran',
    ),
    path(
        'angsuran/<int:jadwal_id>/bayar/',
        rekap_notifikasi_controller.catat_pembayaran_angsuran_view,
        name='catat_pembayaran_angsuran',
    ),
    path(
        'angsuran/kuitansi/<str:no_kuitansi>/',
        rekap_notifikasi_controller.cetak_kuitansi_angsuran_view,
        name='cetak_kuitansi_angsuran',
    ),
    path(
        'rekap-potong-gaji/',
        rekap_notifikasi_controller.rekap_potong_gaji_view,
        name='rekap_potong_gaji',
    ),
    path(
        'rekap-potong-gaji/generate/',
        rekap_notifikasi_controller.generate_rekap_potong_gaji_view,
        name='generate_rekap_potong_gaji',
    ),
    path(
        'rekap-potong-gaji/detail/<int:detail_id>/update-toko/',
        rekap_notifikasi_controller.update_potongan_toko_rekap_view,
        name='update_potongan_toko_rekap',
    ),
    path(
        'rekap-potong-gaji/<int:rekap_id>/konfirmasi-lunas/',
        rekap_notifikasi_controller.konfirmasi_lunas_rekap_gaji_view,
        name='konfirmasi_lunas_rekap_gaji',
    ),
    path(
        'rekap-potong-gaji/<int:rekap_id>/ekspor/',
        rekap_notifikasi_controller.ekspor_rekap_potong_gaji_view,
        name='ekspor_rekap_potong_gaji',
    ),
    path(
        'notifikasi-tagihan/',
        rekap_notifikasi_controller.notifikasi_tagihan_view,
        name='notifikasi_tagihan',
    ),

    # Kuitansi Digital PDF, Laporan Keuangan (Triwulanan & RAT) & Audit Trail Log (Tahap 7 — UC-13, UC-15)
    path(
        'laporan-keuangan/',
        laporan_bukti_controller.laporan_keuangan_view,
        name='laporan_keuangan',
    ),
    path(
        'laporan-keuangan/ekspor/',
        laporan_bukti_controller.ekspor_laporan_keuangan_view,
        name='ekspor_laporan_keuangan',
    ),
    path(
        'kuitansi/<str:no_kuitansi>/pdf/',
        laporan_bukti_controller.unduh_kuitansi_pdf_view,
        name='unduh_kuitansi_pdf',
    ),
    path(
        'audit-trail/',
        laporan_bukti_controller.audit_trail_log_view,
        name='audit_trail_log',
    ),
]
