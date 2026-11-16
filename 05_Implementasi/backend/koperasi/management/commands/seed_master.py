"""
Management command untuk mengisi Master Data awal SI-KKPRIS sesuai SRS v4.0:
- 5 Skema Simpanan (Pokok, Khusus, Wajib, Hari Raya, Berencana)
- 3 Skema Akad Syariah (Murabahah, Ijarah, Hawalah)
- 3 Akun Peran Utama (KETUA, BENDAHARA, ANGGOTA)
- Opsi --with-demo: mengisi contoh transaksi simpanan & pembiayaan untuk tampilan Dashboard UI
"""

from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JadwalAngsuran,
    JenisAkad,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    KeputusanOtorisasiChoices,
    MetodeBayarChoices,
    MetodeMarginChoices,
    MetodePencairanChoices,
    NamaAkadChoices,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PeranPenggunaChoices,
    PersetujuanPembiayaan,
    RealisasiPencairan,
    StatusAnggotaChoices,
    StatusKepegawaianChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)


class Command(BaseCommand):
    help = 'Inisialisasi data master (5 Jenis Simpanan, 3 Jenis Akad Syariah, dan 3 Akun Peran) pada database si_kkpris'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-demo',
            action='store_true',
            help='Tambahkan contoh mutasi simpanan & pembiayaan syariah untuk pratinjau Dashboard UI',
        )

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

        anggota_budi, _ = Anggota.objects.update_or_create(
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

        if options.get('with_demo') and not TransaksiSimpanan.objects.filter(anggota=anggota_budi).exists():
            peta_js = {js.kode: js for js in JenisSimpanan.objects.all()}
            demo_setoran = [
                ('KUI-DEMO-001', 'SPK', Decimal('350000.00'), 'TUNAI', 'Setoran lunas Simpanan Pokok anggota'),
                ('KUI-DEMO-002', 'SKH', Decimal('500000.00'), 'TUNAI', 'Setoran lunas Simpanan Khusus anggota'),
                ('KUI-DEMO-003', 'SWJ', Decimal('1800000.00'), 'POTONG_GAJI', 'Akumulasi Simpanan Wajib 12 bulan'),
                ('KUI-DEMO-004', 'SHR', Decimal('750000.00'), 'POTONG_GAJI', 'Tabungan Simpanan Hari Raya Idul Fitri'),
                ('KUI-DEMO-005', 'SBR', Decimal('1200000.00'), 'TRANSFER', 'Setoran Simpanan Berencana Pendidikan'),
            ]
            for no_kui, kode_js, nom, metode, ket in demo_setoran:
                TransaksiSimpanan.simpanMutasiSimpanan({
                    'anggota_id': anggota_budi.id,
                    'jenis_simpanan_id': peta_js[kode_js].id,
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': no_kui,
                    'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                    'metode_bayar': metode,
                    'nominal': nom,
                    'keterangan': ket,
                })

            akad_mrb = JenisAkad.objects.get(kode='AKD-MRB')
            pmb = Pembiayaan.simpanPengajuanBaru({
                'no_pembiayaan': 'PMB-2026-001',
                'anggota_id': anggota_budi.id,
                'jenis_akad_id': akad_mrb.id,
                'tanggal_pengajuan': date(2026, 7, 10),
                'harga_pokok': Decimal('24000000.00'),
                'margin_persen': Decimal('1.00'),
                'tenor_bulan': 12,
                'no_antrean': 1,
                'tujuan_pembiayaan': 'Pengadaan Laptop & Perangkat Pembelajaran',
            })
            PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                pembiayaan_id=pmb.id,
                pejabat_id=ketua.id,
                keputusan=KeputusanOtorisasiChoices.DISETUJUI,
                catatan='Otorisasi pengeluaran kas disetujui Ketua Koperasi.',
                level_persetujuan=2,
            )
            Pembiayaan.perbaruiStatusPembiayaan(pmb.id, StatusPembiayaanChoices.DISETUJUI_KETUA)
            RealisasiPencairan.simpanRealisasiPencairan(pmb.id, {
                'bendahara_id': bendahara.id,
                'tanggal_realisasi': date(2026, 7, 12),
                'metode_pencairan': MetodePencairanChoices.TRANSFER_BANK,
                'nomor_referensi_bank': 'BNI-SOLOK-20260712',
                'nominal_cair': Decimal('24000000.00'),
                'bukti_transfer_url': 'media/pencairan/bukti_pmb_001.pdf',
            })
            Pembiayaan.perbaruiStatusPembiayaan(pmb.id, StatusPembiayaanChoices.AKTIF, tanggal_cair=date(2026, 7, 12))
            JadwalAngsuran.generateJadwalAngsuran(
                pembiayaan_id=pmb.id,
                tenor_bulan=12,
                porsi_pokok=Decimal('2000000.00'),
                porsi_margin=Decimal('240000.00'),
                tanggal_mulai=date(2026, 7, 12),
            )
            for ke in range(1, 5):
                jadwal_ke = JadwalAngsuran.objects.get(pembiayaan=pmb, angsuran_ke=ke)
                PembayaranAngsuran.simpanPembayaranAngsuran(jadwal_ke.id, {
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': f'KUI-ANG-2026-00{ke}',
                    'nominal_bayar': Decimal('2240000.00'),
                    'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
                    'nomor_referensi': f'RKP-2026-{ke + 7:02d}',
                })

            AuditTrailLog.catatLogAudit(
                pengguna_id=bendahara.id,
                aksi='SEED_DATA_AWAL',
                nama_tabel='transaksi_simpanan',
                record_id=anggota_budi.id,
                detail='Inisialisasi saldo 5 skema simpanan & pembiayaan Murabahah anggota KKP-2026-001.',
            )
            AuditTrailLog.catatLogAudit(
                pengguna_id=ketua.id,
                aksi='OTORISASI_KAS_KETUA',
                nama_tabel='persetujuan_pembiayaan',
                record_id=pmb.id,
                detail='Persetujuan pengeluaran kas pembiayaan PMB-2026-001 (Rp 24.000.000).',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Data contoh transaksi & pembiayaan berhasil ditambahkan.'))
