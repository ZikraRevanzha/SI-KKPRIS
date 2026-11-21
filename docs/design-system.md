# Design System — SI-KKPRIS

Standar visual, token desain, komponen UI, animasi loading, dan aturan responsif aplikasi frontend React (`web/`) untuk **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** — Koperasi KKPRIS SMK Negeri 1 Kota Solok.

Dokumen ini menjadi acuan tunggal bersama [`web/src/styles/index.css`](../web/src/styles/index.css) (Tailwind CSS v4 via `@theme`, tanpa `tailwind.config.js`).

---

## 1. Palet Warna (Aturan 60-30-10) & Rasio Kontras WCAG 2.1 AA

Seluruh rasio kontras di bawah dihitung secara matematis mengikuti rumus luminansi relatif WCAG 2.1. Ambang lulus: **≥ 4,5:1** untuk teks normal, **≥ 3,0:1** untuk teks besar (≥ 18 pt / 14 pt bold) dan batas komponen UI (WCAG 1.4.11).

### A. 60% Utama — Latar & Permukaan (Krem Hangat)

| Token CSS | Hex | Peran |
| --- | --- | --- |
| `--color-canvas` | `#F6F2EA` | Latar halaman utama |
| `--color-surface` | `#FFFFFF` | Permukaan kartu, tabel, formulir, dialog |
| `--color-surface-subtle` | `#FBF9F4` | Latar baris ringan, input nonaktif, pembatas halus |
| `--color-border` | `#E3DCCD` | Garis pembatas kartu dan bagian |
| `--color-border-strong` | `#C8BFA8` | Garis penegas sekunder |
| `--color-border-input` | `#8B8372` | Garis batas kontrol formulir (`input`, `select`, `textarea`) |
| `--color-ink` | `#1F2A24` | Teks utama dan judul |
| `--color-ink-secondary` | `#49574F` | Teks isi sekunder / subjudul |
| `--color-ink-muted` | `#5C6B62` | Keterangan kecil / label pendamping |

### B. 30% Kedua — Identitas Koperasi (Hijau Tua)

| Token CSS | Hex | Peran |
| --- | --- | --- |
| `--color-brand` | `#14452F` | Sidebar, tombol utama, header tabel, tautan, fokus ring |
| `--color-brand-hover` | `#0F3825` | Status *hover* tombol/item navigasi |
| `--color-brand-active` | `#0B2A1C` | Status aktif / ditekan |
| `--color-brand-tint` | `#E3EFE8` | Latar sorotan halus (badge merek, ikon kartu) |
| `--color-brand-ink` | `#FFFFFF` | Teks utama di atas `--color-brand` |
| `--color-brand-muted` | `#C2D8CC` | Teks pendamping di atas `--color-brand` (sidebar) |

### C. 10% Aksen — Emas/Amber (Dipakai Hemat)

| Token CSS | Hex | Peran |
| --- | --- | --- |
| `--color-accent` | `#D99A1E` | Indikator menu aktif, penanda angka kunci dashboard, pilihan terpilih |
| `--color-accent-tint` | `#FDF3DC` | Latar penanda penting (halus) |
| `--color-accent-ink` | `#1F2A24` | Teks di atas warna aksen (**wajib gelap**) |

**Aturan Penggunaan Aksen:**
1. Maksimal ~10% luas layar; **dilarang** untuk latar kartu besar, banner penuh, atau dekorasi semata.
2. Teks di atas `--color-accent` maupun `--color-accent-tint` **selalu** menggunakan `--color-accent-ink` (`#1F2A24`), bukan putih.
3. Aksen tidak digunakan sebagai warna status peringatan (status peringatan memakai oranye-karat `#9A3412` agar berbeda jelas).

### D. Warna Status (Terpisah di Luar Hitungan 60-30-10)

Setiap status **wajib** menampilkan **ikon `lucide-react` + teks** (tidak pernah mengandalkan warna saja).

| Status | Teks / Ikon | Latar | Border |
| --- | --- | --- | --- |
| Sukses | `#166534` | `#ECFDF3` | `#A7F3D0` |
| Peringatan | `#9A3412` | `#FFF3E8` | `#FDBA74` |
| Bahaya | `#B42318` (solid: teks `#FFFFFF`) | `#FEF3F2` | `#FECACA` |
| Info | `#1D4ED8` | `#EFF6FF` | `#BFDBFE` |

### E. Tabel Verifikasi Rasio Kontras (WCAG 2.1 AA)

| Pasangan Warna (Depan di Atas Belakang) | Rasio | Standar AA | Status |
| --- | :---: | :---: | :---: |
| `#1F2A24` di atas `#FFFFFF` (teks utama / kartu) | **14,84 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#1F2A24` di atas `#F6F2EA` (teks utama / kanvas) | **13,29 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#49574F` di atas `#FFFFFF` (teks sekunder / kartu) | **7,61 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#49574F` di atas `#F6F2EA` (teks sekunder / kanvas) | **6,82 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#5C6B62` di atas `#FFFFFF` (teks muted / kartu) | **5,62 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#5C6B62` di atas `#F6F2EA` (teks muted / kanvas) | **5,04 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#FFFFFF` di atas `#14452F` (tombol & sidebar) | **10,93 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#FFFFFF` di atas `#0F3825` (tombol hover) | **13,02 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#C2D8CC` di atas `#14452F` (teks pendamping sidebar) | **7,28 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#14452F` di atas `#E3EFE8` (badge merek / tint) | **9,25 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#1F2A24` di atas `#D99A1E` (teks gelap / aksen emas) | **6,07 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#1F2A24` di atas `#FDF3DC` (teks gelap / aksen tint) | **13,45 : 1** | ≥ 4,5 : 1 | Lulus (AAA) |
| `#D99A1E` di atas `#14452F` (indikator menu aktif UI) | **4,47 : 1** | ≥ 3,0 : 1 (UI) | Lulus (AA UI) |
| `#166534` di atas `#ECFDF3` (status sukses) | **6,76 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#9A3412` di atas `#FFF3E8` (status peringatan) | **6,69 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#B42318` di atas `#FEF3F2` (status bahaya) | **6,05 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#FFFFFF` di atas `#B42318` (tombol bahaya solid) | **6,57 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#1D4ED8` di atas `#EFF6FF` (status info) | **6,16 : 1** | ≥ 4,5 : 1 | Lulus (AA) |
| `#8B8372` di atas `#FFFFFF` (border input UI) | **3,76 : 1** | ≥ 3,0 : 1 (UI) | Lulus (AA UI) |

**Elemen yang dilarang:** gradien ungu/biru, kaca buram (`backdrop-filter: blur`), bayangan berlapis, emoji sebagai ikon, mode gelap, serta pengetikan nilai warna hex langsung di komponen.

---

## 2. Tipografi

- **Keluarga Font:** `IBM Plex Sans` (`400`, `500`, `600`, `700`) dibundel lokal melalui `@fontsource/ibm-plex-sans` (tanpa CDN).
- **Ukuran Teks OS:** `<meta name="text-scale" content="scale" />` aktif di `web/index.html`; stylesheet **tidak** menetapkan `font-size` pada `:root`/`html` sehingga seluruh ukuran `rem` mengikuti preferensi OS.
- **Angka Rupiah:** wajib memakai kelas `.uang-tabular` (`font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;`) dan rata kanan pada tabel, serta diformat hanya melalui `formatRupiah(value: string)`.

| Peran | Ukuran (`rem`) | Bobot | Line-Height | Penggunaan |
| --- | :---: | :---: | :---: | --- |
| Judul Halaman (`h1`) | `1.5rem` (mobile) / `1.75rem` (`md+`) | `700` | `1.25` | `PageHeader` |
| Judul Bagian / Panel (`h2`) | `1.125rem` | `600` | `1.35` | Judul `Card`, `Dialog` |
| Angka Kunci KPI | `1.375rem` – `1.5rem` | `700` | `1.2` | Nilai kartu ringkasan (`tabular-nums`) |
| Teks Isi & Input | `1rem` (input min. 16 px cegah zoom iOS) / `0.9375rem` | `400` | `1.5` | Paragraf, sel tabel, kontrol formulir |
| Label & Meta | `0.875rem` / `0.8125rem` | `500` | `1.4` | Label formulir, badge, teks pendamping |

---

## 3. Daftar Komponen UI (`web/src/components/ui/`)

| Komponen | Peran & Catatan Utama |
| --- | --- |
| `Button` | Varian `primary`, `secondary`, `ghost`, `danger`; tinggi min. 44 px (`md`); prop `loading` + `loadingText` otomatis menonaktifkan tombol (`disabled`, `aria-busy`) dan menampilkan `Spinner` kecil. |
| `Field`, `Input`, `Select`, `Textarea` | Label terikat `htmlFor`/`id` (`useId`), `hint`, galat `role="alert"` via `aria-describedby`, `aria-invalid`, teks min. 16 px, tinggi min. 44 px. |
| `Card` | `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardBody`, `CardFooter` dengan border 1 px `--color-border` dan bayangan tunggal `--shadow-card`. |
| `Badge` | Varian `neutral`, `brand`, `accent`, `success`, `warning`, `danger`, `info`; varian status otomatis menyertakan ikon `lucide-react` + teks. |
| `Table` | Tabel semantik (`<table>`) dengan `role="region"` & `tabIndex={0}`. Pada kontainer `< 40rem` (`@container`), otomatis menjadi kartu bertumpuk dengan label kolom (`data-label`). Kolom angka rata kanan + `.uang-tabular`. |
| `Dialog` & `ConfirmDialog` | Memakai `<dialog>` native (`showModal()`, `aria-labelledby`, tanpa `role="dialog"`/`aria-modal` redundant), `closedby="any"` + fallback klik-luar berbasis koordinat pointer, tombol tutup eksplisit. `ConfirmDialog` menempatkan `autoFocus` pada tombol aman (`Batal`) untuk aksi bahaya. |
| `Toast` & `ToastProvider` | Region notifikasi non-intrusif (`role="region" aria-label="Notifikasi"`, `aria-live="polite"`, tombol tutup keyboard-focusable, jeda timer saat fokus di dalam toast). |
| `Skeleton`, `Spinner`, `TopProgress`, `ProgressBar` | Komponen loading CSS murni mengikuti Bagian 4 di bawah. |
| `EmptyState`, `ErrorState`, `PageHeader` | Keadaan kosong terarah, keadaan galat dengan tombol `"Coba lagi"`, dan header halaman responsif. |

---

## 4. Aturan Animasi Loading (`AGENTS.md` Bagian 7.D)

Seluruh animasi ditulis dengan **CSS murni** dan hanya menganimasikan `transform` dan `opacity`.

| Situasi | Komponen | Animasi | Pemetaan TanStack Query |
| --- | --- | --- | --- |
| Memuat tabel, kartu, daftar, detail | `Skeleton` | Skeleton Shimmer (#5) | `isPending` |
| Pindah halaman / fetch latar belakang | `TopProgress` | Indeterminate Bar (#4) tipis di atas layar | `useIsFetching() > 0` |
| Tombol kirim / simpan / keluar | `Button` (`loading`) + `Spinner` | Spinner Arc (#1) + label (mis. `"Masuk…"`) | mutasi `isPending` / `isSubmitting` |
| Muat awal aplikasi / cek sesi | `Spinner` di tengah layar | Spinner Arc (#1) + teks `"Memuat…"` | `isInitializing` |
| Progres deterministik (pelunasan, unggah) | `ProgressBar` | Percent Bar (#16) | nilai `0–100` dari server / XHR |

**Kewajiban aksesibilitas & anti-kedip:**
- Hook `useDelayedLoading(isLoading, delayMs = 200, minDisplayMs = 400)` menunda tampilan indikator ±200 ms dan mempertahankan tampil minimal ±400 ms saat sudah muncul.
- Kontainer yang sedang memuat menggunakan `aria-busy="true"`; indikator memakai `role="status"` dan teks `sr-only` `"Memuat…"`.
- Pada `@media (prefers-reduced-motion: reduce)`: shimmer menjadi blok statis, top progress menjadi garis statis, dan spinner menyembunyikan lingkaran berputar lalu menampilkan teks `"Memuat…"` statis tanpa gerak.

---

## 5. Layout & Aturan Responsif Mobile-First (`AGENTS.md` Bagian 7.F)

- **Breakpoint:** mobile-first (dasar 375 px → `sm` 640 px → `md` 768 px → `lg` 1024 px → `xl` 1280 px).
- **Navigasi (`AppShell`):**
  - `< lg` (mobile & tablet): sidebar menjadi **Navigation Drawer** native menggunakan `<dialog>` (`showModal()`), dipicu tombol 44×44 px di `Topbar`, tertutup dengan `Esc`, klik di luar panel, tombol tutup, atau perpindahan rute.
  - `≥ lg` (desktop): sidebar hijau tua tetap tampil di kiri dengan lebar tetap, indikator menu aktif beraksen emas di sisi kiri tautan aktif.
  - Tautan *"Lompat ke konten utama"* (`#konten-utama`) tersedia di urutan fokus paling awal.
- **Area sentuh & formulir:** tombol & kontrol input minimal `44×44 px` (`min-h-11`), ukuran teks input minimal `16 px` (`text-base`), tanpa gulir horizontal pada lebar `375`, `768`, dan `1280 px`.
