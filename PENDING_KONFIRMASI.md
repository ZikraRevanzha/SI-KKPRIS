# PENDING_KONFIRMASI.md — Registri Aturan yang Belum Terkonfirmasi

Dokumen ini mencegah angka atau aturan karangan masuk ke sistem. Tiap butir berisi pertanyaan yang siap dikirim ke narasumber, dampaknya di kode, dan perilaku sementara.

**Cara pakai**

- Agent: jangan memberi nilai bawaan diam-diam. Tandai kode dengan `# PENDING PND-xx`.
- Pengguna: kirim pertanyaan ke narasumber, lalu isi bagian **Jawaban** dan ubah status.
- Status: ⏳ belum dijawab · ✅ terjawab (isi jawaban dan tanggal) · ❌ ditolak/tidak berlaku.

---

## A. Untuk Mitra (Eni Mailiza, S.ST, M.Pd.E — Bendahara KKPRIS)

### PND-01 — Besaran margin dan satuannya

- **Pertanyaan:** "Bu, besaran margin/ujrah pembiayaan di KKPRIS berapa persen? Dihitung per bulan, per tahun, atau total dari awal? Apakah sama untuk Murabahah, Ijarah, dan Hawalah? Apakah berbeda menurut tenor atau besar pembiayaan?"
- **Dampak di kode:** `Pembiayaan.hitungSimulasiMarginFlat` (`models.py`), `DEFAULT_MARGIN_PERSEN` (`pembiayaan_controller.py`), `seed_master.py`, halaman simulasi.
- **Perilaku sementara:** nilai contoh dari konfigurasi, ditandai banner "belum dikonfirmasi".
- **Status:** ⏳ · **Jawaban:** —

### PND-02 — Perlakuan Hawalah

- **Pertanyaan:** "Untuk Hawalah, utang apa yang dialihkan dan bagaimana alurnya di KKPRIS (mohon contoh kasus nyata)? Apakah koperasi mengambil margin, atau hanya biaya jasa? Bagaimana cara menghitungnya?"
- **Dampak di kode:** Hawalah saat ini memakai rumus margin flat yang sama dengan akad lain.
- **Perilaku sementara:** rumus tidak diubah, hanya ditandai pending.
- **Status:** ⏳ · **Jawaban:** —

### PND-03 — Alur nyata Murabahah dan Ijarah

- **Pertanyaan:** "Contoh transaksi nyata: untuk Murabahah, barang apa yang dibiayai, dan apakah koperasi membeli barang dulu atau dana diserahkan ke anggota? Untuk Ijarah, jasa atau manfaat apa yang disewa/dibiayai?"
- **Dampak di kode:** arti `harga_pokok` dan `tujuan_pembiayaan`, validasi per akad, halaman "Pilih Akad".
- **Status:** ⏳ · **Jawaban:** —

### PND-04 — Limit pembiayaan per anggota

- **Pertanyaan:** "Pada wawancara disebutkan limit pembiayaan berbeda antar anggota berdasarkan besar simpanan, masa dinas, dan cara bayar. Bagaimana rumus atau tabelnya? Bolehkah satu anggota punya lebih dari satu pembiayaan aktif? Batas Rp70 juta itu per pengajuan atau total semua pembiayaan yang masih berjalan?"
- **Dampak di kode:** belum ada validasi limit per anggota pada pengajuan.
- **Status:** ⏳ · **Jawaban:** —

### PND-05 — Agunan

- **Pertanyaan:** "Jenis agunan apa saja yang diterima (BPKB motor/mobil, sertifikat, lainnya)? Nilai taksiran minimal berapa dibanding pembiayaan? Adakah batas maksimum pembiayaan meski ada agunan?"
- **Dampak di kode:** model `Agunan`, `JenisAgunanChoices`, validasi pokok > Rp70 juta.
- **Status:** ⏳ · **Jawaban:** —

### PND-06 — Pembulatan angsuran

- **Pertanyaan:** "Angsuran dibulatkan ke berapa (rupiah penuh, ratusan, ribuan)? Selisih pembulatan dibebankan ke angsuran terakhir atau dengan cara lain?"
- **Dampak di kode:** perhitungan angsuran bulanan dan angsuran terakhir.
- **Perilaku sementara:** dua desimal, sisa diserap angsuran terakhir.
- **Status:** ⏳ · **Jawaban:** —

### PND-07 — Awal angsuran

- **Pertanyaan:** "Jika pembiayaan cair pada tanggal tertentu, angsuran pertama dipotong dari gaji bulan apa? Bagaimana jika cair setelah tanggal 24?"
- **Dampak di kode:** `JadwalAngsuran.generateJadwalAngsuran` (saat ini: bulan berikutnya, tanggal 24).
- **Status:** ⏳ · **Jawaban:** —

### PND-08 — Pelunasan dipercepat

- **Pertanyaan:** "Jika anggota melunasi lebih cepat, apakah margin sisa tetap dibayar penuh, dikurangi, atau diberi potongan? Bagaimana ketentuannya?"
- **Dampak di kode:** kolom `PembayaranAngsuran.potongan_margin`. Periksa dulu apakah aturan ini memang tertulis di SRS; bila tidak, jangan dihapus, catat sebagai temuan.
- **Status:** ⏳ · **Jawaban:** —

### PND-09 — Laporan tahunan (SHU, neraca, arus kas)

- **Pertanyaan:** "Rumus pembagian SHU menurut AD/ART KKPRIS bagaimana (persentase cadangan, jasa simpanan, jasa transaksi, pengurus, dan lainnya)? Format neraca dan arus kas apa yang dipakai? Apakah ada daftar akun tertulis?"
- **Dampak di kode:** `LaporanKeuangan` dan `laporan_bukti_controller.py` (terkait TBD-05 di SRS).
- **Status:** ⏳ · **Jawaban:** —

### PND-10 — Notifikasi tanggal 10

- **Pertanyaan:** "Pengingat tanggal 10 dikirim lewat WhatsApp, email, atau keduanya? Dikirim manual oleh bendahara atau otomatis? Apakah nomor WA/email anggota sudah terkumpul? Seperti apa format pesannya?"
- **Dampak di kode:** `NotifikasiTagihan`, pilihan kanal, isi pesan.
- **Status:** ⏳ · **Jawaban:** —

---

## B. Untuk Pembimbing

### PND-11 — Arsitektur aplikasi

- **Pertanyaan:** "Apakah penilaian mata kuliah mensyaratkan arsitektur client-server dengan REST API terpisah (React + DRF)? Apakah Postman dan Swagger tetap wajib sebagai deliverable? Jika implementasi memakai Django Template (MVT) dengan Charter dan SRS direvisi, apakah dapat diterima?"
- **Dampak:** menentukan roadmap Tahap 9–14.
- **Status:** ✅ Diputuskan pengguna (18 Nov 2026): Django REST Framework + React + Vite + Tailwind, sesuai Charter. Konfirmasi ke pembimbing tetap disarankan, tetapi tidak memblokir pengerjaan. · **Jawaban:** —

### PND-12 — Validasi kepatuhan syariah

- **Pertanyaan:** "Mohon validasi rumus margin flat untuk Murabahah dan Ijarah serta perlakuan Hawalah dengan acuan fatwa DSN-MUI yang relevan, sebelum dipakai di laporan akhir."
- **Dampak:** `PND-01` dan `PND-02`; mitigasi risiko pada Project Charter.
- **Status:** ⏳ · **Jawaban:** —

---

## C. Riwayat Jawaban

_(Isi ringkasan jawaban beserta tanggal di sini setelah ada konfirmasi.)_
