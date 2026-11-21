"""
Management command untuk mengisi Master Data awal SI-KKPRIS sesuai SRS v4.0:
- 5 Skema Simpanan (Pokok, Khusus, Wajib, Hari Raya, Berencana)
- 3 Skema Akad Syariah (Murabahah, Ijarah, Hawalah)
- 3 Akun Peran Utama (KETUA, BENDAHARA, ANGGOTA)
- Opsi --with-demo: mengisi contoh transaksi simpanan & pembiayaan untuk tampilan Dashboard UI
"""

from datetime import date
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from koperasi.models import (
    Agunan,
    Anggota,
    AuditTrailLog,
    DetailRekapPotongGaji,
    JadwalAngsuran,
    JenisAgunanChoices,
    JenisAkad,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    KanalNotifikasiChoices,
    KeputusanOtorisasiChoices,
    MetodeBayarChoices,
    MetodeMarginChoices,
    MetodePencairanChoices,
    NamaAkadChoices,
    NotifikasiTagihan,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    PengunduranDiri,
    PeranPenggunaChoices,
    PersetujuanPembiayaan,
    RealisasiPencairan,
    RekapPotongGaji,
    StatusAnggotaChoices,
    StatusKepegawaianChoices,
    StatusKirimNotifikasiChoices,
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
                'margin_persen': settings.MARGIN_PERSEN_SEMENTARA,  # PENDING PND-01
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
            simulasi_pmb = Pembiayaan.hitungSimulasiMarginFlat(
                harga_pokok=pmb.harga_pokok,
                margin_persen=pmb.margin_persen,
                tenor_bulan=pmb.tenor_bulan,
            )
            JadwalAngsuran.generateJadwalAngsuran(
                pembiayaan_id=pmb.id,
                tenor_bulan=12,
                porsi_pokok=simulasi_pmb['porsi_pokok'],
                porsi_margin=simulasi_pmb['porsi_margin'],
                tanggal_mulai=date(2026, 7, 12),
            )
            for ke in range(1, 5):
                jadwal_ke = JadwalAngsuran.objects.get(pembiayaan=pmb, angsuran_ke=ke)
                PembayaranAngsuran.simpanPembayaranAngsuran(jadwal_ke.id, {
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': f'KUI-ANG-2026-00{ke}',
                    'nominal_bayar': jadwal_ke.jumlah_angsuran,
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

        if options.get('with_demo') and not Anggota.objects.filter(no_anggota='KKP-2026-002').exists():
            peta_js = {js.kode: js for js in JenisSimpanan.objects.all()}

            # Anggota Demo #2: Siti Rahmah, S.Pd. (PPPK Aktif)
            user_siti, _ = Pengguna.objects.update_or_create(
                username='199003212022212008',
                defaults={
                    'password_hash': default_pw,
                    'nama_lengkap': 'Siti Rahmah, S.Pd.',
                    'peran': PeranPenggunaChoices.ANGGOTA,
                    'is_aktif': True,
                },
            )
            anggota_siti, _ = Anggota.objects.update_or_create(
                pengguna=user_siti,
                defaults={
                    'no_anggota': 'KKP-2026-002',
                    'nik': '1372012103900002',
                    'nama': 'Siti Rahmah, S.Pd.',
                    'status_kepegawaian': StatusKepegawaianChoices.PPPK,
                    'masa_dinas_tahun': 4,
                    'no_hp': '081374556677',
                    'tanggal_masuk': date(2022, 3, 1),
                    'status': StatusAnggotaChoices.AKTIF,
                },
            )
            for no_kui, kode_js, nom in [
                ('KUI-DEMO-201', 'SPK', Decimal('350000.00')),
                ('KUI-DEMO-202', 'SKH', Decimal('500000.00')),
                ('KUI-DEMO-203', 'SWJ', Decimal('900000.00')),
                ('KUI-DEMO-204', 'SHR', Decimal('450000.00')),
            ]:
                TransaksiSimpanan.simpanMutasiSimpanan({
                    'anggota_id': anggota_siti.id,
                    'jenis_simpanan_id': peta_js[kode_js].id,
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': no_kui,
                    'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                    'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
                    'nominal': nom,
                    'keterangan': f'Setoran {peta_js[kode_js].nama} Anggota KKP-2026-002',
                })

            # Anggota Demo #3: Drs. Hendra Wijaya (Pensiunan — Proses Resign / Menunggu Kliring)
            user_hendra, _ = Pengguna.objects.update_or_create(
                username='196608171992031005',
                defaults={
                    'password_hash': default_pw,
                    'nama_lengkap': 'Drs. Hendra Wijaya',
                    'peran': PeranPenggunaChoices.ANGGOTA,
                    'is_aktif': True,
                },
            )
            anggota_hendra, _ = Anggota.objects.update_or_create(
                pengguna=user_hendra,
                defaults={
                    'no_anggota': 'KKP-2026-003',
                    'nik': '1372021708660003',
                    'nama': 'Drs. Hendra Wijaya',
                    'status_kepegawaian': StatusKepegawaianChoices.PENSIUNAN,
                    'masa_dinas_tahun': 32,
                    'no_hp': '081266112233',
                    'tanggal_masuk': date(2005, 7, 1),
                    'status': StatusAnggotaChoices.AKTIF,
                },
            )
            for no_kui, kode_js, nom in [
                ('KUI-DEMO-301', 'SPK', Decimal('350000.00')),
                ('KUI-DEMO-302', 'SKH', Decimal('500000.00')),
                ('KUI-DEMO-303', 'SWJ', Decimal('5400000.00')),
                ('KUI-DEMO-304', 'SBR', Decimal('2500000.00')),
            ]:
                TransaksiSimpanan.simpanMutasiSimpanan({
                    'anggota_id': anggota_hendra.id,
                    'jenis_simpanan_id': peta_js[kode_js].id,
                    'bendahara_id': bendahara.id,
                    'no_kuitansi': no_kui,
                    'jenis_transaksi': JenisTransaksiSimpananChoices.SETOR,
                    'metode_bayar': MetodeBayarChoices.POTONG_GAJI,
                    'nominal': nom,
                    'keterangan': f'Akumulasi {peta_js[kode_js].nama} Anggota KKP-2026-003',
                })

            PengunduranDiri.simpanPermohonanResign(
                anggota_id=anggota_hendra.id,
                alasan='Pensiun / Purna Tugas — Memasuki masa purna bakti TMT 1 November 2026',
                surat_url='media/resign/surat_pensiun_hendra_wijaya.pdf',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Data contoh transaksi, anggota tambahan & pengajuan resign berhasil ditambahkan.'))

        if options.get('with_demo') and not Pembiayaan.objects.filter(no_pembiayaan='PMB-2026-002').exists():
            anggota_siti = Anggota.objects.filter(no_anggota='KKP-2026-002').first()
            if anggota_siti:
                akad_ijr = JenisAkad.objects.get(kode='AKD-IJR')
                akad_mrb = JenisAkad.objects.get(kode='AKD-MRB')

                # Demo Pembiayaan #2: Siti Rahmah — Ijarah Rp 18.000.000 (Menunggu Persetujuan Ketua)
                pmb_002 = Pembiayaan.simpanPengajuanBaru({
                    'no_pembiayaan': 'PMB-2026-002',
                    'anggota_id': anggota_siti.id,
                    'jenis_akad_id': akad_ijr.id,
                    'tanggal_pengajuan': date(2026, 11, 10),
                    'harga_pokok': Decimal('18000000.00'),
                    'margin_persen': settings.MARGIN_PERSEN_SEMENTARA,  # PENDING PND-01
                    'tenor_bulan': 18,
                    'no_antrean': 1,
                    'tujuan_pembiayaan': 'Biaya Pendidikan Studi Lanjut (S2) & Semester',
                })
                PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                    pembiayaan_id=pmb_002.id,
                    pejabat_id=bendahara.id,
                    keputusan=KeputusanOtorisasiChoices.DISETUJUI,
                    catatan='Diverifikasi Bendahara, diteruskan ke Ketua untuk persetujuan kas.',
                    level_persetujuan=1,
                )
                Pembiayaan.perbaruiStatusPembiayaan(
                    pmb_002.id,
                    StatusPembiayaanChoices.MENUNGGU_PERSETUJUAN_KETUA,
                )

                # Demo Pembiayaan #3: Siti Rahmah — Murabahah Rp 75.000.000 (> Rp 70 Jt + Agunan BPKB, Disetujui Ketua / Siap Cair)
                pmb_003 = Pembiayaan.simpanPengajuanBaru({
                    'no_pembiayaan': 'PMB-2026-003',
                    'anggota_id': anggota_siti.id,
                    'jenis_akad_id': akad_mrb.id,
                    'tanggal_pengajuan': date(2026, 11, 12),
                    'harga_pokok': Decimal('75000000.00'),
                    'margin_persen': settings.MARGIN_PERSEN_SEMENTARA,  # PENDING PND-01
                    'tenor_bulan': 30,
                    'no_antrean': 2,
                    'tujuan_pembiayaan': 'Renovasi Rumah Tinggal (> Rp 70 Juta dengan Agunan BPKB)',
                })
                Agunan.simpanDataAgunan(pmb_003.id, {
                    'jenis_agunan': JenisAgunanChoices.BPKB_MOBIL,
                    'no_registrasi': 'BPKB-BA-1892-PK',
                    'nilai_taksiran': Decimal('115000000.00'),
                    'berkas_url': 'media/agunan/bpkb_mobil_siti_rahmah.pdf',
                })
                PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                    pembiayaan_id=pmb_003.id,
                    pejabat_id=bendahara.id,
                    keputusan=KeputusanOtorisasiChoices.DISETUJUI,
                    catatan='Agunan BPKB Mobil asli telah diterima & diverifikasi Bendahara.',
                    level_persetujuan=1,
                )
                PersetujuanPembiayaan.simpanKeputusanOtorisasi(
                    pembiayaan_id=pmb_003.id,
                    pejabat_id=ketua.id,
                    keputusan=KeputusanOtorisasiChoices.DISETUJUI,
                    catatan='Disetujui Ketua (Two-Man Rule), siap dicairkan oleh Bendahara.',
                    level_persetujuan=2,
                )
                Pembiayaan.perbaruiStatusPembiayaan(
                    pmb_003.id,
                    StatusPembiayaanChoices.DISETUJUI_KETUA,
                )
                self.stdout.write(self.style.SUCCESS('[OK] Contoh antrean Persetujuan Kas & Siap Realisasi Pencairan (Tahap 5) berhasil ditambahkan.'))

        if options.get('with_demo') and not RekapPotongGaji.objects.filter(periode_bulan='2026-11').exists():
            pmb_001 = Pembiayaan.objects.filter(no_pembiayaan='PMB-2026-001').first()
            anggota_siti = Anggota.objects.filter(no_anggota='KKP-2026-002').first()
            if pmb_001 and anggota_siti:
                jadwal_ke_5 = JadwalAngsuran.objects.filter(pembiayaan=pmb_001, angsuran_ke=5).first()
                angsuran_ke_5 = jadwal_ke_5.jumlah_angsuran if jadwal_ke_5 else Decimal('0.00')
                simpanan_wajib = Decimal('150000.00')
                rekap_nov = RekapPotongGaji.buatHeaderRekap('2026-11', bendahara.id, kode_rekap='RKP-202611')
                DetailRekapPotongGaji.simpanRincianRekapAnggota(rekap_nov.id, [
                    {
                        'anggota_id': anggota_budi.id,
                        'jadwal_angsuran_id': jadwal_ke_5.id if jadwal_ke_5 else None,
                        'nominal_simpanan_wajib': simpanan_wajib,
                        'nominal_simpanan_sukarela': Decimal('75000.00'),
                        'nominal_angsuran': angsuran_ke_5,
                        'subtotal_potongan': simpanan_wajib + Decimal('75000.00') + angsuran_ke_5,
                    },
                    {
                        'anggota_id': anggota_siti.id,
                        'jadwal_angsuran_id': None,
                        'nominal_simpanan_wajib': simpanan_wajib,
                        'nominal_simpanan_sukarela': Decimal('50000.00'),
                        'nominal_angsuran': Decimal('0.00'),
                        'subtotal_potongan': simpanan_wajib + Decimal('50000.00'),
                    },
                ])
                rekap_nov.total_simpanan_wajib = simpanan_wajib * 2
                rekap_nov.total_angsuran = angsuran_ke_5
                rekap_nov.total_tagihan = (
                    simpanan_wajib * 2 + Decimal('75000.00') + Decimal('50000.00') + angsuran_ke_5
                )
                rekap_nov.save()

                if jadwal_ke_5:
                    angsuran_teks = f'{angsuran_ke_5:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
                    NotifikasiTagihan.simpanLogNotifikasi({
                        'anggota_id': anggota_budi.id,
                        'jadwal_angsuran_id': jadwal_ke_5.id,
                        'bendahara_id': bendahara.id,
                        'kanal_kirim': KanalNotifikasiChoices.WHATSAPP,
                        'tujuan_kirim': anggota_budi.no_hp,
                        'isi_pesan': (
                            'Pengingat tagihan tanggal 10 Koperasi KKPRIS: Angsuran ke-5 PMB-2026-001 '
                            f'sebesar Rp {angsuran_teks} + Simpanan Wajib Rp 150.000.'
                        ),
                        'status_kirim': StatusKirimNotifikasiChoices.TERKIRIM,
                    })
                self.stdout.write(self.style.SUCCESS('[OK] Contoh Rekap Potong Gaji Tanggal 24 & Log Notifikasi Tagihan (Tahap 6) berhasil ditambahkan.'))
