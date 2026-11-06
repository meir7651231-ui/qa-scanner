# Changelog / יומן שינויים

נבנה מתוך היסטוריית ה־git. · Reconstructed from the git history.

## 2026-11 — סידור הריפו · repo tidy-up
- README דו־לשוני (עברית + אנגלית) עם מתג שפה, `assets/hero.svg`, `assets/how.svg`.
- `CHANGELOG.md`, `SECURITY.md`. הפרויקט מסומן **קפוא**.
- `report.html`, `sites.txt`, ברירת המחדל ב־`exposure_audit.py` והדוגמאות ב־`README_AUTO.md` / `docs/index.html`: הוחלפו בדומיינים ונתונים לדוגמה (`*.example`). אין שינוי בלוגיקה.

## 2026-10-02 — אתר `docs/` (GitHub Pages)
- דף בודק הגנת מייל (mailcheck), דפי מידע על SPF/DMARC וספאם, `llms.txt`, `robots.txt`, `sitemap.xml`.
- דף חבילת פרומפטים ודפי מידע נלווים.

## 2026-10-01 — דוח חשיפה · exposure report
- `exposure_audit.py`: 106 ואחר כך 116 בדיקות ב־7 תחומים; רינדור DOM בדפדפן אמיתי; תיקוני false positives בבדיקת קישורים.
- `make_report.py`: דוח HTML/PDF מעוצב · `auto_audit.py`: הרצה על רשימה + סיכום מדורג · `README_AUTO.md`.

## 2026-10-01 — סורק האיכות · the QA scanner
- `scanner.py` (HTML) → `scanner2.py` (דפדפן אמיתי) → `scanner3.py` (נתוני מוצר רשמיים, "מקור האמת").
- `run_batch.py` + `sites.txt` + workflow `qa-scan` ב־GitHub Actions (רץ על push ל־main ובהפעלה ידנית).
- תיקוני false positives: מחירים נקראים רק מאלמנטי מחיר ייעודיים; דילוג על כרטיסים שאינם מוצר.
