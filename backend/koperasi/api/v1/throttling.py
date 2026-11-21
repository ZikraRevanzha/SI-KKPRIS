"""
Throttle khusus untuk pembatasan percobaan login API (AGENTS.md 4.D).
Menggunakan auth_service.ambil_ip_klien agar konsisten dengan aturan TRUSTED_PROXY / REMOTE_ADDR.
"""

from rest_framework.throttling import AnonRateThrottle
from koperasi.services import auth_service


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

    def get_ident(self, request) -> str:
        return auth_service.ambil_ip_klien(request)
