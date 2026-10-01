"""בודק איכות לפני פרסום - סורק אתר ומוצא טעויות יקרות לפני שהן עולות לאוויר.

הכלי מיועד לאתר שלך, או של לקוח ששכר אותך לבדיקה. הוא קורא רק עמודים ציבוריים,
כמו כל גולש רגיל: לא מבצע הזמנות, לא מנסה קופונים, ולא מנסה להיכנס לשום מקום.
"""
import re
import sys
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "QA-PreLaunch-Checker/1.0 (site owner audit)"}

# ביטויי מחיר נפוצים בעברית ובאנגלית: ₪ 1,299.00 / 49.90 ש"ח / $19.99
PRICE_RE = re.compile(r"(?:₪|\$|€)\s?(\d[\d,]*\.?\d*)|(\d[\d,]*\.?\d*)\s?(?:ש[\"״]?ח|שקל)")


class Issue:
    def __init__(self, sev, kind, where, detail):
        self.sev, self.kind, self.where, self.detail = sev, kind, where, detail


def _prices(text):
    out = []
    for m in PRICE_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    return out


def scan_page(url, html, issues):
    soup = BeautifulSoup(html, "lxml")

    # --- בדיקות SEO/תצוגה בסיסיות ---
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not title:
        issues.append(Issue("בינוני", "כותרת חסרה", url, "לעמוד אין <title>. פוגע בגוגל ובשיתוף."))
    elif len(title) > 70:
        issues.append(Issue("נמוך", "כותרת ארוכה", url, f"כותרת באורך {len(title)} תווים (מומלץ עד 60)."))
    desc = soup.find("meta", attrs={"name": "description"})
    if not (desc and desc.get("content", "").strip()):
        issues.append(Issue("נמוך", "תיאור חסר", url, "אין meta description. גוגל ימציא טקסט משלו."))

    # --- תמונות שבורות / בלי טקסט חלופי ---
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if not src:
            issues.append(Issue("בינוני", "תמונה בלי מקור", url, "תג <img> בלי src - תמונה ריקה."))
        if not (img.get("alt") or "").strip():
            issues.append(Issue("נמוך", "תמונה בלי alt", url, f"תמונה בלי טקסט חלופי: {src[:60]}"))

    # --- טקסטים שנשארו בטעות (placeholder) ---
    body_text = soup.get_text(" ", strip=True)
    for bad in ("lorem ipsum", "להשלים", "TODO", "טקסט לדוגמה", "placeholder", "test test"):
        if bad.lower() in body_text.lower():
            issues.append(Issue("גבוה", "טקסט זמני שנשאר", url, f'נמצא הטקסט "{bad}" - כנראה נשכח לפני פרסום.'))

    # --- מחירים: 0, נמוך חשוד, או הנחה קיצונית ---
    prices = _prices(body_text)
    for p in prices:
        if p == 0:
            issues.append(Issue("גבוה", "מחיר 0", url, "נמצא מחיר 0 - מוצר שאפשר 'לקנות' בחינם?"))
        elif 0 < p < 5:
            issues.append(Issue("גבוה", "מחיר נמוך חשוד", url, f"מחיר {p} - ייתכן שחסרה ספרה או נקודה עשרונית."))
    # הנחה קיצונית: מחיר מקורי מול מחיר מבצע באותו עמוד (מתעלמים מ-0 שכבר דווח)
    nums = sorted({p for p in prices if p >= 1})
    if len(nums) >= 2:
        low, high = nums[0], nums[-1]
        if (1 - low / high) >= 0.95:
            issues.append(Issue("גבוה", "הנחה קיצונית", url,
                                f"פער מחירים {high:g} -> {low:g} (מעל 95%). טעות בהגדרת מבצע?"))

    # --- קישורים לבדיקה (מוחזר לסורק הראשי) ---
    links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
    return links, {"title": title, "n_prices": len(prices)}


def check_url_alive(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code >= 400:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True, stream=True)
        return r.status_code
    except requests.RequestException:
        return 0


def crawl(start_url, max_pages=40, check_links=True):
    root = urlparse(start_url).netloc
    seen, queue, issues, pages = set(), deque([start_url]), [], 0
    ext_links_checked = {}
    while queue and pages < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
        except requests.RequestException as e:
            issues.append(Issue("גבוה", "עמוד לא נטען", url, str(e)[:80]))
            continue
        if r.status_code >= 400:
            issues.append(Issue("גבוה", f"שגיאה {r.status_code}", url, "עמוד מחזיר שגיאה."))
            continue
        if "text/html" not in r.headers.get("content-type", ""):
            continue
        pages += 1
        links, _ = scan_page(url, r.text, issues)
        for link in links:
            p = urlparse(link)
            if p.scheme not in ("http", "https"):
                continue
            if p.netloc == root and link not in seen:
                queue.append(link)
            elif check_links and p.netloc != root and link not in ext_links_checked:
                code = check_url_alive(link)
                ext_links_checked[link] = code
                if code == 0 or code >= 400:
                    issues.append(Issue("בינוני", "קישור שבור", url, f"{link[:70]} ({code or 'לא נענה'})"))
        time.sleep(0.4)
    return issues, pages


def report(issues, pages, url):
    order = {"גבוה": 0, "בינוני": 1, "נמוך": 2}
    issues.sort(key=lambda i: order.get(i.sev, 3))
    counts = {s: sum(1 for i in issues if i.sev == s) for s in ("גבוה", "בינוני", "נמוך")}
    print(f"\n{'=' * 60}\n  דוח בדיקת איכות: {url}\n{'=' * 60}")
    print(f"  נסרקו {pages} עמודים.")
    print(f"  נמצאו: {counts['גבוה']} חמורים, {counts['בינוני']} בינוניים, {counts['נמוך']} קלים.\n")
    icon = {"גבוה": "🔴", "בינוני": "🟡", "נמוך": "⚪"}
    for i in issues:
        print(f"  {icon[i.sev]} [{i.kind}] {i.detail}\n     בעמוד: {i.where}")
    if not issues:
        print("  ✅ לא נמצאו בעיות בולטות.")
    print()
    return counts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("שימוש: python3 scanner.py https://your-store.com")
        print("הרץ רק על אתר שלך או של לקוח ששכר אותך לבדיקה.")
        sys.exit(1)
    target = sys.argv[1]
    print(f"סורק את {target} ... (רק עמודים ציבוריים, בלי לבצע שום פעולה)")
    iss, n = crawl(target)
    report(iss, n, target)
