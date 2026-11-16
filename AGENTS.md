# AGENTS.md — Aturan Kerja & Standar Pengembangan Proyek SI-KKPRIS

Dokumen ini berisi instruksi dan aturan wajib yang harus selalu dipatuhi oleh AI Agent pada setiap sesi pengerjaan proyek **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** — Koperasi KKPRIS SMK Negeri 1 Kota Solok.

---

## 1. Standar Pesan Commit GitHub (Conventional Commits)

Bertindaklah sebagai **Senior Software Engineer** yang ahli dalam standar **Conventional Commits**. Tugasmu adalah membuatkan pesan commit GitHub yang rapi, singkat, dan deskriptif dalam Bahasa Indonesia berdasarkan perubahan kode atau deskripsi yang diberikan.

### A. Format Dasar
```text
<type>(<scope>): <subject>

<body>

<footer>
```

### B. Pilihan `<type>` yang Diizinkan (Tetap Gunakan Bahasa Inggris)
* `feat`: fitur baru untuk pengguna
* `fix`: perbaikan bug atau error
* `docs`: perubahan dokumentasi saja
* `style`: perapihan format kode (spasi, titik koma) tanpa mengubah logika
* `refactor`: perubahan struktur kode tanpa menambah fitur atau memperbaiki bug
* `perf`: peningkatan performa aplikasi
* `test`: penambahan atau perbaikan unit test
* `chore`: tugas pemeliharaan rutin, konfigurasi, atau update library

### C. Aturan Penulisan `<subject>` (Dalam Bahasa Indonesia)
* Gunakan **kata kerja aktif berbentuk perintah** (contoh: `"tambah"`, `"perbaiki"`, `"hapus"`, `"ubah"`, **bukan** `"menambahkan"` atau `"ditambahkan"`).
* Awali dengan **huruf kecil** setelah titik dua (`:`).
* **Maksimal 50 karakter** dan **jangan** diakhiri dengan tanda titik (`.`).
* Cantumkan `<scope>` secara opsional jika perubahan spesifik pada modul tertentu (contoh: `feat(login): tambah validasi email`).
  * Referensi scope modul SI-KKPRIS: `init`, `db`, `auth`, `member`, `simpanan`, `pembiayaan`, `agunan`, `approval`, `angsuran`, `rekap`, `laporan`, `ui`, `config`.

### D. Aturan `<body>` dan `<footer>`
* Isi `<body>` **hanya jika perubahan cukup kompleks**, jelaskan *"apa"* yang diubah dan *"mengapa"* perubahan itu dilakukan (maksimal 2–3 poin singkat menggunakan bullet `-`).
* Isi `<footer>` jika ada *breaking change* (tambahkan tanda seru `!` sebelum titik dua di header, misal `feat!:`) atau jika menutup nomor issue (contoh: `Closes #12`).

---

## 2. Aturan Pencatatan Log Harian (`log_pengerjaan.md`)

1. **Wajib Mencatat Setiap Pengerjaan Berdasarkan Tanggal:**
   * Setiap kali ada pengerjaan, pembuatan fitur, atau perubahan kode pada proyek, agen **wajib** mencatat atau memperbarui ringkasan perubahan di dalam berkas [`log_pengerjaan.md`](./log_pengerjaan.md).
   * Catatan wajib dikelompokkan berdasarkan **tanggal pengerjaan hari tersebut** (contoh: `## 📅 14 November 2026`).
2. **Struktur Catatan per Tanggal:**
   * **Tanggal Pengerjaan:** Tanggal dilakukan pekerjaan tersebut.
   * **Fokus / Modul yang Dikerjakan:** Ringkasan modul atau tahapan yang diselesaikan pada hari tersebut.
   * **Rincian Perubahan:** Daftar poin perubahan berkas/fitur yang ditambah, diubah, atau diperbaiki.
   * **Pesan Commit Terkait:** Pesan commit (berstandar Conventional Commits) yang digunakan.
   * **Status & Rencana Selanjutnya:** Catatan progres dan target pengerjaan berikutnya.

---

## 3. Prosedur Mengakhiri Pekerjaan Harian (Push ke GitHub)

* **Repository Remote:** `https://github.com/ZikraRevanzha/SI-KKPRIS.git` (Opsi B: Khusus Kode Implementasi pada `05_Implementasi/`, DDL SQL, `AGENTS.md`, dan `log_pengerjaan.md`).
* **Saat Pengguna Mengakhiri Sesi Harian:**
  Ketika pengguna menyatakan ingin mengakhiri pekerjaan pada hari tersebut (misal: *"selesai untuk hari ini"*, *"akhiri pekerjaan"*, atau *"push ke GitHub"*), agen **wajib** menjalankan langkah berikut secara berurutan:
  1. Memastikan seluruh ringkasan perubahan hari tersebut sudah tercatat lengkap beserta tanggalnya di [`log_pengerjaan.md`](./log_pengerjaan.md).
  2. Memeriksa status perubahan dengan `git status`.
  3. Melakukan staging (`git add`) dan membuat commit (`git commit`) menggunakan format **Conventional Commits** sesuai Bagian 1.
  4. Melakukan push (`git push origin main`) ke repository GitHub.
  5. Melaporkan hasil commit dan status push kepada pengguna.

---

## 4. Pedoman Direktori & Teknis Implementasi SI-KKPRIS

* **Direktori Implementasi:** Seluruh kode program implementasi aplikasi ditempatkan di dalam folder [`05_Implementasi/`](./05_Implementasi) (sejajar dengan folder `UTS/`) dengan pemisahan struktur yang rapi:
  * [`05_Implementasi/backend/`](./05_Implementasi/backend) — seluruh kode *backend* Django (`si_kkpris/`, `koperasi/`, `media/`, `manage.py`, `requirements.txt`, `.env.example`).
  * [`05_Implementasi/frontend/`](./05_Implementasi/frontend) — seluruh kode *frontend* antarmuka (`templates/` HTML dan `static/` CSS/JS/Img).
  * [`05_Implementasi/database/`](./05_Implementasi/database) — skema DDL MySQL (`02_DDL_MySQL_SI-KKPRIS.sql`).
* **Stack Teknologi (Sesuai SRS v4.0):**
  * **Backend:** Python 3.11+ & Django Framework (arsitektur MVT/MVC).
  * **Database:** MySQL 8.0+ (`InnoDB`, `utf8mb4_unicode_ci`) melalui Laragon MySQL 8.4.
  * **Presisi Finansial:** Wajib menggunakan `DecimalField(max_digits=15, decimal_places=2)` / `DECIMAL(15,2)`. Dilarang keras menggunakan `FLOAT` atau `DOUBLE` untuk nilai uang.
  * **Kepatuhan Aturan Bisnis Utama:**
    * 3 Peran Pengguna (`ANGGOTA`, `BENDAHARA`, `KETUA`).
    * 5 Skema Simpanan: Pokok (Rp350.000), Khusus (Rp500.000), Wajib (Rp150.000/bln) bersifat terkunci (`dapat_ditarik = 0`); Hari Raya & Berencana bersifat sukarela (`dapat_ditarik = 1`).
    * Pengajuan Pembiayaan Syariah (*Murabahah, Ijarah, Hawalah*) hanya dibuka tanggal 1–20, tenor maks. 72 bulan, margin flat, dan wajib unggah agunan jika plafon > Rp70.000.000.
    * Otorisasi pengeluaran kas wajib disetujui Ketua (*Two-Man Rule*) sebelum Bendahara mencatat realisasi pencairan *off-system*.
    * Rekap potong gaji di-generate setiap tanggal 24 dan dapat diekspor ke Excel (`.xlsx`) & PDF.

---

## 5. Peta Jalan (Roadmap) 7 Tahap Konstruksi & Pemetaan UI Wireframe

Pengerjaan fitur dilakukan secara **Full-Stack Vertikal per Tahap (Backend Controller + Halaman UI Template sekaligus)**. Pengguna cukup menyebutkan nomor tahap (contoh: *"Kerjakan Tahap 2"* atau *"Lanjut Tahap 3"*), dan agen wajib mengacu pada spesifikasi tahapan serta referensi gambar Wireframe di `04_Wireframe & Desain UI/01_Wireframe_Final_PNG/` berikut:

| Tahap | Fokus Modul & Controller | Cakupan Fitur Backend & Aturan Bisnis | Halaman UI yang Dibangun (Sesuai 22 Wireframe Final) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Tahap 1** | **Fondasi Proyek, Database & 16 Model (3NF)** | Setup `venv`, `requirements.txt`, koneksi MySQL 8.4 `si_kkpris`, implementasi 16 Model `Decimal(15,2)`, command `seed_master`, & unit test model. | *(Fondasi Backend & Database)* | ✅ **Selesai** |
| **Tahap 2** | **Autentikasi, RBAC & Base Dashboard UI** (`AuthController` — `UC-01`) | Login/Logout, ganti password, *session timeout* 30 menit, dekorator RBAC (`ANGGOTA`, `BENDAHARA`, `KETUA`), & pencatatan otomatis `AuditTrailLog`. | **Bentuk Awal UI Utama (Sidebar, Topbar, Tema):**<br/>1. `Login.png`<br/>2. `Dashboard.png` (Dashboard Bendahara & Ketua)<br/>3. `Beranda Anggota.png` (Portal Mandiri Anggota) | ✅ **Selesai** |
| **Tahap 3** | **Manajemen Keanggotaan & Kliring Resign** (`AnggotaController` — `UC-02` s.d. `UC-04`) | Pendaftaran & CRUD anggota oleh Bendahara, *auto-generate* Nomor Anggota, pengajuan *resign* mandiri oleh Anggota, & verifikasi kliring ($\sum \text{Simpanan} - \sum \text{Kewajiban}$). | 4. `Data Anggota.png`<br/>5. `Form Anggota Baru.png`<br/>6. `Ajukan Pengunduran Diri.png`<br/>7. `Verifikasi Pengunduran Diri.png` | ✅ **Selesai** |
| **Tahap 4** | **Transaksi Multi-Simpanan Anggota** (`SimpananController` — `UC-05`, `UC-06`) | Portal rincian saldo 5 skema simpanan (Pokok, Khusus, Wajib, Hari Raya, Berencana), mutasi setor/tarik oleh Bendahara, & proteksi simpanan terkunci (`dapat_ditarik = 0`). | 8. `Kelola Simpanan.png`<br/>9. `Transaksi Baru.png` | ✅ **Selesai** |
| **Tahap 5** | **Pembiayaan Syariah, Agunan, Approval Kas & Realisasi** (`PembiayaanController` — `UC-07` s.d. `UC-10`) | Simulasi & pengajuan *Murabahah/Ijarah/Hawalah* (tgl 1–20, margin flat, tenor $\le 72$ bln), wajib unggah agunan jika $> \text{Rp}70\text{ Juta}$, nomor antrean, **Setujui Pengeluaran Kas** oleh Ketua (*Two-Man Rule*), **Catat Realisasi Pencairan** *off-system*, & *auto-generate* Kartu Angsuran. | 10. `Ajukan Pembiayaan — Pilih Akad.png`<br/>11. `Ajukan Pembiayaan — Nominal & Tenor.png`<br/>12. `Ajukan Pembiayaan — Agunan.png`<br/>13. `Daftar Pembiayaan.png`<br/>14. `Detail Pembiayaan.png`<br/>15. `Persetujuan Kas.png`<br/>16. `Konfirmasi Persetujuan.png` | ⏳ **Berikutnya** |
| **Tahap 6** | **Rekap Potong Gaji (Tgl 24), Angsuran & Notifikasi** (`RekapNotifikasiController` — `UC-11`, `UC-12`, `UC-14`) | *One-Click Generator* rekap potong gaji tanggal 24, ekspor Excel (`.xlsx`) & PDF untuk Bendahara Gaji Sekolah, pelunasan *batch* kolektif maupun cicilan mandiri, & pengingat WA/Email tgl 10. | 17. `Kelola Angsuran.png`<br/>18. `Rekap Potong Gaji.png`<br/>19. `Notifikasi Tagihan.png` | 📋 Terjadwal |
| **Tahap 7** | **Kuitansi Digital, Laporan Keuangan (RAT) & Final QA** (`LaporanBuktiController` — `UC-13`) | Cetak kuitansi PDF (simpanan & angsuran), Laporan Triwulanan (Arus Kas & Realisasi), Laporan Tahunan RAT (SHU & Neraca) ke PDF/Excel, halaman *Audit Trail Log* Ketua, & pengujian akhir. | 20. `Cetak Bukti Transaksi.png`<br/>21. `Cetak Bukti Pembayaran.png`<br/>22. `Laporan Keuangan.png` | 📋 Terjadwal |
