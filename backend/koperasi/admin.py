"""
Konfigurasi Django Admin untuk 16 Model SI-KKPRIS.
Termasuk proteksi append-only pada AuditTrailLog (NFR Auditability).
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import (
    Agunan,
    Anggota,
    AuditTrailLog,
    DetailRekapPotongGaji,
    JadwalAngsuran,
    JenisAkad,
    JenisSimpanan,
    NotifikasiTagihan,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PengunduranDiri,
    PersetujuanPembiayaan,
    RealisasiPencairan,
    RekapPotongGaji,
    TransaksiSimpanan,
)


class PenggunaCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Pengguna
        fields = ('username', 'nama_lengkap', 'peran', 'is_aktif', 'is_staff')


class PenggunaChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Pengguna
        fields = '__all__'


@admin.register(Pengguna)
class PenggunaAdmin(BaseUserAdmin):
    form = PenggunaChangeForm
    add_form = PenggunaCreationForm
    list_display = ('id', 'username', 'nama_lengkap', 'peran', 'is_aktif', 'is_staff', 'created_at')
    list_filter = ('peran', 'is_aktif', 'is_staff', 'is_superuser')
    search_fields = ('username', 'nama_lengkap')
    ordering = ('id',)
    readonly_fields = ('last_login', 'created_at')
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informasi Pengguna', {'fields': ('nama_lengkap', 'peran')}),
        ('Status & Hak Akses', {'fields': ('is_aktif', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Waktu', {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'nama_lengkap', 'peran', 'is_aktif', 'is_staff', 'password1', 'password2'),
            },
        ),
    )


@admin.register(Anggota)
class AnggotaAdmin(admin.ModelAdmin):
    list_display = (
        'no_anggota',
        'nik',
        'nama',
        'status_kepegawaian',
        'masa_dinas_tahun',
        'status',
        'tanggal_masuk',
    )
    list_filter = ('status', 'status_kepegawaian')
    search_fields = ('no_anggota', 'nik', 'nama', 'no_hp')


@admin.register(JenisSimpanan)
class JenisSimpananAdmin(admin.ModelAdmin):
    list_display = ('id', 'kode', 'nama', 'nominal_default', 'is_wajib', 'is_periodik', 'dapat_ditarik')
    list_filter = ('is_wajib', 'is_periodik', 'dapat_ditarik')


@admin.register(TransaksiSimpanan)
class TransaksiSimpananAdmin(admin.ModelAdmin):
    list_display = (
        'no_kuitansi',
        'anggota',
        'jenis_simpanan',
        'jenis_transaksi',
        'metode_bayar',
        'nominal',
        'saldo_sesudah',
        'tanggal_transaksi',
    )
    list_filter = ('jenis_transaksi', 'metode_bayar', 'jenis_simpanan')
    search_fields = ('no_kuitansi', 'anggota__nama', 'anggota__no_anggota')


@admin.register(JenisAkad)
class JenisAkadAdmin(admin.ModelAdmin):
    list_display = ('id', 'kode', 'nama', 'metode_margin', 'tenor_maks_bulan', 'plafon_tanpa_agunan')


@admin.register(Pembiayaan)
class PembiayaanAdmin(admin.ModelAdmin):
    list_display = (
        'no_pembiayaan',
        'no_antrean',
        'anggota',
        'jenis_akad',
        'harga_pokok',
        'total_kewajiban',
        'tenor_bulan',
        'angsuran_bulanan',
        'status',
        'tanggal_pengajuan',
    )
    list_filter = ('status', 'jenis_akad')
    search_fields = ('no_pembiayaan', 'anggota__nama', 'anggota__no_anggota')


@admin.register(Agunan)
class AgunanAdmin(admin.ModelAdmin):
    list_display = ('id', 'pembiayaan', 'jenis_agunan', 'no_registrasi', 'nilai_taksiran', 'created_at')
    list_filter = ('jenis_agunan',)
    search_fields = ('no_registrasi', 'pembiayaan__no_pembiayaan')


@admin.register(PersetujuanPembiayaan)
class PersetujuanPembiayaanAdmin(admin.ModelAdmin):
    list_display = ('id', 'pembiayaan', 'pejabat', 'level_persetujuan', 'keputusan', 'waktu_keputusan')
    list_filter = ('keputusan', 'level_persetujuan')


@admin.register(RealisasiPencairan)
class RealisasiPencairanAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pembiayaan',
        'bendahara',
        'tanggal_realisasi',
        'metode_pencairan',
        'nomor_referensi_bank',
        'nominal_cair',
    )
    list_filter = ('metode_pencairan',)
    search_fields = ('nomor_referensi_bank', 'pembiayaan__no_pembiayaan')


@admin.register(JadwalAngsuran)
class JadwalAngsuranAdmin(admin.ModelAdmin):
    list_display = (
        'pembiayaan',
        'angsuran_ke',
        'jatuh_tempo',
        'porsi_pokok',
        'porsi_margin',
        'jumlah_angsuran',
        'status_bayar',
        'tanggal_bayar',
        'cara_bayar',
    )
    list_filter = ('status_bayar', 'cara_bayar')
    search_fields = ('pembiayaan__no_pembiayaan', 'pembiayaan__anggota__nama')


@admin.register(RekapPotongGaji)
class RekapPotongGajiAdmin(admin.ModelAdmin):
    list_display = (
        'kode_rekap',
        'periode_bulan',
        'tanggal_cut_off',
        'total_simpanan_wajib',
        'total_angsuran',
        'total_tagihan',
        'status_rekap',
    )
    list_filter = ('status_rekap',)
    search_fields = ('kode_rekap', 'periode_bulan')


@admin.register(DetailRekapPotongGaji)
class DetailRekapPotongGajiAdmin(admin.ModelAdmin):
    list_display = (
        'rekap_potong_gaji',
        'anggota',
        'nominal_simpanan_wajib',
        'nominal_simpanan_sukarela',
        'nominal_angsuran',
        'subtotal_potongan',
        'status_potongan',
    )
    list_filter = ('status_potongan', 'rekap_potong_gaji')
    search_fields = ('anggota__nama', 'anggota__no_anggota')


@admin.register(PembayaranAngsuran)
class PembayaranAngsuranAdmin(admin.ModelAdmin):
    list_display = (
        'no_kuitansi',
        'jadwal_angsuran',
        'nominal_bayar',
        'potongan_margin',
        'metode_bayar',
        'tanggal_bayar',
    )
    list_filter = ('metode_bayar',)
    search_fields = ('no_kuitansi', 'nomor_referensi')


@admin.register(NotifikasiTagihan)
class NotifikasiTagihanAdmin(admin.ModelAdmin):
    list_display = ('id', 'anggota', 'jadwal_angsuran', 'kanal_kirim', 'tujuan_kirim', 'status_kirim', 'waktu_kirim')
    list_filter = ('kanal_kirim', 'status_kirim')
    search_fields = ('anggota__nama', 'tujuan_kirim')


@admin.register(PengunduranDiri)
class PengunduranDiriAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'anggota',
        'tanggal_pengajuan',
        'total_hak_simpanan',
        'total_kewajiban_pembiayaan',
        'selisih_akhir',
        'status_kliring',
        'status_pengajuan',
    )
    list_filter = ('status_kliring', 'status_pengajuan')
    search_fields = ('anggota__nama', 'anggota__no_anggota')


@admin.register(AuditTrailLog)
class AuditTrailLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'pengguna', 'aksi', 'nama_tabel', 'record_id', 'ip_address')
    list_filter = ('aksi', 'nama_tabel')
    search_fields = ('pengguna__username', 'detail_perubahan', 'ip_address')
    readonly_fields = (
        'pengguna',
        'aksi',
        'nama_tabel',
        'record_id',
        'detail_perubahan',
        'ip_address',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
