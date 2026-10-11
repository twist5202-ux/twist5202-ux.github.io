#!/usr/bin/env python3
"""
build.py — Generate portofolio keamanan statis dari writeup markdown.

Jalankan:  python build.py
Output:    index.html + writeups/NNN.html + assets/style.css

Desain: dark theme, tanpa dependensi JS eksternal, siap GitHub Pages.
"""
import re
import html
import pathlib
import datetime

import markdown

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "writeups-en"
PORTFOLIO_SRC = ROOT / "PORTFOLIO-EN.md"
OUT = ROOT / "site"
ASSETS = OUT / "assets"

# ── Metadata per write-up (short title, severity, one-line takeaway) ──
META = {
    "001": {
        "short": "SQL Injection → Full Database Compromise",
        "target": "Juice Shop",
        "class": "Injection",
        "sev": "CRITICAL",
        "cvss": "9.8",
        "file": "001-juice-shop-sqli.md",
        "take": "Dumped 24 accounts, cracked the admin hash, and logged in as administrator.",
    },
    "002": {
        "short": "Full Reconnaissance to Exploitation",
        "target": "Juice Shop",
        "class": "Reconnaissance",
        "sev": "MULTI",
        "cvss": "1C·3H·3M·2L",
        "file": "002-juice-shop-full-recon.md",
        "take": "Nine findings, from an open directory listing to a null-byte filter bypass.",
    },
    "003": {
        "short": "Decrypting a Confidential Document (Unpadded RSA)",
        "target": "Juice Shop",
        "class": "Cryptography",
        "sev": "HIGH",
        "cvss": "7.5",
        "file": "003-juice-shop-rsa-decrypt.md",
        "take": "Decompiled the bytecode, found textbook RSA, brute-forced 256 candidates — document fully recovered.",
    },
    "004": {
        "short": "Broken Access Control + DOM XSS",
        "target": "Juice Shop",
        "class": "Access Control",
        "sev": "CRITICAL",
        "cvss": "9.1",
        "file": "004-juice-shop-broken-access-control-xss.md",
        "take": "Modified 36 products in one second without logging in, plus XSS with confirmed execution.",
    },
}

SEV_COLOR = {
    "CRITICAL": "#ff4d5e",
    "HIGH": "#ff9d3d",
    "MEDIUM": "#ffd93d",
    "LOW": "#4dd4ac",
    "MULTI": "#8b9dff",
}

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0d13; --bg2:#0f131b; --card:#131924; --line:#1e2733;
  --fg:#dfe6f0; --dim:#7d8b9e; --acc:#4dffc3; --acc2:#4d8bff;
  --code:#0b0f16; --mono:'JetBrains Mono','Cascadia Code',Consolas,monospace;
}
html{scroll-behavior:smooth}
body{
  background:var(--bg); color:var(--fg);
  font:16px/1.75 'Inter',-apple-system,'Segoe UI',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:860px;margin:0 auto;padding:0 24px}

/* ── header ── */
header.site{
  border-bottom:1px solid var(--line); padding:18px 0;
  position:sticky; top:0; background:rgba(10,13,19,.92);
  backdrop-filter:blur(12px); z-index:20;
}
header.site .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.brand{font-family:var(--mono);font-weight:700;letter-spacing:-.5px;font-size:15px}
.brand .dot{color:var(--acc)}
header.site nav{margin-left:auto;display:flex;gap:18px;font-size:14px}
header.site nav a{color:var(--dim)}
header.site nav a:hover{color:var(--acc)}

/* ── hero ── */
.hero{padding:72px 0 56px;border-bottom:1px solid var(--line)}
.hero .tag{
  display:inline-block;font-family:var(--mono);font-size:12px;letter-spacing:2px;
  text-transform:uppercase;color:var(--acc);border:1px solid var(--acc);
  border-radius:100px;padding:5px 14px;margin-bottom:22px;opacity:.85;
}
.hero h1{font-size:clamp(30px,5.2vw,46px);line-height:1.15;letter-spacing:-1.5px;font-weight:800}
.hero h1 em{font-style:normal;color:var(--acc)}
.hero p.lede{color:var(--dim);font-size:17px;margin-top:20px;max-width:640px}
.stats{display:flex;gap:34px;flex-wrap:wrap;margin-top:38px}
.stat b{display:block;font-family:var(--mono);font-size:26px;color:var(--acc);line-height:1.2}
.stat span{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:1.4px}

/* ── daftar writeup ── */
section.list{padding:56px 0}
h2.sec{
  font-size:13px;text-transform:uppercase;letter-spacing:2.4px;
  color:var(--dim);font-weight:600;margin-bottom:26px;
  display:flex;align-items:center;gap:12px;
}
h2.sec::after{content:'';flex:1;height:1px;background:var(--line)}

.card{
  display:block;background:var(--card);border:1px solid var(--line);
  border-radius:14px;padding:26px 28px;margin-bottom:16px;
  transition:border-color .18s,transform .18s;
}
.card:hover{border-color:var(--acc);transform:translateY(-2px);text-decoration:none}
.card .top{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.badge{
  font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:1px;
  padding:3px 10px;border-radius:6px;border:1px solid currentColor;
}
.card h3{font-size:19px;letter-spacing:-.4px;line-height:1.35;color:var(--fg);font-weight:700}
.card p{color:var(--dim);font-size:14.5px;margin-top:10px}
.card .meta{
  display:flex;gap:16px;margin-top:16px;font-family:var(--mono);
  font-size:12px;color:var(--dim);flex-wrap:wrap;
}
.card .meta .go{color:var(--acc);margin-left:auto}

/* ── about ── */
#about{padding:0 0 56px}
.about-box{
  background:var(--bg2);border:1px solid var(--line);border-radius:14px;
  padding:28px 30px;
}
.about-box p{color:var(--dim);margin-bottom:14px}
.about-box p:last-child{margin-bottom:0}
.about-box strong{color:var(--fg)}
.skills{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.skills span{
  font-family:var(--mono);font-size:12px;color:var(--acc2);
  border:1px solid var(--line);border-radius:6px;padding:4px 10px;
}

/* ── halaman writeup ── */
article{padding:52px 0 80px}
.crumbs{font-family:var(--mono);font-size:13px;color:var(--dim);margin-bottom:26px}
article h1{
  font-size:clamp(24px,4vw,34px);line-height:1.22;letter-spacing:-1px;
  font-weight:800;margin-bottom:26px;
}
.meta-box{
  background:var(--bg2);border:1px solid var(--line);border-left:3px solid var(--acc);
  border-radius:10px;padding:18px 22px;margin-bottom:38px;font-size:14.5px;
}
.meta-box b{color:var(--dim);font-weight:600;display:inline-block;min-width:110px}
article h2{
  font-size:22px;letter-spacing:-.6px;margin:44px 0 16px;padding-top:20px;
  border-top:1px solid var(--line);font-weight:700;
}
article h3{font-size:17px;margin:30px 0 12px;color:var(--acc2);font-weight:700}
article h4{font-size:15px;margin:22px 0 10px;color:var(--fg);font-weight:700}
article p{margin-bottom:16px}
article ul,article ol{margin:0 0 18px 24px}
article li{margin-bottom:8px}
article strong{color:#fff;font-weight:650}
article code{
  background:var(--code);border:1px solid var(--line);border-radius:5px;
  padding:2px 6px;font-family:var(--mono);font-size:.875em;color:var(--acc);
}
article pre{
  background:var(--code);border:1px solid var(--line);border-radius:11px;
  padding:18px 20px;overflow-x:auto;margin:20px 0;font-size:13.5px;line-height:1.65;
}
article pre code{background:none;border:none;padding:0;color:#c8d6e8;font-size:13.5px}
article table{
  width:100%;border-collapse:collapse;margin:22px 0;font-size:14.5px;
  display:block;overflow-x:auto;
}
article th,article td{border:1px solid var(--line);padding:10px 14px;text-align:left}
article th{background:var(--bg2);font-weight:700;font-size:13px;
  text-transform:uppercase;letter-spacing:.8px;color:var(--dim)}
article tr:nth-child(even) td{background:rgba(255,255,255,.013)}
article hr{border:none;border-top:1px solid var(--line);margin:40px 0}
article blockquote{
  border-left:3px solid var(--acc2);background:var(--bg2);padding:14px 22px;
  margin:22px 0;border-radius:0 8px 8px 0;color:var(--dim);
}

/* ── footer ── */
footer.site{
  border-top:1px solid var(--line);padding:34px 0;color:var(--dim);
  font-size:13.5px;margin-top:40px;
}
footer.site .wrap{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
footer.site .mono{font-family:var(--mono);font-size:12px;margin-left:auto}

/* ── pygments (codehilite) ── */
.highlight{background:var(--code);border:1px solid var(--line);border-radius:11px;margin:20px 0}
.highlight pre{margin:0;border:none;background:none}
.highlight .k,.highlight .kd,.highlight .kn{color:#ff79c6}
.highlight .s,.highlight .s1,.highlight .s2,.highlight .sb{color:#f1fa8c}
.highlight .c,.highlight .c1,.highlight .cm{color:#6272a4;font-style:italic}
.highlight .n,.highlight .nf,.highlight .nx{color:#8be9fd}
.highlight .m,.highlight .mi,.highlight .mf{color:#bd93f9}
.highlight .o,.highlight .ow{color:#ff79c6}
.highlight .p{color:#f8f8f2}

@media(max-width:600px){
  .hero{padding:48px 0 40px}
  .stats{gap:22px}
  .card{padding:20px 20px}
  article h2{font-size:19px}
}
@media print{
  header.site,footer.site,.crumbs{display:none}
  body{background:#fff;color:#000}
  .card,article{background:none}
}
"""


def slug_ok(t):
    return t.strip()


def md_to_html(text):
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "codehilite", "toc", "attr_list", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False, "noclose": False}},
    )
    return md.convert(text)


def page(title, body, depth=0, subtitle=""):
    """Bungkus body dalam template halaman."""
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(subtitle or title)}">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="site"><div class="wrap">
  <span class="brand">Twist<span class="dot">://</span>security</span>
  <nav>
    <a href="{up}index.html">Write-ups</a>
    <a href="{up}portfolio.html">Portfolio</a>
    <a href="{up}index.html#about">About</a>
  </nav>
</div></header>
{body}
<footer class="site"><div class="wrap">
  <span>Security research portfolio — testing performed in authorised training labs.</span>
  <span class="mono">built {datetime.date.today().isoformat()}</span>
</div></footer>
</body>
</html>
"""


def build_index(entries):
    cards = []
    for e in entries:
        c = SEV_COLOR.get(e["sev"], "#7d8b9e")
        cards.append(f"""<a class="card" href="writeups/{e['id']}.html">
  <div class="top">
    <span class="badge" style="color:{c}">{e['sev']}</span>
    <span class="badge" style="color:var(--dim)">{html.escape(e['class'])}</span>
  </div>
  <h3>{html.escape(e['short'])}</h3>
  <p>{html.escape(e['take'])}</p>
  <div class="meta">
    <span>target: {html.escape(e['target'])}</span>
    <span>cvss: {html.escape(e['cvss'])}</span>
    <span class="go">read →</span>
  </div>
</a>""")

    n_crit = sum(1 for e in entries if e["sev"] == "CRITICAL")
    body = f"""
<section class="hero"><div class="wrap">
  <span class="tag">Security Research Portfolio</span>
  <h1>Finding the gap is the job.<br><em>Explaining it is the craft.</em></h1>
  <p class="lede">A collection of penetration testing write-ups from authorised training labs.
     Every report is complete: reproduction evidence, root cause located in the code, and concrete remediation.</p>
  <div class="stats">
    <div class="stat"><b>{len(entries)}</b><span>Write-ups</span></div>
    <div class="stat"><b>{n_crit}</b><span>Critical</span></div>
    <div class="stat"><b>4</b><span>Bug Classes</span></div>
    <div class="stat"><b>100%</b><span>Verified</span></div>
  </div>
</div></section>

<section class="list" id="reports"><div class="wrap">
  <h2 class="sec">Reports</h2>
  {''.join(cards)}
</div></section>

<section id="engagements"><div class="wrap">
  <h2 class="sec">Engagements</h2>
  <a class="card" href="portfolio.html">
    <div class="top">
      <span class="badge" style="color:var(--acc)">PORTFOLIO</span>
      <span class="badge" style="color:var(--dim)">Methodology</span>
    </div>
    <h3>Portfolio &amp; Engagements</h3>
    <p>What has been submitted, what is still in progress, and what was deliberately
       held back — plus the eligibility and evidence rules every report had to pass.</p>
    <div class="meta">
      <span>disclosure items: 3</span>
      <span>held findings: 4</span>
      <span class="go">read →</span>
    </div>
  </a>
</div></section>

<section id="about"><div class="wrap">
  <h2 class="sec">About</h2>
  <div class="about-box">
    <p><strong>Twist</strong> — security researcher focused on web application
       penetration testing and vulnerability research.</p>
    <p>Every finding in this portfolio was independently discovered, reproduced, and
       documented. Reports include proof of exploitation, the root cause located in the
       application code, and a fix. Findings that could not be confirmed are stated as
       unconfirmed rather than overstated.</p>
    <p>All testing was performed against <strong>authorised training labs</strong> —
       primarily OWASP Juice Shop, an intentionally vulnerable application maintained
       by OWASP for exactly this purpose. No third-party system was tested without
       written permission.</p>
    <div class="skills">
      <span>Web App Pentesting</span>
      <span>SQL Injection</span>
      <span>Access Control</span>
      <span>XSS</span>
      <span>Cryptanalysis</span>
      <span>Reverse Engineering</span>
      <span>Reconnaissance</span>
      <span>Report Writing</span>
      <span>Python</span>
      <span>JavaScript</span>
      <span>Linux</span>
    </div>
  </div>
</div></section>
"""
    return page("Twist — Security Research Portfolio", body,
                subtitle="Penetration testing write-ups: SQL injection, broken access control, cryptography, reconnaissance.")


def build_article(eid, meta, md_text):
    c = SEV_COLOR.get(meta["sev"], "#7d8b9e")
    body_html = md_to_html(md_text)

    # drop the markdown H1 — we render our own title block
    body_html = re.sub(r"<h1[^>]*>.*?</h1>", "", body_html, count=1, flags=re.S)

    head = f"""<article><div class="wrap">
<div class="crumbs"><a href="../index.html">write-ups</a> / {eid}</div>
<h1>{html.escape(meta['short'])}</h1>
<div class="meta-box">
  <div><b>Target</b> {html.escape(meta['target'])}</div>
  <div><b>Class</b> {html.escape(meta['class'])}</div>
  <div><b>Severity</b> <span class="badge" style="color:{c}">{meta['sev']}</span> <small>cvss {html.escape(meta['cvss'])}</small></div>
  <div><b>Researcher</b> Twist</div>
</div>
{body_html}
<div class="crumbs" style="margin-top:52px"><a href="../index.html">← back to all write-ups</a></div>
</div></article>"""
    return page(f"{meta['short']} — Twist", head, depth=1)


def build_portfolio():
    """Render PORTFOLIO-EN.md -> site/portfolio.html"""
    if not PORTFOLIO_SRC.exists():
        print(f"  ! lewat: {PORTFOLIO_SRC.name} (gak ada)")
        return None
    body_html = md_to_html(PORTFOLIO_SRC.read_text(encoding="utf-8"))
    body_html = re.sub(r"<h1[^>]*>.*?</h1>", "", body_html, count=1, flags=re.S)
    body = f"""<article><div class="wrap">
<div class="crumbs"><a href="index.html">portfolio</a> / engagements</div>
<h1>Portfolio &amp; Engagements</h1>
<div class="meta-box">
  <div><b>Researcher</b> Twist &mdash; <code>twistti</code></div>
  <div><b>Focus</b> source-code audit · broken authorization · web app pentesting</div>
  <div><b>Status</b> work log &mdash; includes what was held back</div>
</div>
{body_html}
</div></article>"""
    dest = OUT / "portfolio.html"
    dest.write_text(page("Portfolio & Engagements — Twist", body,
        subtitle="Submissions, work in progress, held findings, and the method behind each report."),
        encoding="utf-8")
    print(f"  ok  {dest.relative_to(OUT)}  ({dest.stat().st_size:,} byte)")
    return dest


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    entries = []
    for eid in sorted(META):
        meta = META[eid]
        src = SRC / meta["file"]
        if not src.exists():
            print(f"  ! lewat: {src.name} (gak ada)")
            continue
        md_text = src.read_text(encoding="utf-8")
        dest = OUT / "writeups" / f"{eid}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(build_article(eid, meta, md_text), encoding="utf-8")
        meta = dict(meta, id=eid)
        entries.append(meta)
        print(f"  ok  {dest.relative_to(OUT)}  ({dest.stat().st_size:,} byte)")

    build_portfolio()

    (OUT / "index.html").write_text(build_index(entries), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"\n  index.html + {len(entries)} writeup + assets/style.css")
    print(f"  total situs: {total:,} byte")
    print(f"  output: {OUT}")


if __name__ == "__main__":
    main()
