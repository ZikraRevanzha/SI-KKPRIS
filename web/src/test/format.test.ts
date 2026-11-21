import { describe, expect, it } from 'vitest';
import { formatRupiah, formatTanggal } from '@/lib/format';

describe('formatRupiah', () => {
  it('memformat string desimal bulat menjadi Rupiah Indonesia tanpa sen bawaan', () => {
    expect(formatRupiah('0.00')).toBe('Rp 0');
    expect(formatRupiah('0')).toBe('Rp 0');
    expect(formatRupiah('350000.00')).toBe('Rp 350.000');
    expect(formatRupiah('1500000')).toBe('Rp 1.500.000');
    expect(formatRupiah('70000000.00')).toBe('Rp 70.000.000');
    expect(formatRupiah('0001500.00')).toBe('Rp 1.500');
  });

  it('menampilkan sen otomatis bila bagian desimal tidak nol atau opsi tampilkanSen aktif', () => {
    expect(formatRupiah('1428571.43')).toBe('Rp 1.428.571,43');
    expect(formatRupiah('1500000.5')).toBe('Rp 1.500.000,50');
    expect(formatRupiah('1500000.00', { tampilkanSen: true })).toBe('Rp 1.500.000,00');
    expect(formatRupiah('0.00', { tampilkanSen: true })).toBe('Rp 0,00');
  });

  it('menangani nilai negatif dan menormalkan nol negatif', () => {
    expect(formatRupiah('-350000.00')).toBe('-Rp 350.000');
    expect(formatRupiah('-350000.25')).toBe('-Rp 350.000,25');
    expect(formatRupiah('-0.00')).toBe('Rp 0');
  });

  it('menjaga presisi string penuh hingga batas DECIMAL(15,2) tanpa floating-point', () => {
    expect(formatRupiah('9999999999999.99')).toBe('Rp 9.999.999.999.999,99');
  });

  it('mengembalikan tanda hubung untuk string kosong atau tidak valid', () => {
    expect(formatRupiah('')).toBe('-');
    expect(formatRupiah('   ')).toBe('-');
    expect(formatRupiah('bukan-angka')).toBe('-');
    expect(formatRupiah('1.500.000')).toBe('-');
  });
});

describe('formatTanggal', () => {
  it('memformat tanggal ISO (YYYY-MM-DD) dalam Bahasa Indonesia', () => {
    expect(formatTanggal('2026-11-24')).toBe('24 November 2026');
    expect(formatTanggal('2026-01-05', { gaya: 'pendek' })).toBe('5 Jan 2026');
  });

  it('mengonversi timestamp UTC ke zona Asia/Jakarta termasuk saat lintas hari', () => {
    // 17:30 UTC pada 21 Nov 2026 = 00:30 WIB pada 22 Nov 2026
    expect(formatTanggal('2026-11-21T17:30:00Z')).toBe('22 November 2026');
    expect(formatTanggal('2026-11-21T17:30:00Z', { denganWaktu: true })).toBe(
      '22 November 2026, 00.30 WIB',
    );
  });

  it('memformat datetime naif dari Django (USE_TZ=False) sebagai WIB', () => {
    expect(formatTanggal('2026-11-21T13:45:00', { denganWaktu: true })).toBe(
      '21 November 2026, 13.45 WIB',
    );
  });

  it('mengembalikan tanda hubung untuk tanggal kosong atau tidak valid', () => {
    expect(formatTanggal('')).toBe('-');
    expect(formatTanggal('2026-02-31')).toBe('-');
    expect(formatTanggal('bukan-tanggal')).toBe('-');
  });
});
