"""
Konfigurasi paginasi standar REST API v1 SI-KKPRIS (page size 20 sesuai AGENTS.md 4.C.4).
"""

from rest_framework.pagination import PageNumberPagination


class StandarPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
