import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './schema';

export interface ApiErrorShape {
  kode: string;
  pesan: string;
  detail: Record<string, string[]>;
  status?: number;
}

export class ApiError extends Error implements ApiErrorShape {
  readonly kode: string;
  readonly pesan: string;
  readonly detail: Record<string, string[]>;
  readonly status?: number;

  constructor(error: ApiErrorShape, options?: ErrorOptions) {
    super(error.pesan, options);
    this.name = 'ApiError';
    this.kode = error.kode;
    this.pesan = error.pesan;
    this.detail = error.detail;
    this.status = error.status;
  }
}

export function normalizeApiError(payload: unknown, status?: number): ApiErrorShape {
  if (typeof payload === 'object' && payload !== null) {
    const obj = payload as Record<string, unknown>;
    const kode = typeof obj.kode === 'string' && obj.kode ? obj.kode : defaultKodeDariStatus(status);
    const pesan =
      typeof obj.pesan === 'string' && obj.pesan ? obj.pesan : defaultPesanDariStatus(status);
    const detail = normalisasiDetail(obj.detail);
    return { kode, pesan, detail, status };
  }

  return {
    kode: defaultKodeDariStatus(status),
    pesan: defaultPesanDariStatus(status),
    detail: {},
    status,
  };
}

function normalisasiDetail(raw: unknown): Record<string, string[]> {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return {};
  }
  const hasil: Record<string, string[]> = {};
  for (const [kunci, nilai] of Object.entries(raw as Record<string, unknown>)) {
    if (Array.isArray(nilai)) {
      hasil[kunci] = nilai.map((item) => String(item));
    } else if (nilai !== undefined && nilai !== null) {
      hasil[kunci] = [String(nilai)];
    }
  }
  return hasil;
}

function defaultKodeDariStatus(status?: number): string {
  if (status === undefined) return 'GALAT_JARINGAN';
  if (status === 400) return 'VALIDASI_GAGAL';
  if (status === 401) return 'AUTENTIKASI_GAGAL';
  if (status === 403) return 'AKSES_DITOLAK';
  if (status === 404) return 'TIDAK_DITEMUKAN';
  if (status === 429) return 'TERLALU_BANYAK_PERMINTAAN';
  if (status >= 500) return 'GALAT_SERVER';
  return 'PERMINTAAN_GAGAL';
}

function defaultPesanDariStatus(status?: number): string {
  if (status === undefined) {
    return 'Tidak dapat terhubung ke server. Periksa koneksi Anda lalu coba lagi.';
  }
  if (status === 401) return 'Sesi Anda telah berakhir. Silakan login kembali.';
  if (status === 403) return 'Anda tidak memiliki izin untuk mengakses sumber daya ini.';
  if (status === 404) return 'Data yang diminta tidak ditemukan.';
  if (status === 429) return 'Terlalu banyak percobaan. Silakan tunggu beberapa saat.';
  if (status >= 500) return 'Terjadi kesalahan pada server. Silakan coba lagi nanti.';
  return 'Permintaan gagal diproses. Silakan coba lagi.';
}

const AUTH_LOGIN_PATH = '/api/v1/auth/login/';
const AUTH_REFRESH_PATH = '/api/v1/auth/refresh/';
const AUTH_LOGOUT_PATH = '/api/v1/auth/logout/';

function ambilPathname(url: string): string {
  try {
    return new URL(url, 'http://localhost').pathname;
  } catch {
    return url;
  }
}

function tanpaHeaderBearer(pathname: string): boolean {
  return pathname === AUTH_LOGIN_PATH || pathname === AUTH_REFRESH_PATH;
}

function tanpaRetryRefresh(pathname: string): boolean {
  return (
    pathname === AUTH_LOGIN_PATH ||
    pathname === AUTH_REFRESH_PATH ||
    pathname === AUTH_LOGOUT_PATH
  );
}

export interface RefreshOptions {
  /** Panggil handler pengalihan ke /login bila refresh gagal. Default: false. */
  notifyOnFailure?: boolean;
}

export interface ApiClientBundle {
  client: ReturnType<typeof createClient<paths>>;
  getAccessToken: () => string | null;
  setAccessToken: (token: string | null) => void;
  clearAccessToken: () => void;
  refreshAccessToken: (options?: RefreshOptions) => Promise<string | null>;
  setSessionExpiredHandler: (handler: (() => void) | null) => void;
  downloadFile: (path: string, namaFile: string) => Promise<void>;
}

/**
 * Factory klien API SI-KKPRIS berbasis openapi-fetch.
 * - Access token hanya disimpan di variabel memori modul (TIDAK pernah di localStorage/sessionStorage).
 * - Middleware menyisipkan Authorization dan menjalankan single-flight refresh saat 401.
 * - Mendukung penyuntikan fetch khusus untuk pengujian unit.
 */
function ambilBaseUrl(): string {
  if (
    typeof window !== 'undefined' &&
    typeof window.location?.origin === 'string' &&
    window.location.origin !== 'null'
  ) {
    return window.location.origin;
  }
  return '';
}

function gabungUrl(baseUrl: string, path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  return `${baseUrl}${path}`;
}

export function createApiClientBundle(customFetch?: typeof fetch): ApiClientBundle {
  // Variabel memori privat (bukan localStorage/sessionStorage)
  let accessToken: string | null = null;
  let refreshInFlight: Promise<string | null> | null = null;
  let notifySessionExpiredOnFailure = false;
  let sessionExpiredHandler: (() => void) | null = null;
  const retryRequestClones = new WeakMap<Request, Request>();
  const baseUrl = ambilBaseUrl();

  const jalankanFetch: typeof fetch = (input, init) => {
    const fn = customFetch ?? globalThis.fetch;
    return fn(input, init);
  };

  function getAccessToken(): string | null {
    return accessToken;
  }

  function setAccessToken(token: string | null): void {
    accessToken = token;
  }

  function clearAccessToken(): void {
    accessToken = null;
  }

  function setSessionExpiredHandler(handler: (() => void) | null): void {
    sessionExpiredHandler = handler;
  }

  function tanganiSesiKedaluwarsa(): void {
    accessToken = null;
    if (sessionExpiredHandler) {
      sessionExpiredHandler();
      return;
    }
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
  }

  function refreshAccessToken(options?: RefreshOptions): Promise<string | null> {
    if (options?.notifyOnFailure) {
      notifySessionExpiredOnFailure = true;
    }
    if (refreshInFlight) {
      return refreshInFlight;
    }

    refreshInFlight = (async () => {
      try {
        const res = await jalankanFetch(gabungUrl(baseUrl, AUTH_REFRESH_PATH), {
          method: 'POST',
          credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        });
        if (!res.ok) {
          accessToken = null;
          if (notifySessionExpiredOnFailure) {
            tanganiSesiKedaluwarsa();
          }
          return null;
        }
        const data = (await res.json()) as { access?: unknown };
        if (typeof data.access !== 'string' || !data.access) {
          accessToken = null;
          if (notifySessionExpiredOnFailure) {
            tanganiSesiKedaluwarsa();
          }
          return null;
        }
        accessToken = data.access;
        return data.access;
      } catch {
        accessToken = null;
        if (notifySessionExpiredOnFailure) {
          tanganiSesiKedaluwarsa();
        }
        return null;
      } finally {
        refreshInFlight = null;
        notifySessionExpiredOnFailure = false;
      }
    })();

    return refreshInFlight;
  }

  const authMiddleware: Middleware = {
    async onRequest({ request }) {
      const pathname = ambilPathname(request.url);
      if (accessToken && !tanpaHeaderBearer(pathname)) {
        request.headers.set('Authorization', `Bearer ${accessToken}`);
      }
      if (!tanpaRetryRefresh(pathname)) {
        retryRequestClones.set(request, request.clone());
      }
      return request;
    },

    async onResponse({ request, response }) {
      const retryClone = retryRequestClones.get(request);
      retryRequestClones.delete(request);

      if (response.status !== 401) {
        return response;
      }

      const pathname = ambilPathname(request.url);
      if (tanpaRetryRefresh(pathname)) {
        return response;
      }

      const tokenBaru = await refreshAccessToken({ notifyOnFailure: true });
      if (!tokenBaru) {
        return response;
      }

      const retryRequest = retryClone ?? request;
      retryRequest.headers.set('Authorization', `Bearer ${tokenBaru}`);
      return jalankanFetch(retryRequest);
    },
  };

  const client = createClient<paths>({
    baseUrl,
    credentials: 'same-origin',
    fetch: jalankanFetch,
  });
  client.use(authMiddleware);

  async function downloadFile(path: string, namaFile: string): Promise<void> {
    const urlTujuan = gabungUrl(baseUrl, path);
    const buatHeader = (): Headers => {
      const headers = new Headers();
      if (accessToken) {
        headers.set('Authorization', `Bearer ${accessToken}`);
      }
      return headers;
    };

    let response = await jalankanFetch(urlTujuan, {
      method: 'GET',
      credentials: 'same-origin',
      headers: buatHeader(),
    });

    if (response.status === 401) {
      const tokenBaru = await refreshAccessToken({ notifyOnFailure: true });
      if (tokenBaru) {
        response = await jalankanFetch(urlTujuan, {
          method: 'GET',
          credentials: 'same-origin',
          headers: buatHeader(),
        });
      }
    }

    if (!response.ok) {
      let payload: unknown = null;
      try {
        payload = await response.json();
      } catch {
        // Biarkan payload tetap null bila respons bukan JSON
      }
      throw new ApiError(normalizeApiError(payload, response.status));
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    try {
      const tautan = document.createElement('a');
      tautan.href = objectUrl;
      tautan.download = namaFile;
      document.body.appendChild(tautan);
      tautan.click();
      tautan.remove();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }

  return {
    client,
    getAccessToken,
    setAccessToken,
    clearAccessToken,
    refreshAccessToken,
    setSessionExpiredHandler,
    downloadFile,
  };
}

const defaultBundle = createApiClientBundle();

export const apiClient = defaultBundle.client;
export const getAccessToken = defaultBundle.getAccessToken;
export const setAccessToken = defaultBundle.setAccessToken;
export const clearAccessToken = defaultBundle.clearAccessToken;
export const refreshAccessToken = defaultBundle.refreshAccessToken;
export const setSessionExpiredHandler = defaultBundle.setSessionExpiredHandler;
export const downloadFile = defaultBundle.downloadFile;
