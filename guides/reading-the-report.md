<p align="right"><a href="#עברית">עברית</a> · <a href="#english">English</a></p>

# Reading the report · איך לקרוא את הדוח

<a id="עברית"></a>
## עברית

### רמות חומרה
| בפלט | ב־Markdown | משמעות | מה עושים |
|---|---|---|---|
| 🔴 | `[גבוה]` | עולה כסף או אמון עכשיו: מחיר 0, מוצר בלי מחיר, הנחה של 90%+, קוד תבנית גלוי, עמוד שלא נטען | לבדוק בעין היום ולתקן לפני כל דבר אחר |
| 🟡 | `[בינוני]` | כנראה טעות: מחיר מתחת ל־2, כותרת חסרה | לבדוק ולתקן בסבב הקרוב |
| ⚪ | `[נמוך]` | שיפור: ‏meta description חסר, תמונה בלי alt | כשיש זמן |
| ℹ️ | `[מידע]` | לא בעיה: למשל "אין נתוני מוצר" — אולי זה עמוד תוכן ולא חנות | לוודא שזה הגיוני |

### `reports/_SUMMARY.md` (סריקה מהירה)
1. **שורת הספירה** — כמה אתרים נבדקו, כמה חשודים, כמה תקינים, כמה לא נבדקו.
2. **🔎 חשודים** — לכל אתר רק הממצאים ה**חמורים**. מכאן מתחילים.
3. **✅ תקינים** — נקראו נתוני מוצר ולא נמצא ממצא חמור.
4. **⚠️ לא נבדקו** — לא נמצאו נתוני מוצר ואין ממצא חמור (אולי זה לא חנות), או שהסריקה נכשלה בשגיאה. זה לא "תקין".

אתר שלא נטען מופיע ב**חשודים** עם "עמוד לא נטען" או "שגיאה 404" וכדומה.

הפירוט המלא של כל אתר, כולל בינוני וקל, ב־`reports/<site>.md`.

### דוח החשיפה (`reports/<site>.pdf`)
- **הציון** = אחוז הבדיקות שעברו. נמוך יותר = יותר לתקן. זה לא ציון אבטחה.
- הכרטיסים ממוינים **מהחמור לקל**. בכל כרטיס: **מה זה**, **מה זה אומר בשבילך**, **מה לעשות**.
- בדיקות DNS (SPF, ‏DMARC) אמינות. בדיקות שתלויות ב־JavaScript (נגישות, באנר עוגיות) — לאמת בעין.
- דוגמה מלאה: [`examples/sample-report.html`](../examples/sample-report.html) (נתונים מומצאים).

### לפני שפועלים
כל ממצא הוא **חשד**. פותחים את הדף, מוודאים בעין, ורק אז מתקנים — או פונים לבעל האתר, אם ביקש את הבדיקה.

<a id="english"></a>
## English

### Severity levels
| In the output | In Markdown | Meaning | What to do |
|---|---|---|---|
| 🔴 | `[גבוה]` (high) | costs money or trust now: price 0, no price, 90%+ discount, visible template code, page not loading | check by eye today, fix first |
| 🟡 | `[בינוני]` (medium) | probably a mistake: price under 2, missing title | check and fix in the next round |
| ⚪ | `[נמוך]` (low) | improvement: missing meta description, image without alt | when there's time |
| ℹ️ | `[מידע]` (info) | not a problem: e.g. "no product data" — maybe a content page, not a store | make sure it makes sense |

The tool prints Hebrew labels; the English is given here.

### `reports/_SUMMARY.md` (quick scan)
1. **The count line** — sites checked, suspects, clean, not checked.
2. **🔎 Suspects** — for each site, only the **high** findings. Start here.
3. **✅ Clean** — product data was read and no high finding was found.
4. **⚠️ Not checked** — no product data and no high finding (maybe not a store), or the scan crashed with an error. That is not "clean".

A site that doesn't load appears under **suspects** with "page did not load" (`עמוד לא נטען`) or "error 404" and so on.

The full detail per site, including medium and low, is in `reports/<site>.md`.

### The exposure report (`reports/<site>.pdf`)
- **The score** = percent of checks passed. Lower = more to fix. It is not a security rating.
- Cards are sorted **worst-first**. Each says **what it is**, **what it means for you**, **what to do**.
- DNS checks (SPF, DMARC) are reliable. Checks that depend on JavaScript (accessibility, cookie banner) — verify by eye.
- Full example: [`examples/sample-report.html`](../examples/sample-report.html) (invented data).

### Before acting
Every finding is a **suspicion**. Open the page, verify by eye, and only then fix — or contact the site owner, if they asked for the check.
