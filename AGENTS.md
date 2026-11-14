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

* **Direktori Implementasi:** Seluruh kode program implementasi aplikasi ditempatkan di dalam folder [`05_Implementasi/`](./05_Implementasi) (sejajar dengan folder `UTS/`).
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
