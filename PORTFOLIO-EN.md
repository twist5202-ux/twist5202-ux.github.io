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
| Reports submitted | 5 (3 closed, 1 awaiting triage, 1 Immunefi) |
| Reports ready to submit | 0 |
| Findings documented end-to-end | 7 |
| Public bounty programs scoped | 16 |
| Lab write-ups published | 4 |
| Upstream fix pull requests | 1 open |
| On-chain research published | 1 (dev.to, submitted to Taskmarket) |
| Smart-contract reports submitted | 1 (Immunefi, Avail Bridge) |
| Bounties received | **$0** |

The last line is deliberate. A portfolio that only lists wins is a marketing page;
this one is a work log.

---

## Responsible disclosure — work in progress

Reported to public bounty programs. **Vendor names and technical detail are withheld
until each issue is fixed or publicly disclosed in line with program policy.**

| # | Area | Class | Severity | Status |
|---|---|---|---|---|
| 1 | Go serialization library (cloud-native tooling) | Crafted input causes an unrecoverable runtime panic inside a public API | Medium (CVSS 3.1 4.3) | Reported — awaiting triage |
| 2 | Open-source desktop shell — omarchy (QML / JavaScript) | Insufficient verification of plugin provenance: an untrusted plugin can inherit a capability reserved for first-party code and displace a built-in security component | High (CVSS 4.0 8.5) | Submitted — **closed as Not Applicable**: "input comes from the same user who runs the code, so no security boundary was crossed" — accepted as hardening. Fix submitted upstream: [omarchy PR #14966](https://github.com/omacom/omarchy/pull/14966), open |
| 3 | AI SDK (schema validation) | Validation bypass in untrusted-schema handling | Medium (CVSS 4.0 5.3) | Submitted — **closed as Informative** |

Both closes are listed on purpose, and both changed how later work here is scoped:

- **Item 3** was closed because the impact class (resource exhaustion) sits on the
  program's *Core Ineligible Findings* list.
- **Item 2** was closed because the attacker and the victim are the same principal:
  the plugin is code the user chooses to install, at the user's own privilege level.
  By that trust model the finding is hardening, not a boundary crossing — the vendor
  invited a pull request instead, which is the correct channel for it — [PR #14966](https://github.com/omacom/omarchy/pull/14966).

See **Method** below.

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
9. **Name the attacker and the victim first.** If the "victim" is the same principal
   who voluntarily installs the attacker's code at the same privilege level, an
   escalation of what that code can reach is hardening, not a vulnerability — it
   belongs in a pull request, not a report. Real boundary crossings need an
   unauthorised attacker (network-facing, missing authorization) or a different
   victim (another user, tenant, or server).

---

## Tooling

```
recon      subfinder · httpx · nuclei · katana · ffuf · dnsx · naabu · waybackurls
testing    Burp Suite · browser devtools · curl
code       Go toolchain · Node.js · Python (markdown, cvss, requests) · ripgrep · git
mobile     apktool · smali review · AndroidManifest analysis · assetlinks.json verification
contracts  Foundry · solc · Sourcify · Etherscan/BscScan API · DexScreener
analysis   bytecode decompilation · RSA/crypto pitfalls · JS bundle review · CVSS 4.0 & 3.1
onchain    baw CLI (Binance Agentic Wallet) · taskmarket CLI · eth_call / eth_estimateGas
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
---

## Mobile application security — eero (Amazon)

**Report:** HackerOne #4141935 · **Status:** closed as duplicate of #3665834
**Assets:** `com.eero.android` (Android) + `app.eero.com`

The eero Android app completes its SSO login by handing the user's real session
token to the app over the custom URI scheme `eero://jumpto/auth?token=<TOKEN>`.
The receiving activity is `exported="true"` and routes the `/auth` path to
`DeepLinkScreen$SsoResult` with no scheme or host validation — the token is read
straight from the URI and written into `SecureTokenStorage`, after which the
session is treated as authenticated.

Two attack directions from one root cause:

- **Direction A — token theft to account takeover.** Any installed app can declare
  the same `eero://jumpto` scheme and compete to receive the victim's real session
  token during a legitimate login. An attacker holding it controls the victim's
  home-network administration: network settings, connected devices, admins, and
  the Wi-Fi PSK.
- **Direction B — token injection to session fixation.** Because
  `V3DeepLinkActivity` is exported, another app can start it directly with an
  explicit component, bypassing intent-filter matching entirely. The victim's app
  is switched into an attacker-controlled session, and eero's core setup flow then
  has the victim type their home Wi-Fi password into the attacker's account.

**Key analytical finding:** the developers demonstrably know how to bind a
deep-link route to a verified host — `RespondNetworkInvite$Companion.canHandle()`
checks host *and* path exactly against `applinks.eero.com`. The authentication
route is simply not covered by that protection. This is a coverage gap, not a
missing capability, which is why it was argued as worth a Critical assessment.

**Evidence gathered (all public, passive, read-only):**

- `https://app.eero.com/auth/index.html` — HTTP 200, 1,875 bytes; its complete
  client-side logic builds the `eero://` redirect verbatim
- `https://app.eero.com/.well-known/assetlinks.json` — HTTP 200, 1,197 bytes;
  published and correctly binding `com.eero.android` to the release signing
  certificate, but governing only `https` links
- Full exported-component audit of the APK (12 components) — everything else
  clean, documented so the report could not be misread as claiming more than was
  found

**Report structure:** root cause with exact smali locations, live transport proof,
both attack directions with runnable PoC snippets, why the obvious mitigations do
not apply, severity assessment with the argument against it stated plainly, honest
limitations, and six specific remediation steps.

**Outcome:** closed as a duplicate — another researcher reported the same
underlying issue first.

### Exported-component audit — eero Android

| Component | Exported | Permission | Verdict |
|---|---|---|---|
| `SplashActivity` | true | — | launcher, expected |
| **`V3DeepLinkActivity`** | **true** | **—** | **subject of the report** |
| `PreviewActivity` (Compose tooling) | true | — | no-op |
| `GRDDNSProxy` (Guardian) | true | `BIND_VPN_SERVICE` | guarded |
| `RevocationBoundService` (GMS) | true | `REVOCATION_NOTIFICATION` | guarded |
| `SystemJobService` (WorkManager) | true | `BIND_JOB_SERVICE` | guarded |
| `FirebaseInstanceIdReceiver` | true | `c2dm.permission.SEND` | guarded |
| `DiagnosticsReceiver` / `ProfileInstallReceiver` | true | `DUMP` | guarded |
| all 6 providers | false | — | clean |

Also checked and clean: `allowBackup="false"`; no `debuggable`; no
`usesCleartextTraffic` and no `networkSecurityConfig` override; no
`getExternalStoragePublicDirectory`, `/sdcard`, `MODE_WORLD_READABLE` or
`DIRECTORY_DOWNLOADS` in app code; no hardcoded Google/Stripe/AWS keys or JWTs;
FileProvider paths all non-exported; VPN-toggle shortcuts correctly
`android:exported="false"`.

**Not claimed:** the URI-based network-invitation flow is properly protected
(`canHandle()` requires exact verified host *and* path before the invite `code`
is read); `AllowedHosts.isAllowedUrl()` is sound (real URL parser + `//` guard) —
a bypass was looked for and none was found, so none was reported.

---

## On-chain research and writing

### Kintara ($KINS) analysis — Taskmarket TSK-G0YHWMXN

Published: <https://dev.to/twist5202ux/kintara-kins-a-browser-mmo-where-the-token-is-a-door-not-a-currency-2j65>
Status: submitted (5 USDC escrowed, pending review)

1,430-word analysis of a browser-based isometric MMO on Solana, arguing that its
most interesting design decision is that $KINS is a door, not a currency — Gold is
the in-game soft currency, while $KINS gates progression and access (free to Total
Level 10, then 1,000 $KINS held to continue, 24 hours held to unlock Marketplace
listings, trading, wagers, guild-bank deposits and referral earnings).

Every number carries a source and an observation date:

| Metric | Value | Source |
|---|---|---|
| Price | $0.0003078 | DexScreener, PumpSwap pair `F42tZnKPavq1VUcrL6ymhc6YqVpt84fWwgzbNTv2wb3W`, 25 Oct 2026 |
| Liquidity | ~$90,144 | same |
| Market cap / FDV | ~$305,259 | same |
| 24h volume | ~$34,356 | same |
| 24h change | -3.12% | same |
| Players | ~460 online / ~69,530 total | kintara.com live counter, 25 Oct 2026 |
| Monthly active | ~20,540 | Crypto Briefing |
| Token gate | 1,000 $KINS + 24h hold | kintara.wiki/wiki/$KINS |

The article states one promising aspect (the product is real, the wallet is
non-custodial via Privy, and the 24-hour hold is cleaner sybil resistance than
most GameFi staking contracts) and one meaningful risk taken from Kintara's own
wiki (team not publicly identified, no public smart contract audit, treasury
governance not detailed). No roadmap was found, so none was claimed.

The accompanying infographic (1200x675) was produced with the official $KINS logo,
with every figure matching the cited sources.

---

## Web3 and agent tooling

Hands-on with the agentic-commerce stack:

- **Binance Agentic Wallet** (`baw` CLI v1.12.0) — connected an Agentic Wallet,
  verified an `.ai` Agent ID on-chain, and executed free NFT mints through
  `contract-call preview` then `execute`, always simulating first and checking
  `simulationCode`, `riskDetails` and `allowanceChanges` before sending
- **Taskmarket** — ran a worker wallet on Base (agent ID 1130728), discovered open
  tasks, and submitted artifacts through the first-party CLI
- **On-chain NFT minting** — verified contract state (`mintStatus`, `quote`,
  `hasAgentId`, `mintedBy`) via `eth_call` before every mint; resolved function
  selectors from bytecode when no ABI was available; simulated with
  `eth_call` / `eth_estimateGas` before broadcasting
- **Internet Court skill** — reviewed the ERC-7710 / x402 / escrow / adjudication
  stack and its security-scan findings before use

---

## Smart contract security — Avail Bridge (Immunefi)

**Report:** Immunefi submission, Avail Bridge smart contracts · **Status:** submitted
**Severity claimed:** Critical

`SP1Vector.commitHeaderRange` uses `&&` instead of `||` in trusted-header
validation, allowing an approved relayer to commit an attacker-controlled
`dataRootCommitment` and forge arbitrary bridge messages.

**Contracts involved (Ethereum mainnet):**

| Contract | Address |
|---|---|
| VectorX proxy | `0x02993cdc11213985b9b13224f3af289f03bf298d` |
| VectorX implementation (`SP1Vector` v2.0.0) | `0xc6217f1549Cab6f22ac4AC56d42e6C248731a33D` |
| Bridge proxy | `0x054fd961708D8E2B9c10a63F6157c74458889F0a` |
| Bridge implementation (`AvailBridgeV1`) | `0x737539737b44493F65c17eAfE165197b6410d254` |

Deployed state at time of report: `latestBlock = 3616640`,
`latestAuthoritySetId = 914`, `headerRangeCommitmentTreeSize = 2048`,
`checkRelayer = true`, `frozen = false`.

The submission includes a Foundry proof-of-concept (`poc-avail/`) that reproduces
the forged commitment against the deployed bytecode, plus the argument for why the
finding is not "privileged address only" — the relayer role is the intended
attacker model for a bridge, and the bug converts a trusted relayer into an
arbitrary-message forger.

---

## Market research — bounty landscape (20 Oct 2026)

Documented so the numbers behind later prioritisation decisions are reproducible.
Run with the `gh` CLI (account `twist5202-ux`, scopes `repo`/`gist`/`workflow`/
`read:org`) against public platform APIs. All figures come from real queries, not
estimates.

**Headline finding: the open-source bounty market is currently empty.** Of ~561
issues labelled `bounty`, none were claimable. The three large audit platforms had
no active contests.

Evidence per candidate:

- **`AsherKasper/bounty-census`** (independent verifier) — 561 open issues,
  advertised total $1,142,625. After filtering (active repo, <25 bounties, ≥25
  stars, <25 comments): **0 bounties, $0**. 99% of the money concentrated in 3
  repos with abnormal profiles. Algora pays via comment, so labels and issues stay
  open forever; 9 of its 14 prior recommendations were already paid in 2024.
- **`auscaster/frantic-board`** — 592 stars, MIT, "HELP WANTED: AI AGENTS". Real,
  public ledger, x402 payouts (crypto, no bank). But the rates are $1, $1, $1, $2
  per task with 100 slots. Total moved in 126 days: $1,332.35 across 1,577 agents
  = **$0.85 per agent**. Only remaining item of value: #97 at $10, 5 slots.
  Verdict: research experiment, not an income source.

This is why the work moved toward escrowed task marketplaces and bounty programs
with verified payouts rather than open-issue bounty labels.
