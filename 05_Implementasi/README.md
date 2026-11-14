# 05_Implementasi — Source Code Aplikasi SI-KKPRIS

Folder ini merupakan direktori utama tahap **Implementasi (Konstruksi Perangkat Lunak)** untuk **Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)** pada Koperasi Guru & Karyawan (KKPRIS) SMK Negeri 1 Kota Solok.

---

## 🛠️ Spesifikasi Teknis Implementasi

| Komponen | Teknologi / Versi | Keterangan |
| :--- | :--- | :--- |
| **Bahasa Pemrograman** | Python 3.11+ (Lokal: Python 3.13) | Backend utama aplikasi |
| **Web Framework** | Django 4.2+ LTS / 5.x | Arsitektur MVT (*Model-View-Template*) |
| **Database RDBMS** | MySQL 8.0+ (`InnoDB`) | Laragon MySQL 8.4 (`utf8mb4_unicode_ci`) |
| **Tipe Data Moneter** | `DECIMAL(15,2)` / `DecimalField` | Bebas *floating-point roundoff error* |
| **Ekspor Dokumen** | `openpyxl` & `xhtml2pdf` / `reportlab` | Cetak Kuitansi PDF & Ekspor Rekap Gaji `.xlsx` |

---

## 📂 Struktur Sub-Direktori `05_Implementasi/`

```text
05_Implementasi/
├── database/
│   └── 02_DDL_MySQL_SI-KKPRIS.sql   # Skema DDL 16 Tabel (3NF) MySQL 8.0+ InnoDB
└── README.md                        # Dokumentasi panduan folder implementasi
```

*(Folder proyek Django dan virtual environment `venv` akan diinisialisasi di dalam direktori ini pada tahapan coding modul).*
