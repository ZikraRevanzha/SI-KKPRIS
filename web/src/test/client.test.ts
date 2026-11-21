import { afterEach, describe, expect, it, vi } from 'vitest';
import { createApiClientBundle, normalizeApiError } from '@/api/client';

function buatResponJson(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function ambilUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}

function ambilHeader(input: RequestInfo | URL, init: RequestInit | undefined, nama: string): string | null {
  if (input instanceof Request) {
    return input.headers.get(nama);
  }
  return new Headers(init?.headers).get(nama);
}

describe('klien API openapi-fetch & single-flight refresh', () => {
  afterEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('menyimpan access token di memori (bukan localStorage/sessionStorage) dan mengirim Authorization', async () => {
    let authTerkirim: string | null = null;
    const mockFetch: typeof fetch = vi.fn(async (input, init) => {
      authTerkirim = ambilHeader(input, init, 'Authorization');
      return buatResponJson({
        id: 1,
        username: 'bendahara01',
        nama_lengkap: 'Bendahara Dummy',
        peran: 'BENDAHARA',
        peran_label: 'Bendahara Koperasi',
        is_aktif: true,
        anggota: null,
      });
    });

    const bundle = createApiClientBundle(mockFetch);
    bundle.setAccessToken('token-memori-1');

    const { data, error } = await bundle.client.GET('/api/v1/auth/me/');

    expect(error).toBeUndefined();
    expect(data?.username).toBe('bendahara01');
    expect(authTerkirim).toBe('Bearer token-memori-1');
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it('melakukan SATU refresh bersama (single-flight) untuk request paralel 401 lalu mengulang masing-masing sekali', async () => {
    let jumlahRefresh = 0;
    let credentialsRefresh: RequestCredentials | undefined;
    let bodyRetryPost: string | null = null;

    const mockFetch: typeof fetch = vi.fn(async (input, init) => {
      const url = ambilUrl(input);
      const auth = ambilHeader(input, init, 'Authorization');

      if (url.endsWith('/api/v1/auth/refresh/')) {
        jumlahRefresh += 1;
        credentialsRefresh = input instanceof Request ? input.credentials : init?.credentials;
        // Simulasikan jeda jaringan agar seluruh request paralel menunggu promise yang sama
        await new Promise((resolve) => setTimeout(resolve, 15));
        return buatResponJson({ access: 'token-baru-xyz' }, 200);
      }

      if (auth !== 'Bearer token-baru-xyz') {
        return buatResponJson(
          { kode: 'AUTENTIKASI_GAGAL', pesan: 'Token kedaluwarsa.', detail: {} },
          401,
        );
      }

      if (url.endsWith('/api/v1/auth/ganti-password/')) {
        bodyRetryPost = input instanceof Request ? await input.clone().text() : null;
        return buatResponJson({ pesan: 'Kata sandi berhasil diperbarui.' }, 200);
      }

      return buatResponJson(
        {
          id: 2,
          username: 'ketua01',
          nama_lengkap: 'Ketua Dummy',
          peran: 'KETUA',
          peran_label: 'Ketua Koperasi',
          is_aktif: true,
          anggota: null,
        },
        200,
      );
    });

    const bundle = createApiClientBundle(mockFetch);
    bundle.setAccessToken('token-lama-expired');

    const [resMe1, resMe2, resPost] = await Promise.all([
      bundle.client.GET('/api/v1/auth/me/'),
      bundle.client.GET('/api/v1/auth/me/'),
      bundle.client.POST('/api/v1/auth/ganti-password/', {
        body: {
          password_lama: 'Lama1234!',
          password_baru: 'Baru1234!',
          konfirmasi_password: 'Baru1234!',
        },
      }),
    ]);

    expect(jumlahRefresh).toBe(1);
    expect(credentialsRefresh).toBe('same-origin');
    expect(bundle.getAccessToken()).toBe('token-baru-xyz');
    expect(resMe1.data?.username).toBe('ketua01');
    expect(resMe2.data?.username).toBe('ketua01');
    expect(resPost.data?.pesan).toBe('Kata sandi berhasil diperbarui.');
    expect(bodyRetryPost).toContain('Baru1234!');
  });

  it('mengosongkan token dan memanggil handler kedaluwarsa tepat sekali bila refresh gagal', async () => {
    let jumlahRefresh = 0;
    const onExpired = vi.fn();

    const mockFetch: typeof fetch = vi.fn(async (input) => {
      const url = ambilUrl(input);
      if (url.endsWith('/api/v1/auth/refresh/')) {
        jumlahRefresh += 1;
        await new Promise((resolve) => setTimeout(resolve, 10));
        return buatResponJson(
          { kode: 'REFRESH_TOKEN_TIDAK_VALID', pesan: 'Sesi berakhir.', detail: {} },
          401,
        );
      }
      return buatResponJson(
        { kode: 'AUTENTIKASI_GAGAL', pesan: 'Token tidak valid.', detail: {} },
        401,
      );
    });

    const bundle = createApiClientBundle(mockFetch);
    bundle.setAccessToken('token-lama');
    bundle.setSessionExpiredHandler(onExpired);

    const [r1, r2] = await Promise.all([
      bundle.client.GET('/api/v1/auth/me/'),
      bundle.client.GET('/api/v1/auth/me/'),
    ]);

    expect(jumlahRefresh).toBe(1);
    expect(bundle.getAccessToken()).toBeNull();
    expect(onExpired).toHaveBeenCalledTimes(1);
    expect(r1.response.status).toBe(401);
    expect(r2.response.status).toBe(401);
  });

  it('menormalisasi format galat backend dan fallback non-JSON', () => {
    const dariServer = normalizeApiError(
      {
        kode: 'VALIDASI_GAGAL',
        pesan: 'Input tidak valid.',
        detail: { username: ['Wajib diisi.'] },
      },
      400,
    );
    expect(dariServer).toEqual({
      kode: 'VALIDASI_GAGAL',
      pesan: 'Input tidak valid.',
      detail: { username: ['Wajib diisi.'] },
      status: 400,
    });

    const fallback = normalizeApiError(null, 502);
    expect(fallback.kode).toBe('GALAT_SERVER');
    expect(fallback.detail).toEqual({});
    expect(fallback.status).toBe(502);
  });
});
