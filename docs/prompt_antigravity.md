# Prompt untuk Antigravity — SI-KKPRIS

Urutan pakai: **Prompt A → Prompt B → (pasang skill) → Prompt C**.
Salin isi di dalam blok, tempel ke Antigravity. Pastikan `AGENTS.md` dan `PENDING_KONFIRMASI.md` sudah ada di root repository.

---

## Prompt A — Tahap 8A: Tandai Aturan PENDING (tanpa mengubah perilaku bisnis)

```text
Kerjakan Tahap 8A. Baca dulu AGENTS.md dan PENDING_KONFIRMASI.md.

TUJUAN
Tandai semua aturan bisnis yang belum dikonfirmasi mitra. Jangan mengubah rumus atau perilaku bisnis, kecuali memindahkan margin sementara ke konfigurasi seperti di langkah 2.

LANGKAH
1. Beri komentar `# PENDING PND-xx` pada lokasi berikut (cari nomor baris terkini dengan grep, jangan mengandalkan nomor lama):
   - PembiayaanController.DEFAULT_MARGIN_PERSEN di controllers/pembiayaan_controller.py -> PND-01
   - Pembiayaan.hitungSimulasiMarginFlat di models.py -> PND-01. Ganti kalimat docstring yang ambigu ("per bulan atau total") menjadi: "margin_persen = persen dari pokok PER BULAN (flat). Satuan belum dikonfirmasi mitra (PND-01)."
   - Perhitungan Hawalah di PembiayaanController.simulasiPembiayaan -> PND-02 (rumus sama dengan akad lain; JANGAN diubah)
   - JadwalAngsuran.generateJadwalAngsuran (awal jadwal = bulan berikutnya, tanggal 24) -> PND-07
   - PembayaranAngsuran.potongan_margin -> PND-08. Cek apakah aturan ini ada di SRS/dokumen proyek. Jika tidak ada, catat sebagai temuan di log_pengerjaan.md. JANGAN dihapus.
   - Validasi pengajuan pembiayaan: tambahkan komentar `# PENDING PND-04` bahwa limit per anggota dan batas pembiayaan aktif belum divalidasi. JANGAN menambah validasi baru.
   - Service/fungsi laporan keuangan (SHU, neraca) di controllers/laporan_bukti_controller.py -> PND-09
2. Margin sementara:
   - Pindahkan DEFAULT_MARGIN_PERSEN ke settings.MARGIN_PERSEN_SEMENTARA yang dibaca dari env (default Decimal('1.00')).
   - Tambahkan ke .env.example: MARGIN_PERSEN_SEMENTARA=1.00  # PENDING PND-01 — nilai contoh, BUKAN ketetapan koperasi
   - Controller dan seed_master membaca dari settings.
   - Tampilkan catatan "Margin sementara (belum dikonfirmasi koperasi)" pada langkah simulasi di pembiayaan/ajukan_pembiayaan.html dan pada pembiayaan/detail_pembiayaan.html.
   - Jangan mengubah data pembiayaan yang sudah tersimpan.
3. Seed data (management/commands/seed_master.py dan tests.py):
   - Pastikan nama, NIP, dan nomor identitas adalah data dummy. Ganti username/NIP yang berbentuk 18 digit dan terlihat nyata menjadi dummy (contoh: ketua01, bendahara01).
   - Password akun seed dibaca dari env SEED_PASSWORD (tambahkan ke .env.example), bukan ditulis langsung di kode. Jika saat ini hardcoded, laporkan ke saya.
4. Tambahkan test kecil yang memastikan simulasi memakai settings.MARGIN_PERSEN_SEMENTARA (gunakan override_settings).

ATURAN
- Satu commit per tujuan. Contoh: "docs(pembiayaan): tandai aturan yang pending", "refactor(config): pindah margin sementara ke env", "chore(db): ganti data seed dengan data dummy".
- Jalankan check, makemigrations --check, dan test sebelum commit.
- Perbarui log_pengerjaan.md. Jangan menyentuh .env.
```

---

## Prompt B — Tahap 8B: Perbaikan Teknis (tidak perlu mitra)

```text
Kerjakan Tahap 8B. Baca dulu AGENTS.md (terutama Bagian 4.C). Kerjakan item satu per satu, urut. Satu commit per item. Jalankan test setelah tiap item. Jika test gagal, berhenti dan laporkan. Jangan mengubah aturan bisnis yang berstatus PENDING.

ITEM 1 — Angsuran terakhir menyerap sisa pembulatan
Masalah: porsi_pokok = pokok/tenor dibulatkan lalu dikalikan tenor, sehingga jumlah semua angsuran tidak sama dengan total_kewajiban.
Perbaikan:
- Buat SATU fungsi sumber tunggal yang menghasilkan daftar (porsi_pokok, porsi_margin, jumlah_angsuran) per angsuran. Angsuran ke-N (terakhir): porsi_pokok = harga_pokok - porsi_pokok_reguler * (N-1).
- Pakai fungsi itu di JadwalAngsuran.generateJadwalAngsuran (tambahkan parameter harga_pokok; pembiayaan_controller memanggilnya di sekitar baris 583) dan di SEMUA tempat lain yang menghitung angsuran per bulan (pratinjau jadwal di detail_pembiayaan sekitar baris 1052–1068, perhitungan di sekitar baris 726). Gunakan grep untuk menemukan semuanya.
- Tambahkan test invarian: sum(jumlah_angsuran) == total_kewajiban dan sum(porsi_pokok) == harga_pokok, dengan kasus (margin 1,00% per bulan, nilai sementara PND-01):
  a) pokok 10.000.000, tenor 7 -> 6 angsuran @1.528.571,43 dan angsuran terakhir 1.528.571,42; total 10.700.000,00
  b) pokok 70.000.000, tenor 72 -> 71 angsuran @1.672.222,22 dan angsuran terakhir 1.672.222,38; total 120.400.000,00
  c) pokok 25.000.000, tenor 11 -> invarian terpenuhi
  d) margin 0%, pokok 5.000.000, tenor 10 -> 10 x 500.000,00
Commit: fix(pembiayaan): serap sisa pembulatan di angsuran akhir

ITEM 2 — Parser nominal
Masalah: _bersihkan_decimal menganggap "70.000" = 70,00 dan "500.000" = 500,00 (hanya benar jika ada >= 2 titik).
Perbaikan: buat dua fungsi terpisah di satu modul utilitas (mis. koperasi/utils.py):
- bersihkan_rupiah(raw): hilangkan "Rp" dan spasi. Jika cocok regex ^\d{1,3}(\.\d{3})+$ -> hapus titik. Jika mengandung koma -> hapus titik, ganti koma dengan titik. Selain itu langsung Decimal. Hasil quantize 0.01 ROUND_HALF_UP. Format tidak valid -> ValidationError.
- bersihkan_persen(raw): koma atau titik sebagai desimal; TIDAK memperlakukan titik sebagai pemisah ribuan.
Gunakan di SEMUA controller (cek juga simpanan_controller, anggota_controller, rekap_notifikasi_controller). Hapus fungsi lama setelah semua pemanggil dipindah.
Test tabel: "70.000"->70000.00, "500.000"->500000.00, "1.500.000"->1500000.00, "2.500,50"->2500.50, "Rp 150.000"->150000.00, "1500000"->1500000.00, "150000.50"->150000.50, "1,500,000"->ValidationError, persen "1.5"->1.50, persen "1,5"->1.50.
Commit: fix(pembiayaan): perbaiki parser nominal rupiah

ITEM 3 — Hapus float() pada nilai uang
Jalankan: grep -rn "float(" backend. Ganti pada ekspor Excel (rekap potong gaji, simpanan, pembiayaan, laporan) dengan menulis Decimal langsung ke sel openpyxl dan mengatur cell.number_format = '#,##0.00'. Tambahkan test yang membuka file xlsx hasil ekspor dan memastikan nilai sel numerik dan sama dengan data. Hasil grep akhir tidak boleh menyisakan float() untuk uang.
Commit: fix(export): hapus float pada ekspor Excel

ITEM 4 — Kunci baris untuk saldo dan pembayaran
Masalah: saldo_sesudah dihitung berantai tanpa select_for_update, dan pembayaran angsuran bisa ganda jika dua permintaan bersamaan.
Perbaikan, di dalam transaction.atomic():
- Transaksi simpanan: Anggota.objects.select_for_update().get(pk=...) sebelum membaca saldo terakhir.
- Pembayaran angsuran: JadwalAngsuran.objects.select_for_update().get(pk=...), lalu periksa status_bayar di dalam kunci; jika sudah LUNAS, tolak dengan pesan jelas.
- Realisasi pencairan dan persetujuan kas: kunci baris Pembiayaan, periksa status di dalam kunci.
Tambahkan test untuk "bayar dua kali ditolak" (SQLite mengabaikan kunci, cukup uji logika status).
Commit: fix(simpanan): kunci baris saat hitung saldo

ITEM 5 — Template PDF terpisah dari template layar
Masalah: kuitansi PDF dibuat dari simpanan/kuitansi_simpanan_print.html dan angsuran/kuitansi_angsuran_print.html sehingga tombol "Cetak" dan "Unduh PDF" ikut tercetak (ikon emoji menjadi kotak kosong).
Perbaikan: ekstrak isi kuitansi ke partial (mis. simpanan/_kuitansi_isi.html dan angsuran/_kuitansi_isi.html). Template layar = partial + toolbar. Template PDF baru (*_pdf.html, ikuti pola rekap_potong_gaji_pdf.html) = partial saja, tanpa tombol dan tanpa emoji. Controller PDF memakai template PDF.
Test: hasilkan PDF, ekstrak teks dengan pypdf, pastikan nomor kuitansi ada dan kata "Cetak" serta "Unduh" tidak ada.
Commit: fix(pdf): pisahkan template kuitansi PDF

ITEM 6 — URL pada JavaScript
Di frontend/templates/anggota/data_anggota.html (sekitar baris 508) form edit memakai string '/anggota/' + id + '/edit/'. Ganti dengan atribut data-url dari {% url 'edit_anggota' 0 %} lalu ganti segmen 0 lewat JavaScript. Periksa pola serupa untuk catat_pembayaran_angsuran, proses_persetujuan_kas, dan update_potongan_toko_rekap.
Commit: refactor(ui): pakai data-url untuk form edit

ITEM 7 — Konfigurasi dan keamanan
- requirements.txt: hapus PyMySQL setelah memastikan tidak ada import pymysql (grep). Pertahankan mysqlclient.
- settings.AUTH_PASSWORD_HASHERS: hanya PBKDF2PasswordHasher.
- settings: DEBUG default False. SECRET_KEY wajib dari env; jika tidak ada dan DEBUG False, raise ImproperlyConfigured. Hapus SECRET_KEY bawaan dari kode. .env.example tetap DEBUG=True untuk lokal.
- Saat DEBUG False aktifkan SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_SSL_REDIRECT lewat env (jangan memaksa di lokal).
- _ambil_ip_klien di auth_controller: gunakan REMOTE_ADDR; baca X-Forwarded-For hanya jika settings.TRUSTED_PROXY bernilai True (env, default False).
- Pastikan .gitignore sesuai AGENTS.md Bagian 3.
Commit terpisah: chore(config): hapus PyMySQL dari requirements; fix(auth): gunakan hasher PBKDF2 saja; chore(config): wajibkan SECRET_KEY dari env; fix(security): percayai IP dari REMOTE_ADDR

ITEM 8 — Pengujian di MySQL
Jalankan python manage.py test koperasi pada MySQL (Laragon). Laporkan hasilnya. Jika gagal karena izin membuat database test_si_kkpris, beri tahu saya langkah GRANT yang diperlukan.

DILARANG di Tahap 8B
- Mengubah Pengguna menjadi AbstractUser atau menyentuh sistem autentikasi (menunggu PND-11).
- Mengubah rumus margin, perlakuan Hawalah, limit anggota, atau aturan PENDING lain.

AKHIR: perbarui log_pengerjaan.md (rincian, commit, temuan). Laporkan ringkasan hasil dan test.
```

---

## Memasang skill `modern-web-guidance` (kamu yang melakukan, bukan agent)

Pilih salah satu:

1. **Antigravity IDE:** buka `Customizations` → `Build With Google Plugins` → `Modern Web Guidance`.
2. **Antigravity CLI:** `agy plugin install https://github.com/GoogleChrome/modern-web-guidance`
3. **Lewat npx (butuh Node.js):** `npx modern-web-guidance@latest install`

Cek berhasil:

```bash
npx modern-web-guidance@latest search "dialog modal"
```

Hasilnya berupa JSON berisi ID panduan. Perbarui dengan `npx modern-web-guidance@latest update` bila dipasang lewat npx.

---

## Prompt C — Tahap 9: Penyempurnaan UI Template (MVT)

Jalankan **setelah Prompt A dan B selesai** dan skill terpasang.

```text
Kerjakan Tahap 9. Baca dulu AGENTS.md (terutama Bagian 6). Tujuan: UI template Django terlihat dan berperilaku sebagai antarmuka kerja yang rapi dan modern, bukan template generik. Jangan mengubah logika backend, URL, nama field, atau aturan bisnis.

PERSIAPAN
1. Pastikan skill modern-web-guidance tersedia: jalankan `npx modern-web-guidance@latest search "navigation drawer"`. Jika gagal, berhenti dan minta saya memasangnya.
2. Audit frontend/static/css/style.css dan frontend/templates/base.html. Tulis temuan singkat di log_pengerjaan.md: nilai warna/ukuran yang diketik langsung, emoji sebagai ikon, JavaScript yang bisa diganti elemen native, masalah responsif dan aksesibilitas.

PANDUAN YANG DICARI DAN DIPAKAI (cari lewat search, ambil lewat retrieve, ikuti isinya)
- Tata letak dan sidebar: navigation-drawer, navbar, css-layout, responsive-design
- Ikon: icons (ganti emoji di sidebar dengan SVG inline)
- Tabel: responsive-table, sortable-table
- Modal dan popover: dialog, declarative-dialog-popover-control, light-dismiss-a-dialog
- Formulir: required-field-feedback, validate-input-after-interaction, accessible-error-announcement, brand-consistent-forms
- Pesan Django messages: persistent-toast-notifications
- Kartu dan statistik dashboard: card, progress
- Token dan tema: css (arsitektur CSS), browser-ui-theming, serta panduan warna bila ditemukan lewat search
- Gerak: motion (hormati prefers-reduced-motion)
- Ukuran teks OS: respect-os-text-scale

URUTAN KERJA (satu commit per kelompok, scope `ui`)
1. Design tokens di :root (warna, spasi, radius, bayangan, tipografi) dan refaktor style.css agar semua komponen memakai token. Satu warna aksen ditambah warna status.
2. base.html: sidebar/topbar responsif (drawer di layar kecil), ikon SVG, indikator halaman aktif, tautan lompat ke konten.
3. Komponen bersama: tombol, formulir, tabel responsif, toast, dialog.
4. Halaman per kelompok, mengikuti wireframe: auth + dashboard -> anggota -> simpanan -> pembiayaan -> angsuran/rekap/notifikasi -> laporan.
5. Cetak: pastikan stylesheet cetak kuitansi dan laporan rapi (template PDF tidak dikerjakan di sini).

KRITERIA TIAP KELOMPOK HALAMAN
- Tanpa pustaka CSS/JS baru. Tanpa gradien ungu/biru, kaca buram, atau bayangan berlapis. Tanpa emoji sebagai ikon.
- Angka rupiah rata kanan dengan font-variant-numeric: tabular-nums.
- Seluruh fungsi dapat dioperasikan hanya dengan keyboard; fokus terlihat; galat formulir spesifik dalam Bahasa Indonesia dan diumumkan ke pembaca layar.
- Diperiksa di lebar 375, 768, dan 1280 px. Sertakan catatan hasil pemeriksaan di log.
- Test lulus (python manage.py test koperasi) sebelum tiap commit.

Perbarui log_pengerjaan.md. Jika sebuah kebutuhan UI tidak punya panduan di skill, katakan terus terang; jangan mengarang isi panduan.
```
