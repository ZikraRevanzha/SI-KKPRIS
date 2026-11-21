"""
Serializer input dan output untuk endpoint autentikasi JWT (/api/v1/auth/).
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from koperasi.models import Anggota, Pengguna


class GalatSeragamSerializer(serializers.Serializer):
    kode = serializers.CharField(help_text='Kode galat terstandar.')
    pesan = serializers.CharField(help_text='Pesan galat dalam Bahasa Indonesia.')
    detail = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text='Rincian galat per bidang input (kosong bila bukan galat validasi field).',
    )


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=50,
        trim_whitespace=True,
        help_text='Username pengguna atau Nomor Anggota (contoh: bendahara01 atau KKP-2026-001).',
        error_messages={
            'required': 'Username atau Nomor Anggota wajib diisi.',
            'blank': 'Username atau Nomor Anggota tidak boleh kosong.',
        },
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={'input_type': 'password'},
        help_text='Kata sandi akun pengguna.',
        error_messages={
            'required': 'Kata sandi wajib diisi.',
            'blank': 'Kata sandi tidak boleh kosong.',
        },
    )


class ProfilAnggotaRingkasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anggota
        fields = ('id', 'no_anggota', 'nama', 'status', 'status_kepegawaian')
        read_only_fields = fields


class PenggunaMeSerializer(serializers.ModelSerializer):
    peran_label = serializers.SerializerMethodField()
    anggota = serializers.SerializerMethodField()

    class Meta:
        model = Pengguna
        fields = (
            'id',
            'username',
            'nama_lengkap',
            'peran',
            'peran_label',
            'is_aktif',
            'anggota',
        )
        read_only_fields = fields

    def get_peran_label(self, obj: Pengguna) -> str:
        return obj.get_peran_display()

    @extend_schema_field(ProfilAnggotaRingkasSerializer(allow_null=True))
    def get_anggota(self, obj: Pengguna):
        profil = getattr(obj, 'profil_anggota', None)
        if profil is None:
            return None
        return ProfilAnggotaRingkasSerializer(profil).data


class LoginOutputSerializer(serializers.Serializer):
    access = serializers.CharField(help_text='Access token JWT berumur 10 menit.')
    pengguna = PenggunaMeSerializer()


class RefreshOutputSerializer(serializers.Serializer):
    access = serializers.CharField(help_text='Access token JWT baru hasil penyegaran sesi.')


class GantiPasswordInputSerializer(serializers.Serializer):
    password_lama = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            'required': 'Password lama wajib diisi.',
            'blank': 'Password lama tidak boleh kosong.',
        },
    )
    password_baru = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8,
        error_messages={
            'required': 'Password baru wajib diisi.',
            'blank': 'Password baru tidak boleh kosong.',
            'min_length': 'Password baru minimal harus terdiri dari 8 karakter.',
        },
    )
    konfirmasi_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            'required': 'Konfirmasi password baru wajib diisi.',
            'blank': 'Konfirmasi password baru tidak boleh kosong.',
        },
    )

    def validate(self, attrs):
        if attrs['password_baru'] != attrs['konfirmasi_password']:
            raise serializers.ValidationError({
                'konfirmasi_password': ['Konfirmasi password baru tidak cocok.'],
            })
        return attrs


class PesanOutputSerializer(serializers.Serializer):
    pesan = serializers.CharField()
