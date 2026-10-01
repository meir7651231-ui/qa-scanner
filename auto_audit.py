"""מריץ בדיקת חשיפה מלאה על רשימת אתרים, ומכין דוח PDF לכל אחד + סיכום מדורג.

נועד לרוץ על המחשב שלך (לא בענן) — שם אין פרוקסי שחוסם, וכל הבדיקות עובדות
כולל נגישות אמינה. אפשר לתזמן אותו לרוץ לבד בלילה (ראה README).

שימוש:
    python3 auto_audit.py sites.txt

קורא דומיין בכל שורה (# = הערה), כותב ל-reports/:
    reports/<אתר>.pdf        — דוח מלא מעוצב לכל אתר
    reports/_SUMMARY.html    — טבלה מדורגת: מי הכי חשוף (לפנות אליו קודם)

⚠️  אמתו כל ממצא בעיניים לפני פנייה ללקוח. הכלי מצמצם טעויות, לא מבטל אותן.
"""
import os
import sys
import time
import traceback

import exposure_audit as ea
import make_report as mr

OUT = "reports"


def one(url):
    url = url if url.startswith("http") else "https://" + url
    a = ea.Audit(url, render=True)
    findings = a.run()
    bad = [f for f in findings if not f[3]]
    hi = [f for f in bad if f[4] == "גבוה"]
    slug = url.split("//")[-1].strip("/").replace("/", "_").replace(":", "")[:50]
    png = os.path.join(OUT, slug + ".png")
    mr.screenshot(url, png)
    pdf = os.path.join(OUT, slug + ".pdf")
    out = mr.build_report(url, findings, png if os.path.exists(png) else None, pdf)
    return {"url": url, "rendered": a.rendered, "total": len(findings),
            "high": len(hi), "bad": len(bad),
            "high_names": [f[2] for f in hi], "report": out}


def main():
    sites_file = sys.argv[1] if len(sys.argv) > 1 else "sites.txt"
    with open(sites_file, encoding="utf-8") as fh:
        sites = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for i, url in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] {url} ...", flush=True)
        try:
            r = one(url)
            flag = "⚠️ רינדור נכשל" if not r["rendered"] else ""
            print(f"    {r['high']} חמורות / {r['bad']} בעיות · דוח: {r['report']} {flag}")
            rows.append(r)
        except Exception as e:
            print(f"    שגיאה: {e}")
            traceback.print_exc()
            rows.append({"url": url, "high": -1, "bad": -1, "total": 0, "high_names": [], "report": "", "rendered": False})
        time.sleep(1)

    rows.sort(key=lambda r: -r["high"])
    cells = []
    for r in rows:
        if r["high"] < 0:
            cells.append(f"<tr><td>{r['url']}</td><td colspan=3>לא נבדק</td></tr>")
            continue
        names = "، ".join(r["high_names"][:4]) or "—"
        warn = " ⚠️" if not r["rendered"] else ""
        rep = os.path.basename(r["report"]) if r["report"] else ""
        cells.append(f"<tr class='{'hot' if r['high']>=2 else ''}'><td><b>{r['url']}</b>{warn}</td>"
                     f"<td class='n'>{r['high']}</td><td>{names}</td>"
                     f"<td><a href='{rep}'>דוח</a></td></tr>")
    html = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;color:#15212e}}
h1{{font-size:22px}} .sub{{color:#667}} table{{width:100%;border-collapse:collapse;margin-top:16px}}
th,td{{text-align:right;padding:9px 11px;border-bottom:1px solid #e2e8ee;font-size:14px}}
th{{background:#0e6ba8;color:#fff}} tr.hot{{background:#fdf6f5}} td.n{{font-weight:800;color:#c0392b;text-align:center}}
a{{color:#0e6ba8}} .note{{margin-top:14px;color:#8795a2;font-size:12px}}</style></head><body>
<h1>דוח חשיפה מרוכז</h1>
<div class="sub">{len(rows)} אתרים · מדורג לפי מספר בעיות חמורות (הכי חשוף למעלה)</div>
<table><tr><th>אתר</th><th>חמורות</th><th>הבעיות העיקריות</th><th>דוח מלא</th></tr>
{''.join(cells)}</table>
<div class="note">⚠️ אמתו כל ממצא בעיניים לפני פנייה. ⚠️ = הרינדור נכשל, בדיקות הנגישות באתר הזה לא אמינות.</div>
</body></html>"""
    with open(os.path.join(OUT, "_SUMMARY.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"\n✅ סיום. סיכום מדורג: {os.path.join(OUT, '_SUMMARY.html')}")


if __name__ == "__main__":
    main()
