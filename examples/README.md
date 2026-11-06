# examples/

| | |
|---|---|
| `demo-store/` | חנות מומצאת עם באגים מכוונים, להרצה מקומית בלבד · invented store with planted bugs, local only |
| `demo-sites.txt` | רשימת אתרים שמצביעה על חנות ההדגמה · site list pointing at the demo store |
| `sample-report.html` | דוח חשיפה לדוגמה, נתונים מומצאים · sample exposure report, invented data |

```bash
python -m http.server 8000 -d examples/demo-store &
python run_batch.py examples/demo-sites.txt
```

הבאגים בחנות · Planted bugs: מחיר 0 · מוצר בלי מחיר · הנחה של 95% · מחיר 0.5 · `{{ product.title }}` גלוי · קישור עם `{{ collection.handle }}` · אין meta description.
