# ðŸ“‹ LOG PENGERJAAN HARIAN PROYEK SI-KKPRIS

**Nama Proyek:** Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)  
**Studi Kasus:** Koperasi KKPRIS SMK Negeri 1 Kota Solok  
**Pengembang:** Zikra Revanzha (NIM: 2411082025) â€” D4 TRPL Politeknik Negeri Padang  
**Repository GitHub:** [https://github.com/ZikraRevanzha/SI-KKPRIS](https://github.com/ZikraRevanzha/SI-KKPRIS)

---

## ðŸ“… 17 November 2026

### ðŸŽ¯ Fokus / Tahapan Pengerjaan
* **Tahap 5:** Implementasi Modul **Pembiayaan Syariah, Agunan, Approval Kas & Realisasi (`PembiayaanController` â€” `UC-03`, `UC-04`, `UC-06`, `UC-07` | `FR-FIN-01` s.d. `FR-FIN-06`, `BR-01` s.d. `BR-05`)** beserta ke-7 rancangan halaman UI Wireframe Final (`Ajukan Pembiayaan â€” Pilih Akad.png`, `Ajukan Pembiayaan â€” Nominal & Tenor.png`, `Ajukan Pembiayaan â€” Agunan.png`, `Daftar Pembiayaan.png`, `Detail Pembiayaan.png`, `Persetujuan Kas.png`, dan `Konfirmasi Persetujuan.png`).
* **Tahap 6:** Implementasi Modul **Rekap Potong Gaji (Tgl 24), Kelola Angsuran & Notifikasi Tagihan (`RekapNotifikasiController` â€” `UC-11`, `UC-12`, `UC-13`, `UC-14` | `FR-ANG-01` s.d. `FR-ANG-03`, `FR-RKP-01` s.d. `FR-RKP-03`, `FR-NTF-01`)** beserta halaman UI `Kelola Angsuran.png`, `Cetak Bukti Pembayaran.png`, `Rekap Potong Gaji.png`, dan `Notifikasi Tagihan.png`.
* **Tahap 7:** Implementasi Modul **Kuitansi Digital PDF, Laporan Keuangan (Triwulanan & RAT) & Final QA (`LaporanKeuangan` & `LaporanBuktiController` â€” `UC-13`, `UC-15` | `FR-RPT-01` s.d. `FR-RPT-04`, `NFR-SEC-03`)** beserta halaman UI `Laporan Keuangan.png`, generator PDF/Excel, dan halaman `Audit Trail Log`.

### ðŸ› ï¸ Rincian Perubahan
1. **Implementasi `PembiayaanController` (`05_Implementasi/backend/koperasi/controllers/pembiayaan_controller.py`):**
   * Membangun class `PembiayaanController` dengan method `generateNoPembiayaan()`, `hitungNoAntrean()`, `simulasiPembiayaan()`, `inputAgunan()`, `ajukanPembiayaan()`, `verifikasiBendahara()`, `setujuiPengeluaranKas()`, `catatRealisasiPencairan()`, `catatPembayaranAngsuran()`, dan `konfirmasiPelunasanBatch()` sesuai `03_Class_Diagram_SI-KKPRIS.mmd`.
   * Menerapkan aturan bisnis **BR-01 s.d. BR-05** secara ketat:
     * Validasi periode pengajuan tanggal 1 s.d. 20 setiap bulan, metode margin flat `Decimal(15,2)`, dan tenor maksimal 72 bulan.
     * Kewajiban unggah dokumen agunan (`BPKB_MOTOR`, `BPKB_MOBIL`, `SERTIFIKAT_TANAH_RUMAH`) apabila nominal pokok pembiayaan $> \text{Rp }70.000.000$.
     * Penomoran antrean (`no_antrean`) otomatis berdasarkan urutan pengajuan pada bulan berjalan.
     * Otorisasi pengeluaran kas berjenjang (*Two-Man Rule*): verifikasi administrasi Level 1 oleh Bendahara dan otorisasi pengeluaran kas Level 2 oleh Ketua Koperasi (`DISETUJUI_KETUA`).
     * Pencatatan realisasi pencairan *off-system* oleh Bendahara (`RealisasiPencairan`) yang otomatis mengaktifkan pembiayaan (`AKTIF`) dan men-generate Kartu `JadwalAngsuran` sejumlah tenor bulan.
2. **Pembangunan 7 Layar Antarmuka Tahap 5 (`05_Implementasi/frontend/templates/pembiayaan/` & `frontend/static/css/style.css`):**
   * `frontend/templates/pembiayaan/ajukan_pembiayaan.html`: Wizard 3 langkah terintegrasi (`Pilih Akad` 3 kartu *Murabahah/Ijarah/Hawalah*, `Nominal & Tenor` dengan kotak **Pratinjau Angsuran** *real-time*, serta `Agunan` dengan validasi otomatis $> \text{Rp }70.000.000$ dan dropzone unggah `BPKB`).
   * `frontend/templates/pembiayaan/daftar_pembiayaan.html`: 4 kartu statistik (`Total Pembiayaan`, `Pembiayaan Aktif`, `Total Angsuran`, `Sisa Pembiayaan`), bilah filter (`Cari`, `Akad`, `Status`), kotak informasi aturan pembiayaan, tabel 9 kolom dengan *progress bar* cicilan, paginasi (`Sebelumnya`/`Berikutnya`), serta fitur ekspor Excel (`.xlsx`).
   * `frontend/templates/pembiayaan/detail_pembiayaan.html`: tata letak 2 kolom yang memuat panel **Ringkasan Akad** (beserta info Agunan), tabel **Jadwal Angsuran** berpaginasi, panel **Status Persetujuan** (*vertical stepper*: `Diajukan` $\rightarrow$ `Disetujui Ketua` $\rightarrow$ `Direalisasikan`), kotak catatan pencairan *off-system*, serta modal **Catat Realisasi Pencairan** dan **Verifikasi Bendahara**.
   * `frontend/templates/pembiayaan/persetujuan_kas.html`: halaman khusus Ketua Koperasi dengan 3 kartu statistik (`Pengajuan Kas`, `Menunggu Persetujuan`, `Disetujui`), tabel antrean persetujuan kas, dan modal **Konfirmasi Persetujuan** ber-stepper horizontal 2 titik (`Bendahara` â€”â€”â€” `Ketua`).
   * `frontend/templates/pembiayaan/pembiayaan_saya.html`: portal mandiri Anggota (`Pembiayaan Saya`) untuk memantau daftar kontrak pembiayaan pribadi, nomor antrean, dan progress pelunasan.
3. **Implementasi Tahap 6: `RekapNotifikasiController` & Layar UI Angsuran, Rekap Gaji, dan Notifikasi (`05_Implementasi/backend/koperasi/controllers/rekap_notifikasi_controller.py`, `frontend/templates/angsuran/`):**
   * Membangun `RekapNotifikasiController` dengan method `generateRekapPotongGaji()`, `perbaruiPotonganTambahanAnggota()`, `konfirmasiPelunasanKolektif()`, `eksporFileRekapGaji()`, dan `kirimNotifikasiTagihan()`.
   * `frontend/templates/angsuran/kelola_angsuran.html` (`Kelola Angsuran.png` & `Cetak Bukti Pembayaran.png`) dan `kuitansi_angsuran_print.html`: filter `Pilih Pembiayaan` (`Anggota` & `Akad`), 3 kartu statistik (`Total Pembiayaan`, `Terbayar`, `Sisa`), tabel jadwal & pembayaran angsuran, modal input **Catat Pembayaran**, serta dialog & lembar cetak **Cetak Bukti Pembayaran**.
   * `frontend/templates/angsuran/rekap_potong_gaji.html` (`Rekap Potong Gaji.png`) dan `rekap_potong_gaji_pdf.html`: *One-Click Generator* `Generate Rekap` tanggal 24, pemilih `Periode`, tabel rincian (`Anggota`, `Simpanan Wajib`, `Angsuran`, `Belanja Toko`, `Total Potongan`, `Aksi`) beserta baris bawah `Total`, ekspor **Excel (`.xlsx`) & PDF (`.pdf`)** untuk Bendahara Gaji Sekolah, serta **Konfirmasi Lunas Kolektif** yang otomatis membukukan Simpanan Wajib & melunasi angsuran secara *batch*.
   * `frontend/templates/angsuran/notifikasi_tagihan.html` (`Notifikasi Tagihan.png`): tata letak 2 kolom (`Daftar Penerima` dengan pencarian & pemilihan anggota, serta `Pengaturan Pesan` dengan pilihan kanal `WhatsApp`/`Email`, jadwal `Setiap tanggal 10`, dan `Pratinjau Pesan`).
4. **Implementasi Tahap 7: `LaporanKeuangan`, `LaporanBuktiController`, Layar Laporan Keuangan RAT & Audit Trail Log (`05_Implementasi/backend/koperasi/controllers/laporan_bukti_controller.py`, `frontend/templates/laporan/`):**
   * Membangun service `LaporanKeuangan` (`kompilasiArusKasDanRealisasi`, `hitungNeracaDanSHU`, `renderDokumenLaporan`, `generatePdfKuitansi`) dan controller `LaporanBuktiController` (`cetakBuktiTransaksi`, `lihatLaporanKeuangan`, `eksporLaporan`) sesuai `03_Class_Diagram_SI-KKPRIS.mmd`.
   * Membangun `frontend/templates/laporan/laporan_keuangan.html` (`Laporan Keuangan.png` â€” `WD-14`): 3 tab laporan (`Simpanan`, `Pembiayaan`, `Kas Masuk/Keluar`), filter `Periode (Triwulan/Tahunan)` & `Tahun`, 3 kartu ringkasan (`Total Debit`, `Total Kredit`, `Saldo`), panel visualisasi grafik arus kas triwulanan & ikhtisar **Neraca + Alokasi SHU RAT**, tabel buku besar 5 kolom (`Tanggal`, `Keterangan`, `Debit`, `Kredit`, `Saldo`), serta tombol **Ekspor PDF/Excel**.
   * Menyediakan unduhan PDF langsung untuk kuitansi simpanan & angsuran (`/kuitansi/<no_kuitansi>/pdf/`) serta halaman pengawasan **Jejak Audit Sistem (`audit_trail_log.html`)**.
5. **Pengujian Akhir (Final QA â€” 10 Test Suites Lulus 100%):**
   * Menambahkan `test_08_pembiayaan_controller_agunan_approval_realisasi_tahap_5`, `test_09_rekap_potong_gaji_kelola_angsuran_dan_notifikasi_tahap_6`, dan `test_10_laporan_keuangan_rat_kuitansi_pdf_dan_audit_trail_tahap_7` pada `backend/koperasi/tests.py` (seluruh 10 skenario pengujian lulus 100% â€” **OK**).

### ðŸ’¬ Pesan Commit Terkait
```text
feat(pembiayaan): tambah modul pembiayaan syariah
feat(rekap): tambah modul rekap gaji dan angsuran
feat(laporan): tambah laporan rat dan kuitansi pdf
```

### ðŸ“Œ Status & Rencana Selanjutnya
* **Status Hari Ini:** Seluruh **7 Tahap Konstruksi SI-KKPRIS (Tahap 1 s.d. Tahap 7 â€” 16 Model 3NF, 6 Controller/Service, dan 22 Rancangan Layar Wireframe Final)** telah selesai 100% dan lulus pengujian akhir (*Final QA*).
* **Rencana Berikutnya:** Pemeliharaan sistem, demonstrasi aplikasi, dan penyusunan dokumentasi laporan akhir proyek.

---

## ðŸ“… 16 November 2026

### ðŸŽ¯ Fokus / Tahapan Pengerjaan
* **Restrukturisasi Folder Implementasi (`05_Implementasi/`):** Memisahkan komponen **Backend** (`backend/`) dan **Frontend** (`frontend/`) agar struktur proyek lebih rapi, modular, dan terstandar tanpa mengganggu *virtual environment* (`venv`) maupun fungsionalitas Django.
* **Tahap 3:** Implementasi Modul **Manajemen Keanggotaan & Kliring Resign (`AnggotaController` â€” `UC-05`, `UC-08`, `UC-09` | `FR-MBR-01` s.d. `FR-MBR-04`)** beserta 4 rancangan halaman UI (`Data Anggota.png`, `Form Anggota Baru.png`, `Ajukan Pengunduran Diri.png`, dan `Verifikasi Pengunduran Diri.png`).
* **Tahap 4:** Implementasi Modul **Transaksi Multi-Simpanan Anggota (`SimpananController` â€” `UC-02`, `UC-10`, `UC-13` | `FR-SMP-01` s.d. `FR-SMP-03`, `BR-08`)** beserta halaman UI `Kelola Simpanan.png`, `Transaksi Baru.png`, `Cetak Bukti Transaksi.png`, dan portal mandiri `Simpanan Saya`.

### ðŸ› ï¸ Rincian Perubahan
1. **Pemisahan Direktori `backend/` dan `frontend/` di `05_Implementasi/`:**
   * Memindahkan komponen backend (`koperasi/`, `si_kkpris/`, `media/`, `manage.py`, `requirements.txt`, `.env`, `.env.example`) ke dalam `05_Implementasi/backend/`.
   * Memindahkan komponen frontend (`templates/` dan `static/`) ke dalam `05_Implementasi/frontend/` serta melengkapi subfolder `frontend/static/js/.gitkeep` dan `frontend/static/img/.gitkeep`.
   * Mempertahankan `database/`, `venv/`, dan `README.md` di level root `05_Implementasi/`.
2. **Penyesuaian Konfigurasi Path Django:**
   * Menambahkan penyesuaian `sys.path` pada `backend/manage.py`, `backend/si_kkpris/wsgi.py`, dan `backend/si_kkpris/asgi.py` agar perintah Django dapat berjalan konsisten dari `backend/` maupun dari root `05_Implementasi/`.
   * Memperbarui `backend/si_kkpris/settings.py` dengan definisi `BACKEND_DIR`, `PROJECT_ROOT`, dan `FRONTEND_DIR` sehingga `TEMPLATES`, `STATICFILES_DIRS`, `STATIC_ROOT`, `MEDIA_ROOT`, dan pemuatan `.env` terarah ke struktur baru.
3. **Implementasi Tahap 3: `AnggotaController` (`backend/koperasi/controllers/anggota_controller.py`):**
   * Membangun class `AnggotaController` dengan method `generateNoAnggota()`, `kelolaDataAnggota()`, `perbaruiDataAnggota()`, `ajukanPengunduranDiri()`, dan `verifikasiPengunduranDiri()`.
   * Mendukung pembuatan akun login anggota otomatis, pencatatan setoran awal Simpanan Pokok (`Rp350.000`) & Simpanan Khusus (`Rp500.000`) sesuai pilihan skema cicilan pada formulir pendaftaran, serta unggah berkas fotokopi KTP dan surat pengunduran diri ke `media/`.
   * Mengimplementasikan kalkulasi kliring otomatis presisi `Decimal(15,2)`: $\text{Selisih Akhir} = \sum \text{Simpanan} - \sum \text{Kewajiban Pembiayaan}$, penguncian status anggota ke `PROSES_RESIGN`, serta penonaktifan akun (`is_aktif = False`) & status `NON_AKTIF_KELUAR` saat kliring diselesaikan oleh Bendahara.
   * Merekam seluruh aksi keanggotaan dan kliring ke tabel `audit_trail_log`.
4. **Pembangunan 4 Layar Antarmuka Tahap 3 (`frontend/templates/anggota/` & `frontend/static/css/style.css`):**
   * `frontend/templates/anggota/data_anggota.html` (`Data Anggota.png` & `Form Anggota Baru.png`): 3 kartu statistik keanggotaan, bilah filter (`Cari`, `Status`, `Jenis Simpanan`), tabel anggota berpaginasi (`Sebelumnya`/`Berikutnya`), modal **Form Anggota Baru**, modal **Detail Profil Anggota**, dan modal **Edit Profil Anggota**.
   * `frontend/templates/anggota/ajukan_pengunduran_diri.html` (`Ajukan Pengunduran Diri.png`): formulir mandiri anggota (dropdown `Alasan`, `Keterangan`, dropzone `Surat pengunduran diri`, kotak informasi estimasi kliring real-time, serta tabel status permohonan).
   * `frontend/templates/anggota/verifikasi_pengunduran_diri.html` (`Verifikasi Pengunduran Diri.png`): tata letak 2 kolom untuk Bendahara & Ketua (tabel daftar pengajuan di sisi kiri dan kartu **Perhitungan** kliring `Total Simpanan`, `Sisa Pembiayaan`, `Selisih`, status `Dikembalikan ke anggota / Disetor anggota`, pratinjau surat, serta tombol `Tolak` & `Verifikasi` di sisi kanan).
5. **Implementasi Tahap 4: `SimpananController` & Layar UI Simpanan (`backend/koperasi/controllers/simpanan_controller.py`, `frontend/templates/simpanan/`):**
   * Membangun `SimpananController` dengan method `generateNoKuitansiSimpanan()`, `lihatSaldoDanStatus()`, dan `catatSetorTarikSimpanan()` berpresisi `Decimal(15,2)`.
   * Menerapkan aturan bisnis **BR-08** secara ketat: mengunci penarikan (`TARIK`) pada Simpanan Pokok (`SPK`), Wajib (`SWJ`), dan Khusus (`SKH`) (`dapat_ditarik = 0`), mengizinkan penarikan hanya pada Simpanan Hari Raya (`SHR`) dan Berencana (`SBR`) (`dapat_ditarik = 1`), serta menolak penarikan jika melebihi saldo tersedia.
   * Membangun `frontend/templates/simpanan/kelola_simpanan.html` (`Kelola Simpanan.png`, `Transaksi Baru.png`, & `Cetak Bukti Transaksi.png`), `frontend/templates/simpanan/simpanan_anggota.html` (portal `Simpanan Saya` untuk Anggota), dan `frontend/templates/simpanan/kuitansi_simpanan_print.html` (lembar cetak kuitansi resmi) beserta fitur ekspor Excel (`.xlsx`).
6. **Pengujian & Pembaruan Seeder / Dokumentasi:**
   * Memperkaya `seed_master --with-demo` dengan data anggota tambahan (`KKP-2026-002` & `KKP-2026-003`) beserta contoh permohonan pengunduran diri untuk pengujian visual.
   * Menambahkan `test_05_integrasi_frontend_templates_dan_static`, `test_06_anggota_controller_dan_kliring_resign_tahap_3`, dan `test_07_simpanan_controller_dan_ui_tahap_4` pada `backend/koperasi/tests.py` (seluruh 7 skenario pengujian lulus 100% â€” **OK**).
   * Memperbarui status peta jalan pada `AGENTS.md` dan `05_Implementasi/README.md`.

### ðŸ’¬ Pesan Commit Terkait
```text
refactor(config): pisahkan folder backend dan frontend
feat(member): tambah manajemen anggota dan kliring resign
feat(simpanan): tambah modul transaksi multi-simpanan anggota
```

### ðŸ“Œ Status & Rencana Selanjutnya
* **Status Hari Ini:** Restrukturisasi direktori `backend/` & `frontend/`, **Tahap 3** (`AnggotaController`), serta **Tahap 4** (`SimpananController` & 5 Skema Simpanan UI) selesai 100% dan lulus seluruh unit test.
* **Rencana Berikutnya (Tahap 5):** Implementasi **Pembiayaan Syariah, Agunan, Approval Kas & Realisasi (`PembiayaanController` â€” `UC-07` s.d. `UC-10`)** beserta 7 layar UI Pembiayaan & Persetujuan Kas Ketua.

---

## ðŸ“… 15 November 2026

### ðŸŽ¯ Fokus / Tahapan Pengerjaan
* **Tahap 1:** Penyiapan *Virtual Environment* (`venv`) Python & `requirements.txt`, pembuatan basis data `si_kkpris` pada MySQL 8.4 Laragon, serta inisialisasi proyek Django `si_kkpris` dan aplikasi `koperasi` beserta ke-16 Model tabel (3NF), seeder master data, dan unit test.
* **Tahap 2:** Implementasi Modul Autentikasi, RBAC, Session Timeout, & Pencatatan `AuditTrailLog` (`AuthController` â€” `UC-01`) beserta **Bentuk Awal UI Utama** (`Login.png`, `Dashboard.png` Bendahara & Ketua, serta `Beranda Anggota.png`).

### ðŸ› ï¸ Rincian Perubahan
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
   * Menambahkan dan menjalankan *unit test* terintegrasi di `koperasi/tests.py` (4 skenario pengujian melewati seluruh 16 tabel & RBAC â€” **OK**).
5. **Implementasi Tahap 2: `AuthController`, RBAC & Bentuk Awal UI Utama:**
   * Membangun `koperasi/controllers/auth_controller.py` (`AuthController.login`, `AuthController.logout`, `AuthController.gantiPassword`, dekorator `@login_wajib` & `@peran_wajib`, serta pencatatan otomatis `AuditTrailLog`).
   * Membuat filter pemformatan mata uang Rupiah berbasis `Decimal` di `koperasi/templatetags/kkpris_tags.py`.
   * Membangun *Design System* (`static/css/style.css`), *Base Layout* (`templates/base.html`), dan 3 layar utama sesuai Wireframe Final:
     * `templates/auth/login.html` (`Login.png`)
     * `templates/dashboard/dashboard_pengurus.html` (`Dashboard.png` â€” Bendahara & Ketua)
     * `templates/dashboard/beranda_anggota.html` (`Beranda Anggota.png` â€” Portal Mandiri Anggota)

### ðŸ’¬ Pesan Commit Terkait
```text
feat(db): inisialisasi proyek django dan 16 model
docs(config): simpan peta jalan 7 tahap dan pemetaan ui
feat(auth): tambah modul autentikasi rbac dan dashboard ui
```

### ðŸ“Œ Status & Rencana Selanjutnya
* **Status Hari Ini:** **Tahap 1** (Fondasi & 16 Model) dan **Tahap 2** (`AuthController`, RBAC 3 Peran, & Bentuk Awal UI Login + Dashboard Pengurus + Beranda Anggota) selesai 100%.
* **Rencana Berikutnya (Tahap 3):** Implementasi **Manajemen Keanggotaan & Kliring Resign (`AnggotaController` â€” `UC-02` s.d. `UC-04`)** beserta 4 halaman UI (`Data Anggota.png`, `Form Anggota Baru.png`, `Ajukan Pengunduran Diri.png`, dan `Verifikasi Pengunduran Diri.png`).

---

## ðŸ“… 14 November 2026

### ðŸŽ¯ Fokus / Tahapan Pengerjaan
* Persiapan awal tahap Implementasi, penyusunan aturan kerja agen (`AGENTS.md`), pembuatan log harian (`log_pengerjaan.md`), pembuatan direktori `05_Implementasi/`, serta konfigurasi repository GitHub (Opsi B).

### ðŸ› ï¸ Rincian Perubahan
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

### ðŸ’¬ Pesan Commit Terkait
```text
chore(init): tambah struktur awal dan aturan kerja

- Tambah AGENTS.md dan log_pengerjaan.md untuk standarisasi alur kerja harian
- Buat direktori 05_Implementasi beserta skema DDL 16 tabel MySQL 8.0+
- Atur .gitignore khusus kode implementasi dan DDL sesuai opsi B
```

### ðŸ“Œ Status & Rencana Selanjutnya
* **Status Hari Ini:** Inisialisasi struktur implementasi, aturan kerja, dan koneksi GitHub selesai.
* **Rencana Berikutnya:** Setup *Virtual Environment (`venv`)* Python, instalasi Django & pustaka pendukung (`requirements.txt`), konfigurasi koneksi database MySQL 8.4 Laragon, dan pembuatan struktur proyek Django beserta 16 Model sesuai ERD/DDL.

---

## ðŸ“… 18 November 2026

### ðŸŽ¯ Fokus / Modul yang Dikerjakan
Persiapan Langkah 0 roadmap: restrukturisasi repository dan lingkungan kerja.

### ðŸ› ï¸ Rincian Perubahan
* Pindahkan akar repository ke folder `SI-KKPRIS` (`.git` dipindah dari `Proyek/`); `05_Implementasi/*` kini `backend/`, `frontend/`, `database/` di akar.
* Buat ulang virtualenv di `backend/.venv` (menggantikan `venv/` di akar).
* Tambah `.gitignore` sesuai AGENTS.md Bagian 3 (+ `.venv/`).
* Tambah `AGENTS.md` v2, `ROADMAP_PENGERJAAN.md`, `PENDING_KONFIRMASI.md`, `docs/wireframe/` (22 PNG), `docs/prompt_antigravity.md`, `docs/prompt_antigravity_v2.md`.
* Tambah skill proyek di `.agents/` dan `skills-lock.json`.
* Beri tag `mvt-final` pada commit `95fc734` (titik kembali versi MVT).

### ðŸ’¬ Pesan Commit Terkait
`refactor(config): pindahkan akar repo ke SI-KKPRIS`, `docs(config): tambah aturan kerja v2 dan peta jalan`, `chore(config): tambah skill proyek`

### ðŸ”Ž Temuan & PENDING Baru
* Berkas lama `AGENTS.md`, `README.md`, `.gitignore` masih ada di `Proyek/` (di luar repo).
* Roadmap Langkah 0 meminta `ROADMAP_PENGERJAAN.md` di `docs/`, tetapi AGENTS.md meletakkannya di akar; dipakai akar.

### ðŸ“Œ Status & Rencana Selanjutnya
* Langkah 0 selesai; berikutnya Tahap 8A di percakapan baru. PND-01â€“04 dan PND-12 menunggu jawaban mitra.

---

## 📅 21 November 2026

### 🎯 Fokus / Modul yang Dikerjakan
Aturan responsif mobile untuk aplikasi `web/` (belum ada kode; dokumen saja).

### 🛠️ Rincian Perubahan
* `AGENTS.md`: tambah Bagian 7.F (mobile-first, viewport, drawer, tabel menjadi kartu, area sentuh 44 px, formulir, dialog, verifikasi 375/768/1280 px).
* `docs/prompt_antigravity_v2.md`: Prompt 9C butir 5 merujuk 7.F.

### 💬 Pesan Commit Terkait
`docs(design): tambah aturan responsif mobile`

### 🔎 Temuan & PENDING Baru
* Template Django lama (`frontend/`) dibekukan; hanya punya satu media query (1100px). Tidak diubah sesuai keputusan pengguna.

### 📌 Status & Rencana Selanjutnya
* Aturan diterapkan saat Tahap 9B/9C.

---

## 📅 21 November 2026 — Tahap 8A

### 🎯 Fokus / Modul yang Dikerjakan
* **Tahap 8A:** Penandaan aturan bisnis berstatus `PENDING` (`PND-01` s.d. `PND-10`), pemindahan margin sementara ke konfigurasi environment (`MARGIN_PERSEN_SEMENTARA`), serta penggantian data seed & pengujian ke data dummy dengan password dari env (`SEED_PASSWORD`). Mengikuti Addendum Tahap 8 (template Django lama dibekukan, tidak diubah).

### 🛠️ Rincian Perubahan
1. **Penandaan `# PENDING PND-xx` (`models.py`, `pembiayaan_controller.py`, `laporan_bukti_controller.py`):**
   * Menandai `PND-01` (margin sementara + perjelas docstring `Pembiayaan.hitungSimulasiMarginFlat` menjadi per bulan flat), `PND-02` (Hawalah memakai rumus sama dengan akad lain), `PND-04` (limit per anggota dan batas pembiayaan aktif belum divalidasi), `PND-05` (jenis & syarat agunan), `PND-06` (aturan pembulatan), `PND-07` (awal angsuran bulan berikutnya tanggal 24), `PND-08` (`PembayaranAngsuran.potongan_margin`), `PND-09` (`LaporanKeuangan.hitungNeracaDanSHU` & alokasi SHU), dan `PND-10` (`KanalNotifikasiChoices`).
2. **Pemindahan Margin Sementara ke Environment (`settings.py`, `.env.example`, `pembiayaan_controller.py`, `seed_master.py`, `tests.py`):**
   * Menambahkan `MARGIN_PERSEN_SEMENTARA` di `backend/si_kkpris/settings.py` (dibaca dari env, default `Decimal('1.00')`) dan `backend/.env.example`.
   * Mengganti `PembiayaanController.DEFAULT_MARGIN_PERSEN` menjadi `PembiayaanController.ambilMarginSementara()` yang membaca `settings.MARGIN_PERSEN_SEMENTARA`; `seed_master.py` juga membaca dari `settings.MARGIN_PERSEN_SEMENTARA`.
   * Menambahkan `test_11_simulasi_pakai_margin_sementara_dari_settings` dengan `@override_settings`.
   * Melewati perubahan template `ajukan_pembiayaan.html` dan `detail_pembiayaan.html` sesuai Addendum Tahap 8.
3. **Data Seed Dummy & `SEED_PASSWORD` (`settings.py`, `.env.example`, `seed_master.py`, `tests.py`):**
   * Mengganti seluruh nama asli/mirip nyata, username NIP 18 digit, NIK (`137201...`/`137202...`), dan nomor HP di `seed_master.py` dan `tests.py` menjadi data dummy (`ketua01`, `bendahara01`, `anggota01`–`anggota03`, NIK `0000000000000001`–`0000000000000009`).
   * Membaca password akun seed dari env `SEED_PASSWORD` (`settings.SEED_PASSWORD`), menghapus password hardcoded `'Kkpris2026!'` dari `seed_master.py`, dan menambahkan `SEED_PASSWORD` ke `backend/.env.example`.
   * Menambahkan `test_12_seed_master_wajib_seed_password_dari_env` untuk memastikan `seed_master` menolak berjalan bila `SEED_PASSWORD` kosong.

### 💬 Pesan Commit Terkait
```text
docs(pembiayaan): tandai aturan yang pending
refactor(config): pindah margin sementara ke env
chore(db): ganti data seed dengan data dummy
```

### 🔎 Temuan & PENDING Baru
* **`PND-08` (`PembayaranAngsuran.potongan_margin` / muqashah):** Istilah *pelunasan dipercepat (muqashah)* tercantum di `SRS SI-KKPRIS (Versi 4.0).docx` pada `FR-PMB-07`, namun **tidak tercantum** di catatan wawancara (`Wawancara.txt`) dan belum ada rumus/ketentuan potongan dari mitra. Kolom dipertahankan dan ditandai `# PENDING PND-08`.
* **Password hardcoded sebelumnya di `seed_master.py`:** Sebelumnya `default_pw = make_password('Kkpris2026!')` tertulis langsung di kode (kini sudah dipindahkan ke env `SEED_PASSWORD`).
* **Temuan di luar lingkup Tahap 8A:**
  * Password bawaan `'Kkpris2026!'` masih hardcoded di `backend/koperasi/controllers/anggota_controller.py:125` (untuk pendaftaran anggota baru tanpa input password).
  * Tombol demo di `frontend/templates/auth/login.html` masih memakai username lama (`bendahara`, `ketua`) dan password `'Kkpris2026!'`, serta teks di `frontend/templates/anggota/data_anggota.html:329` masih menyebut `Kkpris2026!` (tidak diubah karena template dibekukan sesuai Addendum Tahap 8).
  * Alokasi SHU `40% / 25% / 20% / 15%` di `LaporanKeuangan.hitungNeracaDanSHU` tidak memiliki sumber di wawancara maupun SRS v4.0 (ditandai `# PENDING PND-09`).
  * `backend/.env` lokal tidak disentuh sesuai aturan; pengguna perlu menambahkan `SEED_PASSWORD` (dan opsional `MARGIN_PERSEN_SEMENTARA`) ke `backend/.env` sebelum menjalankan `python manage.py seed_master`.

### 📌 Status & Rencana Selanjutnya
* **Status:** Tahap 8A selesai 100% — `check`, `makemigrations --check --dry-run`, dan `test koperasi` (12 test) lulus pada MySQL 8.4 Laragon (`Ran 12 tests in 11.895s — OK`).
* **Rencana Berikutnya:** Mulai **Tahap 8B** (perbaikan teknis backend) di sesi percakapan baru.

---

## 📅 21 November 2026 — Tahap 8B

### 🎯 Fokus / Modul yang Dikerjakan
* **Tahap 8B:** Perbaikan teknis backend tanpa mengubah aturan bisnis yang berstatus `PENDING`: penyerapan sisa pembulatan di angsuran terakhir, pemisahan parser rupiah & persen, penghapusan `float()` pada ekspor Excel, kunci baris `select_for_update()` untuk saldo/pembayaran/persetujuan/realisasi, pemisahan template PDF kuitansi, pengerasan konfigurasi & keamanan (`PyMySQL`, PBKDF2, `SECRET_KEY`/`DEBUG`, `REMOTE_ADDR`), serta pengujian penuh pada MySQL 8.4 Laragon. Item 6 dilewati sesuai Addendum Tahap 8 (template Django lama dibekukan).

### 🛠️ Rincian Perubahan
1. **Item 1 — Angsuran terakhir menyerap sisa pembulatan (`models.py`, `pembiayaan_controller.py`, `seed_master.py`, `tests.py`):**
   * Membuat fungsi sumber tunggal `Pembiayaan.hitungRincianAngsuran(harga_pokok, margin_persen, tenor_bulan)` dengan angsuran ke-N menyerap sisa pembulatan pokok (`pokok - porsi_pokok_reguler * (N - 1)`).
   * Memakai fungsi tersebut di `Pembiayaan.hitungSimulasiMarginFlat`, `JadwalAngsuran.generateJadwalAngsuran` (menambahkan parameter `harga_pokok` & `margin_persen`), `PembiayaanController.catatRealisasiPencairan`, `_rakit_baris_pembiayaan`, pratinjau jadwal di `detail_pembiayaan_view`, dan `seed_master.py`.
   * Menambahkan `test_13_invarian_pembulatan_angsuran_terakhir` (kasus a: 10 jt / 7 bln, b: 70 jt / 72 bln, c: 25 jt / 11 bln, d: margin 0% 5 jt / 10 bln + pratinjau detail pembiayaan).
2. **Item 2 — Parser nominal rupiah & persen (`utils.py`, `pembiayaan_controller.py`, `simpanan_controller.py`, `rekap_notifikasi_controller.py`, `tests.py`):**
   * Membuat modul `backend/koperasi/utils.py` dengan `bersihkan_rupiah(raw)` (pola ribuan `^\d{1,3}(\.\d{3})+$`, koma sebagai desimal, hapus `Rp` & spasi) dan `bersihkan_persen(raw)` (titik/koma selalu desimal, bukan ribuan).
   * Memindahkan seluruh pemanggil di `pembiayaan_controller.py`, `simpanan_controller.py`, dan `rekap_notifikasi_controller.py` ke utilitas baru, serta menghapus `_bersihkan_decimal`.
   * Menambahkan `test_14_parser_nominal_rupiah_dan_persen` mencakup seluruh tabel uji.
3. **Item 3 — Penghapusan `float()` pada ekspor Excel (`simpanan_controller.py`, `pembiayaan_controller.py`, `rekap_notifikasi_controller.py`, `laporan_bukti_controller.py`, `tests.py`):**
   * Mengganti seluruh `float(...)` pada keempat ekspor `.xlsx` dengan menulis `Decimal` langsung ke sel `openpyxl` beserta `number_format = '#,##0.00'` (termasuk sheet `Neraca & SHU` di `laporan_bukti_controller.py`).
   * Menambahkan `test_15_ekspor_excel_presisi_numerik_decimal` untuk membuka `.xlsx` hasil ekspor dan memverifikasi nilai numerik serta format selnya.
4. **Item 4 — Kunci baris `select_for_update()` (`models.py`, `simpanan_controller.py`, `pembiayaan_controller.py`, `rekap_notifikasi_controller.py`, `tests.py`):**
   * Membungkus transaksi simpanan dengan `transaction.atomic()` + `Anggota.objects.select_for_update().get(...)` sebelum membaca saldo berjalan.
   * Mengunci `JadwalAngsuran` (`select_for_update`) pada `PembayaranAngsuran.simpanPembayaranAngsuran` dan `PembiayaanController.catatPembayaranAngsuran` serta menolak pembayaran ulang bila sudah `LUNAS`.
   * Mengunci `Pembiayaan` pada `verifikasiBendahara`, `setujuiPengeluaranKas`, `catatRealisasiPencairan`, dan `RealisasiPencairan.simpanRealisasiPencairan` serta mengecek status di dalam kunci; mengunci `RekapPotongGaji` pada `konfirmasiPelunasanKolektif`.
   * Menambahkan `test_16_kunci_baris_tolak_pembayaran_dan_aksi_ganda`.
5. **Item 5 — Template PDF kuitansi terpisah (`frontend/templates/simpanan/`, `frontend/templates/angsuran/`, `laporan_bukti_controller.py`, `tests.py`):**
   * Mengekstrak isi kuitansi ke partial `simpanan/_kuitansi_isi.html` dan `angsuran/_kuitansi_isi.html`.
   * Membuat template PDF baru `simpanan/kuitansi_simpanan_pdf.html` dan `angsuran/kuitansi_angsuran_pdf.html` tanpa tombol/emoji mengikuti pola `rekap_potong_gaji_pdf.html`, memperbarui template layar `*_print.html` memakai partial + toolbar, dan mengarahkan `LaporanBuktiController.cetakBuktiTransaksi` ke template `*_pdf.html`.
   * Menambahkan `test_17_kuitansi_pdf_terpisah_dari_template_layar` menggunakan `pypdf.PdfReader`.
6. **Item 6 — Dilewati** sesuai Addendum Tahap 8 (`frontend/templates/` MVT dibekukan).
7. **Item 7 — Konfigurasi & keamanan (`requirements.txt`, `settings.py`, `.env.example`, `auth_controller.py`, `tests.py`):**
   * Menghapus `PyMySQL==1.2.4` dari `backend/requirements.txt` (mempertahankan `mysqlclient==2.3.1`).
   * Menetapkan `AUTH_PASSWORD_HASHERS` hanya `PBKDF2PasswordHasher` (`test_18_konfigurasi_hasher_hanya_pbkdf2`).
   * Mengubah default `DEBUG` menjadi `False`, mewajibkan `SECRET_KEY` dari env (menghapus kunci bawaan di kode), dan mengaktifkan `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` otomatis saat `DEBUG=False` dengan dukungan override env (`test_19_konfigurasi_debug_dan_secret_key_wajib_env`).
   * Memperbarui `_ambil_ip_klien` di `auth_controller.py` agar memakai `REMOTE_ADDR` dan hanya membaca `X-Forwarded-For` bila `settings.TRUSTED_PROXY=True` (default `False`) (`test_20_ambil_ip_klien_hormati_trusted_proxy`).
   * Memverifikasi `.gitignore` sudah sesuai `AGENTS.md` Bagian 3.
8. **Item 8 — Pengujian penuh di MySQL:**
   * Menjalankan `python manage.py check`, `python manage.py makemigrations --check --dry-run`, dan `python manage.py test koperasi -v 2` pada MySQL 8.4 Laragon (`test_si_kkpris`): seluruh 20 test lulus (`Ran 20 tests in 16.927s — OK`).

### 💬 Pesan Commit Terkait
```text
fix(pembiayaan): serap sisa pembulatan di angsuran akhir
fix(pembiayaan): perbaiki parser nominal rupiah
fix(export): hapus float pada ekspor Excel
fix(simpanan): kunci baris saat hitung saldo
fix(pdf): pisahkan template kuitansi PDF
chore(config): hapus PyMySQL dari requirements
fix(auth): gunakan hasher PBKDF2 saja
chore(config): wajibkan SECRET_KEY dari env
fix(security): percayai IP dari REMOTE_ADDR
docs(config): perbarui log pengerjaan tahap 8b
```

### 🔎 Temuan & PENDING Baru
* `rekap_potong_gaji_pdf.html` dan `laporan_keuangan_pdf.html` masih memunculkan peringatan minor `xhtml2pdf`: `Ignoring CSS properties xhtml2pdf does not implement: border-collapse` (tidak mengganggu hasil PDF, di luar lingkup Item 5 yang berfokus pada kuitansi).
* `backend/koperasi/controllers/anggota_controller.py:125` masih memiliki password bawaan `'Kkpris2026!'` untuk registrasi anggota baru tanpa input password (sudah dicatat pada temuan Tahap 8A; di luar lingkup Tahap 8B).

### 📌 Status & Rencana Selanjutnya
* **Status:** Tahap 8B selesai 100% — `check`, `makemigrations --check --dry-run`, `grep float(` (kosong), `grep pymysql` (kosong), dan `test koperasi` (20 test) lulus pada MySQL 8.4 Laragon (`Ran 20 tests in 16.927s — OK`).
* **Rencana Berikutnya:** Mulai **Tahap 9A** (Fondasi API: `Pengguna` custom `AbstractBaseUser`, DRF, JWT cookie, Swagger) di sesi percakapan baru (gunakan mode perencanaan sesuai `ROADMAP_PENGERJAAN.md`).

---

## 📅 21 November 2026 — Tahap 9A

### 🎯 Fokus / Modul yang Dikerjakan
* **Tahap 9A:** Fondasi REST API v1 (`/api/v1/`) dan autentikasi JWT: penambahan DRF, SimpleJWT (`token_blacklist`), dan `drf-spectacular`; konversi model `Pengguna` menjadi `AbstractBaseUser + PermissionsMixin` (`AUTH_USER_MODEL = 'koperasi.Pengguna'`); ekstraksi `koperasi/services/auth_service.py`; permission class per peran; 5 endpoint autentikasi JWT dengan *refresh token* pada cookie `httpOnly` + rotasi + blacklist; exception handler seragam Bahasa Indonesia; Swagger/OpenAPI (`backend/docs/openapi.yaml`); serta suite pengujian API.

### 🛠️ Rincian Perubahan
1. **Dependensi & Konfigurasi (`backend/requirements.txt`, `backend/.env.example`, `backend/si_kkpris/settings.py`):**
   * Memasang dan mengunci versi stabil terbaru yang kompatibel dengan Django 5.2.19: `djangorestframework==3.18.3`, `djangorestframework-simplejwt==5.5.1`, `drf-spectacular==0.30.0`, dan `PyJWT==2.15.1`.
   * Menambahkan `'rest_framework'`, `'rest_framework_simplejwt.token_blacklist'`, dan `'drf_spectacular'` ke `INSTALLED_APPS`.
   * Mengonfigurasi `REST_FRAMEWORK` (JWTAuthentication, `IsAuthenticated`, `JSONRenderer` saja, `handler_galat_seragam`, `StandarPagination` page size 20, throttle `login`, `AutoSchema`, `COERCE_DECIMAL_TO_STRING=True`), `SIMPLE_JWT` (access 10 menit, refresh 30 menit, `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`), pengaturan cookie refresh, dan `SPECTACULAR_SETTINGS` (`SI-KKPRIS API` v1.0.0) berbasis env `API_DOCS_ENABLED` (default `False`; ditambahkan ke `.env.example` dan `.env` lokal atas persetujuan pengguna). Tanpa `django-cors-headers`.
2. **Model `Pengguna` Custom, Migrasi, DDL & Service (`models.py`, `0002_pengguna_custom_user.py`, `admin.py`, `seed_master.py`, `database/02_DDL_MySQL_SI-KKPRIS.sql`, `services/auth_service.py`, `controllers/auth_controller.py`):**
   * Mengubah `Pengguna` menjadi `AbstractBaseUser + PermissionsMixin` dengan `PenggunaManager(BaseUserManager)`, `AUTH_USER_MODEL = 'koperasi.Pengguna'`, kolom `password` (migrasi `RenameField` dari `password_hash`), `last_login`, `is_staff`, `is_superuser`, `groups`, `user_permissions`, serta mempertahankan `is_aktif` + properti `is_active`.
   * Mereset database lokal `si_kkpris` atas persetujuan pengguna dan menjalankan `migrate` (seluruh migrasi termasuk `0002_pengguna_custom_user` dan `token_blacklist` berhasil).
   * Menyinkronkan `database/02_DDL_MySQL_SI-KKPRIS.sql`, `admin.py` (`PenggunaAdmin`), dan `seed_master.py`.
   * Mengekstrak logika autentikasi & audit trail ke `backend/koperasi/services/auth_service.py` dan mendelegasikan `AuthController` lama ke service yang sama.
3. **Fondasi API v1, Permission, Endpoint Auth & OpenAPI (`koperasi/api/v1/*`, `si_kkpris/urls.py`, `backend/docs/openapi.yaml`):**
   * Membuat `exceptions.py` (`{kode, pesan, detail}` Bahasa Indonesia), `pagination.py`, `permissions.py` (`IsAnggota`, `IsBendahara`, `IsKetua`, `IsBendaharaAtauKetua`), `throttling.py` (`LoginRateThrottle` berbasis `ambil_ip_klien`), `serializers/auth_serializers.py`, `views/auth_views.py`, dan `urls.py`.
   * Menyediakan 5 endpoint: `POST /api/v1/auth/login/`, `POST /api/v1/auth/refresh/`, `POST /api/v1/auth/logout/`, `GET /api/v1/auth/me/`, dan `POST /api/v1/auth/ganti-password/`.
   * Mendaftarkan `/api/schema/` dan `/api/docs/` hanya saat `API_DOCS_ENABLED=True` dan menghasilkan `backend/docs/openapi.yaml` (`--validate --fail-on-warn` lulus tanpa peringatan).
4. **Pengujian & Dokumentasi (`koperasi/test_api_auth.py`, `README.md`):**
   * Menambahkan 13 test API di `backend/koperasi/test_api_auth.py` mencakup login (username & `no_anggota`), gagal login, atribut cookie (`httpOnly`, `SameSite=Strict`, `Path`, `Secure`), refresh & rotasi, penolakan token lama (blacklist), logout, `/me/`, `/ganti-password/`, 401 tanpa token, 403 peran salah pada keempat permission class, throttle 429, `AuditTrailLog`, dan aktivasi `/api/schema/` + `/api/docs/`.
   * Menambahkan panduan singkat REST API di `README.md`.

### 💬 Pesan Commit Terkait
```text
chore(config): tambah DRF simplejwt dan drf-spectacular
refactor(auth): ubah Pengguna dan ekstrak service
feat(api): tambah fondasi API v1 dan auth JWT
test(api): tambah tes autentikasi JWT dan izin
docs(api): tambah panduan API dan log tahap 9a
```

### 🔎 Temuan & PENDING Baru
* `python manage.py seed_master --with-demo` pada database lokal `si_kkpris` yang baru direset belum selesai karena `SEED_PASSWORD` belum diisi pada `backend/.env` lokal (pengguna perlu menambahkan `SEED_PASSWORD` di `backend/.env` lalu menjalankan `python manage.py seed_master --with-demo`).
* Tidak ada `PND-xx` baru; aturan bisnis tidak diubah.

### 📌 Status & Rencana Selanjutnya
* **Status:** Tahap 9A selesai 100% — `check` (0 isu), `makemigrations --check --dry-run` (`No changes detected`), `spectacular --file docs/openapi.yaml --validate --fail-on-warn` (lulus), dan `test koperasi` (33 test: 20 lama + 13 API baru) lulus pada MySQL 8.4 Laragon.
* **Rencana Berikutnya:** Mulai **Tahap 9B** (Scaffold aplikasi React `web/`: Vite + TypeScript + Tailwind v4 + API client + auth) di sesi percakapan baru (gunakan mode perencanaan sesuai `ROADMAP_PENGERJAAN.md`).

---

## 📅 21 November 2026 — Tahap 9B

### 🎯 Fokus / Modul yang Dikerjakan
* **Tahap 9B:** Scaffold aplikasi frontend React SPA di folder `web/` (Vite 8 + React 19 + TypeScript 5.9 `strict` + Tailwind CSS v4 lewat `@tailwindcss/vite`), generasi tipe TypeScript dari `backend/docs/openapi.yaml` (`openapi-typescript`), klien API `openapi-fetch` dengan *access token* hanya di memori + *single-flight* refresh `401` + `downloadFile`, `AuthProvider` + `ProtectedRoute`/`RoleRoute` + React Router 8, `QueryClient`, utilitas `formatRupiah` (manipulasi string murni) & `formatTanggal` (`Asia/Jakarta`), halaman login/beranda sementara tanpa gaya untuk verifikasi E2E, unit test Vitest, dan `web/README.md`.

### 🛠️ Rincian Perubahan
1. **Aturan Kerja (`AGENTS.md`):**
   * Memperbarui Bagian 0.5 dan 0.7 sesuai instruksi pengguna: perubahan berkas `.env` wajib meminta persetujuan pengguna terlebih dahulu beserta alasannya.
2. **Inisialisasi `web/`, Tailwind v4 & Tooling (`web/package.json`, `vite.config.ts`, `vitest.config.ts`, `tsconfig.*.json`, `eslint.config.js`, `.prettierrc`, `index.html`, `src/styles/index.css`):**
   * Membuat proyek `web/` dengan `create-vite` (`react-ts`), menyelaraskan `typescript@^5.9.3` agar kompatibel penuh dengan peer `openapi-typescript@7.13.0` (`^5.x`) dan `typescript-eslint@8.73.0` (`<6.1.0`), serta mengganti `oxlint` bawaan template ke ESLint 10 + `eslint-plugin-react-hooks` + `prettier`.
   * Memasang Tailwind CSS v4.3.5 + `@tailwindcss/vite` di `vite.config.ts` dengan `@import "tailwindcss";` pada `src/styles/index.css` tanpa `tailwind.config.js` maupun `postcss.config.js`.
   * Mengonfigurasi alias `'@' -> src`, proxy dev `'/api' -> http://127.0.0.1:8000` (tanpa CORS), `tsconfig` mode `strict`, dan skrip `dev`, `build`, `preview`, `lint`, `typecheck`, `test`, `gen:api`.
3. **Kontrak OpenAPI, Klien API & TanStack Query (`web/src/api/*`):**
   * Menghasilkan `web/src/api/schema.d.ts` melalui `npm run gen:api` dari `backend/docs/openapi.yaml`.
   * Membangun `web/src/api/client.ts` (`openapi-fetch`): *access token* hanya pada variabel memori modul (nol penggunaan `localStorage`/`sessionStorage`), `credentials: 'same-origin'`, `baseUrl` dari `window.location.origin`, middleware penyisip `Authorization`, penyimpanan `request.clone()` di `WeakMap` agar retry `POST`/`PUT`/`PATCH` aman, *single-flight* refresh `401` dengan 1x retry, normalisasi galat `{ kode, pesan, detail }` (`ApiError` dengan `{ cause }`), serta helper `downloadFile(path, namaFile)` berbasis `fetch` + `Authorization` + `blob`.
   * Membangun `web/src/api/queryClient.ts` (`staleTime` 30 detik, `retry: 1` untuk GET kecuali 401/403/404, `retry: false` untuk mutasi) dan `web/src/api/queryKeys.ts`.
4. **Autentikasi, Guard, Router, Utilitas & Halaman Sederhana (`web/src/app/*`, `web/src/lib/*`, `web/src/features/*`):**
   * Membangun `authContext.ts` & `AuthProvider.tsx` (pemulihan sesi awal `refresh -> me` aman terhadap StrictMode, `login()`, `logout()`, `refreshUser()`), `guards.tsx` (`ProtectedRoute` & `RoleRoute`), `routes.tsx` (`/login`, `/`, `/pengurus`, `/ketua`, `/anggota`, `/403`, `*`), dan `providers.tsx`.
   * Membangun `web/src/lib/format.ts` (`formatRupiah` 100% manipulasi string tanpa `parseFloat`/`Number()` dan `formatTanggal` `Intl id-ID` zona `Asia/Jakarta`) serta `web/src/lib/cn.ts`.
   * Membangun halaman sederhana tanpa gaya: `LoginPage.tsx` (React Hook Form + Zod + galat server), `BerandaSementaraPage.tsx`, `ForbiddenPage.tsx`, dan `NotFoundPage.tsx`.
5. **Pengujian Unit & Dokumentasi (`web/src/test/*`, `web/README.md`):**
   * Menambahkan 16 unit test di `format.test.ts` (9 test), `client.test.ts` (4 test termasuk *single-flight* paralel + retry `POST` + gagal refresh), dan `guards.test.tsx` (3 test).
   * Menulis panduan pengembangan di `web/README.md`.

### 💬 Pesan Commit Terkait
```text
docs(config): tambah aturan persetujuan perubahan env
chore(web): inisialisasi proyek Vite React TS dan Tailwind v4
feat(api): tambah klien API openapi-fetch dan skema TS
feat(web): tambah AuthProvider guard router dan util format
test(web): tambah tes unit format klien API dan guard peran
docs(web): tambah dokumentasi web dan log tahap 9b
```

### 🔎 Temuan & PENDING Baru
* `create-vite v9.3.4` memasang `typescript@7.0.2` dan `oxlint` secara bawaan; diselaraskan ke `typescript@^5.9.3` dan `eslint` + `eslint-plugin-react-hooks` agar sesuai Prompt 9B dan kompatibel dengan peer `openapi-typescript@7.13.0` & `typescript-eslint@8.73.0`.
* `python manage.py seed_master --with-demo` telah berhasil dijalankan pada database lokal (akun seed `ketua01`, `bendahara01`, `anggota01` siap).
* Pengujian E2E interaktif melalui subagent browser Chrome tidak dapat terhubung karena *remote debugging* Chrome (`DevToolsActivePort`) tidak aktif; sebagai pengganti, alur proxy live `http://localhost:5173` → `http://127.0.0.1:8000` (`login`, cookie `httpOnly`/`SameSite=Strict`, `/me`, `/refresh` dengan rotasi, `/logout`, `/refresh` 401) telah diverifikasi lewat HTTP client terhadap kedua server yang berjalan, sedangkan verifikasi muat ulang tab di browser disarankan dijalankan langsung oleh pengguna.
* Tidak ada `PND-xx` baru; aturan bisnis dan backend tidak diubah.

### 📌 Status & Rencana Selanjutnya
* **Status:** Tahap 9B selesai — `npm run gen:api`, `npm run lint` (0 error, 0 warning), `npm run typecheck` (lulus), `npm run test` (3 file, 16 test lulus), `npm run build` (`✓ built`), serta verifikasi proxy live Vite → Django lulus.
* **Rencana Berikutnya:** Mulai **Tahap 9C** (Design system 60-30-10, `docs/design-system.md`, komponen UI, AppShell, Login, Dashboard Pengurus, dan Beranda Anggota + 2 endpoint ringkasan) di sesi percakapan baru.

---

## 📅 21 November 2026 — Tahap 9C

### 🎯 Fokus / Modul yang Dikerjakan
* **Tahap 9C:** Design System 60-30-10 (`@theme` Tailwind v4 + `docs/design-system.md`), pustaka komponen UI dasar (`web/src/components/ui/`), kerangka tata letak responsif berbasis peran (`AppShell`, `SidebarNav`, `Topbar`, `navigation.ts`), ekstraksi `dashboard_service.py` + 2 endpoint read-only (`GET /api/v1/dashboard/ringkasan/` & `GET /api/v1/anggota/saya/ringkasan/`), regenerasi OpenAPI & `schema.d.ts`, serta implementasi 3 halaman wireframe pertama (**Login**, **Dashboard Pengurus**, dan **Beranda Anggota**).

### 🛠️ Rincian Perubahan
1. **Backend Service & Endpoint Ringkasan (`dashboard_service.py`, `auth_controller.py`, `dashboard_serializers.py`, `dashboard_views.py`, `api/v1/urls.py`, `test_api_dashboard.py`, `docs/openapi.yaml`):**
   * Mengekstrak agregasi Dashboard Pengurus dan Beranda Anggota dari `auth_controller.py` ke `backend/koperasi/services/dashboard_service.py` sebagai sumber tunggal logika tanpa mengubah aturan bisnis maupun template MVT lama.
   * Menambahkan 2 endpoint read-only: `GET /api/v1/dashboard/ringkasan/` (`IsBendaharaAtauKetua`, `operation_id='dashboard_ringkasan'`) dan `GET /api/v1/anggota/saya/ringkasan/` (`IsAnggota`, `operation_id='anggota_saya_ringkasan'`) dengan seluruh field nominal uang sebagai string desimal `DecimalField(max_digits=15, decimal_places=2, coerce_to_string=True)`.
   * Menambahkan 7 test API di `backend/koperasi/test_api_dashboard.py` (200 Bendahara/Ketua/Anggota, 401 tanpa token, 403 peran lain, format uang string, kasus anggota baru kosong).
   * Meregenerasi `backend/docs/openapi.yaml` (`--validate --fail-on-warn`) dan menyinkronkan `web/src/api/schema.d.ts` via `npm run gen:api`.
2. **Design System & Token Tema (`docs/design-system.md`, `web/index.html`, `web/src/styles/index.css`):**
   * Mendefinisikan token `@theme` Tailwind v4 untuk palet 60-30-10 (`#F6F2EA` krem / `#FFFFFF` permukaan 60%, `#14452F` hijau tua 30%, `#D99A1E` aksen emas 10% dengan teks gelap `#1F2A24`), warna status terpisah (sukses, peringatan burnt-orange, bahaya, info), tipografi `IBM Plex Sans`, bayangan tipis tunggal, dan animasi loading CSS murni (`transform`/`opacity`, `prefers-reduced-motion`).
   * Menambahkan `<meta name="text-scale" content="scale" />` di `web/index.html` tanpa override `font-size` pada `:root`/`html`, gaya `<dialog>` modal & drawer native, serta tabel responsif berbasis `@container` query.
   * Menulis dokumentasi lengkap beserta tabel rasio kontras WCAG 2.1 AA terhitung di `docs/design-system.md`.
3. **Komponen UI Dasar & Layout Responsif (`web/src/components/ui/*`, `web/src/components/layout/*`):**
   * Membangun `Button` (loading + `disabled` + `Spinner`), `Field`, `Input`, `Select`, `Textarea`, `Card`, `Badge` (status selalu dengan ikon `lucide-react` + teks), `Table` (responsif kartu bertumpuk di layar sempit, angka rata kanan `tabular-nums`), `Dialog` (`<dialog>` native + fallback light-dismiss koordinat Safari), `ConfirmDialog`, `ToastProvider` + `useToast`, `Skeleton`, `Spinner`, `TopProgress`, `ProgressBar`, `useDelayedLoading` (±200 ms tunda / ±400 ms min tampil), `EmptyState`, `ErrorState`, dan `PageHeader`.
   * Membangun `navigation.ts` (menu per peran `BENDAHARA` 8 item, `KETUA` 7 item, `ANGGOTA` 5 item), `SidebarNav.tsx`, `Topbar.tsx`, dan `AppShell.tsx` (tautan *"Lompat ke konten utama"*, sidebar tetap mulai `lg`, drawer `<dialog>` native di bawah `lg`, indikator menu aktif aksen emas).
4. **3 Halaman Utama & Pengujian Frontend (`web/src/features/*`, `web/src/app/*`, `web/src/test/*`):**
   * Memperbarui `LoginPage.tsx` (+ `LoginIdentitasPanel.tsx`): React Hook Form + Zod, tanpa checkbox *"Ingat saya"* sesuai keputusan pengguna, tombol tampil/sembunyikan kata sandi, dialog bantuan lupa kata sandi, galat server `role="alert"`, dan tombol loading `"Masuk…"`.
   * Membangun `DashboardPengurusPage.tsx` (+ `DashboardPanels.tsx`, `StatCard.tsx`, `DashboardSkeleton.tsx`, `useDashboardRingkasan.ts`) dan `BerandaAnggotaPage.tsx` (+ `StatusPembiayaanCard.tsx`, `useBerandaAnggotaRingkasan.ts`) lengkap dengan 4 keadaan (memuat skeleton, kosong, galat `"Coba lagi"`, dan berhasil).
   * Memperbarui `routes.tsx` (redirect `/` sesuai peran ke `/dashboard` atau `/beranda`, `ModulTerjadwalPage` terproteksi `RoleRoute` untuk modul Tahap 10–14A, penghapusan `BerandaSementaraPage.tsx`), `guards.tsx`, `providers.tsx`, `ForbiddenPage.tsx`, dan `NotFoundPage.tsx`.
   * Menambahkan 13 unit test baru (`button.test.tsx`, `login.test.tsx`, `navigation.test.tsx`, `dashboard.test.tsx`) sehingga total menjadi 7 file / 29 test lulus.

### 💬 Pesan Commit Terkait
```text
refactor(service): ekstrak service ringkasan dashboard
feat(api): tambah endpoint ringkasan dashboard
test(api): tambah tes endpoint dashboard dan beranda
docs(design): tambah panduan design system dan tema
feat(ui): tambah komponen dasar dan AppShell
feat(web): tambah halaman login dashboard dan beranda
test(web): tambah tes form login menu peran dan UI
docs(web): perbarui log pengerjaan tahap 9c
```

### 🔎 Temuan & PENDING Baru
* **Resolusi pertentangan skill vs `AGENTS.md` (Bagian 9.8):** `modern-web-guidance/spinner` menyarankan memperlambat putaran 6 detik pada `prefers-reduced-motion: reduce`, sedangkan `AGENTS.md` 7.D mewajibkan spinner menjadi teks `"Memuat…"` tanpa gerak (yang diikuti: `AGENTS.md` 7.D). `modern-web-guidance/light-dismiss-a-dialog` mencontohkan `backdrop-filter: blur(2px)`, sedangkan `AGENTS.md` 7.B melarang kaca buram (yang diikuti: `AGENTS.md` 7.B).
* **Audit `web-design-guidelines`:** Ditiadakan sesuai keputusan pengguna.
* **Verifikasi browser 375/768/1280 px & keyboard:** Subagent browser Chrome kembali terblokir karena *remote debugging* Chrome (`DevToolsActivePort`) tidak aktif pada lingkungan lokal; verifikasi visual responsif & login langsung di browser perlu dijalankan oleh pengguna.
* **Ukuran bundle produksi:** `vite build` mencatat chunk utama `index-*.js` sebesar `517,89 kB` (gzip `158,41 kB`); dicatat sebagai temuan untuk dipertimbangkan *code-splitting* rute saat modul Tahap 10–14A bertambah.
* Tidak ada `PND-xx` baru; aturan bisnis tidak diubah.

### 📌 Status & Rencana Selanjutnya
* **Status:** Tahap 9C selesai — Backend: `check` (0 isu), `makemigrations --check --dry-run` (bersih), `spectacular --validate --fail-on-warn` (lulus), `test koperasi` (40 test lulus di MySQL). Frontend: `npm run gen:api` (sinkron), `lint` (0 error/warning), `typecheck` (lulus), `test` (7 file, 29 test lulus), `build` (`✓ built`).
* **Rencana Berikutnya:** Evaluasi **Gerbang 1** sesuai `ROADMAP_PENGERJAAN.md`, lalu lanjut **Tahap 10** (Modul Anggota & Kliring Resign — backend dulu, kemudian frontend) di sesi baru.
