# SI-KKPRIS Web (React + Vite + TypeScript + Tailwind CSS v4)

Aplikasi frontend SPA untuk **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** — Koperasi KKPRIS SMK Negeri 1 Kota Solok.

## Prasyarat

- **Node.js** LTS terbaru (terverifikasi pada `v24.13.1` / `npm 11.8.0`)
- **Backend Django REST API** (`backend/`) berjalan pada `http://127.0.0.1:8000` dengan MySQL 8.x aktif

## Instalasi

```powershell
cd web
npm install
```

## Menjalankan Bersama Backend

Buka dua terminal di root repository `SI-KKPRIS`:

1. **Terminal 1 — Backend Django (`http://127.0.0.1:8000`):**
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   python manage.py runserver
   ```
2. **Terminal 2 — Frontend Vite (`http://localhost:5173`):**
   ```powershell
   cd web
   npm run dev
   ```

Seluruh permintaan ke `/api/*` diteruskan oleh proxy dev Vite (`vite.config.ts`) ke `http://127.0.0.1:8000` tanpa CORS, sehingga cookie refresh token `httpOnly` (`SameSite=Strict`, `Path=/api/v1/auth/`) bekerja sama seperti produksi satu origin.

## Daftar Skrip

| Skrip | Perintah | Fungsi |
| :--- | :--- | :--- |
| `npm run dev` | `vite` | Menjalankan server pengembangan dengan proxy `/api` |
| `npm run build` | `vite build` | Membuild bundel produksi ke `web/dist/` |
| `npm run preview` | `vite preview` | Pratinjau hasil build produksi secara lokal |
| `npm run lint` | `eslint .` | Pemeriksaan linting TypeScript & React Hooks |
| `npm run typecheck` | `tsc --noEmit -p tsconfig.app.json && tsc --noEmit -p tsconfig.node.json` | Pemeriksaan tipe TypeScript (`strict`) |
| `npm run test` | `vitest run` | Menjalankan suite pengujian unit Vitest + Testing Library |
| `npm run gen:api` | `openapi-typescript ../backend/docs/openapi.yaml -o src/api/schema.d.ts` | Menghasilkan tipe TypeScript dari skema OpenAPI backend |

## Struktur Folder `web/src/`

```text
src/
  api/
    schema.d.ts        # Tipe TypeScript hasil generate dari backend/docs/openapi.yaml
    client.ts          # Klien openapi-fetch, token di memori, single-flight 401 refresh, downloadFile
    queryClient.ts     # Konfigurasi TanStack Query (staleTime 30 dtk, retry selektif)
    queryKeys.ts       # Kunci query terpusat
  app/
    authContext.ts     # Tipe & context autentikasi (useAuth)
    AuthProvider.tsx   # Pemulihan sesi awal (refresh -> me), login, logout
    guards.tsx         # ProtectedRoute & RoleRoute (guard peran)
    routes.tsx         # Definisi rute React Router
    providers.tsx      # QueryClientProvider + BrowserRouter + AuthProvider
  components/
    ui/                # Komponen dasar desain sistem (mulai Tahap 9C)
    layout/            # AppShell, Sidebar, Topbar (mulai Tahap 9C)
  features/
    auth/              # Halaman login & beranda sementara
    system/            # Halaman 403 & 404
  lib/
    format.ts          # formatRupiah (manipulasi string murni) & formatTanggal (Asia/Jakarta)
    cn.ts              # Helper penggabung kelas Tailwind (clsx + tailwind-merge)
  styles/
    index.css          # Entry Tailwind CSS v4 (@import "tailwindcss")
  test/
    setup.ts           # Setup Vitest + jest-dom
    *.test.ts(x)       # Pengujian unit
```

## Prinsip Keamanan & Presisi Finansial

- **Token JWT:** *Access token* hanya disimpan pada variabel memori JavaScript (tidak pernah di `localStorage` atau `sessionStorage`). *Refresh token* berada pada cookie `httpOnly`.
- **Presisi uang:** Nominal uang diterima dari API dan dikirim sebagai **string** desimal. Tampilan uang wajib memakai `formatRupiah(value: string)` tanpa `parseFloat`, `Number()`, atau aritmetika uang di browser.
- **Kontrak API:** Setelah `backend/docs/openapi.yaml` diperbarui, selalu jalankan `npm run gen:api` dan commit perubahan `src/api/schema.d.ts`.
