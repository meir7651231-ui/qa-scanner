<p align="right"><a href="#עברית">עברית</a> · <a href="#english">English</a></p>

# Contributing · תרומה לפרויקט

<a id="עברית"></a>
## עברית

**הפרויקט קפוא** ([ROADMAP.md](ROADMAP.md)). אין פיתוח פעיל, ושינויי קוד לא צפויים להתקבל. עדיין מתקבלים בברכה:

- **דיווח על false positive** — ממצא שהכלי דיווח והוא לא נכון. השתמשו בתבנית "False positive".
- **דיווח על באג** — הכלי קורס או לא רץ. השתמשו בתבנית "Bug".
- **תיקוני תיעוד** — טעות ב־README או במדריכים.

### כללים
- **לא לצרף ממצאים על אתר של מישהו אחר** ב־issue ציבורי. שחזרו על אתר שלכם, או על חנות ההדגמה (`examples/demo-store`).
- **לא לסרוק אתרים בלי רשות** — גם לא כדי לבדוק תיקון.
- בעיית אבטחה — לא ב־issue ציבורי; ראו [SECURITY.md](SECURITY.md).

### לבדוק שינוי מקומית
```bash
pip install requests
python -m http.server 8000 -d examples/demo-store &
python run_batch.py examples/demo-sites.txt     # צריך להסתיים ב־exit 0, עם 1 חשוד ו־6 ממצאים חמורים
```

<a id="english"></a>
## English

**The project is frozen** ([ROADMAP.md](ROADMAP.md)). There is no active development, and code changes are not expected to be merged. Still welcome:

- **False-positive reports** — a finding the tool reported that isn't real. Use the "False positive" template.
- **Bug reports** — the tool crashes or won't run. Use the "Bug" template.
- **Documentation fixes** — a mistake in the README or the guides.

### Rules
- **Don't post findings about someone else's site** in a public issue. Reproduce on your own site, or on the demo store (`examples/demo-store`).
- **Don't scan sites without permission** — not even to test a fix.
- Security issues — not in a public issue; see [SECURITY.md](SECURITY.md).

### Checking a change locally
```bash
pip install requests
python -m http.server 8000 -d examples/demo-store &
python run_batch.py examples/demo-sites.txt     # should exit 0, with 1 suspect and 6 high findings
```
