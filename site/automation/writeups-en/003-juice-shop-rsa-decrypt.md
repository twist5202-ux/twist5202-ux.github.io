# [HIGH] Decrypting a Confidential Document — Unpadded RSA Broken by Brute Force

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (local instance — training lab)
**Endpoints:** `/ftp/announcement_encrypted.md` + `/ftp/encrypt.pyc`
**Date:** 9 October 2026
**Researcher:** Twist
**Severity:** HIGH (Sensitive Data Exposure / Cryptographic Issues)

---

## 1. Summary

The file `/ftp/encrypt.pyc` contains the encryption script that leaks the
**algorithm and RSA public key** protecting `announcement_encrypted.md`.

Because encryption is performed **without padding** and each character is
encrypted individually (so the message `m` is always < 256), an attacker can
**brute-force 256 candidates per character** — the 1024-bit modulus never needs
to be factored.

**Result: all 1,194 characters of the confidential document were recovered,
zero failures.**

---

## 2. Impact

| Aspect | Detail |
|---|---|
| Authentication | **Not required** — the file sits in a public directory |
| Cryptographic barrier | **None** — no RSA factorisation needed |
| Attack time | **Under 1 second** for 1,194 characters |
| Data recovered | Confidential "Major Announcement — Token Sale / ICO" document |

The violated principle is **Kerckhoffs's principle**: security must rest on the
key, not on the secrecy of the algorithm. Here the algorithm leaked
(`encrypt.pyc`), the encryption scheme was flawed, and the outcome was a
plaintext document.

---

## 3. Reproduction Steps

### Evidence 1 — Retrieve the encrypted file and the script

```http
GET /ftp/announcement_encrypted.md HTTP/1.1     → 200, 369,237 bytes
GET /ftp/encrypt.pyc%2500.md HTTP/1.1          → 200, 573 bytes  (filter bypass, see write-up 002 §3)
```

`encrypt.pyc` was blocked by the extension filter and retrieved via a
double-encoded null byte. The technique is documented in write-up 002 §3.

### Evidence 2 — Decompile `encrypt.pyc`

```bash
pip install uncompyle6
python -c "from uncompyle6 import decompile_file; import io; \
  b=io.StringIO(); decompile_file('encrypt.pyc', b); print(b.getvalue())"
```

**Decompiled `encrypt.py`:**

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

**Analysis:**

```
N = 1024-bit (309 digits)
e = 65537
Cipher: c_i = ord(char_i)^e mod N   ← PER CHARACTER, NO PADDING
```

### Evidence 3 — Identify the weakness

```
Ciphertext size : 1,194 numbers  → 1,194 plaintext characters
Value range     : all < N (1024-bit)
Average bits    : 1,022.6

Critical weakness:
  plaintext = ord(char) → always < 256
  → search space is only 256 possibilities per character
  → brute force = 256 modular exponentiations
```

### Evidence 4 — The attack: unpadded RSA brute force

```python
N = 14590676800758332323018693934907063529240187237535716439958187101987...
e = 65537

# lookup table: only 256 possibilities
tabel = {}
for m in range(256):
    tabel[pow(m, e, N)] = m     # c : m

# decrypt
vals = [int(x) for x in open('announcement_encrypted.md').read().split()]
plain = "".join(chr(tabel[c]) for c in vals if c in tabel)
```

**Execution result:**

```
lookup table : 256 entries, 0.0s
ciphertext   : 1,194 numbers
decryption   : 0.0s
failures     : 0
```

### Evidence 5 — Recovered document

```
Major Announcement:

Token Sale - Initial Coin Offering

Lorem ipsum dolor sit amet, consetetur sadipscing elitr, ...

URL: /#/tokensale-ico-ea

[...]
```

**1,194 characters, 100% decrypted, zero failures.**

### Note — The Trap

GitHub issue [#1392](https://github.com/juice-shop/juice-shop/issues/1392)
reports that the **N value in the .pyc differs** from the N used to encrypt the
file. Meaning:

```
✗ Factor N            → dead end (N does not match / cannot be factored)
✗ Compute d           → impossible without p and q
✅ BRUTE FORCE 256    → WORKS, because it never needs the correct N at all —
                        it only needs m such that pow(m, e, N) == c
```

**Lesson: attack the weakness of the scheme, not the weakness of the key.**
1024-bit RSA is strong. **Unpadded RSA over a 1-byte message is not.**

---

## 4. Root Cause

Three layered mistakes:

**1. The encryption script was stored in a public directory**

`encrypt.pyc` sat in `/ftp` — handing the algorithm to the attacker (violating
Kerckhoffs's principle).

**2. Textbook RSA — no padding**

```python
# WRONG — textbook RSA
encrypted_document.write(str(pow(ord(char), e, N)) + '\n')

# RIGHT — OAEP padding + block-wise encryption
from Crypto.Cipher import PKCS1_OAEP
cipher = PKCS1_OAEP.new(public_key)
encrypted = cipher.encrypt(data)   # whole message, not per character
```

**3. Per-character encryption**

This collapses the search space to 256. Even with padding, encrypting one
character at a time is a broken pattern.

---

## 5. Remediation

**1. Remove the encryption script from the public directory**

```bash
# encrypt.pyc MUST NOT live in /ftp — move it outside the document root
```

**2. Switch to RSA with OAEP and block-wise encryption**

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

key = RSA.import_key(open('private.pem').read())
cipher = PKCS1_OAEP.new(key)
with open('announcement.md','rb') as f:
    data = f.read()
ct = cipher.encrypt(data)          # whole message, padded
```

**3. Do not use RSA for bulk data**

RSA is for wrapping keys. For files, use a hybrid scheme:

```python
# RSA wraps the AES key; AES encrypts the file
aes_key = os.urandom(32)
ct_file = AESGCM(aes_key).encrypt(nonce, data, None)
ct_key  = PKCS1_OAEP.new(rsa_pub).encrypt(aes_key)
```

**4. Disable `serve-index` directory listing on `/ftp`**

See write-up 002 §2.

**5. Audit every file in the public directory**

Remove or relocate all `.bak`, `.pyc`, `.kdbx`, `.yml`, `.json` files from it.

---

## 6. Appendix — Evidence

```
Decompile   : encrypt.pyc → textbook RSA, N=1024-bit, e=65537
Plaintext   : loot/announcement_DECRYPTED.md  (1,194 characters)
Ciphertext  : loot/announcement_encrypted.md  (369,237 bytes, 1,194 numbers)
Script      : loot2/encrypt.pyc               (573 bytes)
Reference   : GitHub juice-shop/juice-shop issue #1392
```

---

## 7. Unfinished (stated honestly)

```
✗ coupons_2013.md.bak (142 bytes, 12 lines × 10 chars)
  → Not RSA (values are not large integers)
  → Not XOR/ADD/1-byte substitution (best score 0.883, not clean)
  → Column 0 values {k,l,m,n,o,p,q} are CONSECUTIVE in ASCII → ADD component present
  → But a 1-byte shift does not produce clean coupon output
  → Would need the original decrypt.py to reverse the algorithm
  → STATUS: NOT YET SOLVED
```
