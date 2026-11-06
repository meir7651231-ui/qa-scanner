# Security / אבטחה

**English.** qa-scanner only reads public data (web pages, HTTP headers, DNS). It sends no data of yours anywhere,
except DNS lookups through Google's public DNS-over-HTTPS (`dns.google`) in `exposure_audit.py`.
The project is frozen. To report a security issue, contact the repository owner privately
(GitHub user `meir7651231-ui`) — please don't open a public issue.

**עברית.** qa-scanner קורא מידע ציבורי בלבד (עמודי אתר, כותרות HTTP, DNS). הוא לא שולח שום מידע שלך החוצה,
מלבד שאילתות DNS דרך ה־DNS הציבורי של Google ‏(`dns.google`) ב־`exposure_audit.py`.
הפרויקט קפוא. לדיווח על בעיית אבטחה — פנייה פרטית לבעל הריפו (משתמש GitHub ‏`meir7651231-ui`), לא ב־issue ציבורי.

**שימוש אחראי · Responsible use:** מריצים רק על אתר שלך או של לקוח שביקש בדיקה. Run it only on sites you own or are hired to check.
