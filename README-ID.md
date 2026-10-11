# Twist — Security Research Portfolio

Portofolio writeup penetration testing. Situs statis, dibangun dari markdown.

**Isi:** halaman [portfolio & engagements](https://twist5202-ux.github.io/portfolio.html)
(log kerja: submission, temuan yang ditahan, metode) + 4 writeup dari pengujian lab
legal (OWASP Juice Shop) — SQLi, broken access control, DOM XSS, kriptografi, recon menyeluruh.

---

## Struktur

```
security-portfolio/
├── build.py                        # generator: markdown → HTML
├── PORTFOLIO-EN.md                 # sumber: halaman portfolio / engagements
├── writeups-en/                    # sumber: markdown English (yang dipublikasikan)
├── writeups/                       # arsip versi Indonesia
│   ├── 001-juice-shop-sqli.md
│   ├── 002-juice-shop-full-recon.md
│   ├── 003-juice-shop-rsa-decrypt.md
│   └── 004-juice-shop-broken-access-control-xss.md
├── site/                           # HASIL build (yang dipublikasikan)
│   ├── index.html
│   ├── portfolio.html
│   ├── assets/style.css
│   ├── writeups/*.html
│   └── .nojekyll
└── .github/workflows/pages.yml     # auto-build + deploy ke GitHub Pages
```

---

## Cara Pakai Lokal

```bash
# install
python -m pip install markdown pygments

# build
python build.py

# preview
cd site && python -m http.server 8899
# buka http://localhost:8899
```

Setiap kali markdown di `writeups-en/` atau `PORTFOLIO-EN.md` diubah, jalankan `python build.py` lagi.
Metadata judul/severity diatur di dictionary `META` dalam `build.py`.

---

## Cara Publikasi ke GitHub Pages

### Sekali setup (butuh login GitHub)

```bash
gh auth login                    # ikuti instruksi di layar

cd security-portfolio
git add -A
git commit -m "feat: portofolio writeup keamanan"

# opsi A — repo biasa (Pages aktif di /docs atau via Actions)
gh repo create security-writeups --public --source=. --push

# opsi B — repo user (langsung jadi <user>.github.io)
gh repo create <USERNAME>.github.io --public --source=. --push
```

### Aktifkan Pages

```bash
# via CLI
gh api -X POST "repos/{owner}/security-writeups/pages" \
  -f "source[branch]=main" -f "source[path]=/site" 2>/dev/null \
  || echo "atau aktifkan manual: Settings → Pages"

# atau manual di web:
#   Settings → Pages → Source: GitHub Actions
```

Workflow `.github/workflows/pages.yml` akan otomatis
build + deploy setiap push ke `main`.

### URL hasil

```
https://<USERNAME>.github.io/security-writeups/
```
atau kalau pakai repo user:
```
https://<USERNAME>.github.io/
```

---

## Alternatif Tanpa GitHub

Kalau gak mau pakai GitHub, folder `site/` bisa di-upload ke:

| Layanan | Cara |
|---|---|
| Netlify | drag & drop folder `site/` ke app.netlify.com/drop |
| Cloudflare Pages | sambungkan repo, build command `python build.py`, output `site` |
| Vercel | `vercel deploy site` |
| Surge | `npx surge site` |

Semua opsi di atas gratis dan gak perlu kartu kredit.

---

## Catatan Etika

Semua pengujian dilakukan di **lab legal** (OWASP Juice Shop — aplikasi
latihan resmi OWASP yang memang dibuat rentan). Tidak ada sistem pihak
ketiga yang diuji tanpa izin.

---

## Lisensi

Konten writeup: CC BY 4.0. Kode `build.py`: MIT.
