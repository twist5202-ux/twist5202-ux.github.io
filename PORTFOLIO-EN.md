# Portfolio & Engagements

**Twist** — security researcher · HackerOne handle [`twistti`](https://hackerone.com/twistti)

Focus: **source-code audit**, **broken authorization / trust boundaries**, and web
application penetration testing. This page tracks what has actually been submitted,
what is still in progress, and what was deliberately held back — including the
findings that did not work out.

---

## Snapshot

| Metric | Value |
|---|---|
| Reports submitted | 2 (1 closed, 1 awaiting triage) |
| Reports ready to submit | 1 |
| Findings documented end-to-end | 7 |
| Public bounty programs scoped | 16 |
| Lab write-ups published | 4 |
| Bounties received | **$0** |

The last line is deliberate. A portfolio that only lists wins is a marketing page;
this one is a work log.

---

## Responsible disclosure — work in progress

Reported to public bounty programs. **Vendor names and technical detail are withheld
until each issue is fixed or publicly disclosed in line with program policy.**

| # | Area | Class | Severity | Status |
|---|---|---|---|---|
| 1 | Go serialization library (Kubernetes ecosystem) | Crafted input causes an unrecoverable runtime panic inside a public API | Medium (CVSS 3.1 4.3) | Reported — awaiting triage |
| 2 | Open-source desktop shell (QML / JavaScript) | Insufficient verification of plugin provenance: an untrusted plugin can inherit a capability reserved for first-party code and displace a built-in security component | High (CVSS 4.0 8.5) | Report complete, PoC verified — being submitted |
| 3 | AI SDK (schema validation) | Validation bypass in untrusted-schema handling | Medium (CVSS 4.0 5.3) | Submitted — **closed as Informative** |

Item 3 is listed on purpose. It was closed because the impact class (resource
exhaustion) sits on the program's *Core Ineligible Findings* list — a lesson that
changed how every later report here was scoped. See **Method** below.

---

## Held back (evaluated, not submitted)

| Area | Class | Why it was held |
|---|---|---|
| Fintech consumer API | Cross-origin `postMessage` leak (`targetOrigin: "*"`, no frame protection) | Real, but low-value data and the program was dropped before submission |
| Cloud storage buckets | Unauthenticated public listing / read | Program requires asking before reporting on unscoped subdomains; read-only, no personal data → informational at best |
| Blockchain bridge signer | Signing API reachable without authentication | Needs a working PoC before it is worth anyone's triage time |
| Smart-contract fee path | Accounting anomaly in fee handling | Audited twice and reclassified as by-design |

Holding a finding is a decision, not an accident. Every one of these has a written
reason and the evidence preserved locally.

---

## Reconnaissance workstreams

Fingerprinting and scope analysis performed across public bounty programs covering
fintech APIs, cloud infrastructure, a Linux distribution, a hardware company, and
blockchain infrastructure — subdomain enumeration, technology fingerprinting, and
policy/exclusion mapping. Output feeds the "held back" and "work in progress"
sections above; work that produced no finding is not dressed up as one.

---

## Method — how a finding becomes a report

1. **Scope first, tooling second.** Nothing is touched outside a program's written scope.
2. **Eligibility gate before writing.** Extract the program's exclusions verbatim —
   *out of scope*, *in scope but not eligible*, *open scope* clauses, and its list of
   always-rejected finding classes — then match the finding against them. A real bug
   outside the rules is a rejected report.
3. **Avoid the word that gets you rejected.** A panic triggered by one crafted input is
   an input-validation defect, not a denial of service.
4. **Check for AI / automated-scanning prohibitions** in the policy before running any
   scanner.
5. **Reputation is an asset.** Rejected or duplicate reports cost submission privileges
   on some platforms. Unverified findings are not submitted.
6. **Pre-submission checklist is a gate, not advice.** Required fields, asset in scope,
   weakness mapping, severity consistent with the CVSS vector, reproducible steps, and a
   PoC that actually runs — all green before submission.
7. **Evidence standards.** Executable PoC · **negative controls that must fail and do
   fail** · code citation with file and line numbers · raw tool output, not a retelling.
8. **Never overclaim.** Severity is calculated, and where a score is arguable the
   conservative variant is stated alongside it.

---

## Tooling

```
recon      subfinder · httpx · nuclei · katana · ffuf · dnsx · naabu · waybackurls
testing    Burp Suite · browser devtools · curl
code       Go toolchain · Node.js · Python (markdown, cvss, requests) · ripgrep · git
analysis   bytecode decompilation · RSA/crypto pitfalls · JS bundle review · CVSS 4.0 & 3.1
delivery   report writing to platform field structure · evidence packaging
```

---

## Write-ups (authorised labs)

- [SQL injection → full database compromise](writeups/001.html) — CRITICAL
- [Full reconnaissance to exploitation](writeups/002.html) — MULTI
- [Decrypting a confidential document (unpadded RSA)](writeups/003.html) — HIGH
- [Broken access control + DOM XSS](writeups/004.html) — CRITICAL

All lab testing was performed against intentionally vulnerable applications
(primarily OWASP Juice Shop) built for this purpose.

---

## Disclosure policy

- Testing only against programs with published authorisation, and only within scope.
- Requests are identified with the researcher handle (`twistti`) and the platform's
  research header where the program requires it.
- Findings are not published until the affected party has fixed the issue or the
  program's disclosure timeline has elapsed.
- Contact: see the researcher profile linked at the top of this page.
