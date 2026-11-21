"""
Serializer output read-only untuk endpoint ringkasan Dashboard Pengurus dan Beranda Anggota (Tahap 9C).
Seluruh field uang menggunakan DecimalField(coerce_to_string=True) sesuai AGENTS.md 4.C & 4.E.
"""

from rest_framework import serializers
from koperasi.api.v1.serializers.auth_serializers import ProfilAnggotaRingkasSerializer


def _uang_field(**kwargs) -> serializers.DecimalField:
    return serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True,
        **kwargs,
    )


class DistribusiAkadItemSerializer(serializers.Serializer):
    kode = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    jumlah = serializers.IntegerField(read_only=True)
    nominal = _uang_field()
    persen = serializers.IntegerField(read_only=True)


class RincianJenisSimpananItemSerializer(serializers.Serializer):
    kode = serializers.CharField(read_only=True)
    nama = serializers.CharField(read_only=True)
    saldo = _uang_field()
    dapat_ditarik = serializers.BooleanField(read_only=True)
    tinggi_persen = serializers.IntegerField(read_only=True)


class AktivitasTerbaruItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    aksi = serializers.CharField(read_only=True)
    nama_tabel = serializers.CharField(read_only=True)
    detail_perubahan = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    pengguna_nama = serializers.CharField(source='pengguna.nama_lengkap', read_only=True)
    pengguna_peran = serializers.CharField(source='pengguna.peran', read_only=True)


class DashboardRingkasanSerializer(serializers.Serializer):
    hari_ini = serializers.DateField(read_only=True)
    total_anggota_aktif = serializers.IntegerField(read_only=True)
    total_seluruh_anggota = serializers.IntegerField(read_only=True)
    total_simpanan = _uang_field()
    jumlah_pembiayaan_aktif = serializers.IntegerField(read_only=True)
    sisa_tagihan_aktif = _uang_field()
    menunggu_approval_ketua = serializers.IntegerField(read_only=True)
    kas_hari_ini = _uang_field()
    distribusi_akad = DistribusiAkadItemSerializer(many=True, read_only=True)
    rincian_jenis_simpanan = RincianJenisSimpananItemSerializer(many=True, read_only=True)
    aktivitas_terbaru = AktivitasTerbaruItemSerializer(many=True, read_only=True)


class KartuSimpananAnggotaItemSerializer(serializers.Serializer):
    kode = serializers.CharField(read_only=True)
    nama = serializers.CharField(read_only=True)
    nama_lengkap = serializers.CharField(read_only=True)
    saldo = _uang_field()
    dapat_ditarik = serializers.BooleanField(read_only=True)


class StatusPembiayaanAnggotaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    no_pembiayaan = serializers.CharField(read_only=True)
    jenis_akad_kode = serializers.CharField(read_only=True)
    jenis_akad_label = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    no_antrean = serializers.IntegerField(read_only=True)
    angsuran_bulanan = _uang_field()
    sisa_kewajiban = _uang_field()
    angsuran_lunas_count = serializers.IntegerField(read_only=True)
    total_tenor = serializers.IntegerField(read_only=True)
    progress_persen = serializers.IntegerField(read_only=True)


class RiwayatTerakhirAnggotaItemSerializer(serializers.Serializer):
    tanggal = serializers.DateTimeField(read_only=True)
    jenis = serializers.CharField(read_only=True)
    keterangan = serializers.CharField(read_only=True)
    jumlah = _uang_field()
    status = serializers.CharField(read_only=True)
    tipe_badge = serializers.ChoiceField(choices=('success', 'warning'), read_only=True)


class BerandaAnggotaRingkasanSerializer(serializers.Serializer):
    anggota = ProfilAnggotaRingkasSerializer(allow_null=True, read_only=True)
    total_simpanan_anggota = _uang_field()
    kartu_simpanan = KartuSimpananAnggotaItemSerializer(many=True, read_only=True)
    pembiayaan_aktif = StatusPembiayaanAnggotaSerializer(allow_null=True, read_only=True)
    riwayat_terakhir = RiwayatTerakhirAnggotaItemSerializer(many=True, read_only=True)
