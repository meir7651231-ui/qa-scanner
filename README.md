# סורק איכות לאתרים

מוצא בעיות יקרות באתרים לפני שהן עולות כסף: מחירי אפס, הנחות שגויות,
קוד תבנית שדלף, קישורים ותמונות שבורים, שגיאות JavaScript ובעיות SEO.
קורא עמודים ציבוריים בלבד, כמו מבקר רגיל. לא מבצע שום פעולה באתר.

## איך מריצים (מ-GitHub, מומלץ)
1. הכנס אתרים לבדיקה לקובץ `sites.txt` (שורה לכל אתר).
2. ב-GitHub: לשונית **Actions** ← **qa-scan** ← **Run workflow**.
3. בסיום, הדוחות מופיעים בתיקיית `reports/` ובתור artifact להורדה.

## איך מריצים מהמחשב
```
pip install playwright && python -m playwright install chromium
python run_batch.py sites.txt
```
הדוחות נשמרים בתיקיית `reports/`.
