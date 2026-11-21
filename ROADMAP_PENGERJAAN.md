# ROADMAP_PENGERJAAN.md — Urutan Kerja SI-KKPRIS (DRF + React + Vite + Tailwind)

Dokumen ini memberi tahu **prompt mana yang dipakai di langkah mana**, apa yang harus benar sebelum lanjut, dan cara memeriksanya. Ikuti berurutan.

## Aturan emas

1. **Satu prompt = satu sesi/percakapan baru di Antigravity.** Jangan menumpuk beberapa tahap dalam satu sesi.
2. **Jangan lanjut** ke langkah berikutnya sebelum semua kotak "Selesai bila" tercentang.
3. Sebelum setiap langkah: `git status` bersih (semua sudah di-commit). Setelah setiap langkah: baca ringkasan agent, jalankan perintah verifikasi **sendiri**, jangan hanya percaya laporan agent.
4. Gunakan mode perencanaan (jika tersedia) untuk **9A** dan **9B**, baca rencananya, baru setujui.
5. Jika agent mengusulkan sesuatu di luar prompt (fitur baru, mengubah aturan bisnis, menambah pustaka), jawab **tidak**. Minta dicatat sebagai temuan di log.
6. Jika tes gagal, perintahkan: _"Perbaiki penyebabnya. Jangan menghapus atau melemahkan tes."_
7. Ikuti kolom **Prompt** di tabel secara harfiah. Nama file prompt: `prompt_antigravity.md` (Tahap 8) dan `prompt_antigravity_v2.md` (Tahap 9 dan seterusnya).

---

## Langkah 0 — Persiapan (kamu sendiri, tanpa agent)

- [x] Letakkan `AGENTS.md` (v2) dan `PENDING_KONFIRMASI.md` di root repository; salin `ROADMAP_PENGERJAAN.md`, `prompt_antigravity.md`, `prompt_antigravity_v2.md` ke folder `docs/`. _(Catatan: prompt ada di `docs/`; roadmap tetap di root sesuai `AGENTS.md`.)_
- [x] Buat folder `docs/wireframe/` dan salin 22 PNG wireframe final ke sana (agent tidak dapat membaca folder di luar repository).
- [x] Pindahkan virtualenv ke `backend/.venv` (bagian "Virtualenv" di bawah) dan pastikan `.gitignore` sudah ada sebelum `git add` apa pun.
- [x] Buat/lengkapi `.gitignore` sesuai `AGENTS.md` Bagian 3.
- [x] Pasang Node.js LTS terbaru (`node -v` dan `npm -v` harus jalan).
- [x] Pasang skill (lihat bagian "Skill" di bawah).
- [ ] Kirim pertanyaan PND-01 sampai PND-04 ke Bu Eni, dan PND-12 ke pembimbing. **Tidak memblokir** pengerjaan.
- [x] Beri tag titik kembali: `git tag mvt-final` lalu `git push origin mvt-final`.
- [x] Pastikan MySQL (Laragon) berjalan dan `python manage.py test koperasi` lulus di laptopmu sebelum mulai.

---

## Tabel Urutan

| #   | Tahap         | Pekerjaan                                                          | Prompt yang dipakai                                                                                     | Selesai bila                                                                                                                                                                                                                                                                          |
| --- | ------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **8A**        | Tandai aturan PENDING, margin sementara ke konfigurasi, seed dummy | `prompt_antigravity.md` → **Prompt A** + tempelkan **Addendum Tahap 8** di akhir                        | Test lulus; `grep -rn "PENDING PND-" backend` menampilkan penanda; `.env.example` punya `MARGIN_PERSEN_SEMENTARA`                                                                                                                                                                     |
| 2   | **8B**        | Perbaikan teknis backend                                           | `prompt_antigravity.md` → **Prompt B** + **Addendum Tahap 8** (lewati Item 6)                           | Test lulus di MySQL; `grep -rn "float(" backend` kosong untuk uang; test invarian angsuran ada                                                                                                                                                                                        |
| 3   | **9A**        | Fondasi API: `Pengguna` custom, JWT, Swagger                       | `prompt_antigravity_v2.md` → **Prompt 9A**                                                              | `/api/docs/` terbuka; login, refresh, logout, me bekerja; test lama dan baru lulus                                                                                                                                                                                                    |
| 4   | **9B**        | Scaffold `web/`                                                    | **Prompt 9B**                                                                                           | `npm run lint && npm run typecheck && npm run test && npm run build` lulus; login halaman sederhana berhasil terhadap backend nyata                                                                                                                                                   |
| 5   | **9C**        | Design system, layout, 3 halaman                                   | **Prompt 9C**                                                                                           | Login, Dashboard, Beranda Anggota tampil benar di 375/768/1280 px; `docs/design-system.md` ada                                                                                                                                                                                        |
| ★   | **Gerbang 1** | Ukur dan putuskan                                                  | –                                                                                                       | Catat berapa hari Tahap 9A–9C memakan waktu. Tiap modul berikutnya (Tahap 10 sampai 14A, ada 6 pasang backend + frontend) kira-kira sebanding atau lebih besar (12A/12B paling berat). Jika perkiraannya melewati tenggat, hentikan di sini dan bicarakan dengan dosen sebelum lanjut |
| 6   | **10**        | Anggota & resign                                                   | **Blok Parameter Tahap 10** + **Template PM-BE**; lalu **Blok Parameter Tahap 10** + **Template PM-FE** | Halaman 4–7 jalan end-to-end                                                                                                                                                                                                                                                          |
| 7   | **11**        | Simpanan                                                           | Blok Tahap 11 + PM-BE; lalu Blok Tahap 11 + PM-FE                                                       | Halaman 8–9 jalan                                                                                                                                                                                                                                                                     |
| 8   | **12A**       | Pembiayaan: pengajuan                                              | Blok Tahap 12A + PM-BE; lalu + PM-FE                                                                    | Halaman 10–12 jalan; simulasi dari server                                                                                                                                                                                                                                             |
| 9   | **12B**       | Pembiayaan: persetujuan & realisasi                                | Blok Tahap 12B + PM-BE; lalu + PM-FE                                                                    | Halaman 13–16 jalan; _Two-Man Rule_ terbukti lewat test                                                                                                                                                                                                                               |
| 10  | **13**        | Angsuran, rekap, notifikasi                                        | Blok Tahap 13 + PM-BE; lalu + PM-FE                                                                     | Halaman 17–19 jalan; unduhan Excel/PDF berhasil                                                                                                                                                                                                                                       |
| 11  | **14A**       | Kuitansi, laporan, audit                                           | Blok Tahap 14A + PM-BE; lalu + PM-FE                                                                    | Halaman 20–22 + audit trail jalan                                                                                                                                                                                                                                                     |
| 12  | **14B**       | Finalisasi                                                         | **Prompt 14B**                                                                                          | 22 halaman paritas; build produksi jalan; MVT dihapus; Postman dan UAT siap                                                                                                                                                                                                           |

**Cara memakai Blok Parameter + Template:** dalam satu pesan, tempel **Blok Parameter** tahap itu paling atas, lalu **Template PM-BE** (atau PM-FE) di bawahnya. Backend dulu, selesaikan, verifikasi, baru frontend di sesi baru.

---

## Verifikasi per tahap (jalankan sendiri)

**Backend** (di `backend/`, `.venv` aktif):

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test koperasi
python manage.py spectacular --file docs/openapi.yaml   # tidak boleh error
```

**Frontend** (di `web/`):

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

**End-to-end manual (wajib tiap modul):** jalankan `python manage.py runserver` dan `npm run dev` bersamaan, masuk dengan akun seed untuk **tiap peran**, jalankan skenario di Blok Parameter, lalu coba sengaja melakukan aksi yang **tidak boleh** (peran salah, aksi ganda, input tidak valid).

---

## Jika sesuatu salah

| Gejala                             | Tindakan                                                                                                                                        |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Test gagal setelah agent selesai   | Sesi baru: "Jalankan test, perbaiki penyebab kegagalan, jangan ubah tes."                                                                       |
| Agent mengubah aturan bisnis       | `git restore` berkasnya; ulangi prompt dengan tambahan: "Jangan mengubah aturan bisnis; lihat AGENTS.md 4.G."                                   |
| Agent menambah pustaka tak diminta | Minta dicabut; `AGENTS.md` 4.B melarangnya.                                                                                                     |
| Hasil UI terlihat generik          | Tunjukkan Bagian 7 `AGENTS.md`; minta ulang halaman itu saja, sebut aturan yang dilanggar.                                                      |
| Tahap rusak parah                  | `git reset --hard` ke commit terakhir yang baik pada **cabang kerja** (bukan `main` bersama), atau kembali ke tag `mvt-final` untuk bagian MVT. |

---

## Skill yang disarankan

Skill Antigravity berada di `.agent/skills/` (per proyek) atau `~/.gemini/antigravity/skills/` (global). Pasang secukupnya; terlalu banyak skill membuat konteks agent berisik.

1. **`modern-web-guidance`** (GoogleChrome): praktik web modern, aksesibilitas, komponen native. Cara pasang ada di balasan chat.
2. **`web-design-guidelines`** (`vercel-labs/agent-skills`): audit UI (aksesibilitas, fokus, formulir, animasi, tipografi). Dipakai di akhir tiap halaman.
3. **`react-best-practices`** (`vercel-labs/agent-skills`): aturan performa React. Abaikan aturan khusus Next.js/server karena proyek ini SPA Vite.
4. Opsional: `frontend-design` dari repo `anthropics/skills`, untuk arah estetika yang tidak generik.

Pasang hanya dari repo resmi. Baca `SKILL.md` dan skrip di dalamnya sebelum memasang.

---

## Status pending yang bisa menunda modul

Modul tetap dikerjakan sesuai kondisi terkonfirmasi. Jika jawaban mitra datang kemudian:

- Ubah status di `PENDING_KONFIRMASI.md`.
- Buat tahap kecil "Penyesuaian PND-xx" lewat prompt singkat yang menyebut ID dan jawaban mitra. Jangan memakai prompt tahap besar untuk ini.

---

## Virtualenv

Lokasi yang dipakai: **`backend/.venv`**. Virtualenv tidak boleh dipindahkan atau disalin karena menyimpan path absolut; buat ulang:

```powershell
# opsional, dari venv lama: simpan daftar paket untuk dibandingkan dengan requirements.txt
.\venv\Scripts\Activate.ps1
pip freeze > freeze-lama.txt
deactivate

Remove-Item -Recurse -Force venv
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py check
```

Jika PowerShell menolak menjalankan skrip: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. Di editor, pilih interpreter `backend\.venv\Scripts\python.exe` bila tidak terdeteksi otomatis.
