# Changelog / יומן שינויים

לפי אבני דרך, מתוך היסטוריית ה־git. אין גרסאות מתויגות; התאריך הוא המזהה. · By milestone, from the git history. There are no tagged releases; the date is the identifier.

## 2026-11-06 — הפרויקט קפוא · frozen
- README דו־לשוני (עברית + אנגלית) עם מתג שפה, תגיות, ניווט, "מה זה לא עושה", מספרים מדודים ושאלות נפוצות.
- `assets/`: ‏hero, how, before/after, catches, numbers, install (SVG), ‏`demo.gif` (הרצה אמיתית על חנות מקומית), צילום דוח לדוגמה.
- `examples/`: חנות הדגמה מקומית עם באגים מכוונים, `demo-sites.txt`, ‏`sample-report.html` (נתונים מומצאים).
- שמות ודומיינים אמיתיים הוחלפו בדוגמאות (`*.example`) ב־`sites.txt`, ברירת המחדל של `exposure_audit.py`, ‏`docs/index.html` והמדריך.
- סידור השורש (`git mv` בלבד): `scanner.py`, ‏`scanner2.py` → `archive/` · ‏`README_AUTO.md` → `guides/auto-audit.md` · ‏`report.html` → `examples/sample-report.html`.
- `CHANGELOG.md`, ‏`SECURITY.md`. אין שינוי בלוגיקה.

## 2026-10-02 — אתר `docs/` (GitHub Pages)
- דף בודק הגנת מייל (mailcheck) עם תיקון מדויק שנוצר אוטומטית ומנגנון שיתוף.
- דפי מידע: SPF, ‏DMARC, ספאם, Shopify; ‏`sitemap.xml`, ‏`robots.txt`, ‏`llms.txt`.
- דף חבילת פרומפטים ודפי מידע נלווים.

## 2026-10-01 — דוח חשיפה · exposure report
- `exposure_audit.py`: ‏106 בדיקות ב־7 תחומים, ואחר כך 116; רינדור DOM בדפדפן אמיתי לבדיקות שתלויות ב־JS.
- דוח HTML מעוצב ללקוח (`make_report.py`) ו־`auto_audit.py`: ‏PDF לכל אתר + סיכום מדורג.
- תיקוני false positives: בדיקת קישורים שבורים (נתיבי מערכת של Shopify, ‏Cloudflare, ‏mailto/tel), תוכן מעורב.
- דוחות לאתרים ספציפיים מוחרגים מהריפו (`.gitignore`).

## 2026-10-01 — סורק האיכות · the QA scanner
- `scanner.py` (HTML) → `scanner2.py` (דפדפן אמיתי) → `scanner3.py` (נתוני מוצר רשמיים, "מקור האמת").
- `run_batch.py` + `sites.txt` + workflow ‏`qa-scan` ב־GitHub Actions (רץ על push ל־main ובהפעלה ידנית).
- תיקוני false positives: מחירים נקראים רק מאלמנטי מחיר ייעודיים; דילוג על כרטיסים שאינם מוצר.
