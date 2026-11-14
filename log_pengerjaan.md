# 📋 LOG PENGERJAAN HARIAN PROYEK SI-KKPRIS

**Nama Proyek:** Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)  
**Studi Kasus:** Koperasi KKPRIS SMK Negeri 1 Kota Solok  
**Pengembang:** Zikra Revanzha (NIM: 2411082025) — D4 TRPL Politeknik Negeri Padang  
**Repository GitHub:** [https://github.com/ZikraRevanzha/SI-KKPRIS](https://github.com/ZikraRevanzha/SI-KKPRIS)

---

## 📅 14 November 2026

### 🎯 Fokus / Tahapan Pengerjaan
* Persiapan awal tahap Implementasi, penyusunan aturan kerja agen (`AGENTS.md`), pembuatan log harian (`log_pengerjaan.md`), pembuatan direktori `05_Implementasi/`, serta konfigurasi repository GitHub (Opsi B).

### 🛠️ Rincian Perubahan
1. **Pembuatan Aturan Kerja Proyek (`AGENTS.md`):**
   * Menetapkan standar penulisan pesan commit GitHub menggunakan **Conventional Commits** dalam Bahasa Indonesia (`<type>(<scope>): <subject>`).
   * Menetapkan aturan wajib pencatatan ringkasan perubahan harian berdasarkan tanggal di `log_pengerjaan.md`.
   * Menetapkan prosedur *push* ke GitHub saat mengakhiri sesi pengerjaan harian.
2. **Pembuatan Berkas Catatan Harian (`log_pengerjaan.md`):**
   * Membuat dokumen pelacakan riwayat perubahan harian berdasarkan tanggal pengerjaan.
3. **Inisialisasi Direktori `05_Implementasi/` (Sejajar dengan Folder `UTS/`):**
   * Membuat struktur folder `05_Implementasi/` untuk menampung kode program aplikasi.
   * Menyalin skema basis data resmi `02_DDL_MySQL_SI-KKPRIS.sql` (16 tabel 3NF MySQL 8.0+ InnoDB) ke `05_Implementasi/database/02_DDL_MySQL_SI-KKPRIS.sql`.
   * Menambahkan dokumentasi pengantar pada `05_Implementasi/README.md`.
4. **Konfigurasi Git & GitHub (Opsi B):**
   * Membuat berkas `.gitignore` untuk memfokuskan repository GitHub khusus pada kode implementasi (`05_Implementasi/`), skema DDL SQL, aturan agen (`AGENTS.md`), dan catatan harian (`log_pengerjaan.md`).
   * Menghubungkan repository lokal ke remote `https://github.com/ZikraRevanzha/SI-KKPRIS.git`.

### 💬 Pesan Commit Terkait
```text
chore(init): tambah struktur awal dan aturan kerja

- Tambah AGENTS.md dan log_pengerjaan.md untuk standarisasi alur kerja harian
- Buat direktori 05_Implementasi beserta skema DDL 16 tabel MySQL 8.0+
- Atur .gitignore khusus kode implementasi dan DDL sesuai opsi B
```

### 📌 Status & Rencana Selanjutnya
* **Status Hari Ini:** Inisialisasi struktur implementasi, aturan kerja, dan koneksi GitHub selesai.
* **Rencana Berikutnya:** Setup *Virtual Environment (`venv`)* Python, instalasi Django & pustaka pendukung (`requirements.txt`), konfigurasi koneksi database MySQL 8.4 Laragon, dan pembuatan struktur proyek Django beserta 16 Model sesuai ERD/DDL.
