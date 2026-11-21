"""
Utilitas parsing nominal Rupiah dan Persen berpresisi Decimal(15,2) untuk SI-KKPRIS.
Memisahkan parser rupiah dan persen sesuai AGENTS.md Bagian 4.E:
- Pada rupiah, titik diikuti tepat tiga digit (pola ^\\d{1,3}(\\.\\d{3})+$) adalah pemisah ribuan.
- Pada persen, titik dan koma selalu diperlakukan sebagai pemisah desimal, bukan ribuan.
"""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.exceptions import ValidationError


_POLA_RIBUAN_TITIK = re.compile(r'^\d{1,3}(\.\d{3})+$')


def _quantize_dua_desimal(nilai: Decimal, raw) -> Decimal:
    if not nilai.is_finite():
        raise ValidationError(f'Format nominal angka tidak valid: {raw}')
    return nilai.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def bersihkan_rupiah(raw, default: str = None) -> Decimal:
    """
    Mengonversi input nominal Rupiah (string/int/Decimal) menjadi Decimal 2 desimal (ROUND_HALF_UP).
    - Menghilangkan prefiks "Rp" (termasuk "Rp.") dan spasi.
    - Jika cocok pola ^\\d{1,3}(\\.\\d{3})+$ -> titik dianggap pemisah ribuan lalu dihapus.
    - Jika mengandung koma -> hapus titik ribuan dan ganti koma menjadi titik desimal.
    - Selain itu langsung dikonversi dengan Decimal.
    - Format tidak valid menimbulkan ValidationError.
    """
    if raw is None or (isinstance(raw, str) and raw.strip() == ''):
        if default is not None:
            return _quantize_dua_desimal(Decimal(str(default)), raw)
        raise ValidationError('Nominal rupiah wajib diisi.')

    if isinstance(raw, bool):
        raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')

    if isinstance(raw, Decimal):
        return _quantize_dua_desimal(raw, raw)

    if isinstance(raw, int):
        return _quantize_dua_desimal(Decimal(raw), raw)

    if isinstance(raw, float):
        raise ValidationError(
            'Nominal rupiah tidak boleh menggunakan tipe float; gunakan string atau Decimal.'
        )

    teks = str(raw).strip()
    teks = re.sub(r'(?i)rp\.?', '', teks)
    teks = re.sub(r'\s+', '', teks)

    if not teks:
        if default is not None:
            return _quantize_dua_desimal(Decimal(str(default)), raw)
        raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')

    tanda = ''
    if teks[0] in ('+', '-'):
        tanda = teks[0]
        teks = teks[1:]

    if not teks:
        raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')

    if _POLA_RIBUAN_TITIK.match(teks):
        normal = teks.replace('.', '')
    elif ',' in teks:
        if teks.count(',') > 1:
            raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')
        bagian_bulat, bagian_desimal = teks.split(',', 1)
        if not bagian_desimal.isdigit():
            raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')
        if '.' in bagian_bulat:
            if not _POLA_RIBUAN_TITIK.match(bagian_bulat):
                raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')
            bagian_bulat = bagian_bulat.replace('.', '')
        elif not bagian_bulat.isdigit():
            raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')
        normal = f'{bagian_bulat}.{bagian_desimal}'
    else:
        normal = teks

    try:
        nilai = Decimal(f'{tanda}{normal}')
    except (InvalidOperation, ValueError):
        raise ValidationError(f'Format nominal rupiah tidak valid: {raw}')

    return _quantize_dua_desimal(nilai, raw)


def bersihkan_persen(raw, default: str = None) -> Decimal:
    """
    Mengonversi input persentase (margin/ujrah) menjadi Decimal 2 desimal (ROUND_HALF_UP).
    Koma maupun titik selalu diperlakukan sebagai pemisah desimal; TIDAK memperlakukan
    titik sebagai pemisah ribuan.
    """
    if raw is None or (isinstance(raw, str) and raw.strip() == ''):
        if default is not None:
            return _quantize_dua_desimal(Decimal(str(default)), raw)
        raise ValidationError('Nilai persentase wajib diisi.')

    if isinstance(raw, bool):
        raise ValidationError(f'Format persentase tidak valid: {raw}')

    if isinstance(raw, Decimal):
        return _quantize_dua_desimal(raw, raw)

    if isinstance(raw, int):
        return _quantize_dua_desimal(Decimal(raw), raw)

    if isinstance(raw, float):
        raise ValidationError(
            'Nilai persentase tidak boleh menggunakan tipe float; gunakan string atau Decimal.'
        )

    teks = str(raw).strip()
    teks = teks.replace('%', '')
    teks = re.sub(r'\s+', '', teks)

    if not teks:
        if default is not None:
            return _quantize_dua_desimal(Decimal(str(default)), raw)
        raise ValidationError(f'Format persentase tidak valid: {raw}')

    if ',' in teks and '.' in teks:
        raise ValidationError(f'Format persentase tidak valid: {raw}')
    if teks.count(',') > 1 or teks.count('.') > 1:
        raise ValidationError(f'Format persentase tidak valid: {raw}')

    normal = teks.replace(',', '.')
    try:
        nilai = Decimal(normal)
    except (InvalidOperation, ValueError):
        raise ValidationError(f'Format persentase tidak valid: {raw}')

    return _quantize_dua_desimal(nilai, raw)
