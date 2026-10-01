"""בונה דוח PDF מעוצב לאתר אחד מתוך ממצאי exposure_audit — כללי, לכל אתר.
שימוש מהקוד: build_report(url, findings, screenshot_path, out_pdf)
"""
import base64
import glob
import os

SEV_RANK = {"גבוה": 0, "בינוני": 1, "נמוך": 2}
SEV_UI = {"גבוה": ("crit", "חמור"), "בינוני": ("warn", "בינוני"), "נמוך": ("low", "קל")}

# הסבר בעברית לממצאים החשובים: (מה זה, מה זה אומר, מה לעשות)
INFO = {
    "SPF (מניעת זיוף)": ("רשומה שקובעת מי מורשה לשלוח מייל בשם הדומיין.",
                         "כל אחד יכול לשלוח מייל כאילו מכם, והמיילים שלכם נוטים לספאם.",
                         "להוסיף רשומת SPF אחת ב-DNS."),
    "DMARC קיים": ("שכבה שמוודאת שמייל 'מכם' הוא באמת מכם.",
                   "אין הגנה מזיופים, והמסירוּת נפגעת.",
                   "להוסיף רשומת DMARC ב-DNS."),
    "DMARC באכיפה (לא p=none)": ("DMARC קיים אך במצב ניטור בלבד.",
                                 "זיופים מזוהים אך לא נחסמים.",
                                 "להעלות את המדיניות ל-quarantine/reject."),
    "דומיין שליחה ל-Klaviyo מוגדר": ("אימות דומיין ייעודי לפלטפורמת הדיוור.",
                                     "קמפיינים בתשלום נוחתים בספאם — כסף שיווק שהולך לפח.",
                                     "לאמת את דומיין השליחה בהגדרות הדיוור + SPF/DKIM."),
    "מדיניות ללא שם עסק זר (תבנית מועתקת)": ("בדיקה אם המדיניות הועתקה מחנות אחרת.",
                                            "מופיע שם של עסק אחר — פוגע באמון ובתוקף המשפטי.",
                                            "לכתוב מדיניות עם שם ופרטי העסק הנכונים."),
    "מדיניות בעברית": ("האם הדפים המשפטיים בעברית.",
                       "דפים באנגלית בחנות ישראלית — לא עומד בדרישות ולא מובן ללקוח.",
                       "לתרגם את המדיניות לעברית."),
    "מדיניות מפנה לחוק הישראלי": ("האם המדיניות מבוססת על החוק הישראלי.",
                                  "מפנה רק לחוק זר (GDPR/CCPA) — לא רלוונטי לישראל.",
                                  "להתאים לחוק הגנת הפרטיות הישראלי."),
    "ווידג'ט נגישות מותקן": ("כפתור הנגשה לפי תקן 5568.",
                            "חשיפה לתביעת נגישות (עד 50,000 ₪ ללא הוכחת נזק).",
                            "להתקין ווידג'ט נגישות והצהרה."),
    "הצהרת נגישות (תקן 5568)": ("הצהרת נגישות שהחוק מחייב.",
                               "חשיפה משפטית בתחום הנגישות.",
                               "להוסיף הצהרת נגישות."),
    "אין קישורים פנימיים שבורים": ("בדיקת קישורים שמחזירים שגיאה.",
                                   "לקוח שלוחץ מגיע לדף שגיאה — תסכול ואובדן אמון.",
                                   "לתקן או להסיר את הקישור השבור."),
    "כותרת Strict-Transport-Security": ("הוראה להתחבר רק בהצפנה.", "פתח להתקפה על חיבור הלקוח.", "להפעיל HSTS בשרת."),
    "כותרת Content-Security-Policy": ("הגנה מהזרקת קוד.", "אין מה שיעצור הזרקת קוד זדוני.", "להגדיר CSP."),
    "לכל המוצרים יש תמונה": ("בדיקת מוצרים ללא תמונה.", "מוצר בלי תמונה כמעט לא נמכר.", "להוסיף תמונות."),
    "אין מוצר במחיר אפס": ("בדיקת מחירי אפס.", "אפשר 'לקנות' בחינם — אובדן כספי.", "לתקן את המחיר."),
}


def _find_chrome():
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome", "/opt/pw-browsers/chromium*/chrome-linux*/chrome"):
        h = sorted(glob.glob(pat))
        if h:
            return h[-1]
    return None  # במחשב שלך Playwright מוצא את הדפדפן לבד


def screenshot(url, out_png):
    """צילום מסך של דף הבית. מחזיר True אם הצליח."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    chrome = _find_chrome()
    try:
        with sync_playwright() as p:
            launch = {"args": ["--no-sandbox"]}
            if chrome:
                launch["executable_path"] = chrome
            b = p.chromium.launch(**launch)
            pg = b.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 900}).new_page()
            pg.goto(url, wait_until="domcontentloaded", timeout=35000)
            try:
                pg.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            pg.wait_for_timeout(2000)
            pg.screenshot(path=out_png)
            b.close()
        return True
    except Exception:
        return False


def _issue_card(name, sev, note):
    k, lbl = SEV_UI.get(sev, ("low", "קל"))
    info = INFO.get(name)
    ev = f"<div class='ev'>עדות: <span class='mono'>{note}</span></div>" if note else ""
    if info:
        body = (f"<div class='r'><b>מה זה:</b> {info[0]}</div>"
                f"<div class='r'><b>מה זה אומר:</b> {info[1]}</div>"
                f"<div class='r do'><b>מה לעשות:</b> {info[2]}</div>{ev}")
    else:
        body = f"<div class='r'>נקודה לשיפור.</div>{ev}"
    return (f"<div class='issue {k}'><div class='ih'><span class='nm'>{name}</span>"
            f"<span class='tg {k}'>{lbl}</span></div>{body}</div>")


def build_report(url, findings, screenshot_path, out_pdf):
    bad = [(n, sev, note) for _, _, n, ok, sev, note in findings if not ok]
    bad.sort(key=lambda x: SEV_RANK.get(x[1], 3))
    ok_n = sum(1 for f in findings if f[3])
    score = round(ok_n / len(findings) * 100) if findings else 0
    crit = [b for b in bad if b[1] == "גבוה"]
    warn = [b for b in bad if b[1] == "בינוני"]
    low = [b for b in bad if b[1] == "נמוך"]
    host = url.split("//")[-1].strip("/")
    shot = ""
    if screenshot_path and os.path.exists(screenshot_path):
        shot = base64.b64encode(open(screenshot_path, "rb").read()).decode()
    shot_html = f"<img class='shot' src='data:image/png;base64,{shot}'>" if shot else ""
    crit_html = "\n".join(_issue_card(*b) for b in crit) or "<div class='none'>אין בעיות חמורות 👍</div>"
    warn_html = "\n".join(_issue_card(*b) for b in warn)
    low_html = "".join(f"<li>{n}{(' · '+note) if note else ''}</li>" for n, _, note in low)

    HTML = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800;900&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
@page{{size:A4;margin:13mm 11mm}} *{{box-sizing:border-box}}
body{{font-family:Heebo,Arial,sans-serif;color:#15212e;margin:0;font-size:11.5px;line-height:1.6}}
.mono{{font-family:'IBM Plex Mono',monospace;direction:ltr;unicode-bidi:isolate}}
.cover{{background:linear-gradient(140deg,#0e6ba8,#0a3a52);color:#fff;border-radius:14px;padding:24px;margin-bottom:16px}}
.eye{{letter-spacing:.14em;font-size:10px;opacity:.85;font-weight:700}}
.cover h1{{font-size:24px;font-weight:900;margin:8px 0 4px}}
.site{{background:rgba(255,255,255,.18);padding:0 8px;border-radius:6px}}
.sub{{opacity:.9;margin-bottom:14px}}
.flex{{display:flex;gap:16px;align-items:center}}
.shot{{border:3px solid rgba(255,255,255,.3);border-radius:10px;width:56%;max-height:200px;object-fit:cover;object-position:top}}
.score{{text-align:center;flex:1}} .score .s{{font-size:42px;font-weight:900}} .score .o{{font-size:11px;opacity:.85}}
.chips{{display:flex;flex-direction:column;gap:5px;margin-top:10px}}
.chip{{background:rgba(255,255,255,.15);border-radius:20px;padding:3px 10px;font-size:10.5px;font-weight:600}}
h2{{font-size:15px;font-weight:800;margin:16px 0 8px;padding-bottom:5px;border-bottom:2px solid #e2e8ee}} h2.c{{color:#c0392b}}
.issue{{border:1px solid #e2e8ee;border-inline-start:4px solid #8795a2;border-radius:9px;padding:10px 13px;margin-bottom:9px;page-break-inside:avoid}}
.issue.crit{{border-inline-start-color:#c0392b;background:#fdf6f5}} .issue.warn{{border-inline-start-color:#c77d12;background:#fdfaf2}}
.ih{{display:flex;align-items:center;gap:8px;margin-bottom:5px}} .nm{{font-weight:800;font-size:13px}}
.tg{{margin-inline-start:auto;font-size:9.5px;font-weight:700;padding:2px 8px;border-radius:12px}}
.tg.crit{{background:#fbeae8;color:#c0392b}} .tg.warn{{background:#fcf3e2;color:#c77d12}} .tg.low{{background:#eef2f5;color:#7a8894}}
.r{{margin:2px 0}} .r b{{color:#5a6a78}} .r.do{{background:#e8f6ef;color:#1f6b45;border-radius:6px;padding:4px 8px;margin-top:4px}} .r.do b{{color:#1f9d6b}}
.ev{{font-size:10px;color:#8795a2;margin-top:3px}} .none{{color:#1f9d6b;font-weight:700}}
ul{{columns:2;font-size:10.5px;color:#5a6a78;padding-inline-start:16px}}
.foot{{margin-top:16px;border-top:1px solid #e2e8ee;padding-top:9px;color:#8795a2;font-size:9.5px;text-align:center}}
</style></head><body>
<div class="cover">
  <div class="eye">בדיקת אתר · דוח חשיפה</div>
  <h1>מה שאולי לא ידעת על <span class="site">{host}</span></h1>
  <div class="sub">בדקנו {len(findings)} נקודות. הדוח מסודר מהחמור לקל.</div>
  <div class="flex">{shot_html}
    <div class="score"><div class="s">{score}</div><div class="o">מתוך 100</div>
      <div class="chips"><span class="chip">🔴 חמור {len(crit)}</span>
      <span class="chip">🟡 בינוני {len(warn)}</span><span class="chip">⚪ קל {len(low)}</span>
      <span class="chip">✅ תקין {ok_n}</span></div>
    </div>
  </div>
</div>
<h2 class="c">בעיות חמורות — לטפל קודם ({len(crit)})</h2>
{crit_html}
<h2>בעיות בינוניות ({len(warn)})</h2>
{warn_html}
<h2>נקודות קטנות לשיפור ({len(low)})</h2>
<ul>{low_html}</ul>
<div class="foot">בדיקה אוטומטית של מידע ציבורי · נועד לעזור ולהגן על העסק, לא לאיים · {host} · אמתו כל ממצא לפני פנייה</div>
</body></html>"""

    html_path = out_pdf.replace(".pdf", ".html")
    open(html_path, "w", encoding="utf-8").write(HTML)
    try:
        from playwright.sync_api import sync_playwright
        chrome = _find_chrome()
        with sync_playwright() as p:
            launch = {"args": ["--no-sandbox"]}
            if chrome:
                launch["executable_path"] = chrome
            b = p.chromium.launch(**launch)
            pg = b.new_context().new_page()
            pg.goto("file://" + os.path.abspath(html_path), wait_until="networkidle", timeout=40000)
            pg.wait_for_timeout(1200)
            pg.pdf(path=out_pdf, format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            b.close()
        return out_pdf
    except Exception:
        return html_path  # לפחות HTML אם אין דפדפן
