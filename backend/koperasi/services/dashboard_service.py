"""
Service ringkasan Dashboard Pengurus dan Beranda Anggota SI-KKPRIS (Tahap 9C).
Menjadi sumber tunggal logika agregasi untuk controller MVT lama dan REST API v1.
Seluruh nominal keuangan dihitung menggunakan Decimal tanpa float().
"""

from datetime import date
from decimal import Decimal
from django.db.models import Q, Sum
from koperasi.models import (
    Anggota,
    AuditTrailLog,
    JadwalAngsuran,
    JenisSimpanan,
    JenisTransaksiSimpananChoices,
    NamaAkadChoices,
    PembayaranAngsuran,
    Pembiayaan,
    Pengguna,
    StatusAnggotaChoices,
    StatusBayarAngsuranChoices,
    StatusPembiayaanChoices,
    TransaksiSimpanan,
)

URUTAN_KODE_SIMPANAN = ('SPK', 'SWJ', 'SKH', 'SHR', 'SBR')


def ambil_ringkasan_dashboard_pengurus() -> dict:
    """
    Menghimpun seluruh metrik ringkasan untuk halaman Dashboard Pengurus
    (Bendahara & Ketua) memakai aturan agregasi terkonfirmasi yang sudah ada.
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
    ada_pembiayaan = Pembiayaan.objects.exists()
    total_kontrak_akad = Pembiayaan.objects.count() or 1
    for kode_nama, label_nama in NamaAkadChoices.choices:
        jml = Pembiayaan.objects.filter(jenis_akad__nama=kode_nama).count()
        nominal_akad = (
            Pembiayaan.objects.filter(jenis_akad__nama=kode_nama).aggregate(
                total=Sum('harga_pokok')
            )['total']
            or Decimal('0.00')
        )
        persen = round((jml / total_kontrak_akad) * 100) if ada_pembiayaan else 0
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
        item['tinggi_persen'] = (
            max(12, int((item['saldo'] / max_saldo_jenis) * 100))
            if item['saldo'] > 0
            else 8
        )

    # 7. Aktivitas Terbaru (Jejak Audit Terbaru)
    aktivitas_terbaru = list(AuditTrailLog.objects.select_related('pengguna')[:6])

    return {
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


def ambil_ringkasan_beranda_anggota(pengguna: Pengguna) -> dict:
    """
    Menghimpun seluruh data portal mandiri Beranda Anggota:
    5 kartu saldo simpanan, status pembiayaan terakhir, dan 6 riwayat transaksi terbaru.
    """
    anggota = getattr(pengguna, 'profil_anggota', None)

    # 1. 5 Kartu Saldo Simpanan (Pokok, Wajib, Khusus, Hari Raya, Berencana)
    peta_jenis = {js.kode: js for js in JenisSimpanan.objects.all()}
    kartu_simpanan = []
    total_simpanan_anggota = Decimal('0.00')

    for kode in URUTAN_KODE_SIMPANAN:
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
                'jenis': f'{ts.get_jenis_transaksi_display()} - {ts.jenis_simpanan.nama}',
                'keterangan': ts.keterangan or f'Kuitansi {ts.no_kuitansi} ({ts.get_metode_bayar_display()})',
                'jumlah': ts.nominal,
                'status': 'SELESAI',
                'tipe_badge': 'success' if ts.jenis_transaksi == JenisTransaksiSimpananChoices.SETOR else 'warning',
            })
        for pa in PembayaranAngsuran.objects.select_related(
            'jadwal_angsuran',
            'jadwal_angsuran__pembiayaan',
        ).filter(jadwal_angsuran__pembiayaan__anggota=anggota)[:5]:
            riwayat_terakhir.append({
                'tanggal': pa.tanggal_bayar,
                'jenis': f'Angsuran Ke-{pa.jadwal_angsuran.angsuran_ke} ({pa.jadwal_angsuran.pembiayaan.no_pembiayaan})',
                'keterangan': f'Kuitansi {pa.no_kuitansi} ({pa.get_metode_bayar_display()})',
                'jumlah': pa.nominal_bayar,
                'status': 'LUNAS',
                'tipe_badge': 'success',
            })
        riwayat_terakhir.sort(key=lambda x: x['tanggal'], reverse=True)
        riwayat_terakhir = riwayat_terakhir[:6]

    return {
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
