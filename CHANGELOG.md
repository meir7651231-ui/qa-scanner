# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project has no tagged
releases, so each milestone is identified by its date. Reconstructed from the git history.

כל השינויים המשמעותיים בפרויקט. המבנה לפי Keep a Changelog; אין גרסאות מתויגות, ולכן כל אבן דרך מזוהה בתאריך.

## [Unreleased]

Nothing — the project is frozen. See [ROADMAP.md](ROADMAP.md). · אין — הפרויקט קפוא.

## [2026-11-06] — Frozen · קפוא

### Added
- Bilingual README (Hebrew `README.md`, English `README.en.md`) with a language switch, badges, anchor navigation, "Try it now", a 60-second quick start, "What it does not do", measured numbers, demo and FAQ.
- `assets/`: hero, how, before/after, catches, numbers and install SVGs, each in dark and light (`<picture>`); `demo.gif` (a real run on the local demo store); `sample-report.png`.
- `examples/`: a local demo store with planted bugs, `demo-sites.txt`, `sample-report.html` (invented data).
- `guides/ARCHITECTURE.md`, `guides/reading-the-report.md`.
- `CONTRIBUTING.md`, `ROADMAP.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`.

### Changed
- Repository root tidied with `git mv` only: `scanner.py`, `scanner2.py` → `archive/`; `README_AUTO.md` → `guides/auto-audit.md`; `report.html` → `examples/sample-report.html`.
- `requirements.txt` now lists every dependency by feature (`requests`, `beautifulsoup4`, `lxml`, `playwright`). No script or workflow reads it.
- This changelog moved to the Keep a Changelog format.

### Removed
- Real site names and domains from the files at HEAD: `sites.txt`, the `exposure_audit.py` default URL, the `docs/index.html` prefilled domain, and the guide's example now use `*.example`. The git history still contains the old files.

## [2026-10-02] — `docs/` site (GitHub Pages)

### Added
- Email-protection checker page (mailcheck), with an auto-generated exact fix and share buttons.
- Guide pages: SPF, DMARC, spam, Shopify email; `sitemap.xml`, `robots.txt`, `llms.txt`.
- Prompt-pack page and related guide pages.

## [2026-10-01] — Exposure report

### Added
- `exposure_audit.py`: 106 checks in 7 areas, later 116; DOM rendering in a real browser for JavaScript-dependent checks.
- Client-ready HTML report (`make_report.py`) and `auto_audit.py`: a PDF per site plus a ranked summary.

### Fixed
- False positives in the broken-link check (Shopify system paths, Cloudflare `/cdn-cgi`, `mailto:`/`tel:`; 404/410 only) and in the mixed-content check.

### Security
- Generated per-site reports are ignored in `.gitignore`, to keep third-party audits out of the public repository.

## [2026-10-01] — QA scanner

### Added
- `scanner.py` (HTML crawl) → `scanner2.py` (real browser) → `scanner3.py` (official product data, the "source of truth" engine).
- `run_batch.py`, `sites.txt`, and the `qa-scan` GitHub Actions workflow (on push to `main` and on manual run).

### Fixed
- Prices are read only from dedicated price elements (no more `$0.00` false positives); non-product cards (wishlist/login widgets) are skipped.
