"""בודק איכות לפני פרסום - גרסה 2, מבוססת דפדפן אמיתי.

מה שגרסה 1 לימדה אותנו: אתרים רבים בנויים על JavaScript, והמחירים נטענים אחרי שהדפדפן
מריץ קוד. משיכת טקסט גולמי מחזירה תבניות ריקות -> המון אזעקות שווא. לכן גרסה 2:
  1. פותחת דפדפן אמיתי שמריץ את הקוד (כמו שגולש רואה).
  2. קוראת כל כרטיס מוצר *בנפרד* - שם + מחיר + מחיר מבצע משלו.
  3. מדווחת רק על מה שבאמת חשוד, בתוך אותו מוצר.

רק עמודים ציבוריים. לא מבצע הזמנות, לא מנסה קופונים, לא נכנס לשום מקום.
"""
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

CHROME = os.environ.get("QA_CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PRICE_RE = re.compile(r"(?:₪|\$|€)\s?(\d[\d,]*\.?\d*)|(\d[\d,]*\.?\d*)\s?(?:ש[\"״]?ח|שקל)")
TEMPLATE_RE = re.compile(r"\{\{.*?\}\}")  # תבנית שלא עובדה, כמו {{wishlist.id}}
# בוררים נפוצים של כרטיס מוצר במערכות הנפוצות (Magento, Shopify, WooCommerce, ועוד)
CARD_SELECTORS = [".product-item", "li.product", ".product-card", "[class*='product-item']",
                  ".grid__item", ".product"]


class Issue:
    def __init__(self, sev, kind, where, detail):
        self.sev, self.kind, self.where, self.detail = sev, kind, where, detail


def _nums(text):
    out = []
    for m in PRICE_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    return out


def analyze_product(name, text, has_buy, url, issues):
    """בדיקות ברמת מוצר בודד - בלי זליגה בין מוצרים."""
    # מחירים אמיתיים: מתעלמים מ-'0%' (דירוג) ומ'0 ביקורות'
    clean = re.sub(r"\d+%", "", text)
    clean = re.sub(r"\d+\s*(?:reviews?|ביקורות|דירוג)", "", clean, flags=re.I)
    prices = [p for p in _nums(clean)]
    label = name[:45] or url
    if TEMPLATE_RE.search(text):
        issues.append(Issue("גבוה", "תבנית שלא עובדה", url, f'קוד תבנית גלוי במוצר "{label}" - כנראה נשכח לפני פרסום.'))
    # "בלי מחיר" רק אם אין בכרטיס שום מספר שנראה כמו מחיר - שמרני, כדי לא להאשים מוצר תקין
    if has_buy and not re.search(r"\d[\d,]*\.?\d{0,2}", clean):
        issues.append(Issue("גבוה", "מוצר בלי מחיר", url, f'"{label}" ניתן להוספה לעגלה אבל אין לו מחיר גלוי.'))
    for p in prices:
        if p == 0:
            issues.append(Issue("גבוה", "מחיר 0", url, f'"{label}" מתומחר ב-0 - אפשר "לקנות" בחינם.'))
        elif 0 < p < 2:
            issues.append(Issue("בינוני", "מחיר נמוך חשוד", url, f'"{label}" מתומחר ב-{p:g} - אולי חסרה ספרה.'))
    if len(prices) >= 2:
        orig, sale = max(prices), min(prices)
        if sale > 0 and (1 - sale / orig) >= 0.90:
            issues.append(Issue("גבוה", "הנחה קיצונית", url,
                                f'"{label}": {orig:g} -> {sale:g} (מעל 90% הנחה). טעות במבצע?'))


def scan_rendered(page, url, issues):
    html = page.content()
    title = page.title()
    if not title.strip():
        issues.append(Issue("בינוני", "כותרת חסרה", url, "לעמוד אין כותרת (title)."))
    if 'name="description"' not in html and "name='description'" not in html:
        issues.append(Issue("נמוך", "תיאור חסר", url, "אין meta description לגוגל."))
    # תבניות שדלפו לכל העמוד (לא רק מוצרים)
    leaked = set(TEMPLATE_RE.findall(page.inner_text("body")))
    for t in list(leaked)[:5]:
        issues.append(Issue("גבוה", "תבנית שלא עובדה", url, f"קוד גלוי בעמוד: {t[:50]}"))

    cards = []
    for sel in CARD_SELECTORS:
        cards = page.query_selector_all(sel)
        if len(cards) >= 3:
            break
    for c in cards:
        try:
            text = c.inner_text()
        except Exception:
            continue
        n = c.query_selector("a[title], .product-item-link, [class*='name'] a, h2 a, h3 a")
        name = (n.inner_text().strip() if n else "")
        has_buy = bool(c.query_selector("button, [class*='cart' i], [class*='add' i]"))
        analyze_product(name, text, has_buy, url, issues)
    return len(cards), [a.get_attribute("href") for a in page.query_selector_all("a[href]")]


def crawl(start_url, max_pages=15):
    root = urlparse(start_url).netloc
    seen, issues, pages = set(), [], 0
    queue = [start_url]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = b.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        while queue and pages < max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                issues.append(Issue("גבוה", "עמוד לא נטען", url, str(e)[:70]))
                continue
            if resp and resp.status >= 400:
                issues.append(Issue("גבוה", f"שגיאה {resp.status}", url, "העמוד מחזיר שגיאה."))
                continue
            page.wait_for_timeout(3000)  # זמן ל-JS לרנדר מחירים
            pages += 1
            n_cards, links = scan_rendered(page, url, issues)
            for link in links or []:
                if not link:
                    continue
                full = urljoin(url, link)
                if TEMPLATE_RE.search(link):
                    issues.append(Issue("גבוה", "קישור עם קוד תבנית", url, f"קישור שבור: {link[:50]}"))
                    continue
                pu = urlparse(full)
                if pu.scheme in ("http", "https") and pu.netloc == root and full not in seen and len(seen) + len(queue) < max_pages * 3:
                    queue.append(full.split("#")[0])
            time.sleep(0.3)
        b.close()
    return issues, pages


def report(issues, pages, url):
    # נקה כפילויות
    uniq, seen = [], set()
    for i in issues:
        k = (i.kind, i.detail)
        if k not in seen:
            seen.add(k)
            uniq.append(i)
    order = {"גבוה": 0, "בינוני": 1, "נמוך": 2}
    uniq.sort(key=lambda i: order.get(i.sev, 3))
    counts = {s: sum(1 for i in uniq if i.sev == s) for s in order}
    print(f"\n{'=' * 60}\n  דוח בדיקת איכות: {url}\n{'=' * 60}")
    print(f"  נסרקו {pages} עמודים (עם דפדפן אמיתי).")
    print(f"  נמצאו: {counts['גבוה']} חמורים, {counts['בינוני']} בינוניים, {counts['נמוך']} קלים.\n")
    icon = {"גבוה": "🔴", "בינוני": "🟡", "נמוך": "⚪"}
    for i in uniq:
        print(f"  {icon[i.sev]} [{i.kind}] {i.detail}\n     {i.where}")
    if not uniq:
        print("  ✅ לא נמצאו בעיות בולטות.")
    print()
    return uniq, counts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("שימוש: python3 scanner2.py https://your-store.com")
        sys.exit(1)
    target = sys.argv[1]
    print(f"סורק את {target} בדפדפן אמיתי... (רק עמודים ציבוריים, בלי שום פעולה)")
    iss, n = crawl(target)
    report(iss, n, target)
