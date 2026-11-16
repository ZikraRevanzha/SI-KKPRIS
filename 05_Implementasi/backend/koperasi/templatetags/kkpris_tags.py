"""
Custom Template Filters untuk pemformatan mata uang Rupiah berbasis Decimal(15,2).
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template

register = template.Library()


@register.filter(name='rupiah')
def format_rupiah(value, with_decimal=False):
    """
    Memformat nilai Decimal menjadi format Rupiah Indonesia (contoh: Rp 1.500.000).
    Tetap menjaga presisi Decimal tanpa konversi ke float.
    """
    if value is None or value == '':
        value = Decimal('0.00')
    try:
        dec = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return 'Rp 0'

    negatif = dec < Decimal('0.00')
    dec_abs = abs(dec)
    bagian_bulat, bagian_desimal = f"{dec_abs:.2f}".split('.')
    ribuan = f"{int(bagian_bulat):,}".replace(',', '.')

    tanda = '-' if negatif else ''
    if with_decimal:
        return f"{tanda}Rp {ribuan},{bagian_desimal}"
    return f"{tanda}Rp {ribuan}"

