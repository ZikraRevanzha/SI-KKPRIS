# 📋 LOG PENGERJAAN HARIAN PROYEK SI-KKPRIS

**Nama Proyek:** Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)  
**Studi Kasus:** Koperasi KKPRIS SMK Negeri 1 Kota Solok  
**Pengembang:** Zikra Revanzha (NIM: 2411082025) — D4 TRPL Politeknik Negeri Padang  
**Repository GitHub:** [https://github.com/ZikraRevanzha/SI-KKPRIS](https://github.com/ZikraRevanzha/SI-KKPRIS)

---

## 📅 16 November 2026

### 🎯 Fokus / Tahapan Pengerjaan
* **Restrukturisasi Folder Implementasi (`05_Implementasi/`):** Memisahkan komponen **Backend** (`backend/`) dan **Frontend** (`frontend/`) agar struktur proyek lebih rapi, modular, dan terstandar tanpa mengganggu *virtual environment* (`venv`) maupun fungsionalitas Django.

### 🛠️ Rincian Perubahan
1. **Pemisahan Direktori `backend/` dan `frontend/` di `05_Implementasi/`:**
   * Memindahkan komponen backend (`koperasi/`, `si_kkpris/`, `media/`, `manage.py`, `requirements.txt`, `.env`, `.env.example`) ke dalam `05_Implementasi/backend/`.
   * Memindahkan komponen frontend (`templates/` dan `static/`) ke dalam `05_Implementasi/frontend/` serta melengkapi subfolder `frontend/static/js/.gitkeep` dan `frontend/static/img/.gitkeep`.
   * Mempertahankan `database/`, `venv/`, dan `README.md` di level root `05_Implementasi/`.
2. **Penyesuaian Konfigurasi Path Django:**
   * Menambahkan penyesuaian `sys.path` pada `backend/manage.py`, `backend/si_kkpris/wsgi.py`, dan `backend/si_kkpris/asgi.py` agar perintah Django dapat berjalan konsisten dari `backend/` maupun dari root `05_Implementasi/`.
   * Memperbarui `backend/si_kkpris/settings.py` dengan definisi `BACKEND_DIR`, `PROJECT_ROOT`, dan `FRONTEND_DIR` sehingga `TEMPLATES`, `STATICFILES_DIRS`, `STATIC_ROOT`, `MEDIA_ROOT`, dan pemuatan `.env` terarah ke struktur baru.
3. **Pengujian & Pembaruan Dokumentasi:**
   * Menambahkan `test_05_integrasi_frontend_templates_dan_static` pada `backend/koperasi/tests.py` untuk memverifikasi resolusi `frontend/templates/`, `frontend/static/css/style.css`, dan render HTTP `/login/`.
   * Memperbarui diagram pohon direktori serta panduan perintah pada `05_Implementasi/README.md`, `README.md`, dan `AGENTS.md`.

### 💬 Pesan Commit Terkait
```text
refactor(config): pisahkan folder backend dan frontend
```

### 📌 Status & Rencana Selanjutnya
* **Status Hari Ini:** Restrukturisasi direktori `05_Implementasi/backend/` dan `05_Implementasi/frontend/` selesai dan seluruh pengecekan serta unit test terverifikasi lulus.
* **Rencana Berikutnya (Tahap 3):** Implementasi **Manajemen Keanggotaan & Kliring Resign (`AnggotaController` — `UC-02` s.d. `UC-04`)** beserta 4 halaman UI (`Data Anggota.png`, `Form Anggota Baru.png`, `Ajukan Pengunduran Diri.png`, dan `Verifikasi Pengunduran Diri.png`).

---

## 📅 15 November 2026

### 🎯 Fokus / Tahapan Pengerjaan
* **Tahap 1:** Penyiapan *Virtual Environment* (`venv`) Python & `requirements.txt`, pembuatan basis data `si_kkpris` pada MySQL 8.4 Laragon, serta inisialisasi proyek Django `si_kkpris` dan aplikasi `koperasi` beserta ke-16 Model tabel (3NF), seeder master data, dan unit test.
* **Tahap 2:** Implementasi Modul Autentikasi, RBAC, Session Timeout, & Pencatatan `AuditTrailLog` (`AuthController` — `UC-01`) beserta **Bentuk Awal UI Utama** (`Login.png`, `Dashboard.png` Bendahara & Ketua, serta `Beranda Anggota.png`).

### 🛠️ Rincian Perubahan
1. **Penyiapan Virtual Environment & Pustaka (`05_Implementasi/venv/` & `requirements.txt`):**
   * Membuat *virtual environment* Python 3.13.7 di `05_Implementasi/venv/`.
   * Menginstal dan mengunci versi pustaka utama di `05_Implementasi/requirements.txt`: `Django==5.2.19`, `mysqlclient==2.3.1`, `PyMySQL==1.2.4`, `openpyxl==3.1.5`, `reportlab==5.1.0`, `xhtml2pdf==0.2.28`, `python-dotenv==1.2.4`, dan `Pillow==13.0.0`.
2. **Pembuatan Database `si_kkpris` di MySQL 8.4 Laragon:**
   * Membuat database `si_kkpris` (`CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`) pada MySQL 8.4.3 Laragon.
   * Mengimpor ke-16 tabel DDL (`02_DDL_MySQL_SI-KKPRIS.sql`) dan menyinkronkan migrasi awal Django (`0001_initial.py`).
3. **Inisialisasi Proyek Django `si_kkpris` & 16 Model (`koperasi/models.py`):**
   * Mengonfigurasi `si_kkpris/settings.py` dengan koneksi MySQL 8.4 (`STRICT_TRANS_TABLES`), lokalisasi Bahasa Indonesia (`Asia/Jakarta`), enkripsi password PBKDF2, serta *session timeout* otomatis 30 menit (`FR-AUTH-03`).
   * Mengimplementasikan ke-16 Model beserta seluruh method domain sesuai `03_Class_Diagram_SI-KKPRIS.mmd` dan tipe presisi finansial `DecimalField(max_digits=15, decimal_places=2)`:
     1. `Pengguna` (`pengguna`)
     2. `Anggota` (`anggota`)
     3. `JenisSimpanan` (`jenis_simpanan`)
     4. `TransaksiSimpanan` (`transaksi_simpanan`)
     5. `JenisAkad` (`jenis_akad`)
     6. `Pembiayaan` (`pembiayaan`)
     7. `Agunan` (`agunan`)
     8. `PersetujuanPembiayaan` (`persetujuan_pembiayaan`)
     9. `RealisasiPencairan` (`realisasi_pencairan`)
     10. `JadwalAngsuran` (`jadwal_angsuran`)
     11. `RekapPotongGaji` (`rekap_potong_gaji`)
     12. `DetailRekapPotongGaji` (`detail_rekap_potong_gaji`)
     13. `PembayaranAngsuran` (`pembayaran_angsuran`)
     14. `NotifikasiTagihan` (`notifikasi_tagihan`)
     15. `PengunduranDiri` (`pengunduran_diri`)
     16. `AuditTrailLog` (`audit_trail_log`)
   * Mendaftarkan ke-16 model pada `koperasi/admin.py` dengan proteksi *append-only* pada `AuditTrailLog`.
4. **Pembuatan Seeder Master Data & Unit Test:**
   * Membuat command `python manage.py seed_master` (`koperasi/management/commands/seed_master.py`) untuk menginisialisasi 5 skema simpanan, 3 skema akad syariah (*Murabahah, Ijarah, Hawalah*), dan 3 akun peran utama (`ketua`, `bendahara`, `198205142009012004`) beserta opsi `--with-demo`.
   * Menambahkan dan menjalankan *unit test* terintegrasi di `koperasi/tests.py` (4 skenario pengujian melewati seluruh 16 tabel & RBAC — **OK**).
5. **Implementasi Tahap 2: `AuthController`, RBAC & Bentuk Awal UI Utama:**
   * Membangun `koperasi/controllers/auth_controller.py` (`AuthController.login`, `AuthController.logout`, `AuthController.gantiPassword`, dekorator `@login_wajib` & `@peran_wajib`, serta pencatatan otomatis `AuditTrailLog`).
   * Membuat filter pemformatan mata uang Rupiah berbasis `Decimal` di `koperasi/templatetags/kkpris_tags.py`.
   * Membangun *Design System* (`static/css/style.css`), *Base Layout* (`templates/base.html`), dan 3 layar utama sesuai Wireframe Final:
     * `templates/auth/login.html` (`Login.png`)
     * `templates/dashboard/dashboard_pengurus.html` (`Dashboard.png` — Bendahara & Ketua)
     * `templates/dashboard/beranda_anggota.html` (`Beranda Anggota.png` — Portal Mandiri Anggota)

### 💬 Pesan Commit Terkait
```text
feat(db): inisialisasi proyek django dan 16 model
docs(config): simpan peta jalan 7 tahap dan pemetaan ui
feat(auth): tambah modul autentikasi rbac dan dashboard ui
```

### 📌 Status & Rencana Selanjutnya
* **Status Hari Ini:** **Tahap 1** (Fondasi & 16 Model) dan **Tahap 2** (`AuthController`, RBAC 3 Peran, & Bentuk Awal UI Login + Dashboard Pengurus + Beranda Anggota) selesai 100%.
* **Rencana Berikutnya (Tahap 3):** Implementasi **Manajemen Keanggotaan & Kliring Resign (`AnggotaController` — `UC-02` s.d. `UC-04`)** beserta 4 halaman UI (`Data Anggota.png`, `Form Anggota Baru.png`, `Ajukan Pengunduran Diri.png`, dan `Verifikasi Pengunduran Diri.png`).

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
