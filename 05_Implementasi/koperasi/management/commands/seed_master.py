"""
Management command untuk mengisi Master Data awal SI-KKPRIS sesuai SRS v4.0:
- 5 Skema Simpanan (Pokok, Khusus, Wajib, Hari Raya, Berencana)
- 3 Skema Akad Syariah (Murabahah, Ijarah, Hawalah)
- 3 Akun Peran Utama (KETUA, BENDAHARA, ANGGOTA)
"""

from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from koperasi.models import (
    Anggota,
    JenisAkad,
    JenisSimpanan,
    MetodeMarginChoices,
    NamaAkadChoices,
    Pengguna,
    PeranPenggunaChoices,
    StatusAnggotaChoices,
    StatusKepegawaianChoices,
)


class Command(BaseCommand):
    help = 'Inisialisasi data master (5 Jenis Simpanan, 3 Jenis Akad Syariah, dan 3 Akun Peran) pada database si_kkpris'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Seed 5 Skema Jenis Simpanan
        skema_simpanan = [
            {
                'kode': 'SPK',
                'nama': 'Simpanan Pokok',
                'nominal_default': Decimal('350000.00'),
                'is_wajib': True,
                'is_periodik': False,
                'dapat_ditarik': False,
            },
            {
                'kode': 'SKH',
                'nama': 'Simpanan Khusus',
                'nominal_default': Decimal('500000.00'),
                'is_wajib': True,
                'is_periodik': False,
                'dapat_ditarik': False,
            },
            {
                'kode': 'SWJ',
                'nama': 'Simpanan Wajib',
                'nominal_default': Decimal('150000.00'),
                'is_wajib': True,
                'is_periodik': True,
                'dapat_ditarik': False,
            },
            {
                'kode': 'SHR',
                'nama': 'Simpanan Hari Raya',
                'nominal_default': Decimal('0.00'),
                'is_wajib': False,
                'is_periodik': False,
                'dapat_ditarik': True,
            },
            {
                'kode': 'SBR',
                'nama': 'Simpanan Berencana',
                'nominal_default': Decimal('0.00'),
                'is_wajib': False,
                'is_periodik': False,
                'dapat_ditarik': True,
            },
        ]

        for item in skema_simpanan:
            JenisSimpanan.objects.update_or_create(
                kode=item['kode'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS('[OK] 5 Skema Master Jenis Simpanan berhasil diinisialisasi.'))

        # 2. Seed 3 Skema Jenis Akad Syariah
        skema_akad = [
            {
                'kode': 'AKD-MRB',
                'nama': NamaAkadChoices.MURABAHAH,
                'metode_margin': MetodeMarginChoices.FLAT,
                'tenor_maks_bulan': 72,
                'plafon_tanpa_agunan': Decimal('70000000.00'),
            },
            {
                'kode': 'AKD-IJR',
                'nama': NamaAkadChoices.IJARAH,
                'metode_margin': MetodeMarginChoices.FLAT,
                'tenor_maks_bulan': 72,
                'plafon_tanpa_agunan': Decimal('70000000.00'),
            },
            {
                'kode': 'AKD-HWL',
                'nama': NamaAkadChoices.HAWALAH,
                'metode_margin': MetodeMarginChoices.FLAT,
                'tenor_maks_bulan': 72,
                'plafon_tanpa_agunan': Decimal('70000000.00'),
            },
        ]

        for item in skema_akad:
            JenisAkad.objects.update_or_create(
                kode=item['kode'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS('[OK] 3 Skema Master Jenis Akad Syariah berhasil diinisialisasi.'))

        # 3. Seed 3 Akun Peran Utama (KETUA, BENDAHARA, ANGGOTA)
        default_pw = make_password('Kkpris2026!')

        ketua, _ = Pengguna.objects.update_or_create(
            username='ketua',
            defaults={
                'password_hash': default_pw,
                'nama_lengkap': 'Drs. H. Ketua KKPRIS SMKN 1 Kota Solok',
                'peran': PeranPenggunaChoices.KETUA,
                'is_aktif': True,
            },
        )
        bendahara, _ = Pengguna.objects.update_or_create(
            username='bendahara',
            defaults={
                'password_hash': default_pw,
                'nama_lengkap': 'Eni Mailiza, S.ST, M.Pd.E',
                'peran': PeranPenggunaChoices.BENDAHARA,
                'is_aktif': True,
            },
        )
        user_anggota, _ = Pengguna.objects.update_or_create(
            username='198205142009012004',
            defaults={
                'password_hash': default_pw,
                'nama_lengkap': 'Budi Santoso, S.Pd., M.Kom.',
                'peran': PeranPenggunaChoices.ANGGOTA,
                'is_aktif': True,
            },
        )

        Anggota.objects.update_or_create(
            pengguna=user_anggota,
            defaults={
                'no_anggota': 'KKP-2026-001',
                'nik': '1372011405820001',
                'nama': 'Budi Santoso, S.Pd., M.Kom.',
                'status_kepegawaian': StatusKepegawaianChoices.PNS,
                'masa_dinas_tahun': 15,
                'no_hp': '081267890123',
                'tanggal_masuk': date(2015, 1, 10),
                'status': StatusAnggotaChoices.AKTIF,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] 3 Akun Peran Utama ({ketua.username}, {bendahara.username}, {user_anggota.username}) berhasil diinisialisasi.'
            )
        )

