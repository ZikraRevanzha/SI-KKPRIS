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

## 📂 Struktur Sub-Direktori `05_Implementasi/`

```text
05_Implementasi/
├── database/
│   └── 02_DDL_MySQL_SI-KKPRIS.sql       # Skema DDL 16 Tabel (3NF) MySQL 8.0+ InnoDB
├── koperasi/                            # Aplikasi Inti SI-KKPRIS
│   ├── management/commands/
│   │   └── seed_master.py               # Seeder 5 Jenis Simpanan, 3 Akad & 3 Akun Peran
│   ├── migrations/
│   │   └── 0001_initial.py              # Migrasi 16 Model 3NF beserta Index & Constraint
│   ├── admin.py                         # Konfigurasi Admin & Proteksi Append-Only AuditLog
│   ├── models.py                        # 16 Model & Method Domain sesuai Class Diagram
│   └── tests.py                         # Unit Test Integrasi 16 Model & Aturan Bisnis
├── si_kkpris/                           # Konfigurasi Proyek Utama Django
│   ├── settings.py                      # Konfigurasi MySQL 8.4, RBAC, Session & Media
│   ├── urls.py                          # Routing URL Utama
│   └── wsgi.py / asgi.py
├── media/                               # Direktori Unggahan Berkas (Agunan, KTP, Bukti)
├── static/                              # Aset Statis (CSS, JS, Gambar)
├── templates/                           # Template Antarmuka HTML Django
├── .env.example                         # Contoh Konfigurasi Environment
├── manage.py                            # Utilitas Manajemen Django
├── requirements.txt                     # Daftar Pustaka Python Terkunci
└── README.md                            # Dokumentasi Panduan Folder Implementasi
```

---

## 🚀 Panduan Menjalankan Proyek Secara Lokal

1. **Aktifkan Virtual Environment:**
   ```powershell
   cd "05_Implementasi"
   .\venv\Scripts\Activate.ps1
   ```
2. **Jalankan Migrasi & Seed Master Data:**
   ```powershell
   python manage.py migrate
   python manage.py seed_master
   ```
3. **Jalankan Unit Test 16 Model:**
   ```powershell
   python manage.py test -v 2
   ```
4. **Jalankan Server Pengembangan:**
   ```powershell
   python manage.py runserver
   ```
