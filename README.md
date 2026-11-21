# 05_Implementasi — Source Code Aplikasi SI-KKPRIS

Folder ini merupakan direktori utama tahap **Implementasi (Konstruksi Perangkat Lunak)** untuk **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** pada Koperasi Guru & Karyawan (KKPRIS) SMK Negeri 1 Kota Solok.

---

## 🛠️ Spesifikasi Teknis Implementasi

| Komponen | Teknologi / Versi | Keterangan |
| :--- | :--- | :--- |
| **Bahasa Pemrograman** | Python 3.13.7 | Virtual Environment (`05_Implementasi/venv/`) |
| **Web Framework** | Django 5.2.19 LTS | Arsitektur MVT (*Model-View-Template*) |
| **Database RDBMS** | MySQL 8.4.3 (`InnoDB`) | Laragon MySQL 8.4 (`si_kkpris`, `utf8mb4_unicode_ci`) |
| **Tipe Data Moneter** | `DECIMAL(15,2)` / `DecimalField` | Bebas *floating-point roundoff error* |
| **Ekspor Dokumen** | `openpyxl 3.1.5`, `reportlab 5.1.0`, `xhtml2pdf 0.2.28` | Cetak Kuitansi PDF & Ekspor Rekap Gaji `.xlsx` |

---

## 🗺️ Peta Jalan (Roadmap) 7 Tahap Konstruksi & Pemetaan 22 Layar UI

| Tahap | Fokus Modul & Controller | Halaman UI yang Dibangun (`04_Wireframe & Desain UI/01_Wireframe_Final_PNG/`) | Status |
| :--- | :--- | :--- | :---: |
| **Tahap 1** | **Fondasi Proyek, Database & 16 Model (3NF)** | *(Fondasi Backend, Database MySQL 8.4 & Seeder Master Data)* | ✅ **Selesai** |
| **Tahap 2** | **Autentikasi, RBAC & Base Dashboard UI** (`AuthController`) | **Bentuk Awal UI Utama:** `Login.png`, `Dashboard.png` (Bendahara & Ketua), `Beranda Anggota.png` | ✅ **Selesai** |
| **Tahap 3** | **Manajemen Keanggotaan & Kliring Resign** (`AnggotaController`) | `Data Anggota.png`, `Form Anggota Baru.png`, `Ajukan Pengunduran Diri.png`, `Verifikasi Pengunduran Diri.png` | ✅ **Selesai** |
| **Tahap 4** | **Transaksi Multi-Simpanan Anggota** (`SimpananController`) | `Kelola Simpanan.png`, `Transaksi Baru.png` | ✅ **Selesai** |
| **Tahap 5** | **Pembiayaan Syariah, Agunan, Approval Kas & Realisasi** (`PembiayaanController`) | `Ajukan Pembiayaan — Pilih Akad.png`, `Ajukan Pembiayaan — Nominal & Tenor.png`, `Ajukan Pembiayaan — Agunan.png`, `Daftar Pembiayaan.png`, `Detail Pembiayaan.png`, `Persetujuan Kas.png`, `Konfirmasi Persetujuan.png` | ✅ **Selesai** |
| **Tahap 6** | **Rekap Potong Gaji (Tgl 24), Angsuran & Notifikasi** (`RekapNotifikasiController`) | `Kelola Angsuran.png`, `Rekap Potong Gaji.png`, `Notifikasi Tagihan.png` | ✅ **Selesai** |
| **Tahap 7** | **Kuitansi Digital, Laporan Keuangan (RAT) & Final QA** (`LaporanBuktiController`) | `Cetak Bukti Transaksi.png`, `Cetak Bukti Pembayaran.png`, `Laporan Keuangan.png` | ✅ **Selesai** |

---

## 📂 Struktur Sub-Direktori `05_Implementasi/`

```text
05_Implementasi/
├── backend/                             # Seluruh Kode Backend Django (MVT Logic, 16 Model, Test)
│   ├── koperasi/                        # Aplikasi Inti SI-KKPRIS
│   │   ├── controllers/
│   │   │   ├── auth_controller.py          # AuthController, RBAC & Dashboard Views (Tahap 2)
│   │   │   ├── anggota_controller.py       # AnggotaController & Kliring Resign Views (Tahap 3)
│   │   │   ├── simpanan_controller.py      # SimpananController & Mutasi 5 Skema Views (Tahap 4)
│   │   │   ├── pembiayaan_controller.py    # PembiayaanController, Agunan, Approval Kas & Realisasi (Tahap 5)
│   │   │   ├── rekap_notifikasi_controller.py # RekapNotifikasiController, Angsuran & WA/Email Tgl 10 (Tahap 6)
│   │   │   └── laporan_bukti_controller.py # LaporanKeuangan, LaporanBuktiController & AuditLog (Tahap 7)
│   │   ├── management/commands/
│   │   │   └── seed_master.py           # Seeder 5 Jenis Simpanan, 3 Akad & 3 Akun Peran
│   │   ├── migrations/
│   │   │   └── 0001_initial.py          # Migrasi 16 Model 3NF beserta Index & Constraint
│   │   ├── templatetags/
│   │   │   └── kkpris_tags.py           # Filter Format Mata Uang Rupiah Berbasis Decimal
│   │   ├── admin.py                     # Konfigurasi Admin & Proteksi Append-Only AuditLog
│   │   ├── models.py                    # 16 Model & Method Domain sesuai Class Diagram
│   │   ├── tests.py                     # Unit Test Integrasi 16 Model, RBAC & Frontend
│   │   └── urls.py                      # Routing URL Aplikasi Koperasi
│   ├── si_kkpris/                       # Konfigurasi Proyek Utama Django
│   │   ├── settings.py                  # Konfigurasi MySQL 8.4, RBAC, Session, Frontend & Media
│   │   ├── urls.py                      # Routing URL Utama
│   │   └── wsgi.py / asgi.py
│   ├── media/                           # Direktori Unggahan Berkas (Agunan, KTP, Bukti)
│   ├── .env.example                     # Contoh Konfigurasi Environment
│   ├── manage.py                        # Utilitas Manajemen Django
│   └── requirements.txt                 # Daftar Pustaka Python Terkunci
├── database/                            # Skema Basis Data SQL
│   └── 02_DDL_MySQL_SI-KKPRIS.sql       # Skema DDL 16 Tabel (3NF) MySQL 8.0+ InnoDB
├── frontend/                            # Seluruh Kode Antarmuka Pengguna (Templates & Assets)
│   ├── static/                          # Aset Statis (CSS, JS, Gambar)
│   │   ├── css/style.css                # Design System & Stylesheet Utama
│   │   ├── js/                          # Skrip Interaktif Frontend
│   │   └── img/                         # Aset Gambar & Ikon UI
│   └── templates/                       # Template Antarmuka HTML Django (22 Wireframe Final)
│       ├── base.html
│       ├── auth/login.html
│       ├── anggota/                     # Data Anggota, Form Anggota Baru, & Kliring Resign (Tahap 3)
│       ├── simpanan/                    # Kelola Simpanan, Transaksi Baru, & Simpanan Saya (Tahap 4)
│       ├── pembiayaan/                  # Wizard 3 Step Ajukan, Daftar, Detail, & Persetujuan Kas (Tahap 5)
│       ├── angsuran/                    # Kelola Angsuran, Cetak Bukti, Rekap Gaji Tgl 24 & Notifikasi Tgl 10 (Tahap 6)
│       ├── laporan/                     # Laporan Keuangan (Triwulanan & RAT), PDF & Audit Trail Log (Tahap 7)
│       └── dashboard/
├── venv/                                # Python Virtual Environment (Lokal, tidak di-commit)
└── README.md                            # Dokumentasi Panduan Folder Implementasi
```

---

## 🚀 Panduan Menjalankan Proyek Secara Lokal

1. **Aktifkan Virtual Environment & Masuk ke Direktori Backend:**
   ```powershell
   cd "05_Implementasi"
   .\venv\Scripts\Activate.ps1
   cd backend
   ```
2. **Periksa Konfigurasi, Migrasi & Seed Master Data:**
   ```powershell
   python manage.py check
   python manage.py migrate
   python manage.py seed_master
   ```
3. **Jalankan Unit Test (Model, RBAC & Integrasi Frontend):**
   ```powershell
   python manage.py test -v 2
   ```
   *(Atau dari folder `05_Implementasi/`: `python backend\manage.py test koperasi -v 2`)*
4. **Jalankan Server Pengembangan:**
   ```powershell
   python manage.py runserver
   ```

---

## 🔌 REST API & Autentikasi JWT (Tahap 9A)

Backend menyediakan REST API dengan prefix `/api/v1/` menggunakan **Django REST Framework**, **SimpleJWT** (*access token* 10 menit di body + *refresh token* 30 menit berotasi di cookie `httpOnly`, `SameSite=Strict`, `Path=/api/v1/auth/`), dan **drf-spectacular** (OpenAPI 3).

### Menjalankan Server API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py migrate
python manage.py seed_master --with-demo   # pastikan SEED_PASSWORD ada di backend/.env
python manage.py runserver
```

### Mengambil Token & Menggunakan Endpoint Autentikasi

1. **Login** (menerima `username` atau `no_anggota`, contoh `bendahara01` atau `KKP-2026-001`):
   ```powershell
   curl -i -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/login/ `
     -H "Content-Type: application/json" `
     -d '{"username":"bendahara01","password":"<SEED_PASSWORD>"}'
   ```
   Respons `200 OK` mengembalikan `access` dan objek `pengguna`, sekaligus menyetel cookie `kkpris_refresh` (`HttpOnly; SameSite=Strict; Path=/api/v1/auth/`).

2. **Ambil Profil Aktif (`/api/v1/auth/me/`):**
   ```powershell
   curl http://127.0.0.1:8000/api/v1/auth/me/ `
     -H "Authorization: Bearer <ACCESS_TOKEN>"
   ```

3. **Refresh Access Token (rotasi cookie & blacklist token lama):**
   ```powershell
   curl -i -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/refresh/
   ```

4. **Ganti Password:** `POST /api/v1/auth/ganti-password/` (`password_lama`, `password_baru`, `konfirmasi_password`) dengan header `Authorization: Bearer <ACCESS_TOKEN>`.

5. **Logout (blacklist refresh token & hapus cookie):**
   ```powershell
   curl -i -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/logout/
   ```

### Dokumentasi Swagger UI & Skema OpenAPI

- Atur `API_DOCS_ENABLED=True` pada `backend/.env` (hanya untuk pengembangan; baku `False` di produksi).
- **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
- **Skema OpenAPI mentah:** `http://127.0.0.1:8000/api/schema/`
- **Regenerasi berkas skema:**
  ```powershell
  python manage.py spectacular --file docs/openapi.yaml --validate
  ```
