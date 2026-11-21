"""
URL routing REST API v1 (/api/v1/) SI-KKPRIS.
"""

from django.urls import path
from koperasi.api.v1.views.auth_views import (
    GantiPasswordAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    RefreshAPIView,
)

urlpatterns = [
    # Modul Autentikasi JWT (Tahap 9A)
    path('auth/login/', LoginAPIView.as_view(), name='api_auth_login'),
    path('auth/refresh/', RefreshAPIView.as_view(), name='api_auth_refresh'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api_auth_logout'),
    path('auth/me/', MeAPIView.as_view(), name='api_auth_me'),
    path('auth/ganti-password/', GantiPasswordAPIView.as_view(), name='api_auth_ganti_password'),
]
