# AGENTS.md (v2) — Aturan Kerja & Standar Pengembangan Proyek SI-KKPRIS

Aturan wajib bagi AI Agent pada setiap sesi pengerjaan **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** — Koperasi KKPRIS SMK Negeri 1 Kota Solok. Baca seluruhnya di awal setiap sesi. Urutan kerja ada di [`ROADMAP_PENGERJAAN.md`](./ROADMAP_PENGERJAAN.md).

---

## 0. Prinsip Utama

1. **Jangan mengarang aturan bisnis.** Angka, rumus, atau alur yang tidak tertulis di hasil wawancara atau SRS v4.0 tidak boleh diberi nilai bawaan diam-diam. Catat sebagai `PND-xx` di [`PENDING_KONFIRMASI.md`](./PENDING_KONFIRMASI.md), tandai kode dengan `# PENDING PND-xx` (frontend: `// PENDING PND-xx`), dan beri penanda di UI bila nilainya terlihat pengguna.
2. **Urutan sumber kebenaran:** hasil wawancara → SRS v4.0 → ERD/Class Diagram → kode. Jika kode bertentangan, kodenya yang salah.
3. **Skema OpenAPI adalah sumber kebenaran kontrak API.** Frontend tidak menebak bentuk respons; tipe TypeScript dihasilkan dari skema.
4. **Kerjakan hanya yang diminta.** Tidak menambah fitur, mengubah perilaku bisnis, atau merombak arsitektur di luar tahap yang diminta. Temuan lain dicatat di bagian "Temuan" pada `log_pengerjaan.md`.
5. **Lindungi data.** Jangan meng-commit `.env*`, `.venv/`, `venv/`, `node_modules/`, `dist/`, isi `media/`, dump database berisi data asli, maupun `.zip`. Khusus `.env`: jangan mengubah berkas `.env` tanpa menanyakan persetujuan pengguna terlebih dahulu beserta alasan mengapa perlu diubah; jangan membaca atau menampilkan nilai rahasia di luar kebutuhan yang disetujui. Seed dan test memakai data dummy.
6. **Bahasa:** komunikasi, komentar, dan pesan commit dalam Bahasa Indonesia; identifier mengikuti konvensi yang ada (backend: Indonesia; kode frontend: nama komponen dan fungsi boleh Inggris, teks yang tampil ke pengguna wajib Indonesia).
7. **Jika ragu, berhenti dan tanya pengguna.** Wajib berhenti dan meminta persetujuan sebelum: mengubah berkas `.env` (jelaskan alasannya terlebih dahulu), menghapus/mereset database, mengubah model pengguna, menghapus berkas dalam jumlah besar, atau `git push` ke selain `main`.

---

## 1. Standar Pesan Commit (Conventional Commits)

Format: `<type>(<scope>): <subject>` + `<body>` + `<footer>`.

- **type** (Inggris): `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
- **subject** (Indonesia): kata kerja perintah (`tambah`, `perbaiki`, `hapus`, `ubah`), diawali huruf kecil, **maksimal 50 karakter**, tanpa titik.
- **scope** opsional: `init`, `db`, `auth`, `member`, `simpanan`, `pembiayaan`, `agunan`, `approval`, `angsuran`, `rekap`, `laporan`, `ui`, `config`, `security`, `pdf`, `export`, `api`, `service`, `web`, `design`.
- `<body>` hanya bila kompleks (maks. 2–3 poin `-`: apa dan mengapa). `<footer>` untuk _breaking change_ (`feat!:`), `Closes #12`, atau `Refs: PND-01`.
- **Satu commit satu tujuan.** Jangan gabungkan perbaikan bug, refactor, dan fitur.

---

## 2. Log Harian (`log_pengerjaan.md`)

Setiap pengerjaan wajib dicatat per tanggal (`## 📅 18 November 2026`) dengan: **Fokus/Modul**, **Rincian Perubahan**, **Pesan Commit Terkait**, **Temuan & PENDING Baru**, **Status & Rencana Selanjutnya**.

---

## 3. Mengakhiri Pekerjaan Harian (Push ke GitHub)

- **Remote:** `https://github.com/ZikraRevanzha/SI-KKPRIS.git` (isi repository: `backend/`, `frontend/`, `web/`, `database/` (DDL SQL), `docs/`, `AGENTS.md`, `ROADMAP_PENGERJAAN.md`, `PENDING_KONFIRMASI.md`, `log_pengerjaan.md`, `README.md`).
- **Pemicu:** pengguna menyatakan mengakhiri pekerjaan ("selesai untuk hari ini", "push ke GitHub"). Jalankan berurutan; bila ada yang gagal, **jangan commit/push**, laporkan:
  1. Pastikan seluruh perubahan hari itu tercatat di log.
  2. Backend (`backend/`, virtualenv `backend/.venv` aktif): `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `python manage.py test koperasi`.
  3. Frontend (`web/`), bila ada perubahan: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`. Jika skema API berubah: `npm run gen:api` tidak boleh menghasilkan selisih yang belum di-commit.
  4. `git status`: pastikan tidak ada `.env*`, `.venv/`, `venv/`, `node_modules/`, `dist/`, `media/*` (kecuali `.gitkeep`), `*.zip`, `*.sqlite3`, `__pycache__/`, `staticfiles/` yang ter-stage.
  5. `git add`, `git commit` (Bagian 1), `git push origin main`. **Dilarang `--force`.**
  6. Laporkan hasil commit dan push.
- `.gitignore` minimal di root repository:
  ```text
  .venv/
  venv/
  __pycache__/
  *.pyc
  .env
  .env.*
  !.env.example
  node_modules/
  dist/
  *.local
  backend/staticfiles/
  backend/media/*
  !backend/media/.gitkeep
  *.zip
  ```

---

## 4. Arsitektur & Aturan Teknis

### A. Struktur Direktori (root repository = folder `SI-KKPRIS`)

```text
backend/        Django + DRF (API only untuk fitur baru)
  koperasi/
    models.py
    services/        <- logika bisnis (satu-satunya tempat aturan bisnis)
    api/v1/          <- serializers, views, permissions, urls (tipis)
    controllers/     <- LAMA (MVT), dibekukan
  docs/openapi.yaml  <- skema hasil drf-spectacular
web/            React + Vite + TypeScript + Tailwind (aplikasi baru)
frontend/       Template Django LAMA, dibekukan, dihapus di Tahap 14B
database/       DDL MySQL
```

Controller dan template lama **dibekukan**: tidak ada fitur baru, hanya perbaikan bug. Tes lama harus tetap lulus sampai Tahap 14B. Tag git `mvt-final` adalah titik kembali.

### B. Stack Final

- **Backend:** Python 3.11+ (lokal 3.13.7), Django 5.2 LTS, Django REST Framework, `djangorestframework-simplejwt` (+ `token_blacklist`), `drf-spectacular`, MySQL 8.x (`InnoDB`, `utf8mb4_unicode_ci`), satu driver: `mysqlclient`.
- **Frontend:** Node.js LTS terbaru, React, Vite, TypeScript (`strict`), **Tailwind CSS v4 lewat plugin `@tailwindcss/vite`** (tanpa `tailwind.config.js` dan `postcss.config.js`; token di CSS dengan `@theme`; `@import "tailwindcss";` di berkas CSS utama), React Router, TanStack Query, React Hook Form + Zod, `openapi-typescript` + `openapi-fetch`, `lucide-react` (ikon), Vitest + Testing Library, ESLint + Prettier.
- Gunakan versi stabil terbaru yang kompatibel, dan **cek dokumentasi resmi** sebelum menulis konfigurasi; jangan mengandalkan ingatan untuk sintaks instalasi.
- **Dilarang** menambah pustaka UI besar (MUI, Ant, Chakra, Bootstrap), pustaka animasi, atau pustaka state global tanpa persetujuan pengguna.

### C. Aturan API

1. Prefix `/api/v1/`. View DRF **tipis**; seluruh aturan bisnis ada di `services/`. Controller lama dan API memanggil service yang sama.
2. Hak akses: permission class per peran (`ANGGOTA`, `BENDAHARA`, `KETUA`) mengikuti dekorator peran di controller lama. Hak akses tidak boleh diperluas.
3. Format galat seragam: `{ "kode": "...", "pesan": "...", "detail": { "field": ["..."] } }`, pesan Bahasa Indonesia.
4. Paginasi untuk daftar (page size 20). Tanggal ISO 8601. **Uang selalu string desimal** di JSON (jangan menonaktifkan `COERCE_DECIMAL_TO_STRING`).
5. Setiap endpoint punya `tags`, `operation_id` stabil, dan test: sukses, 401, 403 (peran lain), 400 (validasi), serta aturan bisnis kuncinya.
6. Skema: `python manage.py spectacular --file docs/openapi.yaml`. Swagger UI di `/api/docs/` hanya aktif bila `API_DOCS_ENABLED=True`.
7. **CORS tidak dipakai.** Dev memakai proxy Vite; produksi satu origin. Dilarang `CORS_ALLOW_ALL_ORIGINS`.

### D. Autentikasi (JWT)

- `Pengguna` = `AbstractBaseUser` (+ `PermissionsMixin`), `AUTH_USER_MODEL = 'koperasi.Pengguna'`. Login memakai identifier yang berlaku saat ini; aturan login tidak berubah.
- **Access token** singkat (10 menit), disimpan **di memori JavaScript** (bukan `localStorage`/`sessionStorage`). **Refresh token** (30 menit, rotasi + blacklist) di cookie `httpOnly`, `SameSite=Strict`, `Path=/api/v1/auth/`, `Secure` bila bukan DEBUG.
- Tidak aktif > 30 menit = login ulang (sesuai SRS; verifikasi nomor kebutuhan di SRS). Logout memasukkan refresh token ke blacklist.
- Login dibatasi (throttle). Login, logout, dan gagal login tercatat di `AuditTrailLog`. IP memakai `REMOTE_ADDR` kecuali ada konfigurasi proxy tepercaya.

### E. Presisi Finansial

1. `DecimalField(max_digits=15, decimal_places=2)` / `DECIMAL(15,2)`. **Dilarang `float()`/`FLOAT`** untuk uang di model, service, serializer, ekspor Excel/PDF.
2. `ROUND_HALF_UP`, 2 desimal. Selisih pembulatan diserap **angsuran terakhir**. Invarian yang diuji: `sum(jumlah_angsuran) == total_kewajiban` dan `sum(porsi_pokok) == harga_pokok`.
3. Parser rupiah dan parser persen terpisah (titik + tepat tiga digit = pemisah ribuan pada rupiah).
4. **Frontend:** uang diterima dan dikirim sebagai **string**. Satu-satunya cara menampilkan: `formatRupiah(value: string)`. **Dilarang** `parseFloat`, `Number()`, `+x`, atau aritmetika uang di browser. Simulasi dan total selalu dari endpoint.

### F. Konsistensi & Keamanan

- Perubahan saldo/status keuangan: `transaction.atomic()` + `select_for_update()` sebelum menghitung; status dicek **di dalam kunci** (tolak aksi ganda). Frontend menonaktifkan tombol saat pending sebagai lapisan tambahan, bukan pengganti.
- `SECRET_KEY` dan `DEBUG` dari environment; hasher hanya `PBKDF2PasswordHasher`; tanpa `|safe`/`dangerouslySetInnerHTML` pada data pengguna.
- PDF dan Excel **tetap dibuat Django** (template PDF terpisah dari tampilan layar). Endpoint mengembalikan `FileResponse`; frontend mengunduh dengan `fetch` + header Authorization + blob.

### G. Aturan Bisnis

- **Terkonfirmasi:** 3 peran (`ANGGOTA`, `BENDAHARA`, `KETUA`); 5 simpanan: Pokok Rp350.000, Khusus Rp500.000, Wajib Rp150.000/bln terkunci (`dapat_ditarik = 0`), Hari Raya & Berencana sukarela (`dapat_ditarik = 1`); pembiayaan Murabahah/Ijarah/Hawalah: pengajuan tanggal 1–20, tenor maks. 72 bulan, margin **flat**, agunan wajib bila pokok > Rp70.000.000, tanpa denda; angsuran potong gaji, rekap tanggal 24 (Excel & PDF); pengeluaran kas wajib disetujui Ketua (_Two-Man Rule_) sebelum Bendahara mencatat realisasi _off-system_.
- **PENDING (jangan ditebak):** `PND-01` margin, `PND-02` Hawalah, `PND-03` alur akad, `PND-04` limit anggota, `PND-05` agunan, `PND-06` pembulatan, `PND-07` awal angsuran, `PND-08` pelunasan dipercepat, `PND-09` SHU/neraca, `PND-10` notifikasi.

---

## 5. Roadmap

Pengerjaan **vertikal per tahap**. Prompt rinci: `prompt_antigravity.md` (Tahap 8) dan `prompt_antigravity_v2.md` (Tahap 9–14). Acuan wireframe: `docs/wireframe/` (salin 22 PNG wireframe final ke folder ini).

| Tahap   | Fokus                                                                                      | Halaman (22 wireframe) |     Status     |
| :------ | :----------------------------------------------------------------------------------------- | :--------------------- | :------------: |
| 1–7     | Versi Django MVT: 16 model, auth, anggota, simpanan, pembiayaan, rekap, laporan            | 22 halaman template    | ✅ (dibekukan) |
| **8A**  | Tandai aturan PENDING, margin sementara ke konfigurasi, data seed dummy                    | –                      |       ⏳       |
| **8B**  | Perbaikan teknis backend (pembulatan, parser, `float`, kunci baris, PDF, keamanan)         | –                      |       ⏳       |
| **9A**  | Fondasi API: `Pengguna` custom, DRF, JWT cookie, Swagger, struktur `services/` & `api/v1/` | –                      |       ⏳       |
| **9B**  | Scaffold `web/`: Vite + React + TS + Tailwind, API client, auth, router, util uang         | –                      |       ⏳       |
| **9C**  | Design system, layout, Login, Dashboard, Beranda Anggota (+2 endpoint ringkasan)           | 1–3                    |       ⏳       |
| **10**  | Anggota & kliring resign (service → API → React)                                           | 4–7                    |       ⏳       |
| **11**  | Simpanan                                                                                   | 8–9                    |       ⏳       |
| **12A** | Pembiayaan: simulasi, pengajuan, agunan                                                    | 10–12                  |       ⏳       |
| **12B** | Pembiayaan: daftar, detail, persetujuan kas, realisasi                                     | 13–16                  |       ⏳       |
| **13**  | Angsuran, rekap potong gaji, notifikasi                                                    | 17–19                  |       ⏳       |
| **14A** | Kuitansi, laporan keuangan, audit trail                                                    | 20–22                  |       ⏳       |
| **14B** | Finalisasi: build produksi, hapus MVT, Postman, UAT, README                                | –                      |       ⏳       |

Status: ✅ selesai · ⏳ berikutnya. **Jangan memulai tahap berikutnya sebelum seluruh kriteria selesai tahap sebelumnya terpenuhi.**

---

## 6. Aturan Frontend React

1. **Struktur `web/src/`:** `api/` (klien, `schema.d.ts` hasil generate, query keys), `app/` (router, provider, guard), `components/ui/` (komponen dasar), `components/layout/`, `features/<modul>/` (pages, components, schemas, hooks), `lib/` (`format.ts`, `cn.ts`), `styles/index.css`.
2. **State server** hanya lewat TanStack Query (query keys terpusat; invalidasi setelah mutasi). State lokal lewat `useState`/`useReducer`. Tidak ada state global lain.
3. **Formulir:** React Hook Form + Zod; pesan galat Bahasa Indonesia; galat validasi server dipetakan ke field.
4. **Rute:** guard autentikasi dan guard peran; menu dibangun dari konfigurasi per peran. Menyembunyikan menu bukan pengganti otorisasi server.
5. **Setiap halaman wajib punya empat keadaan:** memuat, kosong, galat (dengan "Coba lagi"), dan berhasil.
6. **Aksi tak terbalik** (setujui, realisasi, tarik, hapus) wajib memakai dialog konfirmasi.
7. Tidak ada `any`, `@ts-ignore`, atau `console.log` tersisa. Komponen tidak melebihi sekitar 200 baris; pecah bila lebih.
8. Tidak ada nilai warna/ukuran yang diketik langsung di komponen; pakai token.

---

## 7. Aturan Desain

### A. Skill yang dipakai

- **`modern-web-guidance`:** sebelum menulis UI, cari dan ambil panduan resmi: `npx modern-web-guidance@latest search "<kebutuhan>"`, lalu `retrieve "<id>"`. Bila skill belum terpasang, minta pengguna memasangnya; jangan mengarang isi panduan.
- **`web-design-guidelines`** (bila terpasang): jalankan audit pada halaman yang selesai dan perbaiki temuan yang relevan.
- Utamakan fitur platform web modern (`<dialog>`, Popover API, `:has()`, container queries, `prefers-reduced-motion`) daripada JavaScript kustom.

### B. Warna: aturan 60-30-10

| Porsi         | Peran                                                                                 | Arah warna (titik awal, sesuaikan agar kontras lulus)                             |
| :------------ | :------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------- |
| **60% utama** | Latar halaman dan permukaan                                                           | Krem hangat `#F6F2EA`, permukaan putih `#FFFFFF`, garis `#E3DCCD`, teks `#1F2A24` |
| **30% kedua** | Sidebar, header, tabel header, tombol utama, tautan                                   | Hijau tua `#14452F`, hover `#0F3825`, tint `#E3EFE8`                              |
| **10% aksen** | Penanda: indikator menu aktif, angka kunci dashboard, pilihan terpilih, badge penting | Emas/amber `#D99A1E`; **teks di atas aksen selalu gelap**                         |

- Aksen dipakai hemat (kira-kira 10% luas layar), **bukan** untuk blok besar atau dekorasi.
- **Warna status** (sukses, peringatan, bahaya, info) didefinisikan terpisah dan di luar hitungan 60-30-10. Harus berbeda jelas dari aksen, dipakai hanya untuk status, dan **selalu disertai ikon dan teks** (jangan hanya warna).
- Kontras teks minimal WCAG AA (4,5:1; 3:1 untuk teks besar). Catat rasio kontras di `docs/design-system.md`.
- Tanpa gradien ungu/biru, kaca buram, atau bayangan berlapis. Mode gelap tidak dikerjakan kecuali diminta.

### C. Tipografi & komponen

- Satu keluarga font (disarankan IBM Plex Sans lewat `@fontsource`, tanpa CDN); bila angka tabular tidak tampil benar, pakai Inter. Skala tipografi tetap dan terbatas.
- Angka rupiah rata kanan dengan `font-variant-numeric: tabular-nums`. Tabel padat dan terbaca; label formulir jelas.
- Ikon SVG dari `lucide-react`. **Tanpa emoji sebagai ikon.**
- Wireframe adalah acuan struktur dan isi, bukan warna. Jangan menambah elemen dekoratif yang tidak ada di wireframe.

### D. Animasi loading

Hanya animasi berikut yang dipakai (nomor mengacu daftar "20 Loading Animations" yang kamu bagikan). Semuanya CSS murni, tanpa pustaka.

| Situasi                              | Animasi                                                        | Aturan                                                |
| :----------------------------------- | :------------------------------------------------------------- | :---------------------------------------------------- |
| Memuat tabel, daftar, kartu, detail  | **Skeleton Shimmer** (5)                                       | Bentuk sama dengan konten akhir; tanpa _layout shift_ |
| Pindah halaman, fetch latar belakang | **Indeterminate Bar** (4) tipis di atas layar                  | Tidak memblokir interaksi                             |
| Tombol kirim/simpan/setujui          | **Spinner Arc** (1) kecil di dalam tombol + label "Menyimpan…" | Tombol `disabled` selama pending                      |
| Muat awal aplikasi / cek sesi        | **Spinner Arc** (1) di tengah + teks "Memuat…"                 | Hanya saat belum ada konten                           |
| Unggah agunan, ekspor besar          | **Percent Bar** (16)                                           | Hanya bila progres diketahui (unggah memakai XHR)     |
| Teks kecil yang sedang dihitung      | **Text Shimmer** (18)                                          | Opsional                                              |

Animasi lain di daftar (Bouncing Dots, Pulse Rings, Orbit, Equalizer, Liquid Fill, Battery, Bouncing Ball, dan seterusnya) **tidak dipakai**: terlalu dekoratif untuk aplikasi keuangan dan menambah beban tanpa nilai.

Aturan wajib:

- Indikator baru tampil setelah tertunda ±200 ms (hindari kedipan) dan, bila sudah tampil, minimal ±400 ms.
- Kontainer memakai `aria-busy`; indikator memakai `role="status"` dan teks `sr-only` "Memuat…".
- `prefers-reduced-motion`: shimmer menjadi blok statis; spinner menjadi teks "Memuat…" tanpa gerak.
- Hanya animasikan `transform` dan `opacity`. Transisi UI lain 150–200 ms, tanpa efek memantul.
- Pemetaan TanStack Query: `isPending` → skeleton; `isFetching` (latar) → bar atas; mutasi `isPending` → spinner pada tombol.
- Komponen: `Skeleton`, `Spinner`, `TopProgress`, `ProgressBar` di `components/ui/`.

### E. Aksesibilitas & verifikasi

Kontras AA, fokus keyboard terlihat, semua fungsi bisa tanpa mouse, galat formulir diumumkan ke pembaca layar, hormati ukuran teks OS. Periksa di lebar 375, 768, dan 1280 px sebelum menandai halaman selesai.

### F. Responsif / mobile (aplikasi `web/`)

1. **Mobile-first:** gaya dasar untuk layar kecil, lalu perlebar dengan breakpoint Tailwind (`sm` 640, `md` 768, `lg` 1024, `xl` 1280). Tanpa `max-width` kustom di komponen.
2. `index.html` wajib `<meta name="viewport" content="width=device-width, initial-scale=1">`. Dilarang menonaktifkan zoom (`user-scalable=no`, `maximum-scale`).
3. **Navigasi:** sidebar menjadi drawer di bawah `lg` (tombol menu di Topbar, `<dialog>`/Popover native, fokus terkunci, tutup dengan Esc dan klik di luar). Sidebar tetap tampil mulai `lg`.
4. **Tabel:** di bawah `md` tampil sebagai daftar kartu bertumpuk (label + nilai) atau digulir horizontal di dalam kontainernya; halaman tidak boleh punya gulir horizontal. Angka rupiah tetap rata kanan dan `tabular-nums`.
5. **Formulir:** satu kolom di layar kecil, dua kolom mulai `md`. Tinggi kontrol dan area sentuh minimal 44×44 px; `inputmode`/`autocomplete` sesuai isian (mis. `inputmode="numeric"` untuk nominal, tetap string).
6. **Dialog dan aksi:** dialog konfirmasi memenuhi lebar layar kecil (bottom sheet atau lebar penuh dengan margin); tombol aksi utama dapat dijangkau ibu jari.
7. Gunakan container queries untuk komponen yang lebarnya ditentukan induk; unit `dvh`/`dvw` untuk tinggi layar penuh agar aman di peramban seluler.
8. Teks minimal 16 px pada input (cegah zoom otomatis iOS); hormati ukuran teks OS; hormati `env(safe-area-inset-*)` bila ada elemen menempel di tepi.
9. Verifikasi tiap halaman di 375, 768, dan 1280 px: tanpa gulir horizontal, tanpa teks terpotong, semua fungsi dapat dipakai dengan sentuhan dan keyboard.

---

## 8. Definisi Selesai

- [ ] Backend: `check`, `makemigrations --check`, `test koperasi` lulus (resmi di MySQL).
- [ ] Frontend: `lint`, `typecheck`, `test`, `build` lulus.
- [ ] `docs/openapi.yaml` dan `schema.d.ts` sinkron.
- [ ] Tidak ada `float()` untuk uang di backend, dan tidak ada `parseFloat`/`Number()` untuk uang di frontend.
- [ ] Aturan yang tidak pasti tercatat sebagai `PND-xx`.
- [ ] Ada test untuk perilaku yang diubah atau ditambah.
- [ ] `log_pengerjaan.md` diperbarui; commit mengikuti Bagian 1.
- [ ] Tidak ada berkas terlarang pada commit.

---

## 9. Protokol Anti-Halusinasi & Pelaporan

1. **Bukti sebelum klaim.** Dilarang menulis "selesai", "lulus", "sudah diperbaiki", atau ungkapan sejenis tanpa menjalankan perintah verifikasinya **pada pesan yang sama** dan menampilkan hasilnya. "Seharusnya lulus" atau "terlihat benar" bukan bukti.
2. **Setiap pernyataan faktual diberi label** di laporan: `[Terverifikasi]` (sertakan perintah atau `berkas:baris`), `[Asumsi]`, atau `[PENDING PND-xx]`.
3. **Aturan bisnis hanya dari sumber.** Angka, rumus, dan alur harus dikutip dari hasil wawancara atau SRS beserta lokasinya. Tidak ada sumber berarti `PND-xx`, bukan tebakan atau "nilai yang wajar".
4. **Jangan menebak API.** Sebelum memakai fungsi, parameter, atau konfigurasi pustaka (Django, DRF, simplejwt, drf-spectacular, Vite, Tailwind, React Router, TanStack Query), periksa dokumentasi resmi sesuai versi yang terpasang (mis. lewat Context7 bila tersedia, atau `pip show` / `npm ls`). Bila tidak dapat diperiksa, katakan terus terang.
5. **Ambigu berarti bertanya.** Jangan memilih sendiri tafsiran yang mengubah perilaku bisnis, data, atau arsitektur.
6. **Jangan menyembunyikan kegagalan.** Dilarang melemahkan, menghapus, atau melewati tes agar lulus; dilarang mengganti hasil nyata dengan data tiruan tanpa memberi tahu.
7. **Laporan akhir tiap tugas** memuat lima bagian: _Dikerjakan_, _Diverifikasi_ (perintah + ringkasan hasil), _Tidak diverifikasi_ (beserta alasannya), _Asumsi_, _Temuan di luar lingkup_. Sertakan `git diff --stat` dan jelaskan setiap berkas yang berubah di luar lingkup tugas.
8. **Skill dan `AGENTS.md`:** bila isi sebuah skill bertentangan dengan `AGENTS.md`, yang berlaku `AGENTS.md`. Laporkan pertentangannya.
