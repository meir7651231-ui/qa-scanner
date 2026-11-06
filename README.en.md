<p align="right"><a href="README.md">עברית</a> · <b>English</b></p>

<p align="center"><img src="assets/hero.svg" alt="qa-scanner: finds the expensive mistakes on a website before customers do" width="100%"></p>

<p align="center">
<img src="https://img.shields.io/badge/status-frozen-8a9aa0?style=for-the-badge&labelColor=0b1018" alt="status: frozen">
<img src="https://img.shields.io/badge/python-3.9%2B-2ee6c5?style=for-the-badge&labelColor=0b1018" alt="Python 3.9+">
<img src="https://img.shields.io/badge/reads-public%20pages%20only-ffb84d?style=for-the-badge&labelColor=0b1018" alt="reads public pages only">
<a href="https://github.com/meir7651231-ui/qa-scanner/actions/workflows/scan.yml"><img src="https://github.com/meir7651231-ui/qa-scanner/actions/workflows/scan.yml/badge.svg?branch=main" alt="qa-scan CI"></a>
</p>

<h3 align="center">Finds the expensive mistakes on a website — before they cost money.</h3>

<p align="center"><a href="#the-problem"><b>The problem</b></a> · <a href="#how-it-works">How it works</a> · <a href="#what-it-checks">What it checks</a> · <a href="#whats-inside">What's inside</a> · <a href="#running-it">Running it</a> · <a href="#faq">FAQ</a> · <a href="#status">Status</a></p>

---

> **This project is frozen.** The code works and stays as it is; no changes are planned. See [Status](#status).

## The problem

On a website or online store a small mistake costs real money: a product shown at $0.00, a wrong discount, template code
like `{{ product.title }}` visible to buyers, a broken image, a link to a 404, or a domain anyone can send spoofed email from.
Usually you find out only after a customer complains — or buys at the wrong price.

**qa-scanner walks the site like an ordinary visitor and finds it first.**

## How it works

<p align="center"><img src="assets/how.svg" alt="sites.txt, read public pages, run checks, reports folder" width="100%"></p>

1. **List** — put sites in `sites.txt`, one per line (`#` = comment).
2. **Read** — only public data: HTML, the store's official product data, HTTP headers and DNS. It never clicks, orders, tries coupons or logs in.
3. **Check** — prices, content, links, images, SEO and email security.
4. **Report** — a report per site and a summary ranked worst-first, in `reports/`.

## What it checks

| Area | Examples |
|---|---|
| Prices | zero price, suspiciously low price, extreme discount (over 90%), product with no price |
| Content | template code shown to visitors (`{{ }}`), placeholder text left before launch |
| Links & images | broken links, images that don't load |
| Real browser | checks what a visitor sees after JavaScript runs (`scanner2.py`) |
| SEO | missing or long title, missing description, images without alt |
| Email security | SPF · DMARC — straight from DNS |
| Full exposure report | 100+ checks in 7 areas: regulation, accessibility, email, site security, SEO, performance, trust — see [README_AUTO.md](README_AUTO.md) (Hebrew) |

> ⚠️ The tool reduces mistakes, it doesn't remove them. **Verify every finding by eye** before acting on it.
> Run it only on your own site, or a client's who asked for the check.

## What's inside

| File | What it does |
|---|---|
| `scanner3.py` | "Source of truth" engine: reads the store's official product data (e.g. Shopify) and finds wrong prices and content |
| `run_batch.py` | runs `scanner3` over `sites.txt` and writes Markdown reports to `reports/` |
| `scanner.py` | first version: crawls HTML pages (requests + BeautifulSoup) |
| `scanner2.py` | same idea in a real browser (Playwright) — also sees content loaded by JavaScript |
| `exposure_audit.py` | exposure report: 100+ checks on one site |
| `make_report.py` | turns exposure findings into a styled HTML/PDF report |
| `auto_audit.py` | runs the exposure report over a list: a PDF per site + a ranked summary |
| `.github/workflows/scan.yml` | CI: runs `run_batch.py` on GitHub Actions and uploads the reports as an artifact |
| `docs/` | a separate GitHub Pages site (guides on email security and prompts) |
| `assets/` | images for this README |

## Running it

### From GitHub (nothing to install)
1. Edit `sites.txt`.
2. **Actions** tab → **qa-scan** → **Run workflow**.
3. When it finishes, download the reports from the `qa-reports` artifact.

### Locally — quick scan
```bash
pip install requests beautifulsoup4 lxml
python run_batch.py sites.txt                   # whole list → reports/_SUMMARY.md + one report per site
python scanner3.py https://your-store.example   # one site, output to the screen
```

### Locally — full exposure report
```bash
python exposure_audit.py https://your-site.example --no-render   # no browser
pip install playwright && python -m playwright install chromium
python auto_audit.py sites.txt          # a PDF per site + reports/_SUMMARY.html
```
Full instructions and nightly scheduling: [README_AUTO.md](README_AUTO.md) (Hebrew).

## FAQ

<details><summary><b>Does it change anything on the site?</b></summary>

No. It reads public pages and data only, like any visitor. It places no orders, submits no forms and never logs in.
</details>

<details><summary><b>Why does a cloud run sometimes find nothing?</b></summary>

Some cloud environments have a proxy that blocks browsing to outside sites. On GitHub Actions and on your own machine it works.
</details>

<details><summary><b>Which scanner should I run?</b></summary>

For stores — `run_batch.py` (it uses `scanner3`). For a full report on one site — `exposure_audit.py` / `auto_audit.py`.
`scanner.py` and `scanner2.py` are earlier versions kept for reference.
</details>

<details><summary><b>Can I trust every finding?</b></summary>

The DNS checks (SPF/DMARC) are reliable. Checks that depend on JavaScript (accessibility, cookie banner) need a look by eye.
</details>

## Status

**Frozen (November 2026).** The code stays as it is, CI on `main` passes, and there is no active development.
History: [CHANGELOG.md](CHANGELOG.md) · Reporting a security issue: [SECURITY.md](SECURITY.md).
