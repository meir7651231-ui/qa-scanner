"""מריץ את סורק האיכות על רשימת אתרים ומפיק דוח Markdown לכל אחד.

נועד לרוץ על GitHub Actions, שם יש אינטרנט רגיל בלי פרוקסי חוסם.
קורא כתובות מ-sites.txt (שורה לכל אתר), כותב דוחות לתיקיית reports/.
"""
import os
import re
import sys
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

# ב-GitHub Actions הדפדפן מותקן ע"י הסטפ "playwright install chromium" ונמצא אוטומטית
CHROME = os.environ.get("QA_CHROME") or None
TPL = re.compile(r"\{\{.+?\}\}")
PRICE_RE = re.compile(r"(?:₪|\$|€)\s?(\d[\d,]*\.?\d*)|(\d[\d,]*\.?\d*)\s?(?:ש[\"״]?ח|שקל)")
CARD_SELECTORS = [".product-item", "li.product", ".product-card", "[class*='product-item']",
                  ".grid__item", ".product", "[class*='product-card']"]
IGNORE_HOSTS = ()  # אפשר להוסיף דומיינים של ספקי צד-שלישי להתעלמות


def nums(text):
    out = []
    for m in PRICE_RE.finditer(re.sub(r"\d+%", "", text)):
        raw = m.group(1) or m.group(2)
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    return out


def scan_site(page, url):
    """מחזיר (findings, info). findings = [(severity, kind, detail)]."""
    f = []
    console_errors, failed = [], []
    page.on("pageerror", lambda e: console_errors.append(str(e)[:100]))
    page.on("requestfailed", lambda r: failed.append(r.url))
    resp = page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(5000)
    if resp and resp.status >= 400:
        f.append(("גבוה", f"שגיאה {resp.status}", f"העמוד הראשי מחזיר שגיאה {resp.status}."))
        return f, {}

    title = page.title()
    html = page.content()
    body = page.inner_text("body")

    # 1. קוד תבנית שדלף - אות חזק מאוד, כמעט בלי אזעקות שווא
    for t in list(set(TPL.findall(body)))[:5]:
        f.append(("גבוה", "קוד שלא עובד", f"מופיע למבקר טקסט גולמי של קוד: {t[:50]}"))
    # 2. קישורים עם קוד תבנית שדלף (קישורים שבורים ודאית)
    for a in page.query_selector_all("a[href]"):
        h = a.get_attribute("href") or ""
        if TPL.search(h):
            f.append(("גבוה", "קישור שבור", f"קישור מכיל קוד לא עובד: {h[:50]}"))
            break
    # 3. קריסות JavaScript אמיתיות (לא תקלות רשת)
    for e in console_errors[:4]:
        f.append(("גבוה", "קריסת JavaScript", f"האתר זורק שגיאה בטעינה: {e}"))
    # 4. תמונות שבורות (רק של האתר עצמו, לא ספקי צד-שלישי)
    broken = page.eval_on_selector_all(
        "img", "els=>els.filter(e=>e.complete&&e.naturalWidth===0).map(e=>e.currentSrc||e.src)")
    host = re.sub(r"^www\.", "", url.split("/")[2])
    own = [b for b in broken if host in b]
    if own:
        f.append(("בינוני", "תמונה שבורה", f"{len(own)} תמונות של האתר לא נטענות (לדוגמה: {own[0][:50]})"))
    # 5. SEO בסיסי
    if not title.strip():
        f.append(("בינוני", "כותרת חסרה", "לעמוד אין כותרת (title) - פוגע בגוגל."))
    if 'name="description"' not in html and "name='description'" not in html:
        f.append(("נמוך", "תיאור חסר", "אין meta description - גוגל ימציא טקסט."))

    # 6. בדיקת מוצרים (אם נמצאו כרטיסים)
    cards = []
    for sel in CARD_SELECTORS:
        cards = page.query_selector_all(sel)
        if len(cards) >= 3:
            break
    checked = 0
    for c in cards:
        try:
            text = c.inner_text()
        except Exception:
            continue
        checked += 1
        n_el = c.query_selector("a[title], .product-item-link, h2 a, h3 a, [class*='name'] a")
        name = (n_el.inner_text().strip()[:40] if n_el else "")
        has_buy = bool(c.query_selector("button, [class*='cart' i], [class*='add' i]"))
        clean = re.sub(r"\d+\s*(?:reviews?|ביקורות)", "", text, flags=re.I)
        ps = nums(clean)
        for p in ps:
            if p == 0:
                f.append(("גבוה", "מחיר אפס", f'"{name}" מתומחר ב-0.'))
            elif 0 < p < 2:
                f.append(("בינוני", "מחיר נמוך חשוד", f'"{name}" מתומחר ב-{p:g}.'))
        if len(ps) >= 2 and min(ps) > 0 and (1 - min(ps) / max(ps)) >= 0.90:
            f.append(("גבוה", "הנחה קיצונית", f'"{name}": {max(ps):g} -> {min(ps):g} (מעל 90%).'))
        if has_buy and not re.search(r"\d", clean):
            f.append(("גבוה", "מוצר בלי מחיר", f'"{name}" ניתן לקנייה בלי מחיר גלוי.'))
    return f, {"title": title, "products_checked": checked}


def to_markdown(url, findings, info):
    # הסר כפילויות
    seen, uniq = set(), []
    for x in findings:
        if x[1:] not in seen:
            seen.add(x[1:])
            uniq.append(x)
    order = {"גבוה": 0, "בינוני": 1, "נמוך": 2}
    uniq.sort(key=lambda x: order.get(x[0], 3))
    c = {s: sum(1 for x in uniq if x[0] == s) for s in order}
    icon = {"גבוה": "🔴", "בינוני": "🟡", "נמוך": "⚪"}
    out = [f"# דוח בדיקת איכות\n", f"**אתר:** {url}  ",
           f"**נבדק:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
           f"**מוצרים שנבדקו:** {info.get('products_checked', 0)}\n",
           f"**סיכום:** {c['גבוה']} חמורים · {c['בינוני']} בינוניים · {c['נמוך']} קלים\n", "---\n"]
    if not uniq:
        out.append("✅ לא נמצאו בעיות בולטות בעמוד הראשי.\n")
    for sev, kind, detail in uniq:
        out.append(f"- {icon[sev]} **{kind}** — {detail}")
    out.append("\n---\n*נבדקו עמודים ציבוריים בלבד, כפי שמבקר רגיל רואה. לא בוצעה שום פעולה באתר.*")
    return "\n".join(out)


def main():
    sites_file = sys.argv[1] if len(sys.argv) > 1 else "sites.txt"
    with open(sites_file, encoding="utf-8") as fh:
        sites = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    os.makedirs("reports", exist_ok=True)
    summary = ["# סיכום סריקה\n", f"נבדקו {len(sites)} אתרים ב-{datetime.now(timezone.utc):%Y-%m-%d}\n"]
    with sync_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if CHROME:
            kw["executable_path"] = CHROME
        b = p.chromium.launch(**kw)
        for url in sites:
            print(f"scanning {url} ...")
            ctx = b.new_context(ignore_https_errors=True)
            page = ctx.new_page()
            try:
                findings, info = scan_site(page, url)
            except Exception as e:
                findings, info = [("גבוה", "עמוד לא נטען", str(e)[:80])], {}
            md = to_markdown(url, findings, info)
            slug = re.sub(r"[^a-z0-9]+", "-", url.split("//")[-1].lower()).strip("-")[:50]
            with open(f"reports/{slug}.md", "w", encoding="utf-8") as fh:
                fh.write(md)
            hi = sum(1 for x in findings if x[0] == "גבוה")
            summary.append(f"- **{url}** — {hi} בעיות חמורות → `reports/{slug}.md`")
            ctx.close()
            time.sleep(1)
        b.close()
    with open("reports/_summary.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary))
    print("\n".join(summary))


if __name__ == "__main__":
    main()
