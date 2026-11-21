"""
Definisi 16 Model Basis Data (3NF) — SI-KKPRIS
Koperasi KKPRIS SMK Negeri 1 Kota Solok

Selaras 100% dengan:
1. 02_DDL_MySQL_SI-KKPRIS.sql (16 Tabel MySQL 8.0+ InnoDB utf8mb4_unicode_ci)
2. 03_Class_Diagram_SI-KKPRIS.mmd (Atribut, Relasi, dan Method Domain)
3. Standar Presisi FinansialSRS v4.0: DecimalField(max_digits=15, decimal_places=2)
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone


# ============================================================================
# PILIHAN ENUMERASI (Selaras dengan ENUM pada DDL MySQL 8.0+)
# ============================================================================

class PeranPenggunaChoices(models.TextChoices):
    ANGGOTA = 'ANGGOTA', 'Anggota'
    BENDAHARA = 'BENDAHARA', 'Bendahara Koperasi'
    KETUA = 'KETUA', 'Ketua Koperasi'


class StatusKepegawaianChoices(models.TextChoices):
    PNS = 'PNS', 'PNS'
    PPPK = 'PPPK', 'PPPK'
    HONORER = 'HONORER', 'Honorer'
    PENSIUNAN = 'PENSIUNAN', 'Pensiunan'
    PINDAH_TUGAS = 'PINDAH_TUGAS', 'Pindah Tugas'


class StatusAnggotaChoices(models.TextChoices):
    AKTIF = 'AKTIF', 'Aktif'
    PROSES_RESIGN = 'PROSES_RESIGN', 'Proses Resign'
    NON_AKTIF_KELUAR = 'NON_AKTIF_KELUAR', 'Non-Aktif Keluar'


class JenisTransaksiSimpananChoices(models.TextChoices):
    SETOR = 'SETOR', 'Setor Simpanan'
    TARIK = 'TARIK', 'Tarik Simpanan'


class MetodeBayarChoices(models.TextChoices):
    TUNAI = 'TUNAI', 'Tunai'
    TRANSFER = 'TRANSFER', 'Transfer Bank'
    POTONG_GAJI = 'POTONG_GAJI', 'Potong Gaji'


class NamaAkadChoices(models.TextChoices):
    MURABAHAH = 'MURABAHAH', 'Murabahah (Jual Beli)'
    IJARAH = 'IJARAH', 'Ijarah (Sewa Jasa)'
    HAWALAH = 'HAWALAH', 'Hawalah (Pengalihan Utang)'


class MetodeMarginChoices(models.TextChoices):
    FLAT = 'FLAT', 'Margin Flat'


class StatusPembiayaanChoices(models.TextChoices):
    MENUNGGU_VERIFIKASI = 'MENUNGGU_VERIFIKASI', 'Menunggu Verifikasi Bendahara'
    MENUNGGU_PERSETUJUAN_KETUA = 'MENUNGGU_PERSETUJUAN_KETUA', 'Menunggu Persetujuan Ketua'
    DISETUJUI_KETUA = 'DISETUJUI_KETUA', 'Disetujui Ketua (Siap Cair)'
    DITOLAK = 'DITOLAK', 'Ditolak'
    AKTIF = 'AKTIF', 'Aktif Berjalan'
    LUNAS = 'LUNAS', 'Lunas'


class JenisAgunanChoices(models.TextChoices):
    # PENDING PND-05: daftar jenis agunan yang diterima belum dikonfirmasi mitra.
    BPKB_MOTOR = 'BPKB_MOTOR', 'BPKB Kendaraan Roda Dua (Motor)'
    BPKB_MOBIL = 'BPKB_MOBIL', 'BPKB Kendaraan Roda Empat (Mobil)'
    SERTIFIKAT_TANAH_RUMAH = 'SERTIFIKAT_TANAH_RUMAH', 'Sertifikat Tanah / Rumah (SHM/SHGB)'
    LAINNYA = 'LAINNYA', 'Agunan Lainnya'


class KeputusanOtorisasiChoices(models.TextChoices):
    DISETUJUI = 'DISETUJUI', 'Disetujui'
    DITOLAK = 'DITOLAK', 'Ditolak'


class MetodePencairanChoices(models.TextChoices):
    TUNAI_KASIR = 'TUNAI_KASIR', 'Tunai Kasir'
    TRANSFER_BANK = 'TRANSFER_BANK', 'Transfer Bank'


class StatusBayarAngsuranChoices(models.TextChoices):
    BELUM_LUNAS = 'BELUM_LUNAS', 'Belum Lunas'
    LUNAS = 'LUNAS', 'Lunas'


class StatusRekapGajiChoices(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    DIKUNCI = 'DIKUNCI', 'Dikunci (Siap Potong Gaji)'
    LUNAS_KOLEKTIF = 'LUNAS_KOLEKTIF', 'Lunas Kolektif'


class StatusPotonganGajiChoices(models.TextChoices):
    TERTAGIH = 'TERTAGIH', 'Tertagih'
    TERPOTONG_LUNAS = 'TERPOTONG_LUNAS', 'Terpotong Lunas'
    SELISIH_TUNGGAKAN = 'SELISIH_TUNGGAKAN', 'Selisih / Tunggakan'


class KanalNotifikasiChoices(models.TextChoices):
    # PENDING PND-10: kanal notifikasi (WhatsApp/Email, manual/otomatis) belum dikonfirmasi mitra.
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    EMAIL = 'EMAIL', 'Email'


class StatusKirimNotifikasiChoices(models.TextChoices):
    ANTREAN = 'ANTREAN', 'Dalam Antrean'
    TERKIRIM = 'TERKIRIM', 'Terkirim'
    GAGAL = 'GAGAL', 'Gagal Kirim'


class StatusKliringResignChoices(models.TextChoices):
    BELUM_DIHITUNG = 'BELUM_DIHITUNG', 'Belum Dihitung'
    HAK_PENGEMBALIAN = 'HAK_PENGEMBALIAN', 'Hak Pengembalian ke Anggota'
    WAJIB_SETOR_PELUNASAN = 'WAJIB_SETOR_PELUNASAN', 'Wajib Setor Pelunasan ke Koperasi'
    SELESAI_KLIRING = 'SELESAI_KLIRING', 'Selesai Kliring'


class StatusPengajuanResignChoices(models.TextChoices):
    MENUNGGU_VERIFIKASI = 'MENUNGGU_VERIFIKASI', 'Menunggu Verifikasi Bendahara'
    DISETUJUI_KELUAR = 'DISETUJUI_KELUAR', 'Disetujui Keluar'
    DITOLAK = 'DITOLAK', 'Ditolak'


# ============================================================================
# 1. TABEL: pengguna (Manajemen Akun & RBAC 3 Peran)
# ============================================================================

class PenggunaManager(BaseUserManager):
    """Manager kustom untuk model Pengguna berbasis AbstractBaseUser."""

    def create_user(self, username: str, password: str | None = None, **extra_fields) -> 'Pengguna':
        if not username or not username.strip():
            raise ValueError('Username wajib diisi.')
        username_bersih = username.strip()
        extra_fields.setdefault('nama_lengkap', username_bersih)
        extra_fields.setdefault('peran', PeranPenggunaChoices.ANGGOTA)
        extra_fields.setdefault('is_aktif', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        pengguna = self.model(username=username_bersih, **extra_fields)
        if password and password.startswith('pbkdf2_'):
            pengguna.password = password
        elif password:
            pengguna.set_password(password)
        else:
            pengguna.set_unusable_password()
        pengguna.save(using=self._db)
        return pengguna

    def create_superuser(self, username: str, password: str | None = None, **extra_fields) -> 'Pengguna':
        extra_fields.setdefault('nama_lengkap', username)
        extra_fields.setdefault('peran', PeranPenggunaChoices.KETUA)
        extra_fields.setdefault('is_aktif', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus memiliki is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus memiliki is_superuser=True.')
        return self.create_user(username=username, password=password, **extra_fields)


class Pengguna(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    nama_lengkap = models.CharField(max_length=150)
    peran = models.CharField(
        max_length=20,
        choices=PeranPenggunaChoices.choices,
        default=PeranPenggunaChoices.ANGGOTA,
    )
    is_aktif = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = PenggunaManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nama_lengkap']

    class Meta:
        db_table = 'pengguna'
        verbose_name = 'Pengguna'
        verbose_name_plural = '01. Daftar Pengguna'
        ordering = ['id']

    def __str__(self) -> str:
        return f"{self.username} - {self.nama_lengkap} ({self.peran})"

    @property
    def is_active(self) -> bool:
        """Alias standar Django/SimpleJWT yang terhubung ke kolom is_aktif."""
        return bool(self.is_aktif)

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.is_aktif = bool(value)

    def cekStatusAktif(self) -> bool:
        """Memeriksa apakah akun pengguna berstatus aktif."""
        return bool(self.is_aktif)

    @classmethod
    def verifikasiKredensial(cls, username: str, password: str):
        """Memverifikasi username dan password terhadap hash PBKDF2."""
        try:
            pengguna = cls.objects.get(username=username)
        except cls.DoesNotExist:
            return None
        if pengguna.cekStatusAktif() and pengguna.check_password(password):
            return pengguna
        return None

    @classmethod
    def buatAkunPengguna(cls, data_akun: dict) -> 'Pengguna':
        """Membuat akun pengguna baru dengan password yang di-hash aman."""
        raw_password = data_akun.get('password') or data_akun.get('password_hash', '')
        return cls.objects.create_user(
            username=data_akun['username'],
            password=raw_password,
            nama_lengkap=data_akun['nama_lengkap'],
            peran=data_akun.get('peran', PeranPenggunaChoices.ANGGOTA),
            is_aktif=data_akun.get('is_aktif', True),
        )


# ============================================================================
# 2. TABEL: anggota (Profil Keanggotaan Guru & Pegawai SMKN 1 Kota Solok)
# ============================================================================

class Anggota(models.Model):
    id = models.BigAutoField(primary_key=True)
    pengguna = models.OneToOneField(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='pengguna_id',
        related_name='profil_anggota',
    )
    no_anggota = models.CharField(max_length=30, unique=True)
    nik = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=150)
    status_kepegawaian = models.CharField(
        max_length=20,
        choices=StatusKepegawaianChoices.choices,
    )
    masa_dinas_tahun = models.PositiveIntegerField(default=0)
    no_hp = models.CharField(max_length=20)
    tanggal_masuk = models.DateField()
    tanggal_keluar = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusAnggotaChoices.choices,
        default=StatusAnggotaChoices.AKTIF,
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'anggota'
        verbose_name = 'Anggota Koperasi'
        verbose_name_plural = '02. Daftar Anggota'
        ordering = ['no_anggota']

    def __str__(self) -> str:
        return f"{self.no_anggota} - {self.nama} ({self.status})"

    @classmethod
    def simpanDataAnggota(cls, data_anggota: dict) -> 'Anggota':
        """Menyimpan profil anggota baru beserta nomor anggota unik."""
        return cls.objects.create(**data_anggota)

    @classmethod
    def ambilProfilAnggota(cls, anggota_id: int) -> 'Anggota':
        """Mengambil profil lengkap anggota berdasarkan ID."""
        return cls.objects.select_related('pengguna').get(pk=anggota_id)

    @classmethod
    def ubahStatusAnggota(cls, anggota_id: int, status_baru: str, tanggal_keluar=None) -> bool:
        """Memperbarui status keanggotaan (AKTIF / PROSES_RESIGN / NON_AKTIF_KELUAR)."""
        update_fields = {'status': status_baru}
        if tanggal_keluar is not None:
            update_fields['tanggal_keluar'] = tanggal_keluar
        updated = cls.objects.filter(pk=anggota_id).update(**update_fields)
        return updated > 0


# ============================================================================
# 3. TABEL: jenis_simpanan (5 Skema Simpanan: Pokok, Khusus, Wajib, Hari Raya, Berencana)
# ============================================================================

class JenisSimpanan(models.Model):
    id = models.SmallAutoField(primary_key=True)
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)
    nominal_default = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    is_wajib = models.BooleanField(default=False)
    is_periodik = models.BooleanField(default=False)
    dapat_ditarik = models.BooleanField(
        default=False,
        help_text='False=Terkunci (Pokok/Wajib/Khusus), True=Sukarela (Hari Raya/Berencana)',
    )

    class Meta:
        db_table = 'jenis_simpanan'
        verbose_name = 'Jenis Simpanan'
        verbose_name_plural = '03. Master Jenis Simpanan'
        ordering = ['id']

    def __str__(self) -> str:
        return f"{self.kode} - {self.nama} (Rp{self.nominal_default:,.2f})"

    @classmethod
    def cekDapatDitarik(cls, jenis_simpanan_id: int) -> bool:
        """Mengecek apakah jenis simpanan diizinkan untuk ditarik (sukarela)."""
        jenis = cls.objects.get(pk=jenis_simpanan_id)
        return bool(jenis.dapat_ditarik)

    @classmethod
    def ambilJenisSimpananWajib(cls) -> 'JenisSimpanan':
        """Mengambil entitas master Simpanan Wajib bulanan (Rp150.000)."""
        return cls.objects.filter(is_wajib=True, is_periodik=True).first()


# ============================================================================
# 4. TABEL: transaksi_simpanan (Mutasi Setoran & Penarikan Simpanan Anggota)
# ============================================================================

class TransaksiSimpanan(models.Model):
    id = models.BigAutoField(primary_key=True)
    anggota = models.ForeignKey(
        Anggota,
        on_delete=models.RESTRICT,
        db_column='anggota_id',
        related_name='transaksi_simpanan_list',
    )
    jenis_simpanan = models.ForeignKey(
        JenisSimpanan,
        on_delete=models.RESTRICT,
        db_column='jenis_simpanan_id',
        related_name='transaksi_list',
    )
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        related_name='transaksi_simpanan_dicatat',
    )
    no_kuitansi = models.CharField(max_length=40, unique=True)
    tanggal_transaksi = models.DateTimeField(default=timezone.now)
    jenis_transaksi = models.CharField(
        max_length=10,
        choices=JenisTransaksiSimpananChoices.choices,
    )
    metode_bayar = models.CharField(
        max_length=15,
        choices=MetodeBayarChoices.choices,
        default=MetodeBayarChoices.TUNAI,
    )
    nominal = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_sesudah = models.DecimalField(max_digits=15, decimal_places=2)
    bukti_transaksi_url = models.CharField(max_length=255, null=True, blank=True)
    keterangan = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'transaksi_simpanan'
        verbose_name = 'Transaksi Simpanan'
        verbose_name_plural = '04. Transaksi Simpanan'
        indexes = [
            models.Index(
                fields=['anggota', 'jenis_simpanan'],
                name='idx_transaksi_simpanan_anggota',
            ),
        ]
        ordering = ['-tanggal_transaksi', '-id']

    def __str__(self) -> str:
        return f"{self.no_kuitansi} | {self.jenis_transaksi} Rp{self.nominal:,.2f}"

    @classmethod
    def hitungSaldoBerjalan(cls, anggota_id: int, jenis_simpanan_id: int) -> Decimal:
        """Menghitung saldo berjalan spesifik per jenis simpanan anggota."""
        agregat = cls.objects.filter(
            anggota_id=anggota_id,
            jenis_simpanan_id=jenis_simpanan_id,
        ).aggregate(
            total_setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
            total_tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
        )
        setor = agregat['total_setor'] or Decimal('0.00')
        tarik = agregat['total_tarik'] or Decimal('0.00')
        return (setor - tarik).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def hitungTotalSimpananAnggota(cls, anggota_id: int) -> Decimal:
        """Menghitung akumulasi seluruh saldo simpanan milik anggota."""
        agregat = cls.objects.filter(anggota_id=anggota_id).aggregate(
            total_setor=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.SETOR)),
            total_tarik=Sum('nominal', filter=Q(jenis_transaksi=JenisTransaksiSimpananChoices.TARIK)),
        )
        setor = agregat['total_setor'] or Decimal('0.00')
        tarik = agregat['total_tarik'] or Decimal('0.00')
        return (setor - tarik).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def simpanMutasiSimpanan(cls, data_mutasi: dict) -> 'TransaksiSimpanan':
        """Mencatat transaksi setoran atau penarikan simpanan dengan validasi saldo & aturan kunci."""
        anggota_id = data_mutasi['anggota_id']
        jenis_simpanan_id = data_mutasi['jenis_simpanan_id']
        jenis_transaksi = data_mutasi['jenis_transaksi']
        nominal = Decimal(str(data_mutasi['nominal'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        with transaction.atomic():
            # Kunci baris Anggota sebelum membaca saldo terakhir agar saldo_sesudah berantai konsisten
            Anggota.objects.select_for_update().get(pk=anggota_id)

            saldo_awal = cls.hitungSaldoBerjalan(anggota_id, jenis_simpanan_id)
            if jenis_transaksi == JenisTransaksiSimpananChoices.TARIK:
                if not JenisSimpanan.cekDapatDitarik(jenis_simpanan_id):
                    raise ValidationError(
                        'Simpanan Pokok, Wajib, dan Khusus bersifat terkunci dan hanya dapat dicairkan saat pengunduran diri.'
                    )
                if nominal > saldo_awal:
                    raise ValidationError('Nominal penarikan melebihi saldo simpanan yang tersedia.')
                saldo_sesudah = saldo_awal - nominal
            else:
                saldo_sesudah = saldo_awal + nominal

            return cls.objects.create(
                anggota_id=anggota_id,
                jenis_simpanan_id=jenis_simpanan_id,
                bendahara_id=data_mutasi['bendahara_id'],
                no_kuitansi=data_mutasi['no_kuitansi'],
                jenis_transaksi=jenis_transaksi,
                metode_bayar=data_mutasi.get('metode_bayar', MetodeBayarChoices.TUNAI),
                nominal=nominal,
                saldo_sesudah=saldo_sesudah,
                bukti_transaksi_url=data_mutasi.get('bukti_transaksi_url'),
                keterangan=data_mutasi.get('keterangan'),
            )

    @classmethod
    def cariBerdasarkanKuitansi(cls, no_kuitansi: str):
        """Mencari transaksi simpanan berdasarkan nomor kuitansi unik."""
        return cls.objects.select_related('anggota', 'jenis_simpanan', 'bendahara').filter(
            no_kuitansi=no_kuitansi
        ).first()


# ============================================================================
# 5. TABEL: jenis_akad (Skema Akad Syariah: Murabahah, Ijarah, Hawalah)
# ============================================================================

class JenisAkad(models.Model):
    id = models.SmallAutoField(primary_key=True)
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=20, choices=NamaAkadChoices.choices)
    metode_margin = models.CharField(
        max_length=10,
        choices=MetodeMarginChoices.choices,
        default=MetodeMarginChoices.FLAT,
    )
    tenor_maks_bulan = models.PositiveSmallIntegerField(default=72)
    plafon_tanpa_agunan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('70000000.00'),
    )

    class Meta:
        db_table = 'jenis_akad'
        verbose_name = 'Jenis Akad Syariah'
        verbose_name_plural = '05. Master Jenis Akad Syariah'
        ordering = ['id']

    def __str__(self) -> str:
        return f"{self.kode} - {self.nama} ({self.metode_margin}, Maks {self.tenor_maks_bulan} Bln)"

    @classmethod
    def validasiSkemaAkad(cls, jenis_akad_id: int, tenor_bulan: int) -> bool:
        """Memvalidasi apakah tenor sesuai batas maksimal akad (maks 72 bulan)."""
        akad = cls.objects.get(pk=jenis_akad_id)
        return 1 <= int(tenor_bulan) <= int(akad.tenor_maks_bulan)

    @classmethod
    def ambilBatasPlafonAgunan(cls, jenis_akad_id: int) -> Decimal:
        """Mengambil batas plafon tanpa agunan (default Rp70.000.000,00)."""
        akad = cls.objects.get(pk=jenis_akad_id)
        return akad.plafon_tanpa_agunan


# ============================================================================
# 6. TABEL: pembiayaan (Kontrak Pengajuan & Pembiayaan Syariah Anggota)
# ============================================================================

class Pembiayaan(models.Model):
    id = models.BigAutoField(primary_key=True)
    no_pembiayaan = models.CharField(max_length=40, unique=True)
    anggota = models.ForeignKey(
        Anggota,
        on_delete=models.RESTRICT,
        db_column='anggota_id',
        related_name='pembiayaan_list',
    )
    jenis_akad = models.ForeignKey(
        JenisAkad,
        on_delete=models.RESTRICT,
        db_column='jenis_akad_id',
        related_name='pembiayaan_list',
    )
    tanggal_pengajuan = models.DateField()
    harga_pokok = models.DecimalField(max_digits=15, decimal_places=2)
    margin_persen = models.DecimalField(max_digits=5, decimal_places=2)
    total_margin = models.DecimalField(max_digits=15, decimal_places=2)
    total_kewajiban = models.DecimalField(max_digits=15, decimal_places=2)
    tenor_bulan = models.PositiveSmallIntegerField()
    angsuran_bulanan = models.DecimalField(max_digits=15, decimal_places=2)
    no_antrean = models.PositiveIntegerField()
    tujuan_pembiayaan = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30,
        choices=StatusPembiayaanChoices.choices,
        default=StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
    )
    tanggal_cair = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'pembiayaan'
        verbose_name = 'Pembiayaan Syariah'
        verbose_name_plural = '06. Daftar Pembiayaan Syariah'
        indexes = [
            models.Index(
                fields=['anggota', 'status'],
                name='idx_pembiayaan_anggota_status',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(tenor_bulan__gte=1) & Q(tenor_bulan__lte=72),
                name='chk_tenor_maks',
            ),
        ]
        ordering = ['-tanggal_pengajuan', 'no_antrean']

    def __str__(self) -> str:
        return f"{self.no_pembiayaan} - {self.anggota.nama} (Rp{self.harga_pokok:,.2f})"

    @staticmethod
    def hitungRincianAngsuran(
        harga_pokok: Decimal,
        margin_persen: Decimal,
        tenor_bulan: int,
    ) -> list[tuple[Decimal, Decimal, Decimal]]:
        """
        Fungsi sumber tunggal yang menghasilkan daftar (porsi_pokok, porsi_margin, jumlah_angsuran)
        untuk angsuran ke-1 s.d. ke-N dengan metode margin flat presisi DECIMAL(15,2).
        margin_persen = persen dari pokok PER BULAN (flat). Satuan belum dikonfirmasi mitra (PND-01).
        Selisih pembulatan pokok diserap angsuran terakhir (ke-N) sehingga:
        - sum(porsi_pokok) == harga_pokok
        - sum(jumlah_angsuran) == total_kewajiban
        """
        # PENDING PND-01: besaran dan satuan margin (per bulan/tahun/total) belum dikonfirmasi.
        # PENDING PND-02: Hawalah memakai rumus yang sama dengan akad lain (belum dikonfirmasi).
        # PENDING PND-06: pembulatan 2 desimal ROUND_HALF_UP; sisa diserap angsuran terakhir.
        pokok = Decimal(str(harga_pokok)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        persen = Decimal(str(margin_persen)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        tenor = int(tenor_bulan)
        if tenor < 1 or tenor > 72:
            raise ValidationError('Tenor pembiayaan wajib berada pada rentang 1 s.d. 72 bulan.')

        porsi_pokok_reguler = (pokok / Decimal(tenor)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        porsi_margin = ((pokok * persen) / Decimal('100.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        jumlah_reguler = (porsi_pokok_reguler + porsi_margin).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        rincian = []
        for ke in range(1, tenor + 1):
            if ke < tenor:
                pokok_ke = porsi_pokok_reguler
                jumlah_ke = jumlah_reguler
            else:
                pokok_ke = (pokok - (porsi_pokok_reguler * Decimal(tenor - 1))).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                jumlah_ke = (pokok_ke + porsi_margin).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            rincian.append((pokok_ke, porsi_margin, jumlah_ke))
        return rincian

    @staticmethod
    def hitungSimulasiMarginFlat(
        harga_pokok: Decimal,
        margin_persen: Decimal,
        tenor_bulan: int,
    ) -> dict:
        """
        Menghitung simulasi pembiayaan syariah dengan metode margin flat presisi DECIMAL(15,2).
        margin_persen = persen dari pokok PER BULAN (flat). Satuan belum dikonfirmasi mitra (PND-01).
        """
        pokok = Decimal(str(harga_pokok)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        persen = Decimal(str(margin_persen)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        tenor = int(tenor_bulan)
        rincian = Pembiayaan.hitungRincianAngsuran(
            harga_pokok=pokok,
            margin_persen=persen,
            tenor_bulan=tenor,
        )
        porsi_pokok, porsi_margin, angsuran_bulanan = rincian[0]
        _, _, angsuran_terakhir = rincian[-1]
        total_margin = (porsi_margin * Decimal(tenor)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        total_kewajiban = (pokok + total_margin).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        return {
            'harga_pokok': pokok,
            'margin_persen': persen,
            'tenor_bulan': tenor,
            'porsi_pokok': porsi_pokok,
            'porsi_margin': porsi_margin,
            'total_margin': total_margin,
            'total_kewajiban': total_kewajiban,
            'angsuran_bulanan': angsuran_bulanan,
            'angsuran_terakhir': angsuran_terakhir,
        }

    @classmethod
    def simpanPengajuanBaru(cls, data_pengajuan: dict) -> 'Pembiayaan':
        """Menyimpan pengajuan pembiayaan baru (validasi periode tanggal 1-20 & tenor <= 72 bulan)."""
        tgl_pengajuan = data_pengajuan.get('tanggal_pengajuan') or date.today()
        if not (1 <= tgl_pengajuan.day <= 20):
            raise ValidationError(
                'Pengajuan pembiayaan syariah hanya dibuka pada tanggal 1 s.d. 20 setiap bulannya.'
            )
        simulasi = cls.hitungSimulasiMarginFlat(
            harga_pokok=data_pengajuan['harga_pokok'],
            margin_persen=data_pengajuan['margin_persen'],
            tenor_bulan=data_pengajuan['tenor_bulan'],
        )
        return cls.objects.create(
            no_pembiayaan=data_pengajuan['no_pembiayaan'],
            anggota_id=data_pengajuan['anggota_id'],
            jenis_akad_id=data_pengajuan['jenis_akad_id'],
            tanggal_pengajuan=tgl_pengajuan,
            harga_pokok=simulasi['harga_pokok'],
            margin_persen=simulasi['margin_persen'],
            total_margin=simulasi['total_margin'],
            total_kewajiban=simulasi['total_kewajiban'],
            tenor_bulan=simulasi['tenor_bulan'],
            angsuran_bulanan=simulasi['angsuran_bulanan'],
            no_antrean=data_pengajuan['no_antrean'],
            tujuan_pembiayaan=data_pengajuan['tujuan_pembiayaan'],
            status=StatusPembiayaanChoices.MENUNGGU_VERIFIKASI,
        )

    @classmethod
    def ambilDetailPembiayaan(cls, pembiayaan_id: int) -> 'Pembiayaan':
        """Mengambil detail pembiayaan beserta anggota dan jenis akad."""
        return cls.objects.select_related('anggota', 'jenis_akad').get(pk=pembiayaan_id)

    @classmethod
    def ambilStatusPembiayaanAnggota(cls, anggota_id: int):
        """Mengambil daftar pembiayaan milik anggota tertentu."""
        return cls.objects.select_related('jenis_akad').filter(anggota_id=anggota_id)

    @classmethod
    def hitungSisaKewajibanAnggota(cls, anggota_id: int) -> Decimal:
        """Menghitung total sisa angsuran (pokok + margin) yang belum lunas milik anggota."""
        agregat = JadwalAngsuran.objects.filter(
            pembiayaan__anggota_id=anggota_id,
            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
        ).aggregate(sisa=Sum('jumlah_angsuran'))
        return (agregat['sisa'] or Decimal('0.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    @classmethod
    def perbaruiStatusPembiayaan(cls, pembiayaan_id: int, status_baru: str, tanggal_cair=None) -> bool:
        """Memperbarui status siklus hidup pembiayaan."""
        update_data = {'status': status_baru}
        if tanggal_cair is not None:
            update_data['tanggal_cair'] = tanggal_cair
        return cls.objects.filter(pk=pembiayaan_id).update(**update_data) > 0


# ============================================================================
# 7. TABEL: agunan (Jaminan Pembiayaan untuk Plafon > Rp70.000.000)
# ============================================================================

class Agunan(models.Model):
    id = models.BigAutoField(primary_key=True)
    pembiayaan = models.ForeignKey(
        Pembiayaan,
        on_delete=models.CASCADE,
        db_column='pembiayaan_id',
        related_name='agunan_list',
    )
    jenis_agunan = models.CharField(
        max_length=30,
        choices=JenisAgunanChoices.choices,
    )
    no_registrasi = models.CharField(max_length=100)
    nilai_taksiran = models.DecimalField(max_digits=15, decimal_places=2)
    berkas_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'agunan'
        verbose_name = 'Agunan Pembiayaan'
        verbose_name_plural = '07. Data Agunan Pembiayaan'
        indexes = [
            models.Index(fields=['pembiayaan'], name='idx_agunan_pembiayaan'),
        ]
        ordering = ['id']

    def __str__(self) -> str:
        return f"{self.jenis_agunan} - {self.no_registrasi} (Rp{self.nilai_taksiran:,.2f})"

    @classmethod
    def simpanDataAgunan(cls, pembiayaan_id: int, data_agunan: dict) -> 'Agunan':
        """Menyimpan dokumen agunan untuk pembiayaan berplafon > Rp70.000.000."""
        return cls.objects.create(
            pembiayaan_id=pembiayaan_id,
            jenis_agunan=data_agunan['jenis_agunan'],
            no_registrasi=data_agunan['no_registrasi'],
            nilai_taksiran=Decimal(str(data_agunan['nilai_taksiran'])).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ),
            berkas_url=data_agunan['berkas_url'],
        )

    @classmethod
    def ambilAgunanPembiayaan(cls, pembiayaan_id: int):
        """Mengambil daftar agunan yang terlampir pada suatu pembiayaan."""
        return cls.objects.filter(pembiayaan_id=pembiayaan_id)


# ============================================================================
# 8. TABEL: persetujuan_pembiayaan (Otorisasi Pengeluaran Kas / Two-Man Rule)
# ============================================================================

class PersetujuanPembiayaan(models.Model):
    id = models.BigAutoField(primary_key=True)
    pembiayaan = models.ForeignKey(
        Pembiayaan,
        on_delete=models.RESTRICT,
        db_column='pembiayaan_id',
        related_name='persetujuan_list',
    )
    pejabat = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='pejabat_id',
        related_name='persetujuan_diberikan',
    )
    level_persetujuan = models.PositiveIntegerField(default=1)
    keputusan = models.CharField(
        max_length=15,
        choices=KeputusanOtorisasiChoices.choices,
    )
    catatan = models.CharField(max_length=255, null=True, blank=True)
    waktu_keputusan = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'persetujuan_pembiayaan'
        verbose_name = 'Persetujuan Pembiayaan'
        verbose_name_plural = '08. Log Persetujuan Pengeluaran Kas'
        indexes = [
            models.Index(fields=['pembiayaan'], name='idx_persetujuan_pembiayaan'),
        ]
        ordering = ['-waktu_keputusan']

    def __str__(self) -> str:
        return f"Level {self.level_persetujuan} - {self.keputusan} oleh {self.pejabat.nama_lengkap}"

    @classmethod
    def simpanKeputusanOtorisasi(
        cls,
        pembiayaan_id: int,
        pejabat_id: int,
        keputusan: str,
        catatan: str = None,
        level_persetujuan: int = 1,
    ) -> 'PersetujuanPembiayaan':
        """Mencatat keputusan otorisasi berjenjang (Bendahara Level 1 / Ketua Level 2)."""
        return cls.objects.create(
            pembiayaan_id=pembiayaan_id,
            pejabat_id=pejabat_id,
            level_persetujuan=level_persetujuan,
            keputusan=keputusan,
            catatan=catatan,
        )


# ============================================================================
# 9. TABEL: realisasi_pencairan (Pencatatan Realisasi Pencairan Off-System 1:0..1)
# ============================================================================

class RealisasiPencairan(models.Model):
    id = models.BigAutoField(primary_key=True)
    pembiayaan = models.OneToOneField(
        Pembiayaan,
        on_delete=models.RESTRICT,
        db_column='pembiayaan_id',
        related_name='realisasi_pencairan',
    )
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        related_name='pencairan_direalisasikan',
    )
    tanggal_realisasi = models.DateField()
    metode_pencairan = models.CharField(
        max_length=20,
        choices=MetodePencairanChoices.choices,
    )
    nomor_referensi_bank = models.CharField(max_length=100)
    nominal_cair = models.DecimalField(max_digits=15, decimal_places=2)
    bukti_transfer_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'realisasi_pencairan'
        verbose_name = 'Realisasi Pencairan'
        verbose_name_plural = '09. Realisasi Pencairan Pembiayaan'
        ordering = ['-tanggal_realisasi', '-id']

    def __str__(self) -> str:
        return f"Realisasi {self.pembiayaan.no_pembiayaan} - Rp{self.nominal_cair:,.2f}"

    @classmethod
    def simpanRealisasiPencairan(cls, pembiayaan_id: int, data_realisasi: dict) -> 'RealisasiPencairan':
        """Mencatat realisasi pencairan dana off-system setelah disetujui Ketua Koperasi."""
        with transaction.atomic():
            pembiayaan = Pembiayaan.objects.select_for_update().get(pk=pembiayaan_id)
            if pembiayaan.status != StatusPembiayaanChoices.DISETUJUI_KETUA:
                raise ValidationError(
                    'Pencairan hanya dapat direalisasikan untuk pembiayaan yang telah disetujui Ketua (Two-Man Rule).'
                )
            if cls.objects.filter(pembiayaan_id=pembiayaan_id).exists():
                raise ValidationError(
                    f'Realisasi pencairan untuk {pembiayaan.no_pembiayaan} sudah pernah dicatat.'
                )
            return cls.objects.create(
                pembiayaan_id=pembiayaan_id,
                bendahara_id=data_realisasi['bendahara_id'],
                tanggal_realisasi=data_realisasi.get('tanggal_realisasi') or date.today(),
                metode_pencairan=data_realisasi['metode_pencairan'],
                nomor_referensi_bank=data_realisasi['nomor_referensi_bank'],
                nominal_cair=Decimal(str(data_realisasi['nominal_cair'])).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                bukti_transfer_url=data_realisasi['bukti_transfer_url'],
            )


# ============================================================================
# 10. TABEL: jadwal_angsuran (Kartu Jadwal Angsuran Bulanan)
# ============================================================================

class JadwalAngsuran(models.Model):
    id = models.BigAutoField(primary_key=True)
    pembiayaan = models.ForeignKey(
        Pembiayaan,
        on_delete=models.RESTRICT,
        db_column='pembiayaan_id',
        related_name='jadwal_angsuran_list',
    )
    angsuran_ke = models.PositiveSmallIntegerField()
    jatuh_tempo = models.DateField()
    porsi_pokok = models.DecimalField(max_digits=15, decimal_places=2)
    porsi_margin = models.DecimalField(max_digits=15, decimal_places=2)
    jumlah_angsuran = models.DecimalField(max_digits=15, decimal_places=2)
    status_bayar = models.CharField(
        max_length=15,
        choices=StatusBayarAngsuranChoices.choices,
        default=StatusBayarAngsuranChoices.BELUM_LUNAS,
    )
    tanggal_bayar = models.DateField(null=True, blank=True)
    cara_bayar = models.CharField(
        max_length=15,
        choices=MetodeBayarChoices.choices,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'jadwal_angsuran'
        verbose_name = 'Jadwal Angsuran'
        verbose_name_plural = '10. Kartu Jadwal Angsuran'
        constraints = [
            models.UniqueConstraint(
                fields=['pembiayaan', 'angsuran_ke'],
                name='uk_jadwal_pembiayaan_ke',
            ),
        ]
        indexes = [
            models.Index(
                fields=['jatuh_tempo', 'status_bayar'],
                name='idx_jadwal_jatuh_tempo_status',
            ),
        ]
        ordering = ['pembiayaan', 'angsuran_ke']

    def __str__(self) -> str:
        return f"{self.pembiayaan.no_pembiayaan} - Angsuran Ke-{self.angsuran_ke} ({self.status_bayar})"

    @classmethod
    def generateJadwalAngsuran(
        cls,
        pembiayaan_id: int,
        tenor_bulan: int,
        porsi_pokok: Decimal = None,
        porsi_margin: Decimal = None,
        tanggal_mulai: date = None,
        harga_pokok: Decimal = None,
        margin_persen: Decimal = None,
    ) -> list:
        """
        Meng-generate kartu jadwal angsuran bulanan secara otomatis saat pencairan.
        Menggunakan fungsi sumber tunggal Pembiayaan.hitungRincianAngsuran agar selisih
        pembulatan pokok diserap angsuran terakhir (sum(jumlah_angsuran) == total_kewajiban).
        """
        # PENDING PND-07: angsuran pertama = bulan berikutnya setelah tanggal_mulai, jatuh tempo
        # tanggal 24. Aturan awal angsuran (termasuk cair setelah tanggal 24) belum dikonfirmasi.
        tgl_acuan = tanggal_mulai or date.today()
        tenor = int(tenor_bulan)

        pmb = None
        if harga_pokok is None or margin_persen is None:
            pmb = Pembiayaan.objects.filter(pk=pembiayaan_id).only(
                'harga_pokok', 'margin_persen'
            ).first()

        if harga_pokok is None:
            if pmb is not None:
                harga_pokok = pmb.harga_pokok
            elif porsi_pokok is not None:
                harga_pokok = (
                    Decimal(str(porsi_pokok)) * Decimal(tenor)
                ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                raise ValidationError('harga_pokok wajib disediakan untuk generate jadwal angsuran.')

        if margin_persen is None:
            if pmb is not None:
                margin_persen = pmb.margin_persen
            elif porsi_margin is not None and Decimal(str(harga_pokok)) > Decimal('0.00'):
                margin_persen = (
                    (Decimal(str(porsi_margin)) * Decimal('100.00')) / Decimal(str(harga_pokok))
                ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                margin_persen = Decimal('0.00')

        rincian = Pembiayaan.hitungRincianAngsuran(
            harga_pokok=harga_pokok,
            margin_persen=margin_persen,
            tenor_bulan=tenor,
        )

        jadwal_items = []
        for ke, (pokok_ke, margin_ke, jumlah_ke) in enumerate(rincian, start=1):
            tahun = tgl_acuan.year + ((tgl_acuan.month - 1 + ke) // 12)
            bulan = ((tgl_acuan.month - 1 + ke) % 12) + 1
            jatuh_tempo = date(tahun, bulan, 24)
            jadwal_items.append(
                cls(
                    pembiayaan_id=pembiayaan_id,
                    angsuran_ke=ke,
                    jatuh_tempo=jatuh_tempo,
                    porsi_pokok=pokok_ke,
                    porsi_margin=margin_ke,
                    jumlah_angsuran=jumlah_ke,
                    status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
                )
            )
        return cls.objects.bulk_create(jadwal_items)

    @classmethod
    def ambilTagihanJatuhTempo(cls, periode_bulan: str):
        """Mengambil daftar jadwal angsuran belum lunas pada periode YYYY-MM."""
        tahun, bulan = [int(x) for x in periode_bulan.split('-')]
        return cls.objects.select_related('pembiayaan', 'pembiayaan__anggota').filter(
            jatuh_tempo__year=tahun,
            jatuh_tempo__month=bulan,
            status_bayar=StatusBayarAngsuranChoices.BELUM_LUNAS,
            pembiayaan__status=StatusPembiayaanChoices.AKTIF,
        )

    @classmethod
    def tandaiJadwalLunas(cls, jadwal_id: int, tanggal_bayar: date, cara_bayar: str) -> bool:
        """Menandai satu jadwal angsuran menjadi LUNAS."""
        return (
            cls.objects.filter(pk=jadwal_id).update(
                status_bayar=StatusBayarAngsuranChoices.LUNAS,
                tanggal_bayar=tanggal_bayar,
                cara_bayar=cara_bayar,
            )
            > 0
        )


# ============================================================================
# 11. TABEL: rekap_potong_gaji (Header Rekapitulasi Potong Gaji Tanggal 24)
# ============================================================================

class RekapPotongGaji(models.Model):
    id = models.BigAutoField(primary_key=True)
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        related_name='rekap_potong_gaji_list',
    )
    kode_rekap = models.CharField(max_length=40, unique=True)
    periode_bulan = models.CharField(
        max_length=7,
        unique=True,
        help_text='Format YYYY-MM',
    )
    tanggal_cut_off = models.DateField()
    total_simpanan_wajib = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_angsuran = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_tagihan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    status_rekap = models.CharField(
        max_length=20,
        choices=StatusRekapGajiChoices.choices,
        default=StatusRekapGajiChoices.DIKUNCI,
    )
    tanggal_lunas_kolektif = models.DateField(null=True, blank=True)
    nomor_referensi_transfer = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'rekap_potong_gaji'
        verbose_name = 'Rekap Potong Gaji'
        verbose_name_plural = '11. Header Rekap Potong Gaji (Tgl 24)'
        ordering = ['-periode_bulan']

    def __str__(self) -> str:
        return f"{self.kode_rekap} ({self.periode_bulan}) - Rp{self.total_tagihan:,.2f}"

    @classmethod
    def buatHeaderRekap(cls, periode_bulan: str, bendahara_id: int, kode_rekap: str = None) -> 'RekapPotongGaji':
        """Membuat dokumen header rekap potong gaji bulanan pada tanggal 24."""
        tahun, bulan = [int(x) for x in periode_bulan.split('-')]
        kode = kode_rekap or f"RKP-{tahun}{bulan:02d}"
        return cls.objects.create(
            bendahara_id=bendahara_id,
            kode_rekap=kode,
            periode_bulan=periode_bulan,
            tanggal_cut_off=date(tahun, bulan, 24),
            status_rekap=StatusRekapGajiChoices.DIKUNCI,
        )

    @classmethod
    def perbaruiStatusRekapKolektif(cls, rekap_id: int, no_ref_transfer: str, tanggal_lunas: date = None) -> bool:
        """Memperbarui status header rekap menjadi LUNAS_KOLEKTIF saat dana gaji diterima."""
        return (
            cls.objects.filter(pk=rekap_id).update(
                status_rekap=StatusRekapGajiChoices.LUNAS_KOLEKTIF,
                tanggal_lunas_kolektif=tanggal_lunas or date.today(),
                nomor_referensi_transfer=no_ref_transfer,
            )
            > 0
        )


# ============================================================================
# 12. TABEL: detail_rekap_potong_gaji (Rincian Potong Gaji per Anggota - 3NF)
# ============================================================================

class DetailRekapPotongGaji(models.Model):
    id = models.BigAutoField(primary_key=True)
    rekap_potong_gaji = models.ForeignKey(
        RekapPotongGaji,
        on_delete=models.CASCADE,
        db_column='rekap_potong_gaji_id',
        related_name='detail_list',
    )
    anggota = models.ForeignKey(
        Anggota,
        on_delete=models.RESTRICT,
        db_column='anggota_id',
        related_name='detail_rekap_list',
    )
    jadwal_angsuran = models.ForeignKey(
        JadwalAngsuran,
        on_delete=models.RESTRICT,
        db_column='jadwal_angsuran_id',
        null=True,
        blank=True,
        related_name='detail_rekap_list',
    )
    nominal_simpanan_wajib = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('150000.00'),
    )
    nominal_simpanan_sukarela = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    nominal_angsuran = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    subtotal_potongan = models.DecimalField(max_digits=15, decimal_places=2)
    status_potongan = models.CharField(
        max_length=25,
        choices=StatusPotonganGajiChoices.choices,
        default=StatusPotonganGajiChoices.TERTAGIH,
    )

    class Meta:
        db_table = 'detail_rekap_potong_gaji'
        verbose_name = 'Detail Rekap Potong Gaji'
        verbose_name_plural = '12. Detail Rekap Potong Gaji Anggota'
        constraints = [
            models.UniqueConstraint(
                fields=['rekap_potong_gaji', 'anggota', 'jadwal_angsuran'],
                name='uk_detail_rekap_anggota_jadwal',
            ),
        ]
        ordering = ['rekap_potong_gaji', 'anggota']

    def __str__(self) -> str:
        return f"{self.rekap_potong_gaji.kode_rekap} - {self.anggota.nama} (Rp{self.subtotal_potongan:,.2f})"

    @classmethod
    def simpanRincianRekapAnggota(cls, rekap_id: int, rincian_item: list) -> list:
        """Menyimpan daftar rincian potongan gaji per anggota secara batch."""
        objs = [
            cls(
                rekap_potong_gaji_id=rekap_id,
                anggota_id=item['anggota_id'],
                jadwal_angsuran_id=item.get('jadwal_angsuran_id'),
                nominal_simpanan_wajib=Decimal(str(item.get('nominal_simpanan_wajib', '150000.00'))),
                nominal_simpanan_sukarela=Decimal(str(item.get('nominal_simpanan_sukarela', '0.00'))),
                nominal_angsuran=Decimal(str(item.get('nominal_angsuran', '0.00'))),
                subtotal_potongan=Decimal(str(item['subtotal_potongan'])),
                status_potongan=item.get('status_potongan', StatusPotonganGajiChoices.TERTAGIH),
            )
            for item in rincian_item
        ]
        return cls.objects.bulk_create(objs)

    @classmethod
    def tandaiRincianLunas(cls, rekap_id: int) -> bool:
        """Menandai seluruh rincian anggota pada rekap menjadi TERPOTONG_LUNAS."""
        return (
            cls.objects.filter(rekap_potong_gaji_id=rekap_id).update(
                status_potongan=StatusPotonganGajiChoices.TERPOTONG_LUNAS
            )
            > 0
        )


# ============================================================================
# 13. TABEL: pembayaran_angsuran (Kuitansi Pembayaran Cicilan Mandiri / Kolektif)
# ============================================================================

class PembayaranAngsuran(models.Model):
    id = models.BigAutoField(primary_key=True)
    jadwal_angsuran = models.ForeignKey(
        JadwalAngsuran,
        on_delete=models.RESTRICT,
        db_column='jadwal_angsuran_id',
        related_name='pembayaran_list',
    )
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        related_name='pembayaran_angsuran_dicatat',
    )
    rekap_potong_gaji = models.ForeignKey(
        RekapPotongGaji,
        on_delete=models.SET_NULL,
        db_column='rekap_potong_gaji_id',
        null=True,
        blank=True,
        related_name='pembayaran_angsuran_list',
    )
    no_kuitansi = models.CharField(max_length=40, unique=True)
    tanggal_bayar = models.DateTimeField(default=timezone.now)
    nominal_bayar = models.DecimalField(max_digits=15, decimal_places=2)
    # PENDING PND-08: kolom disebut di SRS v4.0 FR-PMB-07 (muqashah), tetapi besaran/aturan
    # potongan pelunasan dipercepat belum dikonfirmasi mitra. Jangan dihapus.
    potongan_margin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Muqashah / potongan margin jika pelunasan dipercepat',
    )
    metode_bayar = models.CharField(
        max_length=15,
        choices=MetodeBayarChoices.choices,
    )
    nomor_referensi = models.CharField(max_length=100, null=True, blank=True)
    bukti_bayar_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'pembayaran_angsuran'
        verbose_name = 'Pembayaran Angsuran'
        verbose_name_plural = '13. Kuitansi Pembayaran Angsuran'
        indexes = [
            models.Index(fields=['jadwal_angsuran'], name='idx_pembayaran_jadwal'),
        ]
        ordering = ['-tanggal_bayar', '-id']

    def __str__(self) -> str:
        return f"{self.no_kuitansi} - Rp{self.nominal_bayar:,.2f} ({self.metode_bayar})"

    @classmethod
    def simpanPembayaranAngsuran(cls, jadwal_id: int, data_bayar: dict) -> 'PembayaranAngsuran':
        """Mencatat pembayaran angsuran dan memperbarui status jadwal angsuran di dalam kunci baris."""
        with transaction.atomic():
            jadwal = JadwalAngsuran.objects.select_for_update().get(pk=jadwal_id)
            if jadwal.status_bayar == StatusBayarAngsuranChoices.LUNAS:
                raise ValidationError(
                    f'Angsuran ke-{jadwal.angsuran_ke} sudah berstatus LUNAS dan tidak dapat dibayar ulang.'
                )
            pembayaran = cls.objects.create(
                jadwal_angsuran_id=jadwal.id,
                bendahara_id=data_bayar['bendahara_id'],
                rekap_potong_gaji_id=data_bayar.get('rekap_potong_gaji_id'),
                no_kuitansi=data_bayar['no_kuitansi'],
                nominal_bayar=Decimal(str(data_bayar['nominal_bayar'])).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                potongan_margin=Decimal(str(data_bayar.get('potongan_margin', '0.00'))).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                metode_bayar=data_bayar['metode_bayar'],
                nomor_referensi=data_bayar.get('nomor_referensi'),
                bukti_bayar_url=data_bayar.get('bukti_bayar_url'),
            )
            JadwalAngsuran.tandaiJadwalLunas(
                jadwal_id=jadwal.id,
                tanggal_bayar=date.today(),
                cara_bayar=data_bayar['metode_bayar'],
            )
            return pembayaran

    @classmethod
    def cariBuktiAngsuran(cls, no_kuitansi: str):
        """Mencari bukti pembayaran angsuran berdasarkan nomor kuitansi."""
        return cls.objects.select_related(
            'jadwal_angsuran',
            'jadwal_angsuran__pembiayaan',
            'jadwal_angsuran__pembiayaan__anggota',
            'bendahara',
        ).filter(no_kuitansi=no_kuitansi).first()


# ============================================================================
# 14. TABEL: notifikasi_tagihan (Log Pengiriman WA/Email Pengingat Tanggal 10)
# ============================================================================

class NotifikasiTagihan(models.Model):
    id = models.BigAutoField(primary_key=True)
    anggota = models.ForeignKey(
        Anggota,
        on_delete=models.RESTRICT,
        db_column='anggota_id',
        related_name='notifikasi_list',
    )
    jadwal_angsuran = models.ForeignKey(
        JadwalAngsuran,
        on_delete=models.RESTRICT,
        db_column='jadwal_angsuran_id',
        related_name='notifikasi_list',
    )
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        related_name='notifikasi_dikirim',
    )
    kanal_kirim = models.CharField(
        max_length=15,
        choices=KanalNotifikasiChoices.choices,
        default=KanalNotifikasiChoices.WHATSAPP,
    )
    tujuan_kirim = models.CharField(max_length=100)
    isi_pesan = models.CharField(max_length=500)
    status_kirim = models.CharField(
        max_length=15,
        choices=StatusKirimNotifikasiChoices.choices,
        default=StatusKirimNotifikasiChoices.ANTREAN,
    )
    waktu_kirim = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notifikasi_tagihan'
        verbose_name = 'Notifikasi Tagihan'
        verbose_name_plural = '14. Log Notifikasi Tagihan (Tgl 10)'
        indexes = [
            models.Index(
                fields=['anggota', 'jadwal_angsuran'],
                name='idx_notifikasi_anggota_jadwal',
            ),
        ]
        ordering = ['-waktu_kirim']

    def __str__(self) -> str:
        return f"{self.kanal_kirim} ke {self.tujuan_kirim} ({self.status_kirim})"

    @classmethod
    def simpanLogNotifikasi(cls, data_notifikasi: dict) -> 'NotifikasiTagihan':
        """Mencatat log pengiriman pengingat jatuh tempo angsuran."""
        return cls.objects.create(**data_notifikasi)


# ============================================================================
# 15. TABEL: pengunduran_diri (Verifikasi Kliring Hak Simpanan vs Kewajiban)
# ============================================================================

class PengunduranDiri(models.Model):
    id = models.BigAutoField(primary_key=True)
    anggota = models.ForeignKey(
        Anggota,
        on_delete=models.RESTRICT,
        db_column='anggota_id',
        related_name='pengunduran_diri_list',
    )
    bendahara = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='bendahara_id',
        null=True,
        blank=True,
        related_name='pengunduran_diri_diverifikasi',
    )
    tanggal_pengajuan = models.DateField()
    alasan_keluar = models.CharField(max_length=255)
    surat_permohonan_url = models.CharField(max_length=255)
    total_hak_simpanan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_kewajiban_pembiayaan = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    selisih_akhir = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Positif=Pengembalian ke Anggota, Negatif=Wajib Setor Pelunasan',
    )
    status_kliring = models.CharField(
        max_length=30,
        choices=StatusKliringResignChoices.choices,
        default=StatusKliringResignChoices.BELUM_DIHITUNG,
    )
    status_pengajuan = models.CharField(
        max_length=25,
        choices=StatusPengajuanResignChoices.choices,
        default=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI,
    )
    berita_acara_url = models.CharField(max_length=255, null=True, blank=True)
    tanggal_keputusan = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'pengunduran_diri'
        verbose_name = 'Pengunduran Diri Anggota'
        verbose_name_plural = '15. Verifikasi Pengunduran Diri & Kliring'
        indexes = [
            models.Index(
                fields=['anggota', 'status_pengajuan'],
                name='idx_pengunduran_anggota',
            ),
        ]
        ordering = ['-tanggal_pengajuan', '-id']

    def __str__(self) -> str:
        return f"Resign {self.anggota.nama} ({self.status_pengajuan} | Selisih: Rp{self.selisih_akhir:,.2f})"

    @classmethod
    def simpanPermohonanResign(cls, anggota_id: int, alasan: str, surat_url: str) -> 'PengunduranDiri':
        """Mencatat permohonan keluar anggota dan mengunci status anggota ke PROSES_RESIGN."""
        with transaction.atomic():
            Anggota.ubahStatusAnggota(anggota_id, StatusAnggotaChoices.PROSES_RESIGN)
            total_simpanan = TransaksiSimpanan.hitungTotalSimpananAnggota(anggota_id)
            total_kewajiban = Pembiayaan.hitungSisaKewajibanAnggota(anggota_id)
            selisih = (total_simpanan - total_kewajiban).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            status_kliring = (
                StatusKliringResignChoices.HAK_PENGEMBALIAN
                if selisih >= Decimal('0.00')
                else StatusKliringResignChoices.WAJIB_SETOR_PELUNASAN
            )
            return cls.objects.create(
                anggota_id=anggota_id,
                tanggal_pengajuan=date.today(),
                alasan_keluar=alasan,
                surat_permohonan_url=surat_url,
                total_hak_simpanan=total_simpanan,
                total_kewajiban_pembiayaan=total_kewajiban,
                selisih_akhir=selisih,
                status_kliring=status_kliring,
                status_pengajuan=StatusPengajuanResignChoices.MENUNGGU_VERIFIKASI,
            )

    @classmethod
    def hitungKliringResign(
        cls,
        pengunduran_id: int,
        total_simpanan: Decimal,
        total_kewajiban: Decimal,
    ) -> 'PengunduranDiri':
        """Menghitung ulang neraca kliring simpanan vs sisa kewajiban pembiayaan."""
        resign = cls.objects.get(pk=pengunduran_id)
        simpanan = Decimal(str(total_simpanan)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        kewajiban = Decimal(str(total_kewajiban)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        selisih = (simpanan - kewajiban).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        resign.total_hak_simpanan = simpanan
        resign.total_kewajiban_pembiayaan = kewajiban
        resign.selisih_akhir = selisih
        resign.status_kliring = (
            StatusKliringResignChoices.HAK_PENGEMBALIAN
            if selisih >= Decimal('0.00')
            else StatusKliringResignChoices.WAJIB_SETOR_PELUNASAN
        )
        resign.save()
        return resign

    @classmethod
    def selesaikanVerifikasiResign(
        cls,
        pengunduran_id: int,
        bendahara_id: int,
        berita_acara_url: str,
    ) -> bool:
        """Menyelesaikan verifikasi kliring pengunduran diri dan menonaktifkan keanggotaan."""
        with transaction.atomic():
            resign = cls.objects.select_for_update().get(pk=pengunduran_id)
            tgl_keputusan = date.today()
            resign.bendahara_id = bendahara_id
            resign.berita_acara_url = berita_acara_url
            resign.status_kliring = StatusKliringResignChoices.SELESAI_KLIRING
            resign.status_pengajuan = StatusPengajuanResignChoices.DISETUJUI_KELUAR
            resign.tanggal_keputusan = tgl_keputusan
            resign.save()

            Anggota.ubahStatusAnggota(
                resign.anggota_id,
                StatusAnggotaChoices.NON_AKTIF_KELUAR,
                tanggal_keluar=tgl_keputusan,
            )
            Pengguna.objects.filter(pk=resign.anggota.pengguna_id).update(is_aktif=False)
            return True


# ============================================================================
# 16. TABEL: audit_trail_log (Jejak Audit Keamanan Sistem Append-Only)
# ============================================================================

class AuditTrailLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    pengguna = models.ForeignKey(
        Pengguna,
        on_delete=models.RESTRICT,
        db_column='pengguna_id',
        related_name='audit_logs',
    )
    aksi = models.CharField(max_length=100)
    nama_tabel = models.CharField(max_length=64)
    record_id = models.PositiveBigIntegerField()
    detail_perubahan = models.CharField(max_length=500)
    ip_address = models.CharField(max_length=45)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_trail_log'
        verbose_name = 'Log Audit Sistem'
        verbose_name_plural = '16. Jejak Audit Sistem (Audit Trail)'
        indexes = [
            models.Index(
                fields=['pengguna', 'created_at'],
                name='idx_audit_pengguna_waktu',
            ),
        ]
        ordering = ['-created_at', '-id']

    def __str__(self) -> str:
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.pengguna.username} - {self.aksi} ({self.nama_tabel}#{self.record_id})"

    @classmethod
    def catatLogAudit(
        cls,
        pengguna_id: int,
        aksi: str,
        nama_tabel: str,
        record_id: int,
        detail: str,
        ip_address: str = '127.0.0.1',
    ) -> 'AuditTrailLog':
        """Mencatat jejak audit (append-only) atas aksi sensitif pada sistem."""
        return cls.objects.create(
            pengguna_id=pengguna_id,
            aksi=aksi,
            nama_tabel=nama_tabel,
            record_id=record_id,
            detail_perubahan=detail[:500],
            ip_address=ip_address,
        )
