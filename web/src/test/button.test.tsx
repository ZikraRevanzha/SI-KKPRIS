import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Button } from '@/components/ui';

describe('Button', () => {
  afterEach(() => {
    cleanup();
  });

  it('memanggil onClick saat aktif dan tidak sedang loading', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Simpan</Button>);

    const tombol = screen.getByRole('button', { name: 'Simpan' });
    expect(tombol).toBeEnabled();
    fireEvent.click(tombol);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('menonaktifkan klik, menyetel aria-busy, dan menampilkan teks loading saat loading=true', () => {
    const handleClick = vi.fn();
    render(
      <Button loading loadingText="Menyimpan…" onClick={handleClick}>
        Simpan
      </Button>,
    );

    const tombol = screen.getByRole('button', { name: /Menyimpan…/i });
    expect(tombol).toBeDisabled();
    expect(tombol).toHaveAttribute('aria-busy', 'true');
    fireEvent.click(tombol);
    expect(handleClick).not.toHaveBeenCalled();
  });
});
