# Twist — Security Research Portfolio

Penetration testing write-ups. Static site, generated from markdown.

**Contents:** a [portfolio & engagements page](https://twist5202-ux.github.io/portfolio.html)
(work log: submissions, held findings, method) plus 4 write-ups from authorised lab
testing (OWASP Juice Shop) — SQL injection, broken access control, DOM XSS,
cryptography, and full reconnaissance.

---

## Structure

```
security-portfolio/
├── build.py                        # generator: markdown → HTML
├── PORTFOLIO-EN.md                 # SOURCE: portfolio / engagements page
├── writeups-en/                    # SOURCE: English markdown
│   ├── 001-juice-shop-sqli.md
│   ├── 002-juice-shop-full-recon.md
│   ├── 003-juice-shop-rsa-decrypt.md
│   └── 004-juice-shop-broken-access-control-xss.md
├── writeups/                       # Indonesian versions (archive, not published)
├── site/                           # BUILD OUTPUT (what gets published)
│   ├── index.html
│   ├── portfolio.html
│   ├── assets/style.css
│   ├── writeups/*.html
│   └── .nojekyll
└── .github/workflows/pages.yml     # auto-build + deploy to GitHub Pages
```

---

## Local Usage

```bash
# install
python -m pip install markdown pygments

# build
python build.py

# preview
cd site && python -m http.server 8899
# open http://localhost:8899
```

Re-run `python build.py` whenever markdown in `writeups-en/` or `PORTFOLIO-EN.md` changes.
Titles, severities and class labels are configured in the `META` dictionary
inside `build.py`.

---

## Publishing to GitHub Pages

The site is already live. To redeploy after an edit:

```bash
cd security-portfolio
python build.py                     # rebuild (optional — CI rebuilds too)
git add -A
git commit -m "add write-up 005"
git push
# → Actions builds and deploys automatically (~30 seconds)
```

### Live URLs

| | |
|---|---|
| **Site (root)** | https://twist5202-ux.github.io/ |
| **Portfolio page** | https://twist5202-ux.github.io/portfolio.html |
| **Mirror** | https://twist5202-ux.github.io/security-writeups/ |
| **Repo (root)** | https://github.com/twist5202-ux/twist5202-ux.github.io |
| **Repo (mirror)** | https://github.com/twist5202-ux/security-writeups |

Both repositories deploy the same content. The root site
(`<username>.github.io`) serves at the clean URL; the project repo mirrors it.
Pushing to either triggers its own build.

```bash
git push origin main    # → https://twist5202-ux.github.io/security-writeups/
git push root main      # → https://twist5202-ux.github.io/
```

### First-time setup (if cloning fresh)

```bash
gh auth login                       # follow the on-screen instructions
gh repo create security-writeups --public --source=. --remote=origin --push
gh api -X POST "repos/twist5202-ux/security-writeups/pages" -f "build_type=workflow"
```

The workflow in `.github/workflows/pages.yml` handles build + deploy on every
push to `main`. Pages must be set to source **GitHub Actions**
(Settings → Pages → Source).

---

## Alternative Hosting

The `site/` folder is plain static HTML — it works anywhere:

| Service | How |
|---|---|
| Netlify | drag & drop the `site/` folder onto app.netlify.com/drop |
| Cloudflare Pages | connect the repo, build command `python build.py`, output dir `site` |
| Vercel | `vercel deploy site` |
| Surge | `npx surge site` |

All of the above are free and need no credit card.

---

## Adding a New Write-up

1. Write the markdown file in `writeups-en/` (e.g. `005-jwt-manipulation.md`)
2. Add an entry to the `META` dictionary in `build.py`:

```python
"005": {
    "short": "JWT Algorithm Confusion → Privilege Escalation",
    "target": "Juice Shop",
    "class": "Authentication",
    "sev": "HIGH",
    "cvss": "8.1",
    "file": "005-jwt-manipulation.md",
    "take": "One-line summary shown on the index card.",
},
```

3. `python build.py` → `git add -A && git commit -m "add 005" && git push`

---

## Ethics Note

Every test documented here was performed against an **authorised training lab**
— primarily OWASP Juice Shop, an intentionally vulnerable application that OWASP
maintains for exactly this purpose. No third-party system was tested without
written permission.

Findings that could not be confirmed are labelled as unconfirmed in the reports
rather than overstated.

---

## Licence

Write-up content: CC BY 4.0. `build.py`: MIT.
