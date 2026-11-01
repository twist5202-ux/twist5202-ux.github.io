# [HIGH] Dekripsi Dokumen Konfidensial — RSA Tanpa Padding (Brute Force)

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (instance lokal — lab latihan)
**Endpoint:** `/ftp/announcement_encrypted.md` + `/ftp/encrypt.pyc`
**Tanggal:** 9 Oktober 2026
**Peneliti:** Twist
**Severity:** HIGH (Sensitive Data Exposure / Cryptographic Issues)

---

## 1. Ringkasan

File `/ftp/encrypt.pyc` berisi skrip enkripsi yang membocorkan **algoritma + kunci
publik RSA** yang dipakai untuk melindungi `announcement_encrypted.md`.

Karena enkripsi dilakukan **tanpa padding** dan setiap karakter dienkripsi
terpisah (`m` selalu < 256), penyerang bisa **brute-force 256 kandidat per
karakter** — tidak perlu memfaktorkan modulus RSA yang 1024-bit.

**Hasil: seluruh 1.194 karakter dokumen konfidensial berhasil didekripsi (0 gagal).**

---

## 2. Dampak

| Aspek | Detail |
|---|---|
| Autentikasi | **Tidak butuh** — file di direktori publik `/ftp` |
| Kendala kriptografi | **NOL** — tidak perlu faktorisasi RSA |
| Waktu serangan | **< 1 detik** untuk 1.194 karakter |
| Data terungkap | Dokumen konfidensial "Major Announcement — Token Sale / ICO" |

Prinsip yang dilanggar: **prinsip Kerckhoffs** — keamanan harus bergantung pada
kunci privat, bukan pada kerahasiaan algoritma. Di sini algoritmanya bocor
(`encrypt.pyc`), skema enkripsinya cacat, dan hasilnya = dokumen terbuka.

---

## 3. Langkah Reproduksi

### Bukti 1 — Ambil file terenkripsi dan skrip enkripsi

```http
GET /ftp/announcement_encrypted.md HTTP/1.1     → 200, 369.237 byte
GET /ftp/encrypt.pyc%2500.md HTTP/1.1          → 200, 573 byte  (bypass filter, lihat §3 dok 002)
```

File `encrypt.pyc` diblok filter ekstensi → di-bypass pakai null byte
(`%2500`). Detail tekniknya ada di `002-juice-shop-full-recon.md` §3.

### Bukti 2 — Dekompilasi `encrypt.pyc`

```bash
pip install uncompyle6
python -c "from uncompyle6 import decompile_file; import io,sys; \
  b=io.StringIO(); decompile_file('encrypt.pyc', b); print(b.getvalue())"
```

**Hasil dekompilasi (`encrypt.py`):**

```python
confidential_document = open('announcement.md', 'r')
N = 14590676800758332323018693934907063529240187237535716439958187101987
    34387990053589383695714026701498021218180862924674228281570229220767
    46906543401224889672472407926969987100581290103199317858753663710862
    35765651050788371429711563734278891146353510271203276516651841172685
    9837988672111837205085526346618740053
e = 65537
encrypted_document = open('announcement_encrypted.md', 'w')
for char in confidential_document.read():
    encrypted_document.write(str(pow(ord(char), e, N)) + '\n')
encrypted_document.close()
```

**Analisis:**
```
N = 1024-bit (309 digit)
e = 65537
Cipher: c_i = ord(char_i)^e mod N   ← PER KARAKTER, TANPA PADDING
```

### Bukti 3 — Identifikasi kelemahan

```
Ukuran ciphertext  : 1.194 angka  → 1.194 karakter plaintext
Range nilai        : semua < N (1024-bit)
Rata-rata bit      : 1022,6

Kelemahan kritis:
  plaintext = ord(char) → selalu < 256
  → ruang pencarian cuma 256 kemungkinan per karakter
  → brute-force = 256 eksponensiasi modular
```

### Bukti 4 — Serangan: RSA no-padding brute force

```python
N = 14590676800758332323018693934907063529240187237535716439958187101987...
e = 65537

# tabel lookup: 256 kemungkinan saja
tabel = {}
for m in range(256):
    tabel[pow(m, e, N)] = m     # c : m

# dekripsi
vals = [int(x) for x in open('announcement_encrypted.md').read().split()]
plain = "".join(chr(tabel[c]) for c in vals if c in tabel)
```

**Hasil eksekusi:**
```
tabel lookup : 256 entri, 0.0s
ciphertext   : 1.194 angka
dekripsi     : 0.0s
gagal        : 0
```

### Bukti 5 — Isi dokumen terdekripsi

```
Major Announcement:

Token Sale - Initial Coin Offering

Lorem ipsum dolor sit amet, consetetur sadipscing elitr, ...

URL: /#/tokensale-ico-ea

[...]
```

**1.194 karakter, 100% terdekripsi, nol karakter gagal.**

### Catatan — Jebakan yang Ditemukan

GitHub issue Juice Shop [#1392](https://github.com/juice-shop/juice-shop/issues/1392)
melaporkan bahwa **nilai N di dalam .pyc berbeda** dari N yang dipakai untuk
mengenkripsi file. Artinya:

```
✗ Faktorisasi N       → sia-sia (N tidak sesuai / tidak bisa difaktorkan)
✗ Menghitung d        → tidak mungkin tanpa p, q
✅ BRUTE FORCE 256    → JALAN, karena tidak butuh N yang benar untuk
                        SEMUA kandidat — cukup cari m yang menghasilkan c
```

Pelajaran: **selalu serang kelemahan skema, bukan kelemahan kunci.**
1024-bit RSA itu kuat — tapi RSA **tanpa padding** untuk pesan 1 byte tidak.

---

## 4. Akar Masalah

Tiga kesalahan berlapis:

**1. Skrip enkripsi disimpan di direktori publik**
`encrypt.pyc` ada di `/ftp` — menyerahkan algoritma ke penyerang (langgar Kerckhoffs).

**2. RSA tanpa padding (textbook RSA)**
```python
# SALAH — textbook RSA
encrypted_document.write(str(pow(ord(char), e, N)) + '\n')

# BENAR — pakai OAEP padding + enkripsi per-blok
from Crypto.Cipher import PKCS1_OAEP
cipher = PKCS1_OAEP.new(public_key)
encrypted = cipher.encrypt(data)   # pesan utuh, bukan per karakter
```

**3. Enkripsi per karakter**
Membuat ruang pencarian jadi 256. Bahkan dengan padding, mengenkripsi
per karakter itu pola yang buruk.

---

## 5. Saran Perbaikan

**1. Hapus skrip enkripsi dari direktori publik**
```bash
# encrypt.pyc TIDAK BOLEH ada di /ftp — pindah ke luar document root
```

**2. Ganti ke RSA dengan OAEP + enkripsi per-blok**
```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

key = RSA.import_key(open('private.pem').read())
cipher = PKCS1_OAEP.new(key)
with open('announcement.md','rb') as f:
    data = f.read()
ct = cipher.encrypt(data)          # enkripsi utuh, ada padding
```

**3. Jangan pakai RSA untuk data besar**
RSA cuma untuk enkripsi kunci. Untuk file pakai hybrid:
```python
# RSA untuk membungkus kunci AES, AES untuk file
aes_key = os.urandom(32)
ct_file = AESGCM(aes_key).encrypt(nonce, data, None)
ct_key  = PKCS1_OAEP.new(rsa_pub).encrypt(aes_key)
```

**4. Matikan directory listing `serve-index` di `/ftp`**
Lihat `002-juice-shop-full-recon.md` §2.

**5. Audit ulang berkas di direktori publik**
Hapus/relokasi semua `.bak`, `.pyc`, `.kdbx`, `.yml`, `.json` dari sana.

---

## 6. Lampiran — Bukti

```
Dekompilasi : encrypt.pyc → RSA textbook, N=1024-bit, e=65537
Plaintext   : loot/announcement_DECRYPTED.md  (1.194 karakter)
Ciphertext  : loot/announcement_encrypted.md  (369.237 byte, 1.194 angka)
Skrip       : loot2/encrypt.pyc               (573 byte)
Referensi   : GitHub juice-shop/juice-shop issue #1392
```

---

## 7. Yang Belum Selesai (jujur)

```
✗ coupons_2013.md.bak (142 byte, 12 baris × 10 char)
  → Bukan RSA (angkanya bukan numerik besar)
  → Bukan XOR/ADD/substitusi 1-byte (skor maksimum 0.883, tidak bersih)
  → Pos 0 nilai {k,l,m,n,o,p,q} BERURUTAN di ASCII → ada pola ADD
  → Tapi 1-byte shift tidak menghasilkan kupon bersih
  → Butuh decrypt.py (versi asli) untuk membalik algoritmanya
  → STATUS: BELUM TERPECAHKAN
```
