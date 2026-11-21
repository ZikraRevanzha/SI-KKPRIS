-- ============================================================================
-- DDL MySQL 8.0+ (InnoDB) SI-KKPRIS: 16 Tabel Lengkap (3NF)
-- Menangani Temuan: T-01, T-02, T-08, T-09, T-11 serta Defect DEF-05 & DEF-06
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. TABEL: pengguna (Perubahan kolom peran menjadi ENUM - T-11, DEF-06; sinkron AbstractBaseUser + PermissionsMixin Tahap 9A)
CREATE TABLE `pengguna` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `password` VARCHAR(128) NOT NULL,
    `last_login` DATETIME NULL,
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
    `username` VARCHAR(50) NOT NULL,
    `nama_lengkap` VARCHAR(150) NOT NULL,
    `peran` ENUM('ANGGOTA', 'BENDAHARA', 'KETUA') NOT NULL DEFAULT 'ANGGOTA',
    `is_aktif` TINYINT(1) NOT NULL DEFAULT 1,
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pengguna_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. TABEL: anggota (Constraint UNIQUE pengguna_id 1:0..1, ENUM status, INT masa_dinas_tahun - T-11, DEF-05, DEF-06)
CREATE TABLE `anggota` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pengguna_id` BIGINT UNSIGNED NOT NULL,
    `no_anggota` VARCHAR(30) NOT NULL,
    `nik` VARCHAR(20) NOT NULL,
    `nama` VARCHAR(150) NOT NULL,
    `status_kepegawaian` ENUM('PNS', 'PPPK', 'HONORER', 'PENSIUNAN', 'PINDAH_TUGAS') NOT NULL,
    `masa_dinas_tahun` INT UNSIGNED NOT NULL DEFAULT 0,
    `no_hp` VARCHAR(20) NOT NULL,
    `tanggal_masuk` DATE NOT NULL,
    `tanggal_keluar` DATE NULL,
    `status` ENUM('AKTIF', 'PROSES_RESIGN', 'NON_AKTIF_KELUAR') NOT NULL DEFAULT 'AKTIF',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_anggota_pengguna_id` (`pengguna_id`),
    UNIQUE KEY `uk_anggota_no_anggota` (`no_anggota`),
    UNIQUE KEY `uk_anggota_nik` (`nik`),
    CONSTRAINT `fk_anggota_pengguna` FOREIGN KEY (`pengguna_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TABEL: jenis_simpanan (Penambahan kolom dapat_ditarik - T-09)
CREATE TABLE `jenis_simpanan` (
    `id` SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `kode` VARCHAR(20) NOT NULL,
    `nama` VARCHAR(100) NOT NULL,
    `nominal_default` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `is_wajib` TINYINT(1) NOT NULL DEFAULT 0,
    `is_periodik` TINYINT(1) NOT NULL DEFAULT 0,
    `dapat_ditarik` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0=Terkunci (Pokok/Wajib/Khusus), 1=Sukarela (Hari Raya/Berencana)',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_jenis_simpanan_kode` (`kode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. TABEL: transaksi_simpanan (Penambahan bendahara_id, no_kuitansi, metode_bayar - T-09, T-11)
CREATE TABLE `transaksi_simpanan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `anggota_id` BIGINT UNSIGNED NOT NULL,
    `jenis_simpanan_id` SMALLINT UNSIGNED NOT NULL,
    `bendahara_id` BIGINT UNSIGNED NOT NULL,
    `no_kuitansi` VARCHAR(40) NOT NULL,
    `tanggal_transaksi` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `jenis_transaksi` ENUM('SETOR', 'TARIK') NOT NULL,
    `metode_bayar` ENUM('TUNAI', 'TRANSFER', 'POTONG_GAJI') NOT NULL DEFAULT 'TUNAI',
    `nominal` DECIMAL(15,2) NOT NULL,
    `saldo_sesudah` DECIMAL(15,2) NOT NULL,
    `bukti_transaksi_url` VARCHAR(255) NULL,
    `keterangan` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_transaksi_simpanan_kuitansi` (`no_kuitansi`),
    KEY `idx_transaksi_simpanan_anggota` (`anggota_id`, `jenis_simpanan_id`),
    CONSTRAINT `fk_ts_anggota` FOREIGN KEY (`anggota_id`) REFERENCES `anggota` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_ts_jenis_simpanan` FOREIGN KEY (`jenis_simpanan_id`) REFERENCES `jenis_simpanan` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_ts_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. TABEL: jenis_akad (Standarisasi ENUM metode_margin & plafon_tanpa_agunan - T-11)
CREATE TABLE `jenis_akad` (
    `id` TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `kode` VARCHAR(20) NOT NULL,
    `nama` ENUM('MURABAHAH', 'IJARAH', 'HAWALAH') NOT NULL,
    `metode_margin` ENUM('FLAT') NOT NULL DEFAULT 'FLAT',
    `tenor_maks_bulan` SMALLINT UNSIGNED NOT NULL DEFAULT 72,
    `plafon_tanpa_agunan` DECIMAL(15,2) NOT NULL DEFAULT 70000000.00,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_jenis_akad_kode` (`kode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. TABEL: pembiayaan (Penghapusan agunan_url karena dipisah ke tabel agunan, penambahan no_antrean & tujuan_pembiayaan - T-08, T-11)
CREATE TABLE `pembiayaan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `no_pembiayaan` VARCHAR(40) NOT NULL,
    `anggota_id` BIGINT UNSIGNED NOT NULL,
    `jenis_akad_id` TINYINT UNSIGNED NOT NULL,
    `tanggal_pengajuan` DATE NOT NULL,
    `harga_pokok` DECIMAL(15,2) NOT NULL,
    `margin_persen` DECIMAL(5,2) NOT NULL,
    `total_margin` DECIMAL(15,2) NOT NULL,
    `total_kewajiban` DECIMAL(15,2) NOT NULL,
    `tenor_bulan` SMALLINT UNSIGNED NOT NULL,
    `angsuran_bulanan` DECIMAL(15,2) NOT NULL,
    `no_antrean` INT UNSIGNED NOT NULL,
    `tujuan_pembiayaan` VARCHAR(255) NOT NULL,
    `status` ENUM('MENUNGGU_VERIFIKASI', 'MENUNGGU_PERSETUJUAN_KETUA', 'DISETUJUI_KETUA', 'DITOLAK', 'AKTIF', 'LUNAS') NOT NULL DEFAULT 'MENUNGGU_VERIFIKASI',
    `tanggal_cair` DATE NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pembiayaan_nomor` (`no_pembiayaan`),
    KEY `idx_pembiayaan_anggota_status` (`anggota_id`, `status`),
    CONSTRAINT `fk_pembiayaan_anggota` FOREIGN KEY (`anggota_id`) REFERENCES `anggota` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_pembiayaan_akad` FOREIGN KEY (`jenis_akad_id`) REFERENCES `jenis_akad` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_tenor_maks` CHECK (`tenor_bulan` BETWEEN 1 AND 72)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. TABEL BARU: agunan (Relasi 1 Pembiayaan : 0..* Agunan untuk plafon lebih dari Rp70 Juta - T-01, T-08)
CREATE TABLE `agunan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pembiayaan_id` BIGINT UNSIGNED NOT NULL,
    `jenis_agunan` ENUM('BPKB_MOTOR', 'BPKB_MOBIL', 'SERTIFIKAT_TANAH_RUMAH', 'LAINNYA') NOT NULL,
    `no_registrasi` VARCHAR(100) NOT NULL,
    `nilai_taksiran` DECIMAL(15,2) NOT NULL,
    `berkas_url` VARCHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_agunan_pembiayaan` (`pembiayaan_id`),
    CONSTRAINT `fk_agunan_pembiayaan` FOREIGN KEY (`pembiayaan_id`) REFERENCES `pembiayaan` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. TABEL: persetujuan_pembiayaan (Perubahan level_persetujuan ke INT & keputusan ke ENUM - T-11, DEF-05, DEF-06)
CREATE TABLE `persetujuan_pembiayaan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pembiayaan_id` BIGINT UNSIGNED NOT NULL,
    `pejabat_id` BIGINT UNSIGNED NOT NULL,
    `level_persetujuan` INT UNSIGNED NOT NULL DEFAULT 1,
    `keputusan` ENUM('DISETUJUI', 'DITOLAK') NOT NULL,
    `catatan` VARCHAR(255) NULL,
    `waktu_keputusan` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_persetujuan_pembiayaan` (`pembiayaan_id`),
    CONSTRAINT `fk_persetujuan_pembiayaan` FOREIGN KEY (`pembiayaan_id`) REFERENCES `pembiayaan` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_persetujuan_pejabat` FOREIGN KEY (`pejabat_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. TABEL: realisasi_pencairan (Constraint UNIQUE pada pembiayaan_id untuk relasi 1:0..1 - T-08)
CREATE TABLE `realisasi_pencairan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pembiayaan_id` BIGINT UNSIGNED NOT NULL,
    `bendahara_id` BIGINT UNSIGNED NOT NULL,
    `tanggal_realisasi` DATE NOT NULL,
    `metode_pencairan` ENUM('TUNAI_KASIR', 'TRANSFER_BANK') NOT NULL,
    `nomor_referensi_bank` VARCHAR(100) NOT NULL,
    `nominal_cair` DECIMAL(15,2) NOT NULL,
    `bukti_transfer_url` VARCHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_realisasi_pembiayaan_id` (`pembiayaan_id`),
    CONSTRAINT `fk_realisasi_pembiayaan` FOREIGN KEY (`pembiayaan_id`) REFERENCES `pembiayaan` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_realisasi_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. TABEL: jadwal_angsuran (Perubahan status_bayar dan cara_bayar ke ENUM - T-11, DEF-06)
CREATE TABLE `jadwal_angsuran` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pembiayaan_id` BIGINT UNSIGNED NOT NULL,
    `angsuran_ke` SMALLINT UNSIGNED NOT NULL,
    `jatuh_tempo` DATE NOT NULL,
    `porsi_pokok` DECIMAL(15,2) NOT NULL,
    `porsi_margin` DECIMAL(15,2) NOT NULL,
    `jumlah_angsuran` DECIMAL(15,2) NOT NULL,
    `status_bayar` ENUM('BELUM_LUNAS', 'LUNAS') NOT NULL DEFAULT 'BELUM_LUNAS',
    `tanggal_bayar` DATE NULL,
    `cara_bayar` ENUM('POTONG_GAJI', 'TUNAI', 'TRANSFER') NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_jadwal_pembiayaan_ke` (`pembiayaan_id`, `angsuran_ke`),
    KEY `idx_jadwal_jatuh_tempo_status` (`jatuh_tempo`, `status_bayar`),
    CONSTRAINT `fk_jadwal_pembiayaan` FOREIGN KEY (`pembiayaan_id`) REFERENCES `pembiayaan` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. TABEL BARU: rekap_potong_gaji (Header rekapitulasi bulanan - T-01, T-02)
CREATE TABLE `rekap_potong_gaji` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `bendahara_id` BIGINT UNSIGNED NOT NULL,
    `kode_rekap` VARCHAR(40) NOT NULL,
    `periode_bulan` VARCHAR(7) NOT NULL COMMENT 'Format YYYY-MM',
    `tanggal_cut_off` DATE NOT NULL,
    `total_simpanan_wajib` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `total_angsuran` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `total_tagihan` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `status_rekap` ENUM('DRAFT', 'DIKUNCI', 'LUNAS_KOLEKTIF') NOT NULL DEFAULT 'DIKUNCI',
    `tanggal_lunas_kolektif` DATE NULL,
    `nomor_referensi_transfer` VARCHAR(100) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_rekap_kode` (`kode_rekap`),
    UNIQUE KEY `uk_rekap_periode` (`periode_bulan`),
    CONSTRAINT `fk_rekap_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. TABEL BARU: detail_rekap_potong_gaji (Rincian potong gaji per anggota memenuhi 3NF - T-01, T-02)
CREATE TABLE `detail_rekap_potong_gaji` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rekap_potong_gaji_id` BIGINT UNSIGNED NOT NULL,
    `anggota_id` BIGINT UNSIGNED NOT NULL,
    `jadwal_angsuran_id` BIGINT UNSIGNED NULL COMMENT 'NULL jika anggota tidak memiliki cicilan pembiayaan aktif',
    `nominal_simpanan_wajib` DECIMAL(15,2) NOT NULL DEFAULT 150000.00,
    `nominal_simpanan_sukarela` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `nominal_angsuran` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `subtotal_potongan` DECIMAL(15,2) NOT NULL,
    `status_potongan` ENUM('TERTAGIH', 'TERPOTONG_LUNAS', 'SELISIH_TUNGGAKAN') NOT NULL DEFAULT 'TERTAGIH',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_detail_rekap_anggota_jadwal` (`rekap_potong_gaji_id`, `anggota_id`, `jadwal_angsuran_id`),
    CONSTRAINT `fk_detail_rekap_header` FOREIGN KEY (`rekap_potong_gaji_id`) REFERENCES `rekap_potong_gaji` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_detail_rekap_anggota` FOREIGN KEY (`anggota_id`) REFERENCES `anggota` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_detail_rekap_jadwal` FOREIGN KEY (`jadwal_angsuran_id`) REFERENCES `jadwal_angsuran` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. TABEL BARU: pembayaran_angsuran (Pencatatan kuitansi bayar cicilan mandiri/kolektif - T-01, T-11)
CREATE TABLE `pembayaran_angsuran` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `jadwal_angsuran_id` BIGINT UNSIGNED NOT NULL,
    `bendahara_id` BIGINT UNSIGNED NOT NULL,
    `rekap_potong_gaji_id` BIGINT UNSIGNED NULL COMMENT 'Terisi jika dilunasi melalui batch potong gaji',
    `no_kuitansi` VARCHAR(40) NOT NULL,
    `tanggal_bayar` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `nominal_bayar` DECIMAL(15,2) NOT NULL,
    `potongan_margin` DECIMAL(15,2) NOT NULL DEFAULT 0.00 COMMENT 'Muqashah / potongan margin jika pelunasan dipercepat',
    `metode_bayar` ENUM('POTONG_GAJI', 'TUNAI', 'TRANSFER') NOT NULL,
    `nomor_referensi` VARCHAR(100) NULL,
    `bukti_bayar_url` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pembayaran_angsuran_kuitansi` (`no_kuitansi`),
    KEY `idx_pembayaran_jadwal` (`jadwal_angsuran_id`),
    CONSTRAINT `fk_bayar_jadwal` FOREIGN KEY (`jadwal_angsuran_id`) REFERENCES `jadwal_angsuran` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_bayar_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_bayar_rekap` FOREIGN KEY (`rekap_potong_gaji_id`) REFERENCES `rekap_potong_gaji` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. TABEL BARU: notifikasi_tagihan (Log pengiriman WA/Email pengingat tanggal 10 - T-01, UC-14)
CREATE TABLE `notifikasi_tagihan` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `anggota_id` BIGINT UNSIGNED NOT NULL,
    `jadwal_angsuran_id` BIGINT UNSIGNED NOT NULL,
    `bendahara_id` BIGINT UNSIGNED NOT NULL,
    `kanal_kirim` ENUM('WHATSAPP', 'EMAIL') NOT NULL DEFAULT 'WHATSAPP',
    `tujuan_kirim` VARCHAR(100) NOT NULL,
    `isi_pesan` VARCHAR(500) NOT NULL,
    `status_kirim` ENUM('ANTREAN', 'TERKIRIM', 'GAGAL') NOT NULL DEFAULT 'ANTREAN',
    `waktu_kirim` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_notifikasi_anggota_jadwal` (`anggota_id`, `jadwal_angsuran_id`),
    CONSTRAINT `fk_notif_anggota` FOREIGN KEY (`anggota_id`) REFERENCES `anggota` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_notif_jadwal` FOREIGN KEY (`jadwal_angsuran_id`) REFERENCES `jadwal_angsuran` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_notif_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. TABEL: pengunduran_diri (Relasi 1:N dari anggota, penambahan surat_permohonan_url, selisih_akhir, berita_acara_url - T-08, T-11)
CREATE TABLE `pengunduran_diri` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `anggota_id` BIGINT UNSIGNED NOT NULL,
    `bendahara_id` BIGINT UNSIGNED NULL COMMENT 'Terisi saat diverifikasi oleh Bendahara',
    `tanggal_pengajuan` DATE NOT NULL,
    `alasan_keluar` VARCHAR(255) NOT NULL,
    `surat_permohonan_url` VARCHAR(255) NOT NULL,
    `total_hak_simpanan` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `total_kewajiban_pembiayaan` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `selisih_akhir` DECIMAL(15,2) NOT NULL DEFAULT 0.00 COMMENT 'Positif=Pengembalian ke Anggota, Negatif=Wajib Setor Pelunasan',
    `status_kliring` ENUM('BELUM_DIHITUNG', 'HAK_PENGEMBALIAN', 'WAJIB_SETOR_PELUNASAN', 'SELESAI_KLIRING') NOT NULL DEFAULT 'BELUM_DIHITUNG',
    `status_pengajuan` ENUM('MENUNGGU_VERIFIKASI', 'DISETUJUI_KELUAR', 'DITOLAK') NOT NULL DEFAULT 'MENUNGGU_VERIFIKASI',
    `berita_acara_url` VARCHAR(255) NULL,
    `tanggal_keputusan` DATE NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_pengunduran_anggota` (`anggota_id`, `status_pengajuan`),
    CONSTRAINT `fk_resign_anggota` FOREIGN KEY (`anggota_id`) REFERENCES `anggota` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_resign_bendahara` FOREIGN KEY (`bendahara_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. TABEL: audit_trail_log (Jejak audit keamanan sistem - DEF-06)
CREATE TABLE `audit_trail_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pengguna_id` BIGINT UNSIGNED NOT NULL,
    `aksi` VARCHAR(100) NOT NULL,
    `nama_tabel` VARCHAR(64) NOT NULL,
    `record_id` BIGINT UNSIGNED NOT NULL,
    `detail_perubahan` VARCHAR(500) NOT NULL,
    `ip_address` VARCHAR(45) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_audit_pengguna_waktu` (`pengguna_id`, `created_at`),
    CONSTRAINT `fk_audit_pengguna` FOREIGN KEY (`pengguna_id`) REFERENCES `pengguna` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

