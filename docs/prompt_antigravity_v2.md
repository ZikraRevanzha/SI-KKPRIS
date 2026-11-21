# Prompt Antigravity v2 — Tahap 8 (addendum) dan Tahap 9–14

Dipakai bersama `ROADMAP_PENGERJAAN.md`. Salin isi di dalam blok, tempel ke **sesi baru**.

---

## Addendum Tahap 8 (tempel di AKHIR Prompt A dan Prompt B dari `prompt_antigravity.md`)

```text
PENYESUAIAN ARSITEKTUR (AGENTS.md v2):
- Template Django lama dibekukan; jangan membuat atau mengubah UI di template.
- Prompt A: LEWATI bagian "Tampilkan catatan ... pada pembiayaan/ajukan_pembiayaan.html dan detail_pembiayaan.html". Pemindahan margin ke settings.MARGIN_PERSEN_SEMENTARA tetap dikerjakan; nilainya akan diekspos lewat API di Tahap 12A.
- Prompt B: LEWATI ITEM 6 (URL JavaScript di template). ITEM 5 (template PDF terpisah) tetap dikerjakan karena PDF tetap dibuat Django.
```

---

## Prompt 9A — Fondasi API & Autentikasi JWT (backend saja)

```text
Kerjakan Tahap 9A. Baca AGENTS.md (Bagian 0, 4, 8) dan PENDING_KONFIRMASI.md. Hanya backend. Dilarang membuat React atau mengubah aturan bisnis.

LANGKAH
1. Dependensi: tambahkan djangorestframework, djangorestframework-simplejwt, drf-spectacular ke requirements.txt (versi stabil terbaru yang kompatibel dengan Django 5.2; cek dokumentasi resmi masing-masing). Tambahkan 'rest_framework', 'rest_framework_simplejwt.token_blacklist', 'drf_spectacular' ke INSTALLED_APPS.
2. Model pengguna: ubah Pengguna menjadi AbstractBaseUser + PermissionsMixin dan set AUTH_USER_MODEL = 'koperasi.Pengguna'.
   - Periksa dulu seluruh referensi ke Pengguna, kolom password_hash, dan AuthController.
   - Data masih dummy, jadi database LOKAL boleh direset (drop dan buat ulang si_kkpris, migrate, seed_master). TAMPILKAN RENCANA dan TUNGGU PERSETUJUAN SAYA sebelum menghapus database apa pun.
   - Sinkronkan database/02_DDL_MySQL_SI-KKPRIS.sql dengan model baru.
   - Login lama (session, template) harus tetap bekerja; seluruh test lama harus tetap lulus.
3. Struktur: buat koperasi/services/ (mulai dengan auth_service.py: ekstrak logika login dan audit trail dari AuthController; controller lama memanggil service itu), koperasi/api/v1/ (urls.py, permissions.py, exceptions.py, pagination.py, serializers/, views/). Sertakan di urls utama pada prefix /api/v1/.
4. Permission class: IsAnggota, IsBendahara, IsKetua, IsBendaharaAtauKetua, mengikuti aturan peran yang sudah ada. Jangan memperluas hak akses.
5. Endpoint autentikasi:
   - POST /api/v1/auth/login : kembalikan access token di body; set refresh token di cookie httpOnly, SameSite=Strict, Path=/api/v1/auth/, Secure bila DEBUG False.
   - POST /api/v1/auth/refresh : baca refresh dari cookie, rotasi, set cookie baru, kembalikan access baru.
   - POST /api/v1/auth/logout : blacklist refresh, hapus cookie.
   - GET /api/v1/auth/me : id, nama, peran, dan data profil yang dibutuhkan UI.
   - POST /api/v1/auth/ganti-password.
   Pertahankan aturan login yang ada (pesan galat, pembatasan percobaan bila ada). Login, logout, gagal login tercatat di AuditTrailLog.
6. Settings:
   - REST_FRAMEWORK: autentikasi JWT, default permission IsAuthenticated, renderer JSON saja, exception handler seragam {kode, pesan, detail} Bahasa Indonesia, paginasi page size 20, throttle login (scope khusus), JANGAN menonaktifkan COERCE_DECIMAL_TO_STRING.
   - SIMPLE_JWT: ACCESS 10 menit, REFRESH 30 menit, ROTATE_REFRESH_TOKENS=True, BLACKLIST_AFTER_ROTATION=True.
   - Tanpa CORS. Jangan tambahkan django-cors-headers.
7. drf-spectacular: SPECTACULAR_SETTINGS (judul "SI-KKPRIS API", versi 1.0.0, tag per modul). /api/schema/ dan /api/docs/ aktif hanya bila env API_DOCS_ENABLED=True (tambahkan ke .env.example). Hasilkan docs/openapi.yaml.
8. Test API: login sukses dan gagal, atribut cookie (httpOnly, SameSite), refresh dan rotasi, refresh lama ditolak (blacklist), logout, me, 401 tanpa token, 403 peran salah, throttle, audit trail tertulis.
9. Dokumentasi singkat di README bagian API: cara menjalankan, cara mengambil token, lokasi Swagger.

ATURAN
- Satu commit per tujuan (contoh: chore(config): tambah DRF dan simplejwt; refactor(auth): ekstrak service login; feat(api): tambah endpoint autentikasi; test(api): tambah tes autentikasi).
- Jalankan check, makemigrations --check, dan test sebelum tiap commit. Perbarui log_pengerjaan.md.
```

---

## Prompt 9B — Scaffold Aplikasi React (frontend saja)

```text
Kerjakan Tahap 9B. Baca AGENTS.md (Bagian 4.B, 4.D, 4.E, 6). Hanya folder web/. Dilarang mengubah backend kecuali Anda menemukan bug API; jika ada, catat sebagai temuan dan tanyakan dulu.

LANGKAH
1. Periksa node -v. Di root repository buat proyek: npm create vite@latest web dengan template react-ts (ikuti dokumentasi resmi Vite terbaru).
2. Tailwind v4: npm install tailwindcss @tailwindcss/vite; tambahkan plugin tailwindcss() di vite.config.ts; di src/styles/index.css cukup @import "tailwindcss"; plus blok @theme nanti di 9C. JANGAN membuat tailwind.config.js atau postcss.config.js. Verifikasi di dokumentasi resmi Tailwind.
3. Dependensi: react-router, @tanstack/react-query, react-hook-form, zod, @hookform/resolvers, lucide-react, clsx, tailwind-merge, openapi-fetch, dan font via @fontsource (IBM Plex Sans). Dev: typescript, vitest, @testing-library/react, @testing-library/jest-dom, jsdom, eslint (+ plugin react-hooks), prettier, openapi-typescript. Tidak ada pustaka UI besar atau pustaka animasi.
4. vite.config.ts: alias '@' -> src; server.proxy '/api' -> http://127.0.0.1:8000. tsconfig strict.
5. package.json scripts: dev, build, preview, lint, typecheck (tsc --noEmit), test (vitest run), gen:api (openapi-typescript ../backend/docs/openapi.yaml -o src/api/schema.d.ts). Jalankan gen:api dan commit schema.d.ts.
6. Struktur src/ sesuai AGENTS.md 6.1 (api, app, components/ui, components/layout, features, lib, styles).
7. Klien API (src/api/client.ts) dengan openapi-fetch:
   - access token di variabel modul (memori), BUKAN localStorage/sessionStorage;
   - middleware menambahkan Authorization; saat 401 lakukan SATU refresh bersama (single-flight) lalu ulangi permintaan sekali; bila refresh gagal, kosongkan sesi dan arahkan ke /login;
   - normalisasi galat ke {kode, pesan, detail};
   - credentials: 'same-origin' agar cookie refresh terkirim;
   - helper downloadFile(path, namaFile) memakai fetch + Authorization + blob.
8. AuthProvider: saat aplikasi dimuat panggil refresh lalu me untuk memulihkan sesi; sediakan login(), logout(), user. Komponen ProtectedRoute dan RoleRoute (peran). Router: /login, rute terlindungi, 403 dan 404 sederhana.
9. QueryClient: staleTime 30 detik, retry 1 untuk GET (bukan untuk 401/403/404), tanpa retry untuk mutasi.
10. src/lib/format.ts: formatRupiah(value: string), formatTanggal (Intl id-ID, zona Asia/Jakarta). Tanpa parseFloat/Number untuk uang di tempat lain. src/lib/cn.ts.
11. Halaman login SEDERHANA tanpa gaya (hanya untuk membuktikan alur login -> me -> logout terhadap backend nyata). Desain dikerjakan di 9C.
12. Test (Vitest): formatRupiah dan formatTanggal; klien API single-flight refresh (mock); RoleRoute mengizinkan/menolak sesuai peran.
13. web/README.md: cara menjalankan bersama backend, daftar script, struktur folder.

SELESAI bila: npm run lint, typecheck, test, build lulus; dengan backend berjalan, login akun seed berhasil dan refresh setelah muat ulang halaman memulihkan sesi.

ATURAN: satu commit per tujuan (scope web/api), update log_pengerjaan.md, jangan menyimpan token di localStorage.
```

---

## Prompt 9C — Design System, Layout, dan 3 Halaman

```text
Kerjakan Tahap 9C. Baca AGENTS.md (terutama Bagian 6 dan 7). Prasyarat: 9A dan 9B selesai. Gunakan skill modern-web-guidance (jalankan: npx modern-web-guidance@latest search "navigation drawer"; bila gagal, berhenti dan minta saya memasangnya). Jangan mengarang isi panduan.

A. DESIGN SYSTEM
1. Baca wireframe 1-3 (Login.png, Dashboard.png, Beranda Anggota.png) di docs/wireframe/ (jika folder kosong atau tidak ada, berhenti dan minta saya menyalin wireframe ke sana). Wireframe = acuan struktur dan isi, bukan warna.
2. Definisikan token di src/styles/index.css dengan @theme: palet 60-30-10 dari AGENTS.md 7.B (krem hangat 60%, hijau tua 30%, aksen emas 10%), warna status terpisah (berbeda jelas dari aksen, selalu dengan ikon dan teks), skala spasi, radius, bayangan tipis, tipografi (IBM Plex Sans; periksa tabular-nums tampil benar, jika tidak pakai Inter).
3. Tulis docs/design-system.md: palet beserta rasio kontras yang DIHITUNG (AA), skala tipografi, daftar komponen, aturan loading (AGENTS.md 7.D), aturan penggunaan aksen.
4. Komponen src/components/ui/ (hanya yang jelas dibutuhkan; sisanya dibuat saat modul membutuhkan): Button (primary/secondary/ghost/danger, prop loading), Field + Input + Select + Textarea, Card, Badge (status), Table (responsif, kolom angka rata kanan tabular-nums), Dialog (elemen <dialog> native) + ConfirmDialog, Toast (live region), Skeleton (shimmer), Spinner (arc), TopProgress (indeterminate bar), ProgressBar (persen), EmptyState, ErrorState, PageHeader.
   Semua loading mengikuti AGENTS.md 7.D: tunda ±200 ms, aria-busy/role="status"/teks sr-only, dukung prefers-reduced-motion, hanya animasi transform/opacity, CSS murni.
5. Layout: AppShell dengan Sidebar (drawer di layar kecil), Topbar (menu pengguna, keluar), tautan "lompat ke konten", indikator menu aktif (aksen), menu dari konfigurasi per peran (navigation.ts). Ikon lucide-react, TANPA emoji. Patuhi AGENTS.md 7.F (mobile-first, drawer di bawah lg, tabel menjadi kartu di bawah md, area sentuh 44 px, viewport tanpa pembatas zoom, tanpa gulir horizontal).

B. HALAMAN (3)
6. Login: React Hook Form + Zod, galat server tampil jelas, tombol dengan spinner dan teks "Masuk…", tanpa emoji.
7. Dashboard (Bendahara dan Ketua) dan Beranda Anggota: perlu data. Periksa controller lama yang menyuplai data kedua halaman, buat koperasi/services/dashboard_service.py dan endpoint read-only GET /api/v1/dashboard/ringkasan/ (Bendahara/Ketua) serta GET /api/v1/anggota/saya/ringkasan/ (Anggota) memakai logika yang SUDAH ADA (jangan menggandakan). Uang string. Tambahkan test API (200, 401, 403). Regenerasi docs/openapi.yaml dan jalankan npm run gen:api.
8. Setiap halaman punya keadaan memuat (skeleton), kosong, galat ("Coba lagi"), dan berhasil.

C. VERIFIKASI
9. Test Vitest: validasi form login, menu sesuai peran, Button loading menonaktifkan klik.
10. Periksa di lebar 375, 768, 1280 px dan hanya dengan keyboard (gunakan browser Antigravity bila tersedia; bila tidak, katakan terus terang bagian yang tidak dapat diverifikasi). Jalankan audit web-design-guidelines bila skill terpasang dan perbaiki temuan relevan.
11. Backend: check, makemigrations --check, test lulus. Frontend: lint, typecheck, test, build lulus.

DILARANG: gradien ungu/biru, kaca buram, bayangan berlapis, emoji sebagai ikon, nilai warna yang diketik langsung di komponen, pustaka UI atau animasi besar, mode gelap.
Satu commit per kelompok (scope design/ui/api/web). Perbarui log_pengerjaan.md.
```

---

## Blok Parameter per Tahap (tempel di ATAS Template PM-BE atau PM-FE)

### Tahap 10 — Anggota & Kliring Resign

```text
PARAMETER
TAHAP: 10
MODUL: anggota
CONTROLLER LAMA: controllers/anggota_controller.py (AnggotaController)
USE CASE: UC-02 s.d. UC-04
HAK AKSES: ikuti dekorator peran di controller lama (Bendahara kelola anggota dan verifikasi resign; Anggota mengajukan resign dan melihat data sendiri). Jangan mengubah.
HALAMAN: 4 Data Anggota.png, 5 Form Anggota Baru.png, 6 Ajukan Pengunduran Diri.png, 7 Verifikasi Pengunduran Diri.png
CATATAN: Nomor anggota dibuat di server. Kliring resign (total simpanan dikurangi total kewajiban) dihitung di server dan dikirim sebagai string uang.
SKENARIO UJI: (1) Bendahara membuat anggota baru, nomor otomatis; (2) edit dan nonaktifkan anggota; (3) Anggota mengajukan resign; (4) Bendahara memverifikasi, hasil kliring benar untuk selisih lebih dan kurang; (5) Anggota tidak bisa membuka data anggota lain.
```

### Tahap 11 — Simpanan

```text
PARAMETER
TAHAP: 11
MODUL: simpanan
CONTROLLER LAMA: controllers/simpanan_controller.py (SimpananController)
USE CASE: UC-05, UC-06
HAK AKSES: ikuti controller lama (Bendahara mencatat setor/tarik; Anggota melihat saldo sendiri).
HALAMAN: 8 Kelola Simpanan.png, 9 Transaksi Baru.png
CATATAN: Lima jenis simpanan; Pokok, Khusus, Wajib terkunci (dapat_ditarik = 0) sehingga tarik ditolak server. Saldo berantai wajib memakai select_for_update. Cetak kuitansi dikerjakan di Tahap 14A, bukan di sini. Periksa dan pakai parser rupiah baru dari Tahap 8B.
SKENARIO UJI: (1) setor ke tiap jenis simpanan; (2) tarik simpanan sukarela; (3) tarik simpanan terkunci ditolak; (4) tarik melebihi saldo ditolak; (5) klik ganda cepat tidak membuat transaksi ganda.
```

### Tahap 12A — Pembiayaan: Pengajuan

```text
PARAMETER
TAHAP: 12A
MODUL: pembiayaan (pengajuan)
CONTROLLER LAMA: controllers/pembiayaan_controller.py (PembiayaanController; bagian simulasi, pengajuan, agunan)
USE CASE: UC-07
HAK AKSES: ikuti controller lama.
HALAMAN: 10 Ajukan Pembiayaan - Pilih Akad.png, 11 Ajukan Pembiayaan - Nominal & Tenor.png, 12 Ajukan Pembiayaan - Agunan.png
CATATAN: Simulasi dihitung di server (endpoint terpisah) dan JANGAN dihitung ulang di browser. Pengajuan hanya tanggal 1-20 (divalidasi server, pesan jelas di UI). Agunan wajib bila pokok > Rp70.000.000; unggah berkas multipart dengan ProgressBar (gunakan XHR bila perlu progres). Tampilkan penanda "Margin sementara (belum dikonfirmasi koperasi)" PND-01 pada simulasi, dengan nilai dari API (settings.MARGIN_PERSEN_SEMENTARA). Hawalah: rumus tidak diubah, tandai PND-02. Wizard 3 langkah dengan RHF, kembali/lanjut tanpa kehilangan isian.
SKENARIO UJI: (1) simulasi tiga akad; (2) pokok tepat Rp70.000.000 tanpa agunan lolos, Rp70.000.001 wajib agunan; (3) pengajuan tanggal 21 ditolak; (4) tenor 73 bulan ditolak; (5) unggah agunan gagal ukuran/tipe berkas ditolak jelas.
```

### Tahap 12B — Pembiayaan: Persetujuan & Realisasi

```text
PARAMETER
TAHAP: 12B
MODUL: pembiayaan (daftar, detail, persetujuan kas, realisasi)
CONTROLLER LAMA: controllers/pembiayaan_controller.py dan bagian approval kas
USE CASE: UC-08 s.d. UC-10
HAK AKSES: ikuti controller lama (Ketua menyetujui pengeluaran kas; Bendahara mencatat realisasi setelah persetujuan).
HALAMAN: 13 Daftar Pembiayaan.png, 14 Detail Pembiayaan.png, 15 Persetujuan Kas.png, 16 Konfirmasi Persetujuan.png
CATATAN: Two-Man Rule: realisasi tanpa persetujuan Ketua harus ditolak server. Status berpindah hanya lewat service dengan select_for_update dan pengecekan status di dalam kunci. Detail menampilkan kartu/jadwal angsuran memakai fungsi tunggal dari Tahap 8B (angsuran terakhir menyerap sisa). Aksi setujui dan realisasi memakai ConfirmDialog. Antrean (no_antrean) tampil bila dana belum tersedia.
SKENARIO UJI: (1) Ketua menyetujui lalu Bendahara merealisasi; (2) realisasi sebelum persetujuan ditolak; (3) setujui dua kali ditolak; (4) Bendahara tidak bisa menyetujui kas; (5) jadwal angsuran: jumlah angsuran sama dengan total kewajiban.
```

### Tahap 13 — Angsuran, Rekap Potong Gaji, Notifikasi

```text
PARAMETER
TAHAP: 13
MODUL: angsuran, rekap, notifikasi
CONTROLLER LAMA: controllers/rekap_notifikasi_controller.py (RekapNotifikasiController)
USE CASE: UC-11, UC-12, UC-14
HAK AKSES: ikuti controller lama.
HALAMAN: 17 Kelola Angsuran.png, 18 Rekap Potong Gaji.png, 19 Notifikasi Tagihan.png
CATATAN: Rekap potong gaji dibuat tanggal 24; ekspor Excel dan PDF dibuat server dan diunduh lewat downloadFile (blob). Pembayaran angsuran: kunci baris jadwal, tolak bayar ganda. Pelunasan batch kolektif dan cicilan mandiri tetap sesuai perilaku lama. Aturan pelunasan dipercepat dan potongan margin = PND-08 (jangan mengubah, hanya tampilkan apa adanya). Notifikasi WA/Email tanggal 10: kanal dan cara kirim = PND-10; implementasikan hanya yang sudah ada di backend, tanpa menambah integrasi baru.
SKENARIO UJI: (1) generate rekap tanggal 24 dan unduh Excel serta PDF yang isinya sama dengan layar; (2) bayar angsuran, saldo dan status benar; (3) bayar angsuran yang sama dua kali ditolak; (4) batch lunas; (5) halaman notifikasi menampilkan daftar jatuh tempo.
```

### Tahap 14A — Kuitansi, Laporan, Audit

```text
PARAMETER
TAHAP: 14A
MODUL: laporan, kuitansi, audit trail
CONTROLLER LAMA: controllers/laporan_bukti_controller.py (LaporanBuktiController)
USE CASE: UC-13
HAK AKSES: ikuti controller lama (Ketua melihat seluruh laporan dan audit trail).
HALAMAN: 20 Cetak Bukti Transaksi.png, 21 Cetak Bukti Pembayaran.png, 22 Laporan Keuangan.png, ditambah halaman Audit Trail Log (Ketua)
CATATAN: Kuitansi dan laporan PDF/Excel dibuat Django memakai template PDF terpisah dari Tahap 8B (tanpa tombol, tanpa emoji). Frontend menampilkan pratinjau data dan tombol unduh. Laporan SHU/neraca/arus kas: rumus dan format masih PND-09; tampilkan persis perilaku yang ada, beri label "format sementara", dan JANGAN menambah rumus baru. Audit trail: daftar dengan filter tanggal, pengguna, dan aksi; paginasi.
SKENARIO UJI: (1) unduh kuitansi simpanan dan angsuran, PDF tidak memuat tombol; (2) laporan triwulanan tampil dan terunduh; (3) Anggota dan Bendahara tidak bisa membuka audit trail; (4) Ketua melihat audit trail dan filter bekerja.
```

---

## Template PM-BE (backend modul) — tempel DI BAWAH Blok Parameter

```text
Kerjakan BAGIAN BACKEND untuk tahap dan modul pada PARAMETER di atas. Baca AGENTS.md (Bagian 0, 4, 8) dan PENDING_KONFIRMASI.md. Hanya backend. Perilaku bisnis tidak boleh berubah, termasuk yang PENDING.

TUGAS
1. Inventaris dulu: tulis tabel "fungsi lama -> service -> endpoint" di docs/api-<modul>.md (class method dan fungsi *_view di controller lama beserta template yang terkait). Tampilkan ringkasannya, lalu lanjutkan.
2. Ekstrak logika bisnis ke koperasi/services/<modul>_service.py. Controller lama dan view DRF memanggil service yang SAMA; jangan menyalin logika. Test lama harus tetap lulus.
3. Buat serializer (input dan output terpisah), view tipis, permission class, dan URL di koperasi/api/v1/. Uang string (DecimalField). Validasi memanggil service/model; pesan galat Bahasa Indonesia dalam format galat seragam.
4. Operasi tulis: transaction.atomic + select_for_update sesuai AGENTS.md 4.F; status dicek di dalam kunci; tolak aksi ganda.
5. OpenAPI: tag modul, operation_id stabil, contoh respons. Regenerasi docs/openapi.yaml.
6. Test API untuk SETIAP endpoint: sukses (200/201), 401, 403 (peran lain), 400 (validasi), dan aturan bisnis kunci dari PARAMETER (SKENARIO UJI jadi test bila mungkin).
7. Endpoint file (bila ada): FileResponse dengan Content-Disposition.

SELESAI bila: python manage.py check, makemigrations --check, test koperasi lulus; Swagger menampilkan semua endpoint modul; tidak ada float() untuk uang; docs/openapi.yaml terbaru.

ATURAN: satu commit per kelompok (refactor(service) / feat(api) / test(api)), jangan menambah fitur di luar PARAMETER, perbarui log_pengerjaan.md. Laporkan ringkasan endpoint yang dibuat.
```

---

## Template PM-FE (frontend modul) — tempel DI BAWAH Blok Parameter

```text
Kerjakan BAGIAN FRONTEND untuk tahap dan modul pada PARAMETER di atas. Baca AGENTS.md (Bagian 4.E, 6, 7) dan docs/design-system.md. Prasyarat: bagian backend modul ini sudah selesai dan docs/openapi.yaml terbaru. Gunakan skill modern-web-guidance untuk kebutuhan UI yang ada panduannya.

TUGAS
1. Jalankan npm run gen:api; commit schema.d.ts bila berubah.
2. Baca wireframe pada PARAMETER (acuan struktur dan isi; warna dan komponen mengikuti design system).
3. Buat src/features/<modul>/: hooks TanStack Query (query keys terpusat, invalidasi setelah mutasi), skema Zod (pesan Bahasa Indonesia, selaras OpenAPI), pages, components. Daftarkan rute dan menu per peran (guard peran).
4. Setiap halaman: keadaan memuat (Skeleton), kosong (EmptyState), galat (ErrorState + coba lagi), berhasil. Galat validasi server dipetakan ke field.
5. Tombol aksi tulis: disabled + Spinner saat pending. Aksi tak terbalik memakai ConfirmDialog.
6. Uang: tampil lewat formatRupiah(string). Input uang: komponen CurrencyInput yang mengirim string desimal (mis. "1500000.00"). Tidak ada aritmetika uang di browser.
7. Unduhan memakai downloadFile (blob + Authorization). Unggah berkas memakai ProgressBar bila progres diketahui.
8. Aksesibilitas dan responsif: 375, 768, 1280 px; keyboard saja; fokus terlihat; galat formulir diumumkan.
9. Test (Vitest + Testing Library): minimal satu formulir utama (validasi dan submit), satu halaman daftar (memuat -> data -> kosong), dan guard peran.
10. Jalankan npm run lint, typecheck, test, build. Jalankan audit web-design-guidelines bila skill terpasang dan perbaiki temuan relevan.

SELESAI bila: semua perintah di atas lulus; SKENARIO UJI pada PARAMETER berhasil diuji terhadap backend nyata untuk setiap peran (laporkan hasil tiap skenario, jujur bila ada yang tidak dapat diuji).

DILARANG: parseFloat/Number untuk uang, localStorage untuk token, pustaka baru tanpa persetujuan, emoji sebagai ikon, warna/ukuran diketik langsung di komponen.
Satu commit per kelompok (feat(web) / test(web) / refactor(ui)). Perbarui log_pengerjaan.md.
```

---

## Prompt 14B — Finalisasi

```text
Kerjakan Tahap 14B. Baca AGENTS.md. Prasyarat: Tahap 9-14A selesai.

1. PARITAS: buat tabel docs/paritas-halaman.md untuk 22 halaman wireframe: halaman, rute React, endpoint, status. Tampilkan kepada saya. JANGAN menghapus apa pun sebelum saya menyetujui tabel ini.
2. Build produksi: npm run build menghasilkan web/dist. Sajikan lewat Django (mis. WhiteNoise atau view catch-all untuk non-/api yang mengembalikan index.html). Satu origin, tanpa CORS. Dokumentasikan cara menjalankan dalam satu perintah.
3. Setelah saya menyetujui paritas: hapus controller view lama (fungsi *_view), urls lama, template dan folder frontend/ (template), serta test yang hanya menguji view lama (pindahkan yang masih relevan menjadi test service/API). Pertahankan services, models, dan test API. Titik kembali: tag mvt-final.
4. Postman: hasilkan koleksi dari docs/openapi.yaml ke docs/postman/ (koleksi + environment, skrip pra-permintaan untuk login). Charter mewajibkan dokumentasi pengujian API.
5. docs/UAT.md: skenario per use case UC-01 s.d. UC-14 per peran, kolom hasil, catatan, dan tempat tanda tangan mitra.
6. Keamanan: python manage.py check --deploy, pastikan cookie Secure dan DEBUG False untuk mode produksi, tanpa CORS, npm audit (laporkan temuan), pastikan tidak ada rahasia di repository.
7. README akhir: prasyarat, instalasi, konfigurasi .env, menjalankan, test, build, struktur folder, akun demo (dummy), daftar PENDING yang belum terjawab.
8. Perbarui AGENTS.md Bagian 5 (status tahap) dan log_pengerjaan.md. Jangan mengubah aturan bisnis.
```
