"""
View REST API v1 read-only untuk Dashboard Pengurus dan Beranda Anggota (Tahap 9C).
Seluruh logika agregasi berasal dari koperasi.services.dashboard_service.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from koperasi.api.v1.permissions import IsAnggota, IsBendaharaAtauKetua
from koperasi.api.v1.serializers.auth_serializers import GalatSeragamSerializer
from koperasi.api.v1.serializers.dashboard_serializers import (
    BerandaAnggotaRingkasanSerializer,
    DashboardRingkasanSerializer,
)
from koperasi.models import Pengguna
from koperasi.services import dashboard_service


class DashboardRingkasanAPIView(APIView):
    """Mengembalikan metrik ringkasan Dashboard Pengurus (Bendahara & Ketua)."""

    permission_classes = [IsBendaharaAtauKetua]

    @extend_schema(
        tags=['Dashboard'],
        operation_id='dashboard_ringkasan',
        summary='Ambil ringkasan dashboard pengurus',
        description=(
            'Mengembalikan 4 kartu statistik utama, tren 5 skema simpanan, distribusi 3 akad syariah, '
            'dan 6 aktivitas audit trail terbaru untuk Bendahara dan Ketua Koperasi. '
            'Seluruh nilai uang berupa string desimal.'
        ),
        responses={
            200: DashboardRingkasanSerializer,
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Token tidak ada atau tidak valid.'),
            403: OpenApiResponse(response=GalatSeragamSerializer, description='Hanya Bendahara atau Ketua yang diizinkan.'),
        },
    )
    def get(self, request):
        ringkasan = dashboard_service.ambil_ringkasan_dashboard_pengurus()
        serializer = DashboardRingkasanSerializer(ringkasan)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BerandaAnggotaRingkasanAPIView(APIView):
    """Mengembalikan ringkasan portal mandiri Beranda Anggota untuk anggota yang login."""

    permission_classes = [IsAnggota]

    @extend_schema(
        tags=['Dashboard'],
        operation_id='anggota_saya_ringkasan',
        summary='Ambil ringkasan beranda anggota aktif',
        description=(
            'Mengembalikan 5 saldo simpanan anggota, status pembiayaan terakhir beserta progres angsuran, '
            'dan maksimal 6 riwayat transaksi terakhir milik anggota yang sedang login. '
            'Seluruh nilai uang berupa string desimal.'
        ),
        responses={
            200: BerandaAnggotaRingkasanSerializer,
            401: OpenApiResponse(response=GalatSeragamSerializer, description='Token tidak ada atau tidak valid.'),
            403: OpenApiResponse(response=GalatSeragamSerializer, description='Hanya Anggota yang diizinkan.'),
        },
    )
    def get(self, request):
        pengguna = Pengguna.objects.select_related('profil_anggota').get(pk=request.user.pk)
        ringkasan = dashboard_service.ambil_ringkasan_beranda_anggota(pengguna)

        pembiayaan = ringkasan['pembiayaan_aktif']
        pembiayaan_payload = None
        if pembiayaan is not None:
            pembiayaan_payload = {
                'id': pembiayaan.id,
                'no_pembiayaan': pembiayaan.no_pembiayaan,
                'jenis_akad_kode': pembiayaan.jenis_akad.nama,
                'jenis_akad_label': pembiayaan.jenis_akad.get_nama_display(),
                'status': pembiayaan.status,
                'status_label': pembiayaan.get_status_display(),
                'no_antrean': pembiayaan.no_antrean,
                'angsuran_bulanan': pembiayaan.angsuran_bulanan,
                'sisa_kewajiban': ringkasan['sisa_kewajiban'],
                'angsuran_lunas_count': ringkasan['angsuran_lunas_count'],
                'total_tenor': ringkasan['total_tenor'],
                'progress_persen': ringkasan['progress_persen'],
            }

        payload = {
            'anggota': ringkasan['anggota'],
            'total_simpanan_anggota': ringkasan['total_simpanan_anggota'],
            'kartu_simpanan': ringkasan['kartu_simpanan'],
            'pembiayaan_aktif': pembiayaan_payload,
            'riwayat_terakhir': ringkasan['riwayat_terakhir'],
        }
        serializer = BerandaAnggotaRingkasanSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
